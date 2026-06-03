"""FastAPI endpoint exposing run_turn() as a POST /recommend endpoint."""

from __future__ import annotations
from pydantic import BaseModel
from .agent import run_turn


class RecommendRequest(BaseModel):
    user_message: str
    session_id: str = "default"
    user_id: str = "anonymous"


class RecommendResponse(BaseModel):
    response: str
    tool_calls: list[str]
    session_summary: dict


def create_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    app = FastAPI(title="RecommendationAgent")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/recommend", response_model=RecommendResponse)
    async def recommend(req: RecommendRequest):
        from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
        try:
            result = await run_turn(
                user_message=req.user_message,
                session_id=req.session_id,
                user_id=req.user_id,
            )
            return RecommendResponse(
                response=result["response"],
                tool_calls=result["tool_calls"],
                session_summary=result["session_summary"],
            )
        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered) as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=422,
                content={
                    "guardrail": True,
                    "guardrail_message": str(e),
                    "response": str(e),
                    "tool_calls": [],
                    "session_summary": {},
                },
            )

    return app


app = create_app()
