from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models import (
    GuardrailResult,
    PrivacyConsent,
    PrivacyLevel,
    PrivacyRegion,
    UserPrivacyProfile,
)
from app.services.privacy_guardrail import privacy_guardrail
from app.services.safety_guardrail import check_safety

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


class UpdateProfileRequest(BaseModel):
    privacy_level: Optional[PrivacyLevel] = None
    consents: Optional[PrivacyConsent] = None
    region: Optional[PrivacyRegion] = None
    data_retention_days: Optional[int] = None


class ConsentUpdateRequest(BaseModel):
    consents: PrivacyConsent


class SanitizeRequest(BaseModel):
    text: str
    user_id: str = "default"


class AgentAccessRequest(BaseModel):
    agent_name: str
    data_fields: list[str]
    user_id: str = "default"


class OutputCheckRequest(BaseModel):
    recommendations: list[dict]
    user_id: str = "default"


class OptOutResponse(BaseModel):
    status: str
    message: str


class ForgetResponse(BaseModel):
    status: str
    message: str


class ExportResponse(BaseModel):
    data: Optional[dict] = None
    status: str


@router.post("/check-safety")
async def check_safety_route(body: SanitizeRequest):
    profile = privacy_guardrail.get_or_create_profile(body.user_id)
    result = await check_safety(body.text, profile.region)
    return result


@router.get("/profile/{user_id}", response_model=UserPrivacyProfile)
async def get_profile(user_id: str):
    return privacy_guardrail.get_or_create_profile(user_id)


@router.put("/profile/{user_id}", response_model=UserPrivacyProfile)
async def update_profile(user_id: str, body: UpdateProfileRequest):
    profile = privacy_guardrail.get_or_create_profile(user_id)
    if body.privacy_level is not None:
        profile.privacy_level = body.privacy_level
    if body.consents is not None:
        profile.consents = body.consents
    if body.region is not None:
        profile.region = body.region
    if body.data_retention_days is not None:
        profile.data_retention_days = body.data_retention_days
    privacy_guardrail.update_profile(user_id, profile)
    return profile


@router.put("/consent/{user_id}", response_model=UserPrivacyProfile)
async def update_consent(user_id: str, body: ConsentUpdateRequest):
    profile = privacy_guardrail.update_consent(user_id, body.consents)
    if not profile:
        raise HTTPException(404, "User profile not found")
    return profile


@router.post("/sanitize", response_model=GuardrailResult)
async def sanitize_input(body: SanitizeRequest):
    return await privacy_guardrail.check_input(body.text, body.user_id)


@router.post("/check-access", response_model=GuardrailResult)
async def check_agent_access(body: AgentAccessRequest):
    return await privacy_guardrail.check_agent_access(
        body.agent_name, body.data_fields, body.user_id
    )


@router.post("/check-output", response_model=GuardrailResult)
async def check_output(body: OutputCheckRequest):
    return await privacy_guardrail.check_output(body.recommendations, body.user_id)


@router.post("/forget/{user_id}", response_model=ForgetResponse)
async def forget_user(user_id: str):
    await privacy_guardrail.forget_user(user_id)
    return ForgetResponse(
        status="ok",
        message=f"User {user_id} data erased (GDPR Right to Erasure)",
    )


@router.post("/opt-out/{user_id}", response_model=OptOutResponse)
async def opt_out_of_sale(user_id: str):
    profile = privacy_guardrail.opt_out_of_sale(user_id)
    if not profile:
        raise HTTPException(404, "User profile not found")
    return OptOutResponse(
        status="ok",
        message=f"User {user_id} opted out of data sale (CCPA Right to Opt-Out)",
    )


@router.get("/export/{user_id}", response_model=ExportResponse)
async def export_data(user_id: str):
    data = privacy_guardrail.export_profile(user_id)
    if not data:
        return ExportResponse(status="no_data", data=None)
    return ExportResponse(status="ok", data=data)


@router.get("/regions", response_model=list[str])
async def list_regions():
    return [r.value for r in PrivacyRegion]


@router.get("/levels", response_model=list[str])
async def list_levels():
    return [l.value for l in PrivacyLevel]
