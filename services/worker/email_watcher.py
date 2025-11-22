import asyncio
import datetime
import email
import os
import tempfile
from collections.abc import Iterable
from email.utils import getaddresses, parseaddr
from typing import Any

import structlog
from imapclient import IMAPClient
from sqlalchemy import create_engine, insert, select, text, update  # noqa: F401
from sqlalchemy.exc import SQLAlchemyError

from awa_common.llm import EmailLLMResult, LLMClient
from awa_common.metrics import record_email_enriched, record_email_needs_manual_review
from awa_common.minio import create_boto3_client, get_bucket_name
from awa_common.settings import settings
from awa_common.utils.env import env_str
from services.api.app.decision.models import METADATA, inbox_messages, inbox_threads
from services.etl import load_csv

logger = structlog.get_logger(__name__).bind(component="email_watcher")

BUCKET = get_bucket_name()


def _parse_addresses(values: Iterable[str]) -> list[str]:
    return [addr for _, addr in getaddresses(list(values)) if addr]


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if isinstance(payload, (bytes, bytearray)):
                    try:
                        return payload.decode(part.get_content_charset() or "utf-8")
                    except Exception:
                        continue
                if isinstance(payload, str):
                    return payload
                continue
        for part in msg.walk():
            if part.get_content_type().startswith("text/"):
                payload = part.get_payload(decode=True)
                if isinstance(payload, (bytes, bytearray)):
                    try:
                        return payload.decode(part.get_content_charset() or "utf-8")
                    except Exception:
                        continue
    payload = msg.get_payload(decode=True)
    if isinstance(payload, (bytes, bytearray)):
        try:
            return payload.decode(msg.get_content_charset() or "utf-8")
        except Exception:
            return payload.decode("utf-8", errors="ignore")
    if isinstance(payload, str):
        return payload
    return ""


def _message_id(msg: email.message.Message, fallback: str) -> str:
    mid = msg.get("Message-ID") or msg.get("Message-Id")
    if mid:
        return mid.strip()
    return fallback


def _thread_id(msg: email.message.Message, message_id: str) -> str:
    reply_to = msg.get("In-Reply-To") or msg.get("References")
    if reply_to:
        return reply_to.strip()
    return message_id


def _has_price_list_attachment(msg: email.message.Message) -> bool:
    for part in msg.walk():
        name = part.get_filename()
        if not name:
            continue
        lower = name.lower()
        if lower.endswith((".csv", ".xlsx", ".xlsm", ".xls", ".pdf")):
            return True
    return False


class EmailClassificationStore:
    def __init__(self, db_url: str):  # pragma: no cover - exercised via integration
        self.engine = create_engine(db_url)
        try:
            METADATA.create_all(self.engine)
        except AttributeError:
            # Test double may not implement full SQLAlchemy engine API; skip DDL when unsupported.
            pass

    def close(self) -> None:  # pragma: no cover - trivial
        self.engine.dispose()

    def persist_message(  # pragma: no cover - DB side effects
        self,
        payload: dict[str, Any],
        classification: EmailLLMResult | None,
        error: str | None = None,
    ) -> None:
        intent = classification.intent.value if classification else None
        facts = classification.facts.model_dump() if classification else {}
        provider = classification.provider if classification else None
        confidence = classification.confidence if classification else None
        recipients = {"to": payload.get("to", []), "cc": payload.get("cc", [])}
        needs_manual_review = bool(error) or classification is None
        received_at = payload.get("received_at") or datetime.datetime.now(datetime.UTC)
        with self.engine.begin() as conn:
            existing_thread = conn.execute(
                select(inbox_threads.c.thread_id).where(inbox_threads.c.thread_id == payload["thread_id"])
            ).scalar_one_or_none()
            if existing_thread:
                conn.execute(
                    update(inbox_threads)
                    .where(inbox_threads.c.thread_id == payload["thread_id"])
                    .values(
                        last_cls=intent,
                        **{"class": intent},
                        last_msg_at=received_at,
                        updated_at=datetime.datetime.now(datetime.UTC),
                    )
                )
            else:
                conn.execute(
                    insert(inbox_threads).values(
                        thread_id=payload["thread_id"],
                        state="open",
                        **{"class": intent},
                        last_cls=intent,
                        last_msg_at=received_at,
                    )
                )
            already = conn.execute(
                select(inbox_messages.c.message_id).where(inbox_messages.c.message_id == payload["message_id"])
            ).scalar_one_or_none()
            if already:
                return
            conn.execute(
                insert(inbox_messages).values(
                    message_id=payload["message_id"],
                    thread_id=payload["thread_id"],
                    subject=payload.get("subject"),
                    sender=payload.get("sender"),
                    recipients=recipients,
                    body=payload.get("body"),
                    has_price_list_attachment=payload.get("has_price_list_attachment", False),
                    language=payload.get("language"),
                    intent=intent,
                    facts=facts,
                    llm_provider=provider,
                    confidence=confidence,
                    needs_manual_review=needs_manual_review,
                    error=error,
                )
            )


