# Question Quality Evaluation Rubric

## 1. Purpose

This document defines a full quality-check rubric for newly generated speaking questions in the AI-Powered Adaptive Spoken English Learning Platform.

It is designed for:

- IELTS-style speaking questions
- CEFR-aligned speaking questions
- human review and automated review
- pilot validation before live release

This rubric is adapted to the project while grounded in published quality principles from:

- IELTS official scoring and reliability resources
- Cambridge English exam production and pretesting process
- CEFR level-alignment principles

## 2. Source Base

The rubric is built from the following public sources:

1. Cambridge English exam production and pretesting:
   https://www.cambridgeenglish.org/exams-and-tests/producing-exams/#pretesting
2. IELTS scoring in detail:
   https://ielts.org/take-a-test/your-results/ielts-scoring-in-detail
3. IELTS test statistics and reliability controls:
   https://ielts.org/researchers/our-research/test-statistics
4. Cambridge English CEFR overview:
   https://www.cambridgeenglish.org/exams-and-tests/cefr/
5. Council of Europe CEFR portal:
   https://www.coe.int/en/web/common-european-framework-reference-languages

## 3. Quality Principles

Every generated question must satisfy these principles:

1. It must measure speaking ability, not unrelated subject knowledge alone.
2. It must match the target question type and level.
3. It must be clear and answerable.
4. It must be fair to diverse candidate groups.
5. It must be scoreable using the platform rubric.
6. It must be pretested before live-bank promotion.
7. It must be statistically monitored after pilot use.

## 4. Question Categories

### 4.1 IELTS Speaking Part 1

- Familiar, personal, everyday topics
- Expected response: short answer
- Recommended target duration: 15-40 seconds
- Example focus: home, studies, hobbies, routine, preferences

### 4.2 IELTS Speaking Part 2

- Cue-card long turn
- One topic with guided bullet points
- Recommended target duration: 60-120 seconds
- Example focus: describe a person, event, place, experience

### 4.3 IELTS Speaking Part 3

- Abstract, analytical, follow-up discussion
- Recommended target duration: 30-90 seconds
- Example focus: causes, comparisons, social impact, opinions, future implications

### 4.4 CEFR Speaking Items

- A1-A2: personal, concrete, simple and familiar
- B1-B2: opinions, comparison, reasons, practical issues
- C1-C2: abstract issues, justification, evaluation, nuanced argument

## 5. Evaluation Workflow

All generated questions must pass through this sequence:

1. Generate from approved seed or blueprint.
2. Run automated hard-gate checks.
3. Compute automated weighted quality score.
4. Run reviewer validation.
5. Send accepted items to pilot.
6. Evaluate pilot statistics.
7. Promote, revise, or reject.

## 6. Stage A: Hard Validation Gates

If any gate fails, the question cannot move to pilot or live use.

| Gate | Rule | Validation Method | Pass/Fail |
|---|---|---|---|
| Safety | No harmful, hateful, sexual, violent, illegal, or age-inappropriate content | safety classifier + keyword policy | Pass required |
| Clarity | Prompt has one clear task and no severe ambiguity | ambiguity detector + reviewer check | Pass required |
| Construct fit | Prompt elicits spoken language suitable for speaking assessment | rule-based classifier | Pass required |
| Level declared | Target pathway and level/band must be explicitly assigned | metadata validation | Pass required |
| Format fit | Prompt must match IELTS Part 1, 2, 3 or CEFR speaking template | structural rule check | Pass required |
| Duplicate control | Prompt must not be too similar to live bank items | semantic similarity threshold | Pass required |
| Scorability | Prompt must produce language usable for scoring dimensions | scoring-coverage check | Pass required |

### 6.1 Duplicate Threshold

Use cosine or semantic similarity against live item bank.

- Reject if similarity >= 0.85
- Manual review if similarity is between 0.75 and 0.84
- Pass if similarity < 0.75

