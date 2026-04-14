"""Database-backed QA store."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from backend.db.models import ItemLifecycleORM, QAValidationReportORM, QuestionItemORM
from backend.db.session import db_session
from backend.qa_engine.config import ItemStatus
from backend.qa_engine.schemas import ItemLifecycle, QAValidationReport, QuestionItem


def save_item(item: QuestionItem) -> None:
    with db_session() as db:
        row = db.scalar(select(QuestionItemORM).where(QuestionItemORM.item_id == item.item_id))
        payload = item.model_dump(mode="json")
        if row:
            row.payload_json = payload
            row.updated_at = datetime.utcnow()
        else:
            db.add(QuestionItemORM(item_id=item.item_id, payload_json=payload, updated_at=datetime.utcnow()))


def get_item(item_id: str) -> QuestionItem | None:
    with db_session() as db:
        row = db.scalar(select(QuestionItemORM).where(QuestionItemORM.item_id == item_id))
        return QuestionItem.model_validate(row.payload_json) if row else None


def list_items() -> list[QuestionItem]:
    with db_session() as db:
        rows = db.scalars(select(QuestionItemORM)).all()
        return [QuestionItem.model_validate(row.payload_json) for row in rows]


def save_lifecycle(lifecycle: ItemLifecycle) -> None:
    with db_session() as db:
        row = db.scalar(select(ItemLifecycleORM).where(ItemLifecycleORM.item_id == lifecycle.item_id))
        payload = lifecycle.model_dump(mode="json")
        if row:
            row.payload_json = payload
            row.updated_at = datetime.utcnow()
        else:
            db.add(ItemLifecycleORM(item_id=lifecycle.item_id, payload_json=payload, updated_at=datetime.utcnow()))


def get_lifecycle(item_id: str) -> ItemLifecycle | None:
    with db_session() as db:
        row = db.scalar(select(ItemLifecycleORM).where(ItemLifecycleORM.item_id == item_id))
        return ItemLifecycle.model_validate(row.payload_json) if row else None


def save_report(report: QAValidationReport) -> None:
    with db_session() as db:
        row = db.scalar(select(QAValidationReportORM).where(QAValidationReportORM.report_id == report.report_id))
        payload = report.model_dump(mode="json")
        if row:
            row.item_id = report.item_id
            row.payload_json = payload
        else:
            db.add(QAValidationReportORM(report_id=report.report_id, item_id=report.item_id, payload_json=payload))


def get_report(report_id: str) -> QAValidationReport | None:
    with db_session() as db:
        row = db.scalar(select(QAValidationReportORM).where(QAValidationReportORM.report_id == report_id))
        return QAValidationReport.model_validate(row.payload_json) if row else None


def list_active_items(exclude_item_id: str | None = None) -> list[QuestionItem]:
    with db_session() as db:
        lifecycle_rows = db.scalars(select(ItemLifecycleORM)).all()
        active_ids = []
        for lifecycle_row in lifecycle_rows:
            lifecycle = ItemLifecycle.model_validate(lifecycle_row.payload_json)
            current_status = getattr(lifecycle.current_status, "value", lifecycle.current_status)
            if current_status == ItemStatus.ACTIVE.value:
                if exclude_item_id and lifecycle.item_id == exclude_item_id:
                    continue
                active_ids.append(lifecycle.item_id)

        if not active_ids:
            return []

        rows = db.scalars(select(QuestionItemORM).where(QuestionItemORM.item_id.in_(active_ids))).all()
        return [QuestionItem.model_validate(row.payload_json) for row in rows]
