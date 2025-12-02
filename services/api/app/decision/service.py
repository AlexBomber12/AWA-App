from __future__ import annotations

import datetime as dt
import time
from collections import Counter
from collections.abc import Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.metrics import (
    DECISION_ENGINE_LATENCY_SECONDS,
    DECISION_INBOX_SIZE,
    DECISION_TASKS_CREATED_TOTAL,
    DECISION_TASKS_RESOLVED_TOTAL,
    _with_base_labels,
)
from services.api.app.decision import repository
from services.api.app.decision.models import DecisionCandidate, DecisionTaskRecord, PlannedDecisionTask

logger = structlog.get_logger(__name__)

ROI_CRITICAL_THRESHOLD = -5.0
ROI_TARGET = 12.0
OBSERVE_PRIORITY = 10
REQUEST_PRIORITY = 90
CONTINUE_PRIORITY = 20


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _metric_labels(**labels: str) -> dict[str, str]:
    resolved = _with_base_labels(**labels)
    return dict(resolved)


def _build_entity(candidate: DecisionCandidate) -> dict[str, object]:
    entity: dict[str, object] = {"type": "sku_vendor", "asin": candidate.asin}
    if candidate.vendor_id is not None:
        entity["vendor_id"] = candidate.vendor_id
    if candidate.category:
        entity["category"] = candidate.category
    return entity


def _build_links(candidate: DecisionCandidate) -> dict[str, object]:
    links: dict[str, object] = {"asin": candidate.asin}
    if candidate.vendor_id is not None:
        links["vendor_id"] = candidate.vendor_id
    if candidate.category:
        links["category"] = candidate.category
    return links


