from __future__ import annotations

from backend.db.models import (  # noqa: F401
    AuthSessionORM,
    ClassORM,
    ItemLifecycleORM,
    LearnerProfileORM,
    PracticeSessionORM,
    ProgressRecordORM,
    QAValidationReportORM,
    QuestionItemORM,
    RawDocumentORM,
    ScreeningPackORM,
    UserAccountORM,
)
from backend.db.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)