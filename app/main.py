"""FastAPI web application for the DeepTrace Phase 1 planning foundation."""

from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.logging import configure_logging, log_event
from app.providers import DeterministicPlanModel, PlanModel
from app.validation import QuestionValidationError, normalize_question
from app.workflow import PlanningWorkflow


PACKAGE_DIR = Path(__file__).resolve().parent


def create_app(plan_model: PlanModel | None = None) -> FastAPI:
    """Application factory supporting deterministic provider injection in tests."""

    configure_logging()
    logger = logging.getLogger("deeptrace.web")
    templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))

    application = FastAPI(
        title="DeepTrace",
        description="Phase 1 research-planning workflow foundation",
        version="0.1.0",
    )
    application.mount(
        "/static",
        StaticFiles(directory=str(PACKAGE_DIR / "static")),
        name="static",
    )
    application.state.planning_workflow = PlanningWorkflow(
        plan_model or DeterministicPlanModel()
    )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "deeptrace", "phase": "1"}

    @application.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"question": "", "plan": None, "error": None, "result": None},
        )

    @application.post("/plan", response_class=HTMLResponse)
    async def create_plan(request: Request, question: str = Form(default="")) -> HTMLResponse:
        request_started = perf_counter()
        log_event(logger, "request_started", route="/plan")
        try:
            normalized_question = normalize_question(question)
            result = await application.state.planning_workflow.run(normalized_question)
            log_event(
                logger,
                "request_completed",
                route="/plan",
                request_id=result.request_id,
                status=result.status,
                latency_ms=round((perf_counter() - request_started) * 1000, 3),
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": normalized_question,
                    "plan": result.plan,
                    "result": result,
                    "error": None,
                },
            )
        except QuestionValidationError as error:
            log_event(
                logger,
                "request_rejected",
                route="/plan",
                reason="invalid_question",
                latency_ms=round((perf_counter() - request_started) * 1000, 3),
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={"question": question, "plan": None, "result": None, "error": str(error)},
                status_code=400,
            )
        except Exception:
            logger.exception(
                "request_failed",
                extra={"event_data": {"event": "request_failed", "route": "/plan"}},
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": question,
                    "plan": None,
                    "result": None,
                    "error": "DeepTrace could not create the plan. Please try again.",
                },
                status_code=500,
            )

    return application


app = create_app()
