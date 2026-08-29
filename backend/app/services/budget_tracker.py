import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.database import (
    create_budget_entry as db_create_entry,
    create_budget_limit as db_create_limit,
    delete_budget_entry as db_delete_entry,
    delete_budget_limit as db_delete_limit,
    get_budget_entries as db_get_entries,
    get_budget_limits as db_get_limits,
    get_db,
    update_budget_limit as db_update_limit,
)
from app.models import (
    BudgetAlternative,
    BudgetCheckRequest,
    BudgetCheckResult,
    BudgetEntry,
    BudgetLimit,
    BudgetPeriod,
    SpendingSummary,
)


class BudgetTracker:
    ALERT_THRESHOLD_WARN = 0.75
    ALERT_THRESHOLD_CRITICAL = 0.90

    def _get_cutoff(self, period: BudgetPeriod) -> str:
        now = datetime.now()
        if period == BudgetPeriod.daily:
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.weekly:
            cutoff = now - timedelta(days=now.weekday())
            cutoff = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return cutoff.isoformat()

    def track_entry(self, user_id: str, product_id: str, product_name: str,
                    category: str, amount: float, quantity: int = 1,
                    note: Optional[str] = None) -> BudgetEntry:
        entry = BudgetEntry(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            product_id=product_id,
            product_name=product_name,
            category=category,
            amount=amount,
            quantity=quantity,
            timestamp=datetime.now().isoformat(),
            note=note,
        )
        with get_db() as conn:
            db_create_entry(conn, entry)
        return entry

    def get_summary(self, user_id: str, period: BudgetPeriod) -> SpendingSummary:
        cutoff = self._get_cutoff(period)
        with get_db() as conn:
            entries = db_get_entries(conn, user_id, since=cutoff)
            limits = db_get_limits(conn, user_id)

        total_spent = sum(e.amount * e.quantity for e in entries)
        category_breakdown: dict[str, float] = {}
        for e in entries:
            cat_total = e.amount * e.quantity
            category_breakdown[e.category] = round(category_breakdown.get(e.category, 0) + cat_total, 2)

        if period == BudgetPeriod.daily:
            days = 1
        elif period == BudgetPeriod.weekly:
            days = 7
        else:
            days = 30
        daily_average = round(total_spent / days, 2)

        alerts: list[str] = []
        applicable_limits = [l for l in limits if l.category is None]
        for limit in applicable_limits:
            pct = total_spent / limit.limit_amount if limit.limit_amount > 0 else 0
            if pct >= 1.0:
                alerts.append(f"OVER BUDGET: ${total_spent:.2f} of ${limit.limit_amount:.2f} limit ({pct:.0%})")
            elif pct >= self.ALERT_THRESHOLD_CRITICAL:
                alerts.append(f"CRITICAL: ${total_spent:.2f} of ${limit.limit_amount:.2f} limit ({pct:.0%})")
            elif pct >= self.ALERT_THRESHOLD_WARN:
                alerts.append(f"WARNING: ${total_spent:.2f} of ${limit.limit_amount:.2f} limit ({pct:.0%})")

        for cat, spent in category_breakdown.items():
            for limit in limits:
                if limit.category == cat and limit.limit_amount > 0:
                    pct = spent / limit.limit_amount
                    if pct >= 1.0:
                        alerts.append(f"OVER {cat} BUDGET: ${spent:.2f} of ${limit.limit_amount:.2f}")
                    elif pct >= self.ALERT_THRESHOLD_CRITICAL:
                        alerts.append(f"CRITICAL {cat}: ${spent:.2f} of ${limit.limit_amount:.2f} ({pct:.0%})")
                    elif pct >= self.ALERT_THRESHOLD_WARN:
                        alerts.append(f"WARNING {cat}: ${spent:.2f} of ${limit.limit_amount:.2f} ({pct:.0%})")

        return SpendingSummary(
            user_id=user_id,
            period=period,
            total_spent=round(total_spent, 2),
            entry_count=len(entries),
            category_breakdown=category_breakdown,
            daily_average=daily_average,
            limits=[l for l in limits if l.category is None],
            alerts=alerts,
        )

    def check_budget(self, request: BudgetCheckRequest) -> BudgetCheckResult:
        new_total = request.amount * request.quantity
        if new_total <= 0:
            return BudgetCheckResult(
                within_budget=True, current_spending=0.0, limit=0.0,
                remaining=0.0, message="Invalid amount.", alerts=[],
            )

        with get_db() as conn:
            limits = db_get_limits(conn, request.user_id)

        daily_limit = next((l for l in limits if l.period == BudgetPeriod.daily and l.category is None), None)
        weekly_limit = next((l for l in limits if l.period == BudgetPeriod.weekly and l.category is None), None)
        monthly_limit = next((l for l in limits if l.period == BudgetPeriod.monthly and l.category is None), None)

        alerts: list[str] = []
        worst_within = True

        for period_limit in [daily_limit, weekly_limit, monthly_limit]:
            if period_limit is None:
                continue
            cutoff = self._get_cutoff(period_limit.period)
            with get_db() as conn:
                entries = db_get_entries(conn, request.user_id, since=cutoff)
            current_spending = sum(e.amount * e.quantity for e in entries)
            remaining = period_limit.limit_amount - current_spending
            new_remaining = remaining - new_total

            if new_remaining < 0:
                worst_within = False
                alerts.append(
                    f"{period_limit.period.value} budget exceeded: ${current_spending + new_total:.2f} / ${period_limit.limit_amount:.2f}"
                )
            elif period_limit.limit_amount > 0:
                usage_pct = (current_spending + new_total) / period_limit.limit_amount
                if usage_pct >= self.ALERT_THRESHOLD_CRITICAL:
                    alerts.append(
                        f"{period_limit.period.value} budget critical: ${current_spending + new_total:.2f} / ${period_limit.limit_amount:.2f}"
                    )
                elif usage_pct >= self.ALERT_THRESHOLD_WARN:
                    alerts.append(
                        f"{period_limit.period.value} budget warning: ${current_spending + new_total:.2f} / ${period_limit.limit_amount:.2f}"
                    )

        cat_limits = [l for l in limits if l.category == request.category]
        for cat_limit in cat_limits:
            cutoff = self._get_cutoff(cat_limit.period)
            with get_db() as conn:
                entries = db_get_entries(conn, request.user_id, since=cutoff)
            cat_spent = sum(e.amount * e.quantity for e in entries if e.category == request.category)
            cat_new_total = cat_spent + new_total
            if cat_new_total > cat_limit.limit_amount:
                worst_within = False
                alerts.append(
                    f"{request.category} {cat_limit.period.value} category budget exceeded: ${cat_new_total:.2f} / ${cat_limit.limit_amount:.2f}"
                )
            elif cat_limit.limit_amount > 0:
                cat_usage = cat_new_total / cat_limit.limit_amount
                if cat_usage >= self.ALERT_THRESHOLD_CRITICAL:
                    alerts.append(
                        f"{request.category} {cat_limit.period.value} category budget critical: ${cat_new_total:.2f} / ${cat_limit.limit_amount:.2f}"
                    )
                elif cat_usage >= self.ALERT_THRESHOLD_WARN:
                    alerts.append(
                        f"{request.category} {cat_limit.period.value} category budget warning: ${cat_new_total:.2f} / ${cat_limit.limit_amount:.2f}"
                    )

        ref_limit = monthly_limit or weekly_limit or daily_limit
        if ref_limit:
            cutoff = self._get_cutoff(ref_limit.period)
            with get_db() as conn:
                entries = db_get_entries(conn, request.user_id, since=cutoff)
            current_spending = sum(e.amount * e.quantity for e in entries)
            remaining = ref_limit.limit_amount - current_spending
            if worst_within:
                message = f"Purchase fits within your {ref_limit.period.value} budget. ${remaining - new_total:.2f} remaining after."
            else:
                message = f"Purchase exceeds your {ref_limit.period.value} budget by ${abs(remaining - new_total):.2f}."
            return BudgetCheckResult(
                within_budget=worst_within,
                current_spending=round(current_spending, 2),
                limit=ref_limit.limit_amount,
                remaining=round(max(remaining - new_total, 0), 2),
                message=message,
                alerts=alerts,
            )

        if alerts and cat_limits:
            primary_cat_limit = cat_limits[0]
            cutoff = self._get_cutoff(primary_cat_limit.period)
            with get_db() as conn:
                entries = db_get_entries(conn, request.user_id, since=cutoff)
            cat_spending = sum(e.amount * e.quantity for e in entries if e.category == request.category)
            return BudgetCheckResult(
                within_budget=worst_within,
                current_spending=round(cat_spending, 2),
                limit=primary_cat_limit.limit_amount,
                remaining=round(max(primary_cat_limit.limit_amount - cat_spending - new_total, 0), 2),
                message=f"Purchase exceeds your {request.category} category budget.",
                alerts=alerts,
            )

        return BudgetCheckResult(
            within_budget=True,
            current_spending=0.0,
            limit=0.0,
            remaining=0.0,
            message="No budget limits set. This purchase is allowed.",
            alerts=[],
        )

    def set_limit(self, user_id: str, period: BudgetPeriod, limit_amount: float,
                  category: Optional[str] = None) -> BudgetLimit:
        now = datetime.now().isoformat()
        with get_db() as conn:
            existing = [
                l for l in db_get_limits(conn, user_id)
                if l.period == period and l.category == category
            ]
        if existing:
            existing[0].limit_amount = limit_amount
            existing[0].updated_at = now
            with get_db() as conn:
                db_update_limit(conn, existing[0])
            return existing[0]

        limit = BudgetLimit(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            period=period,
            limit_amount=limit_amount,
            category=category,
            created_at=now,
            updated_at=now,
        )
        with get_db() as conn:
            db_create_limit(conn, limit)
        return limit

    def get_limits(self, user_id: str) -> list[BudgetLimit]:
        with get_db() as conn:
            return db_get_limits(conn, user_id)

    def delete_limit(self, limit_id: str, user_id: str) -> bool:
        if limit_id not in {item.id for item in self.get_limits(user_id)}:
            return False
        with get_db() as conn:
            return db_delete_limit(conn, limit_id)

    def delete_entry(self, entry_id: str, user_id: str) -> bool:
        if entry_id not in {item.id for item in self.get_entries(user_id)}:
            return False
        with get_db() as conn:
            return db_delete_entry(conn, entry_id)

    def get_entries(self, user_id: str, period: Optional[BudgetPeriod] = None) -> list[BudgetEntry]:
        cutoff = self._get_cutoff(period) if period else None
        with get_db() as conn:
            return db_get_entries(conn, user_id, since=cutoff)


budget_tracker = BudgetTracker()