## 7. Stage B: Weighted Quality Rubric

Each dimension is scored from 0.0 to 1.0 automatically, then converted into a weighted score.

### 7.0 Mathematical Definitions

Let:

- $q$ be a generated question
- $s_i(q)$ be the normalized score for criterion $i$, where $0 \le s_i(q) \le 1$
- $w_i$ be the weight for criterion $i$
- $g_j(q)$ be the hard-gate result for gate $j$, where $g_j(q) \in \{0,1\}$

Then a question passes all hard gates only if:

$$
GatePass(q) = \prod_{j=1}^{m} g_j(q)
$$

If any gate fails, then $GatePass(q)=0$ and the question is rejected before weighted scoring.

### 7.1 Weight Table

| Criterion | Weight | Meaning |
|---|---:|---|
| Construct Alignment | 0.20 | Measures intended speaking ability |
| Level Fit | 0.20 | Matches target IELTS/CEFR level |
| Clarity | 0.15 | Clear, understandable, unambiguous |
| Response Elicitation Quality | 0.15 | Likely to generate enough scorable speech |
| Fairness and Safety | 0.10 | No bias, exclusion, or inappropriate content |
| Originality | 0.10 | New enough compared with existing bank |
| Scorability | 0.10 | Can be reliably evaluated with rubric |

### 7.2 Formula

For each criterion, assign an automatic score between 0.0 and 1.0.

$$
FinalScore_{0-1} = \sum (Weight_i \times Score_i)
$$

$$
FinalScore_{0-100} = FinalScore_{0-1} \times 100
$$

Because the weights sum to 1.00, the normalized score is bounded:

$$
0 \le FinalScore_{0-1} \le 1
$$

Full form:

$$
FinalScore_{0-1}(q)=w_1s_1(q)+w_2s_2(q)+w_3s_3(q)+w_4s_4(q)+w_5s_5(q)+w_6s_6(q)+w_7s_7(q)
$$

### 7.3 Score Conversion for Human Review

To convert any automated score to a 0-5 reviewer-style score:

$$
ReviewerScore_{0-5} = round(5 \times Score_i)
$$

## 8. How Each Criterion Is Measured Automatically

### 8.0 Automated Measurement Policy

Weights are fixed at policy level, but the underlying scores must come from measurable signals rather than reviewer intuition alone.

The platform must therefore separate:

1. policy weights $w_i$
2. measurable automatic signals for each criterion
3. threshold-based decisions based on the computed score

This avoids a purely subjective evaluation model.

For any generated question $q$:

$$
FinalScore(q)=\sum_{i=1}^{n}(w_i \times s_i(q))
$$

Where:

- $w_i$ is the fixed criterion weight
- $s_i(q)$ is the measured automatic score for criterion $i$
- $0 \le s_i(q) \le 1$

The project uses the following fixed policy weights:

| Criterion | Symbol | Weight |
|---|---|---:|
| Construct Alignment | $w_1$ | 0.20 |
| Level Fit | $w_2$ | 0.20 |
| Clarity | $w_3$ | 0.15 |
| Response Elicitation Quality | $w_4$ | 0.15 |
| Fairness and Safety | $w_5$ | 0.10 |
| Originality | $w_6$ | 0.10 |
| Scorability | $w_7$ | 0.10 |

And:

$$
\sum_{i=1}^{7} w_i = 1.00
$$

Therefore:

$$
0 \le FinalScore(q) \le 1
$$

And the percentage form is:

$$
FinalScore_{100}(q)=100 \times FinalScore(q)
$$

To convert any normalized score into a reviewer-facing 0-5 score:

$$
ReviewerScore_i(q)=round(5 \times s_i(q))
$$

### 8.1 Construct Alignment (Weight 0.20)

Measures whether the question really targets speaking ability intended by the blueprint.

Suggested checks:

- similarity to approved descriptor bank
- task-type classifier confidence
- speaking-construct keyword coverage

