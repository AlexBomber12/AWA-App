from __future__ import annotations

import asyncio
import hashlib
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import asyncpg
import structlog
from jinja2 import Environment, StrictUndefined, TemplateError

from awa_common.dsn import build_dsn
from awa_common.settings import settings as SETTINGS
from awa_common.utils.env import env_str
from services.alert_bot.config import AlertRule

# Logging --------------------------------------------------------------------
_LOGGER = structlog.get_logger(__name__).bind(
    service=SETTINGS.SERVICE_NAME or "worker",
    env=SETTINGS.ENV,
    version=SETTINGS.VERSION,
    component="alert_rules",
)


# Database connection settings ------------------------------------------------
def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value is None:
            continue
        stripped = value.strip()
        if stripped:
            return stripped
    return None


DSN = _first_non_empty(env_str("PG_ASYNC_DSN"), SETTINGS.PG_ASYNC_DSN) or build_dsn(sync=False)

ALERT_DB_POOL_MIN_SIZE = SETTINGS.ALERT_DB_POOL_MIN_SIZE
ALERT_DB_POOL_MAX_SIZE = max(ALERT_DB_POOL_MIN_SIZE, SETTINGS.ALERT_DB_POOL_MAX_SIZE)
ALERT_DB_POOL_TIMEOUT = SETTINGS.ALERT_DB_POOL_TIMEOUT
ALERT_DB_POOL_ACQUIRE_TIMEOUT = SETTINGS.ALERT_DB_POOL_ACQUIRE_TIMEOUT
ALERT_DB_POOL_ACQUIRE_RETRIES = max(1, SETTINGS.ALERT_DB_POOL_ACQUIRE_RETRIES)
ALERT_DB_POOL_RETRY_DELAY = SETTINGS.ALERT_DB_POOL_RETRY_DELAY

DB_POOL: asyncpg.Pool | None = None
_POOL_LOCK = asyncio.Lock()


async def init_db_pool() -> asyncpg.Pool:
    """Initialise (or return) the shared asyncpg connection pool."""

    global DB_POOL
    if DB_POOL is not None:
        return DB_POOL
    if not DSN:
        raise RuntimeError("PG_ASYNC_DSN is not configured")
    async with _POOL_LOCK:
        if DB_POOL is None:
            DB_POOL = await asyncpg.create_pool(
                dsn=DSN,
                min_size=ALERT_DB_POOL_MIN_SIZE,
                max_size=ALERT_DB_POOL_MAX_SIZE,
                timeout=ALERT_DB_POOL_TIMEOUT,
            )
    if DB_POOL is None:  # pragma: no cover - defensive only
        raise RuntimeError("Database pool initialisation failed")
    return DB_POOL


async def close_db_pool() -> None:
    """Close the shared asyncpg pool when the bot shuts down."""

    global DB_POOL
    pool = DB_POOL
    if pool is None:
        return
    DB_POOL = None
    await pool.close()


async def fetch_rows(query: str, *args: Any) -> list[asyncpg.Record]:
    pool = await init_db_pool()
    last_exc: Exception | None = None
    for attempt in range(1, ALERT_DB_POOL_ACQUIRE_RETRIES + 1):
        try:
            async with pool.acquire(timeout=ALERT_DB_POOL_ACQUIRE_TIMEOUT) as conn:
                rows = await conn.fetch(query, *args)
                return list(rows)
        except (TimeoutError, asyncpg.PostgresError) as exc:
            last_exc = exc
            if attempt >= ALERT_DB_POOL_ACQUIRE_RETRIES:
                raise
            await asyncio.sleep(ALERT_DB_POOL_RETRY_DELAY)
    if last_exc:  # pragma: no cover - loop ensures raise above
        raise last_exc
    return []


async def query_roi_breaches(min_roi_pct: float, min_duration_days: int) -> list[asyncpg.Record]:
    return await fetch_rows(
        "SELECT asin, roi_pct FROM roi_view WHERE roi_pct < $1 AND updated_at < now() - interval '$2 days'",
        min_roi_pct,
        min_duration_days,
    )


async def query_price_increase(delta_pct: float) -> list[asyncpg.Record]:
    return await fetch_rows(
        """
        WITH t AS (
            SELECT vendor_id, sku, cost,
                   LAG(cost) OVER (PARTITION BY vendor_id, sku ORDER BY updated_at) AS prev_cost,
                   updated_at
            FROM vendor_prices
        )
        SELECT sku, vendor_id, ROUND((cost - prev_cost) / prev_cost * 100, 2) AS delta
        FROM t
        WHERE prev_cost IS NOT NULL AND delta > $1
        ORDER BY updated_at DESC
        """,
        delta_pct,
    )