async def _classify_email_async(client: LLMClient, payload: dict[str, Any]) -> tuple[EmailLLMResult | None, str | None]:
    # pragma: no cover - network-dependent
    try:
        result = await client.classify_email(
            subject=payload.get("subject", ""),
            body=payload.get("body", ""),
            sender=payload.get("sender", ""),
            to=payload.get("to", []),
            cc=payload.get("cc", []),
            has_price_list_attachment=payload.get("has_price_list_attachment", False),
            language=payload.get("language"),
            metadata={"sender_domain": payload.get("sender_domain")},
        )
        record_email_enriched("success")
        return result, None
    except Exception as exc:  # pragma: no cover - network failures
        record_email_enriched("error")
        record_email_needs_manual_review(exc.__class__.__name__)
        logger.warning(
            "email.llm.failed",
            message_id=payload.get("message_id"),
            provider_hint=payload.get("provider_hint"),
            error=str(exc),
            error_type=exc.__class__.__name__,
        )
        return None, str(exc)


def _normalize_email_message(msg: email.message.Message, uid: int) -> dict[str, Any]:
    fallback_id = f"uid-{uid}"
    message_id = _message_id(msg, fallback_id)
    thread_id = _thread_id(msg, message_id)
    sender = parseaddr(msg.get("From", ""))[1]
    to = _parse_addresses(msg.get_all("To", []))
    cc = _parse_addresses(msg.get_all("Cc", []))
    sender_domain = sender.split("@", 1)[1].lower() if sender and "@" in sender else None
    received_at = None
    try:
        date_value = msg.get("Date")
        if date_value:
            received_at = email.utils.parsedate_to_datetime(date_value)
    except Exception:
        received_at = None
    return {
        "message_id": message_id,
        "thread_id": thread_id,
        "subject": msg.get("Subject"),
        "sender": sender,
        "sender_domain": sender_domain,
        "to": to,
        "cc": cc,
        "body": (_extract_body(msg) or "")[:16000],
        "has_price_list_attachment": _has_price_list_attachment(msg),
        "language": msg.get_content_charset() or None,
        "received_at": received_at or datetime.datetime.now(datetime.UTC),
    }


def main() -> dict[str, str]:
    """Upload CSV/XLSX attachments to MinIO and trigger ingestion.

    Returns {"status": "success"} when processing completes.
    """
    email_cfg = getattr(settings, "email", None)
    host = env_str("IMAP_HOST", default=email_cfg.host if email_cfg else getattr(settings, "IMAP_HOST", None))
    user = env_str("IMAP_USER", default=email_cfg.username if email_cfg else getattr(settings, "IMAP_USER", None))
    password = env_str("IMAP_PASS", default=email_cfg.password if email_cfg else getattr(settings, "IMAP_PASS", None))
    if not host or not user or not password:
        raise RuntimeError("IMAP configuration is missing")
    s3 = create_boto3_client()
    llm_enabled = bool(getattr(settings, "llm", None) and getattr(settings.llm, "enable_email", False))
    if getattr(settings, "TESTING", False) or os.getenv("PYTEST_CURRENT_TEST"):
        llm_enabled = False
    llm_client = LLMClient() if llm_enabled else None
    store = EmailClassificationStore(settings.DATABASE_URL) if llm_enabled else None

    with IMAPClient(host) as client:
        client.login(user, password)
        client.select_folder("INBOX")
        for uid in client.search(["UNSEEN"]):
            msg_bytes = client.fetch(uid, ["RFC822"])[uid][b"RFC822"]
            msg = email.message_from_bytes(msg_bytes)
            normalized = _normalize_email_message(msg, uid)
            classification: EmailLLMResult | None = None
            error_detail: str | None = None
            if llm_enabled and llm_client:  # pragma: no cover - network-assisted classification
                classification, error_detail = asyncio.run(_classify_email_async(llm_client, normalized))
            if store:
                try:
                    store.persist_message(normalized, classification, error=error_detail)
                except SQLAlchemyError as db_exc:  # pragma: no cover - DB failure path
                    record_email_needs_manual_review("db_error")
                    logger.error(
                        "email.llm.persist_failed",
                        message_id=normalized.get("message_id"),
                        error=str(db_exc),
                        error_type=db_exc.__class__.__name__,
                    )
            for part in msg.walk():
                name = part.get_filename()
                if not name:
                    continue
                if not (name.endswith(".csv") or name.endswith(".xlsx")):
                    continue
                data: Any = part.get_payload(decode=True)
                if not isinstance(data, bytes | bytearray):
                    data = b""
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                today = datetime.date.today().strftime("%Y-%m")
                dst = f"raw/amazon/{today}/{name}"
                s3.upload_file(tmp_path, BUCKET, dst)
                result = load_csv.main(["--source", f"minio://{dst}", "--table", "auto"])
                load_id = None
                inserted = None
                if isinstance(result, tuple) and len(result) == 2:
                    load_id, inserted = result
                elif isinstance(result, dict):
                    load_id = result.get("load_log_id")
                    inserted = result.get("rows")
                if load_id is not None and inserted is not None:
                    engine = create_engine(settings.DATABASE_URL)
                    with engine.begin() as db:
                        db.execute(
                            text("UPDATE load_log SET status='success', inserted_rows=:n WHERE id=:id"),
                            {"n": inserted, "id": load_id},
                        )
                    engine.dispose()
                os.remove(tmp_path)
            client.add_flags(uid, ["\\Seen"])
    if store:
        store.close()
    return {"status": "success"}


if __name__ == "__main__":
    main()