Detailed implementation guidance:

- DescriptorSimilarity: semantic similarity between the generated question and a validated descriptor or seed bank for the target speaking construct.
- TaskTypeConfidence: model confidence that the question belongs to the intended category, such as IELTS Part 1, Part 2, Part 3, or CEFR speaking task type.
- ConstructCoverage: whether the prompt is likely to elicit language evidence useful for the intended speaking construct.

Example formula:

$$
ConstructAlignment = 0.45 \times DescriptorSimilarity + 0.30 \times TaskTypeConfidence + 0.25 \times ConstructCoverage
$$

Suggested threshold:

- Pass >= 0.75
- Review 0.60-0.74
- Fail < 0.60

### 8.2 Level Fit (Weight 0.20)

Measures whether the difficulty matches target level/band.

Suggested features:

- lexical difficulty
- topic abstractness
- expected response length
- cognitive demand
- level-classifier confidence

Detailed implementation guidance:

- LexicalFit: how closely prompt vocabulary matches the target level profile.
- TopicFit: how well topic familiarity or abstractness matches the level target.
- DurationFit: whether the predicted answer length matches the expected band or CEFR response range.
- CognitiveFit: whether the task operation matches the level, for example describe, explain, compare, evaluate, or synthesize.
- ClassifierConfidence: a model-estimated probability that the question belongs to the intended level.

Suggested formula:

$$
LevelFit = 0.30 \times LexicalFit + 0.20 \times TopicFit + 0.20 \times DurationFit + 0.15 \times CognitiveFit + 0.15 \times ClassifierConfidence
$$

Where each subscore is normalized to $[0,1]$.

Suggested threshold:

- Pass >= 0.75
- Review 0.60-0.74
- Fail < 0.60

### 8.3 Clarity (Weight 0.15)

Measures whether the prompt is easy to understand.

Suggested features:

- sentence length
- number of clauses
- ambiguity score
- grammar correctness

Detailed implementation guidance:

- Simplicity: inverse penalty for excessive prompt length.
- ClauseControl: score decreases when the prompt contains too many nested clauses or multiple tasks.
- AmbiguityRisk: score increases when pronoun reference, unclear scope, or multiple interpretations are detected.
- GrammarCorrectness: score decreases when generated text contains grammatical errors or malformed instructions.

Suggested formula:

$$
Clarity = 0.30 \times Simplicity + 0.25 \times ClauseControl + 0.25 \times (1-AmbiguityRisk) + 0.20 \times GrammarCorrectness
$$

Suggested threshold:

- Pass >= 0.80
- Review 0.65-0.79
- Fail < 0.65

### 8.4 Response Elicitation Quality (Weight 0.15)

Measures whether the prompt is likely to produce enough spoken output.

Suggested features:

- predicted response duration
- open-endedness score
- answerability score
- expected content richness

Detailed implementation guidance:

- DurationAdequacy: match between predicted response time and target module.
- OpenEndedness: whether the question invites extended language rather than yes/no only.
- Answerability: whether candidates can reasonably answer using expected background knowledge.
- ContentRichness: whether the question can elicit enough variety for lexical, grammar, and coherence evidence.

Suggested formula:

$$
Elicitation = 0.35 \times DurationAdequacy + 0.25 \times OpenEndedness + 0.20 \times Answerability + 0.20 \times ContentRichness
$$

Suggested threshold:

- Pass >= 0.75
- Review 0.60-0.74
- Fail < 0.60

### 8.5 Fairness and Safety (Weight 0.10)

Measures whether the prompt avoids bias or exclusion.

Suggested features:

- bias-risk model score
- sensitive-topic flag
- region/culture dependency detector
- age appropriateness check

Detailed implementation guidance:

- BiasRisk: estimated risk that success depends unfairly on demographic background.
- SensitiveTopicRisk: estimated risk of distressing, inappropriate, or institutionally unsuitable content.
- CulturalDependencyRisk: whether the question assumes local knowledge or culturally specific experiences.
- AgeAppropriateness: whether the topic is suitable for the intended learner group.

