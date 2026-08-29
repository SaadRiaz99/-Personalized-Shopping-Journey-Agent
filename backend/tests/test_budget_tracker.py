import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

from app.models import BudgetPeriod, BudgetEntry, BudgetLimit, BudgetCheckRequest
from app.services.budget_tracker import budget_tracker, BudgetTracker
from app.database import get_db, init_db

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "agent_reports")


def _write_report(agent_name: str, content: str):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, f"{agent_name}_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# 1. BUDGET TRACKER — Entry Tracking (10 cases)
# ============================================================

@pytest.mark.asyncio
class TestBudgetEntrySuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def setup_class(cls):
        init_db()
        cls.REPORT = []
        cls.passed = 0
        cls.failed = 0

    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_track_single_entry(self):
        entry = budget_tracker.track_entry(
            user_id="test_budget_user", product_id="p1",
            product_name="Laptop", category="Electronics", amount=999.99,
        )
        assert entry.id
        assert entry.amount == 999.99
        assert entry.user_id == "test_budget_user"
        self._record("track_single_entry", True)

    def test_track_entry_with_quantity(self):
        entry = budget_tracker.track_entry(
            user_id="test_budget_user", product_id="p2",
            product_name="T-Shirt", category="Fashion", amount=29.99, quantity=3,
        )
        assert entry.quantity == 3
        self._record("track_entry_with_quantity", True)

    def test_track_entry_with_note(self):
        entry = budget_tracker.track_entry(
            user_id="test_budget_user", product_id="p3",
            product_name="Book", category="Books", amount=14.99, note="Birthday gift",
        )
        assert entry.note == "Birthday gift"
        self._record("track_entry_with_note", True)

    def test_track_entry_generates_timestamp(self):
        entry = budget_tracker.track_entry(
            user_id="test_budget_user", product_id="p4",
            product_name="Mouse", category="Electronics", amount=24.99,
        )
        assert entry.timestamp
        self._record("track_entry_generates_timestamp", True)

    def test_track_entry_generates_id(self):
        entry = budget_tracker.track_entry(
            user_id="test_budget_user", product_id="p5",
            product_name="Keyboard", category="Electronics", amount=79.99,
        )
        assert len(entry.id) == 8
        self._record("track_entry_generates_id", True)

    def test_track_entry_zero_quantity(self):
        entry = budget_tracker.track_entry(
            user_id="test_budget_user", product_id="p6",
            product_name="Free Item", category="Home", amount=0.0, quantity=1,
        )
        assert entry.amount == 0.0
        self._record("track_entry_zero_quantity", True)

    def test_track_multiple_entries_same_user(self):
        uid = "test_multi_user"
        budget_tracker.track_entry(uid, "p1", "Item1", "Electronics", 100.0)
        budget_tracker.track_entry(uid, "p2", "Item2", "Fashion", 50.0)
        entries = budget_tracker.get_entries(uid)
        assert len(entries) >= 2
        self._record("track_multiple_entries_same_user", True)

    def test_track_entry_category_saved(self):
        entry = budget_tracker.track_entry(
            user_id="test_cat_user", product_id="p7",
            product_name="Sneakers", category="Sports", amount=129.99,
        )
        assert entry.category == "Sports"
        self._record("track_entry_category_saved", True)

    def test_delete_existing_entry(self):
        entry = budget_tracker.track_entry(
            user_id="test_del_user", product_id="pd1",
            product_name="To Delete", category="Home", amount=10.0,
        )
        result = budget_tracker.delete_entry(entry.id, "test_del_user")
        assert result is True
        self._record("delete_existing_entry", True)

    def test_delete_nonexistent_entry(self):
        result = budget_tracker.delete_entry("nonexistent_id", "test_del_user")
        assert result is False
        self._record("delete_nonexistent_entry", True)

    @classmethod
    def teardown_class(cls):
        _write_report("BudgetTracker_Entries", "\n".join(
            f"- {'PASS' if r['passed'] else 'FAIL'}: {r['name']} {r.get('detail', '')}"
            for r in cls.REPORT
        ))


