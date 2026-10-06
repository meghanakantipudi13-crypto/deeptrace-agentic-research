"""FastAPI application for durable, human-approved DeepTrace research."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import AsyncIterator

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.checkpointing import open_checkpointer
from app.logging import configure_logging, log_event
from app.memory import (
    MemoryCorruptionError,
    MemoryNotFoundError,
    ResearchMemoryRepository,
    build_memory_repository,
    record_from_outcome,
)
from app.models import ApprovalResumePayload, CancelledResearchResult, PlanStep
from app.providers import DeterministicPlanModel, PlanModel
from app.research_workflow import (
    ResearchWorkflow,
    WorkflowNotAwaitingApprovalError,
    WorkflowNotFoundError,
)
from app.search import SearchProvider, build_search_provider
from app.validation import QuestionValidationError, normalize_question
from app.workflow import PlanningWorkflow


PACKAGE_DIR = Path(__file__).resolve().parent


def create_app(
    plan_model: PlanModel | None = None,
    search_provider: SearchProvider | None = None,
    memory_repository: ResearchMemoryRepository | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> FastAPI:
    """Application factory supporting deterministic provider injection in tests."""

    configure_logging()
    logger = logging.getLogger("deeptrace.web")
    templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))

    selected_plan_model = plan_model or DeterministicPlanModel()
    selected_search_provider = search_provider or build_search_provider()
    selected_memory = memory_repository or build_memory_repository()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        if checkpointer is not None:
            application.state.research_workflow = ResearchWorkflow(
                selected_plan_model,
                selected_search_provider,
                checkpointer=checkpointer,
            )
            yield
            return
        async with open_checkpointer() as selected_checkpointer:
            application.state.research_workflow = ResearchWorkflow(
                selected_plan_model,
                selected_search_provider,
                checkpointer=selected_checkpointer,
            )
            yield

    application = FastAPI(
        title="DeepTrace",
        description="Phase 5 durable research memory and human-approved workflow",
        version="0.5.0",
        lifespan=lifespan,
    )
    application.mount(
        "/static",
        StaticFiles(directory=str(PACKAGE_DIR / "static")),
        name="static",
    )
    application.state.planning_workflow = PlanningWorkflow(selected_plan_model)
    application.state.memory_repository = selected_memory

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "deeptrace", "phase": "5"}

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
            pending = await application.state.research_workflow.start(normalized_question)
            log_event(
                logger,
                "request_completed",
                route="/research",
                request_id=pending.workflow_id,
                status=pending.status,
                search_calls=0,
                latency_ms=round((perf_counter() - request_started) * 1000, 3),
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": normalized_question,
                    "plan": pending.plan,
                    "pending": pending,
                    "research": None,
                    "cancelled": None,
                    "result": pending,
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
                    "pending": None,
                    "research": None,
                    "cancelled": None,
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
                    "pending": None,
                    "research": None,
                    "cancelled": None,
                    "result": None,
                    "error": "DeepTrace could not create the approval checkpoint. Please try again.",
                },
                status_code=500,
            )

    @application.post("/research/{workflow_id}/decision", response_class=HTMLResponse)
    async def decide_research(
        request: Request,
        workflow_id: str,
        decision: str = Form(default=""),
        step_title: list[str] = Form(default=[]),
        step_purpose: list[str] = Form(default=[]),
        step_evidence: list[str] = Form(default=[]),
    ) -> HTMLResponse:
        request_started = perf_counter()
        pending = None
        try:
            pending = await application.state.research_workflow.get_pending(workflow_id)
            modified_steps = None
            if decision == "modify":
                expected = len(pending.plan.steps)
                if not (
                    len(step_title)
                    == len(step_purpose)
                    == len(step_evidence)
                    == expected
                ):
                    raise ValueError("Modified plan fields do not match the proposed plan.")
                modified_steps = []
                for index, (title, purpose, evidence_text) in enumerate(
                    zip(step_title, step_purpose, step_evidence, strict=True),
                    start=1,
                ):
                    evidence = [
                        item.strip()
                        for item in evidence_text.replace(";", "\n").splitlines()
                        if item.strip()
                    ]
                    modified_steps.append(
                        PlanStep(
                            order=index,
                            title=title.strip(),
                            purpose=purpose.strip(),
                            evidence_needed=evidence,
                        )
                    )
            approval = ApprovalResumePayload(
                decision=decision,
                modified_steps=modified_steps,
            )
            outcome = await application.state.research_workflow.resume(
                workflow_id,
                approval,
            )
            memory_error = None
            record = record_from_outcome(outcome)
            memory_started = perf_counter()
            try:
                log_event(
                    logger,
                    "memory_save_started",
                    session_id=record.session_id,
                    status=record.status,
                )
                await application.state.memory_repository.save(record)
                log_event(
                    logger,
                    "memory_save_completed",
                    session_id=record.session_id,
                    status=record.status,
                    latency_ms=round((perf_counter() - memory_started) * 1000, 3),
                )
            except Exception:
                logger.exception(
                    "memory_save_failed",
                    extra={
                        "event_data": {
                            "event": "memory_save_failed",
                            "session_id": record.session_id,
                            "status": record.status,
                        }
                    },
                )
                memory_error = "The workflow finished, but its history record could not be saved."
            if isinstance(outcome, CancelledResearchResult):
                return templates.TemplateResponse(
                    request=request,
                    name="index.html",
                    context={
                        "question": outcome.question,
                        "plan": outcome.plan,
                        "pending": None,
                        "research": None,
                        "cancelled": outcome,
                        "result": outcome,
                        "error": memory_error,
                    },
                )
            verification_by_source = {
                item.source_id: item for item in outcome.verifications
            }
            log_event(
                logger,
                "request_completed",
                route="/research/{workflow_id}/decision",
                request_id=outcome.request_id,
                status=outcome.status,
                approval_decision=outcome.approval_decision,
                plan_modified=outcome.plan_modified,
                search_calls=outcome.usage.search_calls,
                retrieval_passes=outcome.usage.retrieval_passes,
                termination_reason=outcome.termination_reason,
                latency_ms=round((perf_counter() - request_started) * 1000, 3),
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": outcome.plan.question,
                    "plan": outcome.plan,
                    "pending": None,
                    "research": outcome,
                    "cancelled": None,
                    "result": outcome,
                    "verification_by_source": verification_by_source,
                    "error": memory_error,
                },
            )
        except (ValidationError, ValueError) as error:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": pending.plan.question if pending else "",
                    "plan": pending.plan if pending else None,
                    "pending": pending,
                    "research": None,
                    "cancelled": None,
                    "result": pending,
                    "error": str(error),
                },
                status_code=400,
            )
        except WorkflowNotFoundError as error:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": "",
                    "plan": None,
                    "pending": None,
                    "research": None,
                    "cancelled": None,
                    "result": None,
                    "error": str(error),
                },
                status_code=404,
            )
        except WorkflowNotAwaitingApprovalError as error:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": "",
                    "plan": None,
                    "pending": None,
                    "research": None,
                    "cancelled": None,
                    "result": None,
                    "error": str(error),
                },
                status_code=409,
            )
        except Exception:
            logger.exception(
                "approval_request_failed",
                extra={
                    "event_data": {
                        "event": "approval_request_failed",
                        "route": "/research/{workflow_id}/decision",
                        "workflow_id": workflow_id,
                    }
                },
            )
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "question": pending.plan.question if pending else "",
                    "plan": pending.plan if pending else None,
                    "pending": pending,
                    "research": None,
                    "cancelled": None,
                    "result": pending,
                    "error": "DeepTrace could not process this approval safely.",
                },
                status_code=500,
            )

    @application.get("/history", response_class=HTMLResponse)
    async def history(request: Request) -> HTMLResponse:
        memory_started = perf_counter()
        log_event(logger, "memory_list", operation="started")
        try:
            sessions = await application.state.memory_repository.list_recent(limit=50)
            log_event(
                logger,
                "memory_list",
                operation="completed",
                record_count=len(sessions),
                latency_ms=round((perf_counter() - memory_started) * 1000, 3),
            )
            return templates.TemplateResponse(
                request=request,
                name="history.html",
                context={"sessions": sessions, "error": None},
            )
        except Exception:
            logger.exception(
                "memory_list_failed",
                extra={"event_data": {"event": "memory_list_failed", "operation": "list"}},
            )
            return templates.TemplateResponse(
                request=request,
                name="history.html",
                context={"sessions": [], "error": "Research history is temporarily unavailable."},
                status_code=500,
            )

    @application.get("/history/{session_id}", response_class=HTMLResponse)
    async def history_detail(request: Request, session_id: str) -> HTMLResponse:
        memory_started = perf_counter()
        log_event(logger, "memory_load", operation="started", session_id=session_id)
        try:
            record = await application.state.memory_repository.get(session_id)
            log_event(
                logger,
                "memory_load",
                operation="completed",
                session_id=record.session_id,
                status=record.status,
                latency_ms=round((perf_counter() - memory_started) * 1000, 3),
            )
            return templates.TemplateResponse(
                request=request,
                name="history_detail.html",
                context={"record": record, "error": None},
            )
        except MemoryNotFoundError as error:
            return templates.TemplateResponse(
                request=request,
                name="history_detail.html",
                context={"record": None, "error": str(error)},
                status_code=404,
            )
        except MemoryCorruptionError:
            logger.exception(
                "memory_load_failed",
                extra={
                    "event_data": {
                        "event": "memory_load_failed",
                        "operation": "get",
                        "session_id": session_id,
                        "reason": "invalid_record",
                    }
                },
            )
            return templates.TemplateResponse(
                request=request,
                name="history_detail.html",
                context={"record": None, "error": "This research record is invalid or corrupted."},
                status_code=422,
            )
        except Exception:
            logger.exception(
                "memory_load_failed",
                extra={
                    "event_data": {
                        "event": "memory_load_failed",
                        "operation": "get",
                        "session_id": session_id,
                        "reason": "provider_error",
                    }
                },
            )
            return templates.TemplateResponse(
                request=request,
                name="history_detail.html",
                context={"record": None, "error": "This research record is temporarily unavailable."},
                status_code=500,
            )

    return application


app = create_app()