Suggested formula:

$$
FairnessSafety = 0.35 \times (1-BiasRisk) + 0.25 \times (1-SensitiveTopicRisk) + 0.20 \times (1-CulturalDependencyRisk) + 0.20 \times AgeAppropriateness
$$

Suggested threshold:

- Pass >= 0.90
- Review 0.75-0.89
- Fail < 0.75

### 8.6 Originality (Weight 0.10)

Measures whether the prompt is different enough from the bank.

Detailed implementation guidance:

- Compute similarity against all active items and all recently retired items.
- Use the maximum observed similarity as the control value.
- Penalize the score if the prompt is structurally or semantically too close to existing items.

Suggested formula:

$$
Originality = 1 - MaxSimilarityToExistingBank
$$

Suggested threshold:

- Pass >= 0.75
- Review 0.60-0.74
- Fail < 0.60

### 8.7 Scorability (Weight 0.10)

Measures whether the prompt can support consistent scoring.

Suggested checks:

- likely to elicit fluency evidence
- likely to elicit lexical evidence
- likely to elicit grammar evidence
- likely to elicit coherence evidence

Detailed implementation guidance:

- FluencyCoverage: the prompt should make it possible to speak continuously rather than answer with one phrase.
- LexicalCoverage: the prompt should allow enough vocabulary choice.
- GrammarCoverage: the prompt should allow sentence variation rather than isolated words only.
- CoherenceCoverage: the prompt should allow linking, explanation, or organization.

Suggested formula:

$$
Scorability = 0.25 \times FluencyCoverage + 0.25 \times LexicalCoverage + 0.25 \times GrammarCoverage + 0.25 \times CoherenceCoverage
$$

Suggested threshold:

- Pass >= 0.75
- Review 0.60-0.74
- Fail < 0.60

## 9. Numeric Decision Rules

After all hard gates pass, compute the final score.

| Final Score | Decision |
|---:|---|
| 80-100 | Promote to Pilot |
| 65-79 | Revise and Regenerate |
| Below 65 | Reject |

### Critical Override Rule

Reject immediately if any of these are true:

- unsafe content
- severe ambiguity
- major level mismatch
- strong fairness risk
- not scoreable

This can be implemented as:

$$
CriticalFail(q)=\max(Unsafe, SevereAmbiguity, MajorLevelMismatch, StrongFairnessRisk, NotScorable)
$$

If $CriticalFail(q)=1$, then the final decision is Reject regardless of weighted score.

## 10. IELTS-Specific Validation Rules

IELTS question generation must be template-controlled. A question must first be classified into Part 1, Part 2, or Part 3 before quality scoring is finalized.

### 10.1 Part 1 Recognition Rules

Part 1 questions should:

- focus on personal, familiar topics
- avoid abstract social analysis
- be answerable in 15-40 seconds
- avoid multi-step instructions

Additional recognition constraints:

- one direct prompt only
- no bullet list
- no cue-card phrasing
- no heavy abstract reasoning requirement
- topic should be common across most test-taker backgrounds

Examples of acceptable topics:

- routines
- hobbies
- food
- hometown
- study/work

Suggested automatic Part 1 score:

$$
P1Score = 0.40 \times Familiarity + 0.25 \times ShortResponseFit + 0.20 \times PersonalTopicFit + 0.15 \times (1-Abstractness)
$$

Recommended validation thresholds:

- Accept as Part 1 if $P1Score \ge 0.75$
- Review if $0.60 \le P1Score < 0.75$
- Reject classification if $P1Score < 0.60$

### 10.2 Part 2 Recognition Rules

Part 2 questions should:

- use long-turn cue-card format
- contain a main prompt plus 3-4 bullet points
- target 60-120 second answers

Additional recognition constraints:

- cue-card format must be explicit
- include guidance such as "you should say"
- contain 3-4 sub-prompts or bullet points
- topic must support extended monologue

Suggested automatic Part 2 score:

$$
P2Score = 0.35 \times CueCardStructure + 0.25 \times BulletPointFit + 0.25 \times LongTurnFit + 0.15 \times TopicDepth
$$

Recommended validation thresholds:

- Accept as Part 2 if $P2Score \ge 0.75$
- Review if $0.60 \le P2Score < 0.75$
- Reject classification if $P2Score < 0.60$

### 10.3 Part 3 Recognition Rules

Part 3 questions should:

- be analytical or abstract
- often ask why, how, compare, should, impact, future
- be linked conceptually to Part 2 theme
- target 30-90 second answers

Additional recognition constraints:

- prompt should invite analysis or justification
- prompt often uses why, how, compare, impact, should, future, or causes
- prompt should not be limited to a simple personal fact answer

Suggested automatic Part 3 score:

$$
P3Score = 0.35 \times AbstractDiscussionFit + 0.25 \times AnalyticalVerbFit + 0.20 \times ThemeLink + 0.20 \times ExtendedResponseFit
$$

Then assign the IELTS speaking part as:

$$
PredictedPart(q)=\arg\max(P1Score, P2Score, P3Score)
$$

If the maximum part score is below 0.60, the item must be rejected as malformed.

## 10.4 Worked IELTS Part 1 Example

Generated question:

"Do you usually plan your day in advance, or do you prefer to decide things as you go? Why?"

Target:

- IELTS Speaking
- Part 1
- familiar daily-routine topic
- expected answer length: 20-40 seconds

Example automatic criterion scores:

| Criterion | Weight | AutoScore | Weighted Contribution |
|---|---:|---:|---:|
| Construct Alignment | 0.20 | 0.88 | 0.176 |
| Level Fit | 0.20 | 0.82 | 0.164 |
| Clarity | 0.15 | 0.91 | 0.1365 |
| Response Elicitation Quality | 0.15 | 0.86 | 0.129 |
| Fairness and Safety | 0.10 | 0.97 | 0.097 |
| Originality | 0.10 | 0.79 | 0.079 |
| Scorability | 0.10 | 0.90 | 0.090 |

Calculation:

$$
FinalScore(q)=0.176+0.164+0.1365+0.129+0.097+0.079+0.090
$$

$$
FinalScore(q)=0.8715
$$

$$
FinalScore_{100}(q)=87.15
$$

Example part-classification support values:

- $Familiarity = 0.95$
- $ShortResponseFit = 0.90$
- $PersonalTopicFit = 0.88$
- $Abstractness = 0.10$

Then:

$$
P1Score = 0.40(0.95) + 0.25(0.90) + 0.20(0.88) + 0.15(1-0.10)
$$

$$
P1Score = 0.38 + 0.225 + 0.176 + 0.135 = 0.916
$$

Decision:

- hard gates passed
- part classification valid for Part 1
- final score 87.15
- outcome: Promote to Pilot

## 11. CEFR Level Recognition Rules

Generated CEFR items should be labeled using prompt characteristics first, then confirmed through pilot performance.

### 11.1 Initial Rule-Based Labeling

| Level | Prompt profile |
|---|---|
| A1 | very familiar topic, basic vocabulary, simple answer |
| A2 | familiar daily-life topic, short explanation |
| B1 | opinion + simple reason |
| B2 | comparison, justification, discussion of pros and cons |
| C1 | abstract issue, deeper evaluation, nuanced reasoning |
| C2 | highly abstract, subtle distinctions, complex argument |

Suggested CEFR level scoring functions:

$$
A1(q)=0.35 \times Familiarity + 0.30 \times Simplicity + 0.20 \times LowAbstractness + 0.15 \times ShortResponseFit
$$