# ============================================================
# 2. BUDGET LIMITS — 10 cases
# ============================================================

@pytest.mark.asyncio
class TestBudgetLimitSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def setup_class(cls):
        init_db()
        cls.REPORT = []
        cls.passed = 0
        cls.failed = 0

    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_set_monthly_limit(self):
        limit = budget_tracker.set_limit("test_limit_user", BudgetPeriod.monthly, 1000.0)
        assert limit.limit_amount == 1000.0
        assert limit.period == BudgetPeriod.monthly
        self._record("set_monthly_limit", True)

    def test_set_daily_limit(self):
        limit = budget_tracker.set_limit("test_limit_user", BudgetPeriod.daily, 100.0)
        assert limit.period == BudgetPeriod.daily
        self._record("set_daily_limit", True)

    def test_set_weekly_limit(self):
        limit = budget_tracker.set_limit("test_limit_user", BudgetPeriod.weekly, 500.0)
        assert limit.period == BudgetPeriod.weekly
        self._record("set_weekly_limit", True)

    def test_set_category_limit(self):
        limit = budget_tracker.set_limit(
            "test_limit_user", BudgetPeriod.monthly, 200.0, category="Electronics",
        )
        assert limit.category == "Electronics"
        self._record("set_category_limit", True)

    def test_update_existing_limit(self):
        budget_tracker.set_limit("test_upd_user", BudgetPeriod.monthly, 500.0)
        updated = budget_tracker.set_limit("test_upd_user", BudgetPeriod.monthly, 750.0)
        assert updated.limit_amount == 750.0
        limits = budget_tracker.get_limits("test_upd_user")
        monthly = [l for l in limits if l.period == BudgetPeriod.monthly and l.category is None]
        assert len(monthly) == 1
        self._record("update_existing_limit", True)

    def test_get_limits(self):
        budget_tracker.set_limit("test_gl_user", BudgetPeriod.monthly, 200.0)
        budget_tracker.set_limit("test_gl_user", BudgetPeriod.weekly, 100.0)
        limits = budget_tracker.get_limits("test_gl_user")
        assert len(limits) >= 2
        self._record("get_limits", True)

    def test_delete_existing_limit(self):
        limit = budget_tracker.set_limit("test_dl_user", BudgetPeriod.monthly, 300.0)
        result = budget_tracker.delete_limit(limit.id, "test_dl_user")
        assert result is True
        self._record("delete_existing_limit", True)

    def test_delete_nonexistent_limit(self):
        result = budget_tracker.delete_limit("nonexistent_limit_id", "test_dl_user")
        assert result is False
        self._record("delete_nonexistent_limit", True)

    def test_limit_has_timestamps(self):
        limit = budget_tracker.set_limit("test_ts_user", BudgetPeriod.monthly, 100.0)
        assert limit.created_at
        assert limit.updated_at
        self._record("limit_has_timestamps", True)

    def test_limit_has_id(self):
        limit = budget_tracker.set_limit("test_id_user", BudgetPeriod.daily, 50.0)
        assert len(limit.id) == 8
        self._record("limit_has_id", True)

    @classmethod
    def teardown_class(cls):
        _write_report("BudgetTracker_Limits", "\n".join(
            f"- {'PASS' if r['passed'] else 'FAIL'}: {r['name']} {r.get('detail', '')}"
            for r in cls.REPORT
        ))


# ============================================================
# 3. BUDGET SUMMARY — 12 cases
# ============================================================