async def query_buybox_drop(drop_pct: float) -> list[asyncpg.Record]:
    return await fetch_rows(
        """
        SELECT asin, 100 * (price_48h - price_now) / price_48h AS drop_pct
        FROM buybox_prices
        WHERE drop_pct > $1
        """,
        drop_pct,
    )


async def query_high_returns(returns_pct: float) -> list[asyncpg.Record]:
    return await fetch_rows("SELECT asin, returns_ratio FROM returns_view WHERE returns_ratio > $1", returns_pct)


async def query_stale_price_lists(stale_days: int) -> list[asyncpg.Record]:
    return await fetch_rows(
        "SELECT vendor_id FROM vendor_prices GROUP BY vendor_id HAVING MAX(updated_at) < now() - interval '$1 days'",
        stale_days,
    )


# Alert events and templates --------------------------------------------------
MAX_MESSAGE_BYTES = 4096


@dataclass(slots=True)
class AlertEvent:
    rule_id: str
    chat_ids: list[str]
    text: str
    dedupe_key: str
    parse_mode: str | None = "HTML"
    disable_web_page_preview: bool = True


_HTML_ENV = Environment(
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)
_TEXT_ENV = Environment(
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)

DEFAULT_TEMPLATES: dict[str, str] = {
    "roi_drop": """⚠️ ROI ниже {{ params.min_roi_pct }}% по {{ count }} SKU.
{% for row in rows -%}
• {{ row.asin }} — {{ "%.2f"|format(row.roi_pct) }}%
{% endfor %}
""",
    "buybox_loss": """🏷️ Buy Box просел > {{ params.drop_pct }}% по {{ count }} листингам.
{% for row in rows -%}
• {{ row.asin }} — {{ "%.2f"|format(row.drop_pct) }}%
{% endfor %}
""",
    "returns_spike": """🔄 Возвраты > {{ params.returns_pct }}% по {{ count }} товар(ам).
{% for row in rows -%}
• {{ row.asin }} — {{ "%.2f"|format(row.returns_ratio) }}%
{% endfor %}
""",
    "price_outdated": """📜 Обновите прайс-лист. {{ count }} поставщик(ов) без апдейта > {{ params.stale_days }} дн.
{% for row in rows -%}
• vendor {{ row.vendor_id }}
{% endfor %}
""",
    "price_increase_pct": """💸 Закупочная цена выросла > {{ params.grow_pct }}% для {{ count }} SKU.
{% for row in rows -%}
• {{ row.sku }} — {{ "%.2f"|format(row.delta) }}%
{% endfor %}
""",
    "fallback": "{{ rule }} triggered {{ count }} event(s).",
}


def render_template(template: str, context: Mapping[str, Any], *, parse_mode: str | None = "HTML") -> list[str]:
    env = _HTML_ENV if (parse_mode or "").upper() == "HTML" else _TEXT_ENV
    try:
        rendered = env.from_string(template).render(**context)
    except TemplateError as exc:
        _LOGGER.error("alert_rule.template_error", rule=context.get("rule"), error=str(exc))
        return [f"[template error] {exc}"]
    return _chunk_text(rendered.strip())


def _chunk_text(text: str, limit: int = MAX_MESSAGE_BYTES) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    cursor = 0
    length = len(text)
    while cursor < length:
        end = min(length, cursor + limit)
        if end < length:
            newline = text.rfind("\n", cursor, end)
            if newline > cursor:
                end = newline + 1
        chunk = text[cursor:end].strip()
        if chunk:
            chunks.append(chunk)
        cursor = end
    return chunks or [text[-limit:]]


RuleHandler = Callable[[AlertRule], Awaitable[list[AlertEvent]]]
_RULE_HANDLERS: dict[str, RuleHandler] = {}


def register_rule_handler(name: str) -> Callable[[RuleHandler], RuleHandler]:
    def decorator(func: RuleHandler) -> RuleHandler:
        _RULE_HANDLERS[name] = func
        return func

    return decorator


def get_rule_handler(rule_type: str) -> RuleHandler | None:
    return _RULE_HANDLERS.get(rule_type)


async def evaluate_rule(rule: AlertRule) -> list[AlertEvent]:
    handler = get_rule_handler(rule.type)
    if handler is None:
        _LOGGER.warning("alert_rule.handler_missing", rule_id=rule.id, rule_type=rule.type)
        return []
    return await handler(rule)