$$
A2(q)=0.30 \times Familiarity + 0.25 \times DailyLifeFit + 0.25 \times ShortExplanationFit + 0.20 \times BasicLexicalFit
$$

$$
B1(q)=0.30 \times OpinionFit + 0.25 \times ReasonGivingFit + 0.25 \times MediumResponseFit + 0.20 \times ModerateLexicalFit
$$

$$
B2(q)=0.30 \times ComparisonFit + 0.25 \times JustificationFit + 0.25 \times DiscussionFit + 0.20 \times AbstractnessMidHigh
$$

$$
C1(q)=0.30 \times EvaluationFit + 0.25 \times NuanceFit + 0.25 \times AbstractnessHigh + 0.20 \times LongResponseFit
$$

$$
C2(q)=0.30 \times SynthesisFit + 0.25 \times SubtleDistinctionFit + 0.25 \times ComplexArgumentFit + 0.20 \times VeryHighAbstractness
$$

Assign the initial CEFR level by:

$$
PredictedCEFR(q)=\arg\max(A1(q), A2(q), B1(q), B2(q), C1(q), C2(q))
$$

The initial CEFR labeling model should use at least these measured signals:

- lexical difficulty
- syntax complexity
- topic abstractness
- cognitive operation class
- expected response length

Suggested normalized input vector:

$$
X(q) = [LexicalDifficulty, SyntaxComplexity, TopicAbstractness, CognitiveDemand, ResponseLengthFit]
$$

### 11.2 Response-Time Expectations by CEFR

| Level | Recommended response duration |
|---|---:|
| A1 | 10-20 sec |
| A2 | 15-30 sec |
| B1 | 25-45 sec |
| B2 | 40-70 sec |
| C1 | 60-100 sec |
| C2 | 90-150 sec |

### 11.3 CEFR Review Rule

If the predicted level and pilot performance disagree, relabel or retire the item.

Confidence can be measured as:

$$
CEFRConfidence = Score_{top1} - Score_{top2}
$$

If $CEFRConfidence < 0.08$, send the item to human review.

## 11.4 CEFR Prompt Profiles for Automatic Recognition

| Level | Expected prompt characteristics |
|---|---|
| A1 | very familiar, concrete, simple words, single-step answer |
| A2 | everyday topic, short explanation or preference |
| B1 | opinion plus simple reason or short experience explanation |
| B2 | comparison, justification, advantages and disadvantages |
| C1 | abstract issue, nuanced argument, conditional reasoning |
| C2 | complex synthesis, subtle distinctions, critical evaluation |

## 11.5 CEFR Level Recognition Example Logic

Use the question only as a preliminary estimate. Final labeling must be confirmed through pilot evidence.

Example interpretation rules:

- If mostly A1-A2 learners answer fluently and coherently, the question is too easy for B1 or above.
- If B2 learners show strong breakdowns, the question may actually be C1-level or badly written.
- The final level should be the band where response quality and discrimination are strongest.

This can be operationalized by observing response success by known-level groups.

For level $L$:

$$
PerformanceMatch(L)=0.5 \times FluencySuccess(L)+0.3 \times CoherenceSuccess(L)+0.2 \times CompletionSuccess(L)
$$

Then assign the empirical level:

$$
EmpiricalCEFR(q)=\arg\max_L PerformanceMatch(L)
$$

If $EmpiricalCEFR(q) \ne PredictedCEFR(q)$, the item must be relabeled, revised, or rejected.

## 12. Pilot Validation Rules

Pilot testing is mandatory before live promotion.

### 12.1 Minimum Sample Size

- High-stakes items: minimum 100 pilot responses
- Low-stakes early-stage practice items: minimum 50 pilot responses, then recheck at 100

### 12.2 Pilot Metrics

Track at minimum:

- mean response length
- response completion rate
- predicted level-fit stability
- human review confirmation rate
- subgroup fairness flags

Suggested equations:

$$
MeanResponseLength = \frac{1}{n}\sum_{k=1}^{n} ResponseSeconds_k
$$