@pytest.mark.asyncio
class TestBudgetSummarySuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def setup_class(cls):
        init_db()
        cls.REPORT = []
        cls.passed = 0
        cls.failed = 0
        cls.uid = "test_summary_user_" + uuid.uuid4().hex[:8]
        for i in range(5):
            budget_tracker.track_entry(
                cls.uid, f"ps{i}", f"Product {i}", "Electronics", 100.0 * (i + 1),
            )
        budget_tracker.track_entry(cls.uid, "ps5", "Fashion Item", "Fashion", 50.0)
        budget_tracker.set_limit(cls.uid, BudgetPeriod.monthly, 2000.0)

    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_summary_returns_user_id(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.monthly)
        assert s.user_id == self.uid
        self._record("summary_returns_user_id", True)

    def test_summary_total_spent_positive(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.monthly)
        assert s.total_spent > 0
        self._record("summary_total_spent_positive", True)

    def test_summary_entry_count(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.monthly)
        assert s.entry_count >= 5
        self._record("summary_entry_count", True)

    def test_summary_category_breakdown(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.monthly)
        assert "Electronics" in s.category_breakdown
        assert "Fashion" in s.category_breakdown
        self._record("summary_category_breakdown", True)

    def test_summary_category_amounts(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.monthly)
        assert s.category_breakdown["Fashion"] == 50.0
        self._record("summary_category_amounts", True)

    def test_summary_daily_average(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.monthly)
        assert s.daily_average > 0
        self._record("summary_daily_average", True)

    def test_summary_includes_limits(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.monthly)
        assert len(s.limits) >= 1
        assert s.limits[0].limit_amount == 2000.0
        self._record("summary_includes_limits", True)

    def test_summary_daily_period(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.daily)
        assert s.period == BudgetPeriod.daily
        self._record("summary_daily_period", True)

    def test_summary_weekly_period(self):
        s = budget_tracker.get_summary(self.uid, BudgetPeriod.weekly)
        assert s.period == BudgetPeriod.weekly
        self._record("summary_weekly_period", True)

    def test_summary_empty_user(self):
        s = budget_tracker.get_summary("nonexistent_user_xyz", BudgetPeriod.monthly)
        assert s.total_spent == 0.0
        assert s.entry_count == 0
        self._record("summary_empty_user", True)

    def test_summary_alert_over_budget(self):
        uid = "test_alert_over_" + str(id(self))
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 100.0)
        budget_tracker.track_entry(uid, "pa1", "Over Item", "Electronics", 150.0)
        s = budget_tracker.get_summary(uid, BudgetPeriod.monthly)
        assert any("OVER" in a for a in s.alerts)
        self._record("summary_alert_over_budget", True)

    def test_summary_alert_warning_threshold(self):
        uid = "test_alert_warn_" + str(id(self))
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 1000.0)
        budget_tracker.track_entry(uid, "pb1", "Warn Item", "Electronics", 800.0)
        s = budget_tracker.get_summary(uid, BudgetPeriod.monthly)
        assert any("WARNING" in a for a in s.alerts)
        self._record("summary_alert_warning_threshold", True)

    @classmethod
    def teardown_class(cls):
        _write_report("BudgetTracker_Summary", "\n".join(
            f"- {'PASS' if r['passed'] else 'FAIL'}: {r['name']} {r.get('detail', '')}"
            for r in cls.REPORT
        ))


# ============================================================
# 4. BUDGET CHECK — 12 cases
# ============================================================

