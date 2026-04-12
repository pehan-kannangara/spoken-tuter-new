"""
Seed Loader

Loads all pre-approved questions from the question bank into the QA store
and transitions them straight to ACTIVE status, bypassing the QA pipeline.

Called once at application startup via FastAPI lifespan.
"""

from __future__ import annotations

import logging
from datetime import datetime

from backend.data.question_bank import ALL_SEED_QUESTIONS
from backend.qa_engine.config import ItemStatus
from backend.qa_engine.lifecycle import create_lifecycle, transition_item
from backend.qa_engine.schemas import (
    IELTSSpeakingPart,
    ItemStatus as ItemStatusEnum,
    LanguageDomain,
    Pathway,
    QuestionItem,
    SkillFocus,
    TargetLevel,
)
from backend.qa_engine.store import get_item, save_item, save_lifecycle

logger = logging.getLogger(__name__)


def _coerce(value: str, enum_cls: type) -> object:
    """Return enum member matching value string, or the value itself if not found."""
    try:
        return enum_cls(value)
    except ValueError:
        return value


def seed_question_bank(force_reload: bool = False) -> int:
    """
    Insert all seed questions into the in-memory QA store as ACTIVE items.

    Args:
        force_reload: If True, re-seed even items already in the store.

    Returns:
        Number of items seeded (skipped duplicates not counted).
    """
    seeded = 0
    skipped = 0

    for raw in ALL_SEED_QUESTIONS:
        item_id = raw["item_id"]

        if not force_reload and get_item(item_id) is not None:
            skipped += 1
            continue

        try:
            # Parse generation_timestamp
            gen_ts = raw.get("generation_timestamp")
            if isinstance(gen_ts, str):
                gen_ts = datetime.fromisoformat(gen_ts)
            elif gen_ts is None:
                gen_ts = datetime.utcnow()

            item = QuestionItem(
                item_id=item_id,
                spec_id=raw["spec_id"],
                instruction=raw["instruction"],
                prompt_text=raw.get("prompt_text"),
                pathway=_coerce(raw["pathway"], Pathway),
                target_level=_coerce(raw["target_level"], TargetLevel),
                task_type=_coerce(raw["task_type"], IELTSSpeakingPart),
                domain=_coerce(raw["domain"], LanguageDomain),
                skill_focus=_coerce(raw["skill_focus"], SkillFocus),
                generated_by=raw.get("generated_by", "seed_bank"),
                generation_timestamp=gen_ts,
                status=ItemStatus.ACTIVE,
            )
        except Exception as exc:
            logger.warning("Skipping seed item %s — parse error: %s", item_id, exc)
            continue

        # Persist item
        save_item(item)

        # Create lifecycle and fast-track to ACTIVE
        lifecycle = create_lifecycle(item, created_by="seed_loader")

        # DRAFT → AUTO_VALIDATED → ACTIVE (two hops, both valid)
        _, _, lifecycle = transition_item(
            lifecycle,
            ItemStatus.AUTO_VALIDATED,
            reason="Seed bank: pre-approved item",
            triggered_by="seed_loader",
        )
        _, _, lifecycle = transition_item(
            lifecycle,
            ItemStatus.ACTIVE,
            reason="Seed bank: activated on startup",
            triggered_by="seed_loader",
        )

        save_lifecycle(lifecycle)
        seeded += 1

    logger.info(
        "Seed loader complete — %d items seeded, %d already present (skipped).",
        seeded,
        skipped,
    )
    return seeded