def _reason(
    code: str, message: str, *, data: dict[str, object] | None = None, metric: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {"code": code, "message": message}
    if metric:
        payload["metric"] = metric
    if data:
        payload["data"] = data
    return payload


def _alternative(
    action: str,
    *,
    label: str | None = None,
    impact: str | None = None,
    confidence: float | None = None,
    why: Sequence[dict[str, object]] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {"action": action}
    if label:
        payload["label"] = label
    if impact:
        payload["impact"] = impact
    if confidence is not None:
        payload["confidence"] = confidence
    if why:
        payload["why"] = list(why)
    return payload


def build_decision_task(
    *,
    candidate: DecisionCandidate,
    decision: str,
    priority: int,
    summary: str,
    default_action: str | None,
    why: Sequence[dict[str, object]],
    alternatives: Sequence[dict[str, object]],
    deadline: dt.datetime | None = None,
    state: str = "pending",
    metrics: dict[str, float] | None = None,
) -> PlannedDecisionTask:
    return PlannedDecisionTask(
        asin=candidate.asin,
        vendor_id=candidate.vendor_id,
        decision=decision,
        priority=priority,
        summary=summary,
        default_action=default_action,
        why=list(why),
        alternatives=list(alternatives),
        deadline_at=deadline,
        entity=_build_entity(candidate),
        metrics=metrics or {},
        links=_build_links(candidate),
        state=state,
    )


def _evaluate_candidate(candidate: DecisionCandidate) -> PlannedDecisionTask | None:
    if candidate.observe_only:
        return build_decision_task(
            candidate=candidate,
            decision="blocked_observe",
            priority=OBSERVE_PRIORITY,
            summary="Observe-only SKU – hold pricing changes",
            default_action="Do not change price until manual review",
            why=[_reason("observe_only_category", "SKU is marked as observe-only")],
            alternatives=[_alternative("wait_until", label="Re-evaluate after next ingest")],
            metrics=_candidate_metrics(candidate),
        )

    if candidate.roi_pct is None:
        return None

    roi_value = float(candidate.roi_pct)
    metrics_payload = _candidate_metrics(candidate)

    if roi_value <= ROI_CRITICAL_THRESHOLD:
        deadline = _now() + dt.timedelta(days=2)
        return build_decision_task(
            candidate=candidate,
            decision="request_price",
            priority=REQUEST_PRIORITY,
            summary="ROI critical – request updated quote",
            default_action="Ask vendor for improved price to restore ROI",
            why=[
                _reason(
                    "roi_guardrail",
                    f"{roi_value:.1f}% <= {ROI_CRITICAL_THRESHOLD:.1f}%",
                    metric="roi_pct",
                    data={"threshold": ROI_CRITICAL_THRESHOLD},
                ),
            ],
            alternatives=[
                _alternative("wait_until", label="Pause until next ROI ingest"),
                _alternative("switch_vendor", label="Switch vendor if alternate is available"),
            ],
            deadline=deadline,
            metrics=metrics_payload,
        )

    if roi_value < ROI_TARGET:
        deadline = _now() + dt.timedelta(days=5)
        return build_decision_task(
            candidate=candidate,
            decision="request_discount",
            priority=max(REQUEST_PRIORITY - 20, 10),
            summary="ROI below target – request discount",
            default_action="Negotiate discount to hit ROI target",
            why=[
                _reason(
                    "roi_under_target",
                    f"{roi_value:.1f}% < {ROI_TARGET:.1f}%",
                    metric="roi_pct",
                    data={"target": ROI_TARGET},
                ),
            ],
            alternatives=[_alternative("wait_until", label="Observe for 24h")],
            deadline=deadline,
            metrics=metrics_payload,
        )

    # ROI acceptable; emit a low-priority continue task only when close to the target
    if roi_value <= ROI_TARGET + 5:
        return build_decision_task(
            candidate=candidate,
            decision="continue",
            priority=CONTINUE_PRIORITY,
            summary="ROI healthy – continue current pricing",
            default_action="Monitor ROI and keep current vendor terms",
            why=[_reason("roi_ok", f"{roi_value:.1f}% >= {ROI_TARGET:.1f}%")],
            alternatives=[_alternative("wait_until", label="Revisit after next snapshot")],
            metrics=metrics_payload,
        )

    return None


def _candidate_metrics(candidate: DecisionCandidate) -> dict[str, float]:
    metrics_payload: dict[str, float] = {}
    if candidate.roi_pct is not None:
        metrics_payload["roi"] = float(candidate.roi_pct)
    if candidate.risk_adjusted_roi is not None:
        metrics_payload["riskAdjustedRoi"] = float(candidate.risk_adjusted_roi)
    if candidate.cost is not None:
        metrics_payload["cogs"] = float(candidate.cost)
    if candidate.fees is not None:
        metrics_payload["fees"] = float(candidate.fees)
    if candidate.buybox_price is not None:
        metrics_payload["price"] = float(candidate.buybox_price)
    return metrics_payload


async def generate_tasks(
    session: AsyncSession,
    *,
    limit: int = repository.DEFAULT_GENERATION_LIMIT,
    dry_run: bool = False,
) -> tuple[list[DecisionTaskRecord], list[PlannedDecisionTask], int]:
    started = time.perf_counter()
    candidates = await repository.fetch_decision_candidates(session, limit=limit)
    plans = []
    for candidate in candidates:
        plan = _evaluate_candidate(candidate)
        if plan:
            plans.append(plan)

    saved: list[DecisionTaskRecord] = []
    if not dry_run and plans:
        saved = await repository.upsert_tasks(session, plans, now=_now())
        _record_created_metrics(saved)
        await _update_inbox_gauge(session)
    duration = time.perf_counter() - started
    DECISION_ENGINE_LATENCY_SECONDS.labels(**_metric_labels()).observe(duration)
    logger.info(
        "decision_engine.run",
        dry_run=dry_run,
        candidates=len(candidates),
        planned=len(plans),
        saved=len(saved),
        duration_s=duration,
    )
    return saved, plans, len(candidates)


def _record_created_metrics(saved: Sequence[DecisionTaskRecord]) -> None:
    counter = Counter(task.decision for task in saved)
    by_priority = Counter((task.decision, task.priority) for task in saved)
    for decision, count in counter.items():
        DECISION_TASKS_CREATED_TOTAL.labels(**_metric_labels(decision=decision)).inc(count)
    for (decision, priority), count in by_priority.items():
        logger.info(
            "decision.tasks.created",
            decision=decision,
            priority=priority,
            count=count,
        )


async def _update_inbox_gauge(session: AsyncSession) -> None:
    summary = await repository.summarize_states(session, [])
    pending = summary.get("pending", 0)
    DECISION_INBOX_SIZE.labels(**_metric_labels(state="pending")).set(pending)


async def apply_task(
    session: AsyncSession,
    task_id: str,
    *,
    actor: str | None = None,
    note: str | None = None,
) -> DecisionTaskRecord | None:
    updated = await repository.update_task_state(
        session,
        task_id,
        "applied",
        actor=actor,
        note=note,
        event_type="decision_applied",
    )
    if updated:
        DECISION_TASKS_RESOLVED_TOTAL.labels(**_metric_labels(decision=updated.decision, state="applied")).inc()
        await _update_inbox_gauge(session)
        logger.info(
            "decision.tasks.resolved",
            task_id=task_id,
            decision=updated.decision,
            state="applied",
            priority=updated.priority,
        )
    return updated


async def dismiss_task(
    session: AsyncSession,
    task_id: str,
    *,
    actor: str | None = None,
    note: str | None = None,
    next_request_at: dt.datetime | None = None,
) -> DecisionTaskRecord | None:
    updated = await repository.update_task_state(
        session,
        task_id,
        "dismissed",
        actor=actor,
        note=note,
        next_request_at=next_request_at,
        event_type="decision_dismissed",
    )
    if updated:
        DECISION_TASKS_RESOLVED_TOTAL.labels(**_metric_labels(decision=updated.decision, state="dismissed")).inc()
        await _update_inbox_gauge(session)
        logger.info(
            "decision.tasks.resolved",
            task_id=task_id,
            decision=updated.decision,
            state="dismissed",
            priority=updated.priority,
        )
    return updated


__all__ = [
    "apply_task",
    "build_decision_task",
    "dismiss_task",
    "generate_tasks",
]
