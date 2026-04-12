"""
Assessment Scorer

Text-based scoring engine implementing the IELTS Speaking assessment rubric.
Since audio is unavailable, Pronunciation is excluded; the three scoreable
criteria are Fluency & Coherence (FC), Lexical Resource (LR), and
Grammatical Range & Accuracy (GRA).

All scoring is deterministic (no LLM calls) — fully auditable.

Scoring scale: 1.0 – 9.0 in 0.5-band steps (standard IELTS convention).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Linguistic resources
# ---------------------------------------------------------------------------

DISCOURSE_MARKERS: set[str] = {
    "however", "furthermore", "moreover", "therefore", "consequently",
    "in addition", "on the other hand", "for example", "for instance",
    "in contrast", "as a result", "although", "despite", "nevertheless",
    "in conclusion", "firstly", "secondly", "thirdly", "finally",
    "additionally", "similarly", "in fact", "actually", "personally",
    "to be honest", "in my opinion", "i believe", "i think", "because of this",
    "having said that", "on top of that", "what is more", "at the same time",
    "to sum up", "to begin with", "apart from that",
}

SUBORDINATING_CONJUNCTIONS: set[str] = {
    "although", "because", "since", "while", "whereas", "unless",
    "until", "even though", "as long as", "in order to", "so that",
    "provided that", "when", "whenever", "wherever", "whether",
}

# Simple past / present perfect / future / conditional markers
TENSE_MARKERS: dict[str, set[str]] = {
    "past":       {"was", "were", "had", "did", "went", "came", "said", "told",
                   "made", "took", "gave", "found", "knew", "thought", "became"},
    "present":    {"is", "are", "have", "has", "do", "does", "am", "seems",
                   "appears", "feel", "think", "believe", "consider"},
    "future":     {"will", "would", "shall", "going to", "plan to", "intend to",
                   "hope to"},
    "conditional": {"would", "could", "might", "should", "if", "unless"},
}

# Stopwords to exclude before TTR calculation
STOPWORDS: set[str] = {
    "a", "an", "the", "and", "but", "or", "so", "yet", "nor",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "up", "about", "into", "through", "during", "before", "after",
    "above", "below", "between", "out", "off", "over", "under",
    "again", "very", "just", "also", "then", "there", "here",
    "what", "which", "who", "how", "when", "where", "why",
    "not", "no", "can", "will", "would", "could", "should", "may",
    "might", "shall",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> list[str]:
    """Lowercase words only, strip punctuation."""
    return re.findall(r"\b[a-z]+\b", text.lower())


def _sentences(text: str) -> list[str]:
    """Split into sentences on terminal punctuation."""
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]


def _content_words(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def _count_discourse_markers(text: str) -> int:
    lower = text.lower()
    return sum(1 for m in DISCOURSE_MARKERS if m in lower)


def _count_subordinating(text: str) -> int:
    lower = text.lower()
    return sum(1 for c in SUBORDINATING_CONJUNCTIONS if re.search(r"\b" + c + r"\b", lower))


def _tense_variety(tokens: list[str]) -> int:
    """Returns count of distinct tense categories present (0–4)."""
    found = set()
    token_set = set(tokens)
    for tense, markers in TENSE_MARKERS.items():
        if token_set & markers:
            found.add(tense)
    return len(found)


def _clamp_band(value: float) -> float:
    """Clamp to [1.0, 9.0] and round to nearest 0.5."""
    clamped = max(1.0, min(9.0, value))
    return round(clamped * 2) / 2


# ---------------------------------------------------------------------------
# Three scoreable criteria
# ---------------------------------------------------------------------------

def score_fluency_coherence(
    text: str,
    task_type: str = "part_1",
) -> float:
    """
    Fluency & Coherence proxy from text length and discourse organisation.

    Expected word counts per task type (informed by IELTS examiner notes):
      part_1 / cefr_basic / cefr_simple : 50–120 words
      part_2 / cefr_intermediate        : 150–250 words
      part_3 / cefr_upper_intermediate  : 80–200 words
    """
    tokens = _tokenise(text)
    word_count = len(tokens)
    sentences = _sentences(text)
    num_sentences = max(len(sentences), 1)
    marker_count = _count_discourse_markers(text)

    # --- Length score (0–8) ---
    short_task = task_type in (
        "part_1", "cefr_basic", "cefr_simple",
    )
    long_task = task_type in ("part_2",)

    if short_task:
        # Expect 50–120 words for a good Band 5–7
        length_score = min(word_count / 15.0, 8.0)
    elif long_task:
        length_score = min(word_count / 25.0, 8.0)
    else:
        # part_3 / intermediate
        length_score = min(word_count / 20.0, 8.0)

    # --- Discourse marker bonus (0–1) ---
    marker_bonus = min(marker_count * 0.25, 1.0)

    # --- Sentence variety penalty (many single-word sentences = low fluency) ---
    avg_sent_len = word_count / num_sentences
    if avg_sent_len < 5:
        coherence_penalty = 1.5
    elif avg_sent_len < 8:
        coherence_penalty = 0.5
    else:
        coherence_penalty = 0.0

    raw = length_score + marker_bonus - coherence_penalty
    return _clamp_band(raw)


def score_lexical_resource(text: str) -> float:
    """
    Lexical Resource via Type-Token Ratio and vocabulary sophistication.

    TTR = unique content words / total content words
    Avg content word length acts as a sophistication proxy.
    """
    tokens = _tokenise(text)
    content = _content_words(tokens)

    if not content:
        return 1.0

    total = len(content)
    unique = len(set(content))
    ttr = unique / total

    avg_len = sum(len(w) for w in content) / total

    # TTR → base band
    if ttr >= 0.80:
        ttr_band = 8.0
    elif ttr >= 0.70:
        ttr_band = 7.0
    elif ttr >= 0.60:
        ttr_band = 6.0
    elif ttr >= 0.50:
        ttr_band = 5.0
    elif ttr >= 0.40:
        ttr_band = 4.0
    elif ttr >= 0.30:
        ttr_band = 3.0
    else:
        ttr_band = 2.0

    # Avg word length bonus (> 6 chars = more sophisticated)
    len_bonus = max(0.0, (avg_len - 4.0) * 0.3)

    raw = ttr_band + len_bonus
    return _clamp_band(raw)


def score_grammatical_range(text: str) -> float:
    """
    Grammatical Range & Accuracy via sentence complexity and tense variety.

    Longer sentences with subordinating clauses and tense variety → higher bands.
    """
    tokens = _tokenise(text)
    sentences = _sentences(text)
    num_sentences = max(len(sentences), 1)
    word_count = max(len(tokens), 1)

    avg_sent_len = word_count / num_sentences
    sub_count = _count_subordinating(text)
    tense_count = _tense_variety(tokens)

    # Average sentence length → base band
    if avg_sent_len >= 25:
        base = 8.0
    elif avg_sent_len >= 20:
        base = 7.0
    elif avg_sent_len >= 16:
        base = 6.0
    elif avg_sent_len >= 12:
        base = 5.0
    elif avg_sent_len >= 8:
        base = 4.0
    elif avg_sent_len >= 5:
        base = 3.0
    else:
        base = 2.0

    # Complexity bonus: subordinating conjunctions
    complexity_bonus = min(sub_count * 0.25, 1.0)

    # Tense variety bonus (0–4 distinct tenses found)
    tense_bonus = min(tense_count * 0.25, 1.0)

    raw = base + complexity_bonus + tense_bonus
    return _clamp_band(raw)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

@dataclass
class ScoringResult:
    fluency_coherence: float
    lexical_resource: float
    grammatical_range: float
    overall_band: float
    cefr_level: str
    word_count: int
    sentence_count: int
    discourse_markers_found: int
    ttr: float
    avg_sentence_length: float


_CEFR_THRESHOLDS = [
    (8.5, "c2"),
    (7.0, "c1"),
    (5.5, "b2"),
    (4.0, "b1"),
    (3.0, "a2"),
    (0.0, "a1"),
]


def _band_to_cefr(band: float) -> str:
    for threshold, level in _CEFR_THRESHOLDS:
        if band >= threshold:
            return level
    return "a1"


def score_response(
    transcript: str,
    task_type: str = "part_1",
) -> ScoringResult:
    """
    Full scoring pipeline for one learner response.

    Args:
        transcript:  Learner's spoken response text
        task_type:   Question type (part_1 | part_2 | part_3 | cefr_*)

    Returns:
        ScoringResult with per-criterion bands + overall IELTS band + CEFR level
    """
    if not transcript or not transcript.strip():
        return ScoringResult(
            fluency_coherence=1.0,
            lexical_resource=1.0,
            grammatical_range=1.0,
            overall_band=1.0,
            cefr_level="a1",
            word_count=0,
            sentence_count=0,
            discourse_markers_found=0,
            ttr=0.0,
            avg_sentence_length=0.0,
        )

    tokens = _tokenise(transcript)
    content = _content_words(tokens)
    sentences = _sentences(transcript)

    fc  = score_fluency_coherence(transcript, task_type)
    lr  = score_lexical_resource(transcript)
    gra = score_grammatical_range(transcript)

    # Overall = arithmetic mean of the three text-scoreable criteria
    overall_raw = (fc + lr + gra) / 3.0
    overall_band = _clamp_band(overall_raw)
    cefr = _band_to_cefr(overall_band)

    ttr = (
        len(set(content)) / len(content)
        if content else 0.0
    )
    avg_sent_len = (
        len(tokens) / max(len(sentences), 1)
    )

    return ScoringResult(
        fluency_coherence=fc,
        lexical_resource=lr,
        grammatical_range=gra,
        overall_band=overall_band,
        cefr_level=cefr,
        word_count=len(tokens),
        sentence_count=len(sentences),
        discourse_markers_found=_count_discourse_markers(transcript),
        ttr=round(ttr, 3),
        avg_sentence_length=round(avg_sent_len, 1),
    )