$$
CompletionRate = \frac{CompletedResponses}{TotalPilotAttempts}
$$

$$
HumanConfirmationRate = \frac{HumanApprovedLabels}{TotalReviewedPilotItems}
$$

$$
LevelStability = 1 - \frac{LevelRelabelCount}{TotalPilotItems}
$$

$$
FairnessFlagRate = \frac{FlaggedSubgroupChecks}{TotalSubgroupChecks}
$$

Suggested overall pilot score:

$$
PilotScore = 0.25 \times ResponseLengthFit + 0.25 \times CompletionRate + 0.20 \times LevelStability + 0.15 \times HumanConfirmationRate + 0.15 \times (1-FairnessFlagRate)
$$

### 12.3 Pilot Outcomes

| Pilot Result | Action |
|---|---|
| strong performance | Promote to Live Bank |
| mixed performance | Recalibrate and Re-pilot |
| poor performance | Reject |

Suggested thresholds:

- Promote to Live Bank if $PilotScore \ge 0.80$
- Recalibrate and Re-pilot if $0.65 \le PilotScore < 0.80$
- Reject if $PilotScore < 0.65$

## 13. Example Evaluation

Generated IELTS Part 1 question:

"Do you usually plan your day in advance, or do you prefer to decide things as you go? Why?"

Automated scores:

| Criterion | Weight | Score |
|---|---:|---:|
| Construct Alignment | 0.20 | 0.88 |
| Level Fit | 0.20 | 0.82 |
| Clarity | 0.15 | 0.91 |
| Response Elicitation Quality | 0.15 | 0.86 |
| Fairness and Safety | 0.10 | 0.97 |
| Originality | 0.10 | 0.79 |
| Scorability | 0.10 | 0.90 |

Calculation:

$$
FinalScore = (0.20 \times 0.88) + (0.20 \times 0.82) + (0.15 \times 0.91) + (0.15 \times 0.86) + (0.10 \times 0.97) + (0.10 \times 0.79) + (0.10 \times 0.90)
$$

$$
FinalScore = 0.8715
$$

$$
FinalScore_{0-100} = 87.15
$$

Decision:

- Hard gates: passed
- Final score: 87.15
- Outcome: Promote to Pilot

## 14. Reviewer Form Template

### Item Metadata

- Item ID:
- Seed ID:
- Pathway:
- Module:
- Target Level:
- Reviewer:
- Date:

### Hard Gates

- Safety: Pass / Fail
- Clarity: Pass / Fail
- Construct Fit: Pass / Fail
- Level Declared: Pass / Fail
- Format Fit: Pass / Fail
- Duplicate Check: Pass / Fail
- Scorability: Pass / Fail

### Weighted Scores

- Construct Alignment:
- Level Fit:
- Clarity:
- Response Elicitation Quality:
- Fairness and Safety:
- Originality:
- Scorability:

### Decision

- Final Score:
- Promote to Pilot / Revise and Regenerate / Reject
- Reviewer Notes:

## 15. Recommended Storage Fields

Store these for every generated item:

- item_id
- seed_id
- generator_version
- pathway
- module
- target_level
- question_text
- duplicate_similarity
- construct_alignment_score
- level_fit_score
- clarity_score
- elicitation_score
- fairness_score
- originality_score
- scorability_score
- hard_gate_results
- final_score
- decision
- pilot_attempt_count
- pilot_status
- reviewer_notes

Recommended derived fields:

- gate_pass
- critical_fail
- predicted_part
- predicted_cefr_level
- predicted_level_confidence
- pilot_score
- fairness_flag_rate
- completion_rate

## 16. Final Policy Summary

An item may go live only if:

1. all hard gates pass
2. weighted score is 80 or above
3. pilot sample meets minimum size
4. pilot evidence confirms level fit and acceptable performance
5. no fairness or reliability concern remains unresolved