@pytest.mark.asyncio
class TestBudgetCheckSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def setup_class(cls):
        init_db()
        cls.REPORT = []
        cls.passed = 0
        cls.failed = 0

    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_check_within_budget(self):
        uid = "test_check_ok"
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 1000.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pc1", product_name="Laptop", category="Electronics", amount=500.0)
        result = budget_tracker.check_budget(req)
        assert result.within_budget is True
        self._record("check_within_budget", True)

    def test_check_over_budget(self):
        uid = "test_check_over_" + str(id(self))
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 100.0)
        budget_tracker.track_entry(uid, "pco1", "Existing", "Electronics", 80.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pco2", product_name="Expensive", category="Electronics", amount=50.0)
        result = budget_tracker.check_budget(req)
        assert result.within_budget is False
        self._record("check_over_budget", True)

    def test_check_returns_current_spending(self):
        uid = "test_check_spend"
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 500.0)
        budget_tracker.track_entry(uid, "pcs1", "Item", "Home", 200.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pcs2", product_name="New Item", category="Home", amount=50.0)
        result = budget_tracker.check_budget(req)
        assert result.current_spending >= 200.0
        self._record("check_returns_current_spending", True)

    def test_check_returns_limit(self):
        uid = "test_check_limit"
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 750.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pcl1", product_name="Item", category="Electronics", amount=100.0)
        result = budget_tracker.check_budget(req)
        assert result.limit == 750.0
        self._record("check_returns_limit", True)

    def test_check_no_limit_set(self):
        uid = "test_check_nolim_" + str(hash("unique1"))
        req = BudgetCheckRequest(user_id=uid, product_id="pnl1", product_name="Item", category="Home", amount=100.0)
        result = budget_tracker.check_budget(req)
        assert result.within_budget is True
        assert "No budget limits" in result.message
        self._record("check_no_limit_set", True)

    def test_check_with_quantity(self):
        uid = "test_check_qty"
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 200.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pq1", product_name="Item", category="Electronics", amount=50.0, quantity=5)
        result = budget_tracker.check_budget(req)
        assert result.within_budget is False
        self._record("check_with_quantity", True)

    def test_check_alerts_generated(self):
        uid = "test_check_alerts_" + str(id(self))
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 100.0)
        budget_tracker.track_entry(uid, "pca1", "Near Limit", "Electronics", 90.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pca2", product_name="Add", category="Electronics", amount=15.0)
        result = budget_tracker.check_budget(req)
        assert len(result.alerts) > 0
        self._record("check_alerts_generated", True)

    def test_check_category_limit_exceeded(self):
        uid = "test_cat_limit_" + uuid.uuid4().hex[:8]
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 100.0, category="Electronics")
        budget_tracker.track_entry(uid, "pcc1", "Elec Item", "Electronics", 80.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pcc2", product_name="New Elec", category="Electronics", amount=40.0)
        result = budget_tracker.check_budget(req)
        assert any("Electronics" in a for a in result.alerts)
        self._record("check_category_limit_exceeded", True)

    def test_check_category_not_exceeded(self):
        uid = "test_check_catok_" + str(id(self))
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 200.0, category="Fashion")
        req = BudgetCheckRequest(user_id=uid, product_id="pcok1", product_name="Dress", category="Fashion", amount=50.0)
        result = budget_tracker.check_budget(req)
        assert result.within_budget is True
        self._record("check_category_not_exceeded", True)

    def test_check_message_within(self):
        uid = "test_check_msgin"
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 500.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pm1", product_name="Item", category="Home", amount=50.0)
        result = budget_tracker.check_budget(req)
        assert "fits within" in result.message
        self._record("check_message_within", True)

    def test_check_message_over(self):
        uid = "test_check_msgover_" + str(id(self))
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 100.0)
        budget_tracker.track_entry(uid, "pmo1", "Existing", "Home", 90.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pmo2", product_name="Over", category="Home", amount=30.0)
        result = budget_tracker.check_budget(req)
        assert "exceeds" in result.message
        self._record("check_message_over", True)

    def test_check_zero_amount(self):
        uid = "test_check_zero"
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 100.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pz1", product_name="Free", category="Home", amount=0.0)
        result = budget_tracker.check_budget(req)
        assert result.within_budget is True
        self._record("check_zero_amount", True)

    @classmethod
    def teardown_class(cls):
        _write_report("BudgetTracker_Check", "\n".join(
            f"- {'PASS' if r['passed'] else 'FAIL'}: {r['name']} {r.get('detail', '')}"
            for r in cls.REPORT
        ))


# ============================================================
# 5. BUDGET TRACKER EDGE CASES — 8 cases
# ============================================================

@pytest.mark.asyncio
class TestBudgetEdgeCases:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def setup_class(cls):
        init_db()
        cls.REPORT = []
        cls.passed = 0
        cls.failed = 0

    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_get_entries_all(self):
        uid = "test_entries_all"
        budget_tracker.track_entry(uid, "pe1", "Item1", "Home", 10.0)
        budget_tracker.track_entry(uid, "pe2", "Item2", "Fashion", 20.0)
        entries = budget_tracker.get_entries(uid)
        assert len(entries) >= 2
        self._record("get_entries_all", True)

    def test_get_entries_by_period(self):
        uid = "test_entries_period"
        budget_tracker.track_entry(uid, "pep1", "Item", "Home", 10.0)
        entries = budget_tracker.get_entries(uid, period=BudgetPeriod.daily)
        assert isinstance(entries, list)
        self._record("get_entries_by_period", True)

    def test_multiple_users_isolated(self):
        budget_tracker.track_entry("iso_user_a", "pia1", "A Item", "Electronics", 100.0)
        budget_tracker.track_entry("iso_user_b", "pib1", "B Item", "Fashion", 200.0)
        entries_a = budget_tracker.get_entries("iso_user_a")
        entries_b = budget_tracker.get_entries("iso_user_b")
        assert all(e.user_id == "iso_user_a" for e in entries_a)
        assert all(e.user_id == "iso_user_b" for e in entries_b)
        self._record("multiple_users_isolated", True)

    def test_summary_multiple_categories(self):
        uid = "test_multi_cat"
        budget_tracker.track_entry(uid, "pmc1", "Elec", "Electronics", 100.0)
        budget_tracker.track_entry(uid, "pmc2", "Fashion", "Fashion", 50.0)
        budget_tracker.track_entry(uid, "pmc3", "Home", "Home", 30.0)
        s = budget_tracker.get_summary(uid, BudgetPeriod.monthly)
        assert len(s.category_breakdown) >= 3
        self._record("summary_multiple_categories", True)

    def test_check_daily_vs_monthly(self):
        uid = "test_daily_monthly"
        budget_tracker.set_limit(uid, BudgetPeriod.daily, 50.0)
        budget_tracker.set_limit(uid, BudgetPeriod.monthly, 1000.0)
        req = BudgetCheckRequest(user_id=uid, product_id="pdm1", product_name="Item", category="Home", amount=30.0)
        result = budget_tracker.check_budget(req)
        assert result.within_budget is True
        self._record("check_daily_vs_monthly", True)

    def test_summary_category_percentages(self):
        uid = "test_cat_pct_" + uuid.uuid4().hex[:8]
        budget_tracker.track_entry(uid, "ppc1", "Big", "Electronics", 300.0)
        budget_tracker.track_entry(uid, "ppc2", "Small", "Fashion", 100.0)
        s = budget_tracker.get_summary(uid, BudgetPeriod.monthly)
        assert s.category_breakdown["Electronics"] == 300.0
        assert s.category_breakdown["Fashion"] == 100.0
        self._record("summary_category_percentages", True)

    def test_budget_tracker_class_exists(self):
        bt = BudgetTracker()
        assert hasattr(bt, "track_entry")
        assert hasattr(bt, "check_budget")
        assert hasattr(bt, "set_limit")
        assert hasattr(bt, "get_summary")
        self._record("budget_tracker_class_exists", True)

    def test_module_singleton(self):
        from app.services.budget_tracker import budget_tracker as bt
        assert isinstance(bt, BudgetTracker)
        self._record("module_singleton", True)

    @classmethod
    def teardown_class(cls):
        _write_report("BudgetTracker_EdgeCases", "\n".join(
            f"- {'PASS' if r['passed'] else 'FAIL'}: {r['name']} {r.get('detail', '')}"
            for r in cls.REPORT
        ))