def _rows_to_dicts(rows: list[asyncpg.Record]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _hash_key(*parts: str) -> str:
    payload = "::".join(parts).encode("utf-8", "ignore")
    digest = hashlib.sha1(payload, usedforsecurity=False).hexdigest()
    return digest


def _render_events(
    rule: AlertRule, context: dict[str, Any], *, dedupe_hint: str, template_fallback: str
) -> list[AlertEvent]:
    template = (
        rule.template
        or DEFAULT_TEMPLATES.get(rule.type)
        or DEFAULT_TEMPLATES.get(template_fallback)
        or DEFAULT_TEMPLATES["fallback"]
    )
    texts = render_template(template, context, parse_mode=rule.parse_mode)
    events: list[AlertEvent] = []
    for idx, text in enumerate(texts):
        dedupe = f"{rule.id}:{dedupe_hint}:{idx}:{text}"
        events.append(
            AlertEvent(
                rule_id=rule.id,
                chat_ids=list(rule.chat_ids),
                text=text,
                dedupe_key=f"{rule.id}:{_hash_key(dedupe)}",
                parse_mode=rule.parse_mode,
            )
        )
    return events


def _build_context(rule: AlertRule, rows: Sequence[Mapping[str, Any]], params: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule": rule.id,
        "type": rule.type,
        "params": params,
        "rows": rows,
        "count": len(rows),
        "generated_at": int(time.time()),
        "settings": {
            "env": SETTINGS.ENV,
            "service": SETTINGS.SERVICE_NAME or "worker",
        },
    }


@register_rule_handler("roi_drop")
@register_rule_handler("roi")
async def handle_roi_drop(rule: AlertRule) -> list[AlertEvent]:
    min_roi = float(rule.params.get("min_roi_pct", SETTINGS.ROI_THRESHOLD))
    min_days = int(rule.params.get("min_days", SETTINGS.ROI_DURATION_DAYS))
    rows = await query_roi_breaches(min_roi, min_days)
    if not rows:
        return []
    context = _build_context(
        rule,
        _rows_to_dicts(rows),
        params={"min_roi_pct": min_roi, "min_days": min_days},
    )
    return _render_events(rule, context, dedupe_hint=f"{min_roi}:{min_days}", template_fallback="roi_drop")


@register_rule_handler("price_increase_pct")
async def handle_price_increase(rule: AlertRule) -> list[AlertEvent]:
    grow_pct = float(rule.params.get("grow_pct", SETTINGS.COST_DELTA_PCT))
    rows = await query_price_increase(grow_pct)
    if not rows:
        return []
    context = _build_context(
        rule,
        _rows_to_dicts(rows),
        params={"grow_pct": grow_pct},
    )
    return _render_events(rule, context, dedupe_hint=f"{grow_pct}", template_fallback="price_increase_pct")


@register_rule_handler("buybox_loss")
@register_rule_handler("buybox_drop_pct")
async def handle_buybox_loss(rule: AlertRule) -> list[AlertEvent]:
    drop_pct = float(rule.params.get("drop_pct", SETTINGS.PRICE_DROP_PCT))
    rows = await query_buybox_drop(drop_pct)
    if not rows:
        return []
    context = _build_context(
        rule,
        _rows_to_dicts(rows),
        params={"drop_pct": drop_pct},
    )
    return _render_events(rule, context, dedupe_hint=f"{drop_pct}", template_fallback="buybox_loss")


@register_rule_handler("returns_spike")
@register_rule_handler("returns_rate_pct")
async def handle_returns(rule: AlertRule) -> list[AlertEvent]:
    returns_pct = float(rule.params.get("returns_pct", SETTINGS.RETURNS_PCT))
    rows = await query_high_returns(returns_pct)
    if not rows:
        return []
    context = _build_context(
        rule,
        _rows_to_dicts(rows),
        params={"returns_pct": returns_pct},
    )
    return _render_events(rule, context, dedupe_hint=f"{returns_pct}", template_fallback="returns_spike")


@register_rule_handler("price_outdated")
@register_rule_handler("stale_price_days")
async def handle_price_outdated(rule: AlertRule) -> list[AlertEvent]:
    stale_days = int(rule.params.get("stale_days", SETTINGS.STALE_DAYS))
    rows = await query_stale_price_lists(stale_days)
    if not rows:
        return []
    context = _build_context(
        rule,
        _rows_to_dicts(rows),
        params={"stale_days": stale_days},
    )
    return _render_events(rule, context, dedupe_hint=f"{stale_days}", template_fallback="price_outdated")


@register_rule_handler("custom")
async def handle_custom(rule: AlertRule) -> list[AlertEvent]:
    payload = rule.params.get("payload")
    if not payload:
        _LOGGER.info("alert_rule.custom.no_payload", rule_id=rule.id)
        return []
    rows = payload if isinstance(payload, list) else [payload]
    context = _build_context(rule, rows, params=rule.params)
    return _render_events(rule, context, dedupe_hint="custom", template_fallback="fallback")


__all__ = [
    "AlertEvent",
    "evaluate_rule",
    "register_rule_handler",
    "get_rule_handler",
    "render_template",
    "init_db_pool",
    "close_db_pool",
    "query_roi_breaches",
    "query_price_increase",
    "query_buybox_drop",
    "query_high_returns",
    "query_stale_price_lists",
]
