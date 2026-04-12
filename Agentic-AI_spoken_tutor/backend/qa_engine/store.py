"""
In-memory QA store for MVP development.

This acts as a temporary persistence layer until PostgreSQL is integrated.
"""

from threading import Lock

from backend.qa_engine.config import ItemStatus
from backend.qa_engine.schemas import ItemLifecycle, QAValidationReport, QuestionItem

_ITEMS: dict[str, QuestionItem] = {}
_LIFECYCLES: dict[str, ItemLifecycle] = {}
_REPORTS: dict[str, QAValidationReport] = {}
_LOCK = Lock()


def save_item(item: QuestionItem) -> None:
    with _LOCK:
        _ITEMS[item.item_id] = item


def get_item(item_id: str) -> QuestionItem | None:
    with _LOCK:
        return _ITEMS.get(item_id)


def list_items() -> list[QuestionItem]:
    with _LOCK:
        return list(_ITEMS.values())


def save_lifecycle(lifecycle: ItemLifecycle) -> None:
    with _LOCK:
        _LIFECYCLES[lifecycle.item_id] = lifecycle


def get_lifecycle(item_id: str) -> ItemLifecycle | None:
    with _LOCK:
        return _LIFECYCLES.get(item_id)


def save_report(report: QAValidationReport) -> None:
    with _LOCK:
        _REPORTS[report.report_id] = report


def get_report(report_id: str) -> QAValidationReport | None:
    with _LOCK:
        return _REPORTS.get(report_id)


def list_active_items(exclude_item_id: str | None = None) -> list[QuestionItem]:
    with _LOCK:
        items = []
        for item_id, item in _ITEMS.items():
            lifecycle = _LIFECYCLES.get(item_id)
            if not lifecycle:
                continue
            current_status = getattr(lifecycle.current_status, "value", lifecycle.current_status)
            if current_status == ItemStatus.ACTIVE.value:
                if exclude_item_id and item_id == exclude_item_id:
                    continue
                items.append(item)
        return items
