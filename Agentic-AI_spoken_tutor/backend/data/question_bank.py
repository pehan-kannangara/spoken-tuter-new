"""
Question Bank Seed Data

Representative IELTS Speaking (Part 1, 2, 3) and CEFR (A1–B2) questions.
These are pre-approved items that bypass the QA pipeline and are seeded
directly as ACTIVE items on startup.

Each entry maps to the QuestionItem Pydantic schema.
"""

from datetime import datetime

# ---------------------------------------------------------------------------
# IELTS PART 1  — Short personal questions  (target: b1 / b2)
# Expected response: 60–120 seconds
# ---------------------------------------------------------------------------
IELTS_PART_1: list[dict] = [
    # --- Home & Accommodation ---
    {
        "item_id": "QB-P1-001",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Can you tell me a bit about where you currently live?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-002",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "What do you like most about your home or neighbourhood?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-003",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Is there anything you would like to change about your home?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "everyday",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- Work & Study ---
    {
        "item_id": "QB-P1-004",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Do you currently work or are you a student? Tell me about it.",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "academic",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-005",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "What do you enjoy most about your work or studies?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "academic",
        "skill_focus": "lexical_resource",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-006",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "What are your future plans regarding your career or education?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_1",
        "domain": "academic",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- Hobbies & Leisure ---
    {
        "item_id": "QB-P1-007",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "What hobbies or leisure activities do you enjoy in your free time?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-008",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "How much time do you spend on your hobby each week?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-009",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Did you have the same hobbies when you were a child?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "everyday",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- Food & Eating ---
    {
        "item_id": "QB-P1-010",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "What kinds of food do you most enjoy eating?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "everyday",
        "skill_focus": "lexical_resource",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-011",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Do you prefer cooking at home or eating out? Why?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "everyday",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- Technology ---
    {
        "item_id": "QB-P1-012",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "How often do you use the internet, and what do you mainly use it for?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "technology",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-013",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "What do you think is the most useful piece of technology in your daily life?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_1",
        "domain": "technology",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-014",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Do you think technology has changed the way people communicate with each other?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_1",
        "domain": "technology",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- Travel ---
    {
        "item_id": "QB-P1-015",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Do you enjoy travelling? Why or why not?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "travel",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-016",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "What type of accommodation do you prefer when you travel?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "travel",
        "skill_focus": "lexical_resource",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- Music & Arts ---
    {
        "item_id": "QB-P1-017",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "What kind of music do you enjoy, and why do you like it?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "culture",
        "skill_focus": "lexical_resource",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P1-018",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Do you play any musical instruments or have you ever tried to learn one?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "culture",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- Environment ---
    {
        "item_id": "QB-P1-019",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "Do you try to be environmentally friendly in your daily life? How?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_1",
        "domain": "environment",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- Health ---
    {
        "item_id": "QB-P1-020",
        "spec_id": "SPEC-IELTS-P1",
        "instruction": "How do you try to maintain a healthy lifestyle?",
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "b1",
        "task_type": "part_1",
        "domain": "health",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
]

# ---------------------------------------------------------------------------
# IELTS PART 2  — Long turn with cue card  (target: b2 / c1)
# Expected response: 120–180 seconds
# prompt_text holds the cue card bullet points
# ---------------------------------------------------------------------------
IELTS_PART_2: list[dict] = [
    {
        "item_id": "QB-P2-001",
        "spec_id": "SPEC-IELTS-P2",
        "instruction": (
            "Describe a person you greatly admire. "
            "You should say: who this person is, how you know them, "
            "what qualities they have, and explain why you admire them so much."
        ),
        "prompt_text": (
            "You should say:\n"
            "• Who this person is\n"
            "• How you know or know about them\n"
            "• What qualities or achievements they have\n"
            "• Explain why you admire them so much"
        ),
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_2",
        "domain": "everyday",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P2-002",
        "spec_id": "SPEC-IELTS-P2",
        "instruction": (
            "Describe a place you have visited that you found particularly interesting. "
            "You should say: where it is, when and why you went there, "
            "what you did there, and explain what made it so interesting."
        ),
        "prompt_text": (
            "You should say:\n"
            "• Where the place is\n"
            "• When and why you visited it\n"
            "• What you did or saw there\n"
            "• Explain what made it particularly interesting to you"
        ),
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_2",
        "domain": "travel",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P2-003",
        "spec_id": "SPEC-IELTS-P2",
        "instruction": (
            "Describe an important event in your life. "
            "You should say: what the event was, when it happened, "
            "who was involved, and explain why it was so important to you."
        ),
        "prompt_text": (
            "You should say:\n"
            "• What the event was\n"
            "• When it happened and where\n"
            "• Who was involved\n"
            "• Explain why it was so important or memorable for you"
        ),
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_2",
        "domain": "everyday",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P2-004",
        "spec_id": "SPEC-IELTS-P2",
        "instruction": (
            "Describe a book or film that had a significant impact on you. "
            "You should say: what it was about, when you read or watched it, "
            "what stood out to you, and explain why it was so meaningful."
        ),
        "prompt_text": (
            "You should say:\n"
            "• What the book or film was about\n"
            "• When you read or watched it\n"
            "• What particularly stood out or impressed you\n"
            "• Explain why it had such a significant impact on you"
        ),
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_2",
        "domain": "culture",
        "skill_focus": "lexical_resource",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P2-005",
        "spec_id": "SPEC-IELTS-P2",
        "instruction": (
            "Describe a skill you would like to learn. "
            "You should say: what the skill is, why you want to learn it, "
            "how you would go about learning it, and explain how it would benefit you."
        ),
        "prompt_text": (
            "You should say:\n"
            "• What the skill is\n"
            "• Why you want to learn it\n"
            "• How you would go about learning it\n"
            "• Explain how it would benefit your life or career"
        ),
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_2",
        "domain": "academic",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P2-006",
        "spec_id": "SPEC-IELTS-P2",
        "instruction": (
            "Describe a piece of technology that you find particularly useful. "
            "You should say: what it is, how often you use it, "
            "what you use it for, and explain why you find it so useful."
        ),
        "prompt_text": (
            "You should say:\n"
            "• What the technology is\n"
            "• How often you use it\n"
            "• What you mainly use it for\n"
            "• Explain why you find it so useful or important in your life"
        ),
        "pathway": "ielts",
        "target_level": "b2",
        "task_type": "part_2",
        "domain": "technology",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P2-007",
        "spec_id": "SPEC-IELTS-P2",
        "instruction": (
            "Describe a time when you achieved something you are proud of. "
            "You should say: what you achieved, when and how you achieved it, "
            "what challenges you faced, and explain why you are so proud of it."
        ),
        "prompt_text": (
            "You should say:\n"
            "• What you achieved\n"
            "• When and how you achieved it\n"
            "• What challenges or difficulties you faced\n"
            "• Explain why you feel particularly proud of this achievement"
        ),
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_2",
        "domain": "everyday",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P2-008",
        "spec_id": "SPEC-IELTS-P2",
        "instruction": (
            "Describe an environmental problem in your country or region. "
            "You should say: what the problem is, how it developed, "
            "how it affects people, and explain what you think should be done to tackle it."
        ),
        "prompt_text": (
            "You should say:\n"
            "• What the environmental problem is\n"
            "• How it developed or became widespread\n"
            "• How it affects the lives of people in the area\n"
            "• Explain what steps you think should be taken to address it"
        ),
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_2",
        "domain": "environment",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
]

# ---------------------------------------------------------------------------
# IELTS PART 3  — Abstract discussion  (target: c1)
# Expected response: 120–180 seconds
# ---------------------------------------------------------------------------
IELTS_PART_3: list[dict] = [
    {
        "item_id": "QB-P3-001",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "In what ways has technology changed the way people communicate "
            "in society compared to previous generations?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "technology",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-002",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "What are the advantages and disadvantages of the increasing trend "
            "of people working from home?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "business",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-003",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "How important is environmental awareness in today's society, "
            "and what responsibilities do individuals have towards protecting the environment?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "environment",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-004",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "What impact has social media had on the mental health of young people, "
            "and how should this be addressed?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "health",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-005",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "How should governments balance the need for economic development "
            "with the protection of the natural environment?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "environment",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-006",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "In what ways can education systems be improved to better prepare "
            "students for the challenges of the modern workforce?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "academic",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-007",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "Do you think people today are more or less socially connected than "
            "in the past? What factors contribute to this?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "everyday",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-008",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "What role should businesses and corporations play in addressing "
            "global challenges such as climate change and inequality?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "business",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-009",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "How has globalisation affected cultural identity, and do you think "
            "this is mostly positive or negative for societies?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "culture",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-010",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "To what extent do you think artificial intelligence will transform "
            "the job market, and how should individuals and governments prepare for this?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "technology",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-011",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "Some people believe that university education should be free for all. "
            "What are the arguments for and against this view?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "academic",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-P3-012",
        "spec_id": "SPEC-IELTS-P3",
        "instruction": (
            "In your view, what are the most significant challenges that "
            "young people face in today's society, and how can these be overcome?"
        ),
        "prompt_text": None,
        "pathway": "ielts",
        "target_level": "c1",
        "task_type": "part_3",
        "domain": "everyday",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
]

# ---------------------------------------------------------------------------
# CEFR GRADED QUESTIONS  (A1 – B2)
# task_type uses a string label instead of IELTS part enum
# ---------------------------------------------------------------------------
CEFR_QUESTIONS: list[dict] = [
    # --- A1: Very simple personal questions ---
    {
        "item_id": "QB-CEFR-001",
        "spec_id": "SPEC-CEFR-A1",
        "instruction": "Tell me your name and where you are from.",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "a1",
        "task_type": "cefr_basic",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-CEFR-002",
        "spec_id": "SPEC-CEFR-A1",
        "instruction": "What do you do every day? Tell me about your daily routine.",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "a1",
        "task_type": "cefr_basic",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-CEFR-003",
        "spec_id": "SPEC-CEFR-A1",
        "instruction": "What is your favourite colour, food, or animal? Why do you like it?",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "a1",
        "task_type": "cefr_basic",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- A2: Simple descriptions and preferences ---
    {
        "item_id": "QB-CEFR-004",
        "spec_id": "SPEC-CEFR-A2",
        "instruction": "Describe your family. How many people are in your family and what do they do?",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "a2",
        "task_type": "cefr_simple",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-CEFR-005",
        "spec_id": "SPEC-CEFR-A2",
        "instruction": "What do you like to do in your free time? Describe one activity you enjoy.",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "a2",
        "task_type": "cefr_simple",
        "domain": "everyday",
        "skill_focus": "fluency",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-CEFR-006",
        "spec_id": "SPEC-CEFR-A2",
        "instruction": "Describe the town or city where you live. What is it like?",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "a2",
        "task_type": "cefr_simple",
        "domain": "everyday",
        "skill_focus": "lexical_resource",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- B1: Moderate complexity, opinions and explanations ---
    {
        "item_id": "QB-CEFR-007",
        "spec_id": "SPEC-CEFR-B1",
        "instruction": "Tell me about a typical day in your life. What do you usually do from morning to evening?",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "b1",
        "task_type": "cefr_intermediate",
        "domain": "everyday",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-CEFR-008",
        "spec_id": "SPEC-CEFR-B1",
        "instruction": "What are your future plans for your career or studies? What steps are you taking to achieve your goals?",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "b1",
        "task_type": "cefr_intermediate",
        "domain": "academic",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-CEFR-009",
        "spec_id": "SPEC-CEFR-B1",
        "instruction": "Talk about a country or place you would love to visit. Why does it interest you?",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "b1",
        "task_type": "cefr_intermediate",
        "domain": "travel",
        "skill_focus": "lexical_resource",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    # --- B2: Abstract topics and more developed answers ---
    {
        "item_id": "QB-CEFR-010",
        "spec_id": "SPEC-CEFR-B2",
        "instruction": "Describe a significant challenge you have faced in your life and explain how you dealt with it.",
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "b2",
        "task_type": "cefr_upper_intermediate",
        "domain": "everyday",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-CEFR-011",
        "spec_id": "SPEC-CEFR-B2",
        "instruction": (
            "In your opinion, how has the use of social media changed the way "
            "people form relationships and communicate?"
        ),
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "b2",
        "task_type": "cefr_upper_intermediate",
        "domain": "technology",
        "skill_focus": "mixed",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
    {
        "item_id": "QB-CEFR-012",
        "spec_id": "SPEC-CEFR-B2",
        "instruction": (
            "What do you think are the most important qualities a good leader should have? "
            "Give reasons and examples to support your view."
        ),
        "prompt_text": None,
        "pathway": "cefr",
        "target_level": "b2",
        "task_type": "cefr_upper_intermediate",
        "domain": "business",
        "skill_focus": "coherence",
        "generated_by": "seed_bank",
        "generation_timestamp": datetime(2025, 1, 1).isoformat(),
        "status": "active",
    },
]

# ---------------------------------------------------------------------------
# Master list — all seed items combined
# ---------------------------------------------------------------------------
ALL_SEED_QUESTIONS: list[dict] = (
    IELTS_PART_1 + IELTS_PART_2 + IELTS_PART_3 + CEFR_QUESTIONS
)

# Convenience look-up maps
QUESTIONS_BY_ID: dict[str, dict] = {q["item_id"]: q for q in ALL_SEED_QUESTIONS}

QUESTIONS_BY_PATHWAY_LEVEL: dict[str, list[dict]] = {}
for _q in ALL_SEED_QUESTIONS:
    _key = f"{_q['pathway']}:{_q['target_level']}"
    QUESTIONS_BY_PATHWAY_LEVEL.setdefault(_key, []).append(_q)

QUESTIONS_BY_TASK_TYPE: dict[str, list[dict]] = {}
for _q in ALL_SEED_QUESTIONS:
    QUESTIONS_BY_TASK_TYPE.setdefault(_q["task_type"], []).append(_q)
