"""
Feedback Generator

Produces criterion-specific, actionable written feedback for each IELTS
scoring dimension based on the assessed band.

All messages are deterministic strings — no LLM calls required.
The output is structured so the front-end can render colour-coded cards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.agents.assessment_scoring.scorer import ScoringResult


# ---------------------------------------------------------------------------
# Feedback message banks keyed by (lower_bound, upper_bound) band ranges
# ---------------------------------------------------------------------------

_FC_DESCRIPTIONS: list[tuple[tuple[float, float], str]] = [
    ((1.0, 2.5), "Your response was very brief. You provided little information and stopped frequently."),
    ((3.0, 3.5), "Your answer was short and hesitant. Some ideas were present but not developed."),
    ((4.0, 4.5), "You gave a basic response. There were some pauses and limited development of ideas."),
    ((5.0, 5.5), "You provided a moderate response with some development, though hesitations were noticeable."),
    ((6.0, 6.5), "Your response was generally fluent with reasonable development of most ideas."),
    ((7.0, 7.5), "You spoke fluently with good cohesion. Ideas were logically developed and connected."),
    ((8.0, 8.5), "Excellent fluency and coherence. Ideas flowed naturally with effective use of discourse markers."),
    ((9.0, 9.0), "Outstanding fluency and coherence — native-like natural delivery with flawless organisation."),
]

_FC_TIPS: list[tuple[tuple[float, float], list[str]]] = [
    ((1.0, 3.5), [
        "Aim to speak for at least 1–2 minutes on each question.",
        "Use the PEER technique: Point → Evidence → Example → Restate.",
        "Practise filler phrases: 'That's a good question…', 'Let me think about that…'",
    ]),
    ((4.0, 5.5), [
        "Develop each point with a specific example or personal story.",
        "Use simple connectors: 'because', 'so', 'and then', 'after that'.",
        "Record yourself speaking for 1 minute daily on random topics.",
    ]),
    ((6.0, 7.5), [
        "Add more discourse markers: 'Furthermore…', 'On the other hand…', 'In contrast…'",
        "Vary your sentence length — mix short punchy sentences with longer explanations.",
        "Avoid repeating the same phrases; paraphrase your points instead.",
    ]),
    ((8.0, 9.0), [
        "Work on stylistic variety and rhetorical devices to reach the top band.",
        "Ensure every point connects to the overarching argument naturally.",
    ]),
]

_LR_DESCRIPTIONS: list[tuple[tuple[float, float], str]] = [
    ((1.0, 2.5), "Very limited vocabulary. Most words were simple and heavily repeated."),
    ((3.0, 3.5), "Basic vocabulary with significant repetition. Range was insufficient for the topic."),
    ((4.0, 4.5), "Limited vocabulary range. You relied on common words and phrases without much variety."),
    ((5.0, 5.5), "Adequate vocabulary for the task, though repetition and imprecise choices were frequent."),
    ((6.0, 6.5), "A satisfactory range of vocabulary. Meaning was clear despite some imprecision."),
    ((7.0, 7.5), "Good vocabulary range with effective use of less common items and collocations."),
    ((8.0, 8.5), "Wide and precise vocabulary. Idiomatic usage and topic-specific terms used naturally."),
    ((9.0, 9.0), "Near-native vocabulary breadth. Rare and nuanced word choices used appropriately."),
]

_LR_TIPS: list[tuple[tuple[float, float], list[str]]] = [
    ((1.0, 3.5), [
        "Learn 5 new topic words each day using spaced repetition (e.g., Anki).",
        "Replace general words: 'good' → 'beneficial/effective', 'bad' → 'detrimental/problematic'.",
        "Practise using nouns and verbs specific to each topic (technology, environment, health).",
    ]),
    ((4.0, 5.5), [
        "Use synonyms and paraphrases to avoid word repetition.",
        "Learn word families: 'effect / effective / effectively / effectiveness'.",
        "Read graded English articles (BBC Learning English, VOA) to build topic vocabulary.",
    ]),
    ((6.0, 7.5), [
        "Learn common collocations: 'raise awareness', 'tackle a problem', 'have a detrimental impact'.",
        "Practise topic-specific idioms appropriate to the IELTS context.",
        "Notice how native speakers group words in podcasts and films.",
    ]),
    ((8.0, 9.0), [
        "Explore advanced academic and technical vocabulary specific to Part 3 themes.",
        "Ensure natural use of idiomatic expressions without forced or unnatural insertions.",
    ]),
]

_GRA_DESCRIPTIONS: list[tuple[tuple[float, float], str]] = [
    ((1.0, 2.5), "Very limited grammatical structures. Only isolated words or simple fixed phrases were used."),
    ((3.0, 3.5), "Simple sentences only. Frequent errors made meaning difficult to follow at times."),
    ((4.0, 4.5), "Basic sentence structures were used but complex structures were largely absent or error-prone."),
    ((5.0, 5.5), "A mix of simple and limited complex sentences. Errors were noticeable but rarely caused confusion."),
    ((6.0, 6.5), "A mix of simple and complex structures. Some errors present but meaning remained clear."),
    ((7.0, 7.5), "Good range of structures used with reasonable accuracy. Errors were minor and infrequent."),
    ((8.0, 8.5), "Wide range of complex structures with high accuracy. Only very minor slips present."),
    ((9.0, 9.0), "Full range of structures used with consistent accuracy — native-level grammatical control."),
]

_GRA_TIPS: list[tuple[tuple[float, float], list[str]]] = [
    ((1.0, 3.5), [
        "Start with Subject + Verb + Object sentences: 'I enjoy cooking because it relaxes me.'",
        "Practise adding 'because', 'so', 'and' to join two simple sentences.",
        "Use basic tenses correctly: present simple for habits, past simple for stories.",
    ]),
    ((4.0, 5.5), [
        "Practise relative clauses: 'The city where I grew up has changed significantly.'",
        "Use conditional sentences: 'If I had more time, I would learn photography.'",
        "Use a range of tenses — don't stick only to present simple.",
    ]),
    ((6.0, 7.5), [
        "Use passive voice where appropriate: 'This problem has been widely discussed.'",
        "Practise complex noun phrases: 'the rapid development of AI technology'.",
        "Ensure subject-verb agreement is consistent, especially with collective nouns.",
    ]),
    ((8.0, 9.0), [
        "Explore advanced grammatical structures: nominal clauses, cleft sentences.",
        "Review any subtle errors in article/preposition usage.",
    ]),
]

_OVERALL_DESCRIPTIONS: dict[str, str] = {
    "a1": "You are at an A1 (Beginner) level. The priority is building basic vocabulary and simple sentence structures.",
    "a2": "You are at an A2 (Elementary) level. Focus on expanding vocabulary and producing short, connected sentences.",
    "b1": "You are at a B1 (Intermediate) level. You can communicate on familiar topics but need more range and development.",
    "b2": "You are at a B2 (Upper-Intermediate) level. You communicate clearly, with good range and reasonable accuracy.",
    "c1": "You are at a C1 (Advanced) level. Your English is effective and flexible with only occasional imprecision.",
    "c2": "You are at a C2 (Proficient) level. You demonstrate near-native fluency, accuracy, and expressive range.",
    "unknown": "Your level could not be determined from this response. Please provide a longer answer.",
}


# ---------------------------------------------------------------------------
# Lookup helper
# ---------------------------------------------------------------------------

def _match_range(
    band: float,
    table: list[tuple[tuple[float, float], Any]],
) -> Any:
    for (lo, hi), value in table:
        if lo <= band <= hi:
            return value
    # fallback to last entry
    return table[-1][1]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class FeedbackBundle:
    fc_description: str
    lr_description: str
    gr_description: str
    fc_tips: list[str]
    lr_tips: list[str]
    gr_tips: list[str]
    overall_description: str
    band_label: str          # e.g. "Band 6.0"
    cefr_label: str          # e.g. "B2"
    encouragement: str
    next_focus: str          # highest-priority area to work on


def generate_feedback(result: ScoringResult) -> FeedbackBundle:
    """
    Generate structured feedback bundle from a ScoringResult.
    Returns deterministic, criterion-specific feedback.
    """
    fc_desc  = _match_range(result.fluency_coherence,   _FC_DESCRIPTIONS)
    lr_desc  = _match_range(result.lexical_resource,    _LR_DESCRIPTIONS)
    gr_desc  = _match_range(result.grammatical_range,   _GRA_DESCRIPTIONS)

    fc_tips  = list(_match_range(result.fluency_coherence,  _FC_TIPS))
    lr_tips  = list(_match_range(result.lexical_resource,   _LR_TIPS))
    gr_tips  = list(_match_range(result.grammatical_range,  _GRA_TIPS))

    cefr = result.cefr_level.lower()
    overall_desc = _OVERALL_DESCRIPTIONS.get(cefr, _OVERALL_DESCRIPTIONS["unknown"])

    # Determine highest-priority focus area (lowest scoring criterion)
    scores = {
        "Fluency & Coherence":       result.fluency_coherence,
        "Lexical Resource":          result.lexical_resource,
        "Grammatical Range":         result.grammatical_range,
    }
    weakest = min(scores.items(), key=lambda kv: kv[1])[0]

    # Encouragement message keyed to overall band
    if result.overall_band >= 7.0:
        encouragement = "Excellent work! You are performing at a high level."
    elif result.overall_band >= 5.5:
        encouragement = "Good effort! With consistent practice you can reach C1/Band 7."
    elif result.overall_band >= 4.0:
        encouragement = "You are making progress! Focus on the tips below to move to the next level."
    else:
        encouragement = "Keep practising! Every session builds your confidence and skill."

    return FeedbackBundle(
        fc_description=str(fc_desc),
        lr_description=str(lr_desc),
        gr_description=str(gr_desc),
        fc_tips=fc_tips,
        lr_tips=lr_tips,
        gr_tips=gr_tips,
        overall_description=overall_desc,
        band_label=f"Band {result.overall_band:.1f}",
        cefr_label=cefr.upper(),
        encouragement=encouragement,
        next_focus=weakest,
    )
