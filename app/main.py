"""FastAPI web application for the DeepTrace Phase 3 research loop."""

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
from app.research_workflow import ResearchWorkflow
from app.search import SearchProvider, build_search_provider
from app.validation import QuestionValidationError, normalize_question
from app.workflow import PlanningWorkflow


PACKAGE_DIR = Path(__file__).resolve().parent


def create_app(
    plan_model: PlanModel | None = None,
    search_provider: SearchProvider | None = None,
) -> FastAPI:
    """Application factory supporting deterministic provider injection in tests."""

    configure_logging()
    logger = logging.getLogger("deeptrace.web")
    templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))

    selected_plan_model = plan_model or DeterministicPlanModel()
    selected_search_provider = search_provider or build_search_provider()
    application = FastAPI(
        title="DeepTrace",
        description="Phase 3 bounded iterative retrieval and self-correction",
        version="0.3.0",
    )
    application.mount(
        "/static",
        StaticFiles(directory=str(PACKAGE_DIR / "static")),
        name="static",
    )
    application.state.planning_workflow = PlanningWorkflow(selected_plan_model)
    application.state.research_workflow = ResearchWorkflow(
        selected_plan_model,
        selected_search_provider,
    )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "deeptrace", "phase": "3"}

    @application.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "question": "",
                "plan": None,
                "research": None,
                "error": None,
                "result": None,
            },
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
                    "research": None,
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
                context={
                    "question": question,
                    "plan": None,
                    "research": None,
                    "result": None,
                    "error": str(error),
                },
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
                    "research": None,
                    "result": None,
                    "error": "DeepTrace could not create the plan. Please try again.",
                },
                status_code=500,
            )

    @application.post("/research", response_class=HTMLResponse)
    async def research(request: Request, question: str = Form(default="")) -> HTMLResponse:
        request_started = perf_counter()
        log_event(logger, "request_started", route="/research")
        try:
            normalized_question = normalize_question(question)
            result = await application.state.research_workflow.run(normalized_question)
            verification_by_source = {
                item.source_id: item for item in result.verifications
            }
            log_event(
                logger,
                "request_completed",
                route="/research",
                request_id=result.request_id,
                status=result.status,
                search_provider=result.search_provider_label,
                search_is_simulated=result.search_is_simulated,
                search_calls=result.usage.search_calls,
                retrieval_passes=result.usage.retrieval_passes,
                sources_retained=result.usage.sources_retained,
                termination_reason=result.termination_reason,
                latency_ms=round((perf_counter() - request_started) * 1000, 3),
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": normalized_question,
                    "plan": result.plan,
                    "research": result,
                    "result": result,
                    "verification_by_source": verification_by_source,
                    "error": None,
                },
            )
        except QuestionValidationError as error:
            log_event(
                logger,
                "request_rejected",
                route="/research",
                reason="invalid_question",
                latency_ms=round((perf_counter() - request_started) * 1000, 3),
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": question,
                    "plan": None,
                    "research": None,
                    "result": None,
                    "error": str(error),
                },
                status_code=400,
            )
        except Exception:
            logger.exception(
                "request_failed",
                extra={"event_data": {"event": "request_failed", "route": "/research"}},
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": question,
                    "plan": None,
                    "research": None,
                    "result": None,
                    "error": "DeepTrace could not complete the first research pass. Please try again.",
                },
                status_code=500,
            )

    return application


app = create_app()
