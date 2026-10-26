# Output schemas

## Single-turn output

Recommended file: `outputs/<run_id>/single_turn_responses.jsonl`

| Field | Purpose |
|---|---|
| `run_id` | Experiment run identifier |
| `request_id` | Unique request identifier |
| `case_id` | Input case identifier |
| `emotion` | ED emotion label; metadata only |
| `model_alias` | Stable local model name |
| `provider` | API provider |
| `model_id` | Exact API model/version |
| `condition_id` | One of the six conditions |
| `role_type` | `no_role`, `cp_role`, or `es_role` |
| `prompt_level` | `no_prompt` or `simple_prompt` |
| `messages` | Exact messages sent to the API |
| `ed_user_1` | Raw ED user message |
| `ed_ground_truth` | ED Assistant 1; never sent to the model |
| `model_response` | Generated response |
| `repeat_id` | Repeated sample index |
| `generation_params` | Actual decoding parameters |
| `latency_ms` | Request latency |
| `input_tokens` | Provider-reported input tokens |
| `output_tokens` | Provider-reported output tokens |
| `finish_reason` | Completion status from provider |
| `status` | `success` or `error` |
| `error_type` | Normalized failure category |
| `error_message` | Raw/normalized error description |
| `timestamp` | Request completion time |
| `prompt_version` | Prompt template version |
| `dataset_version` | Dataset version |

Reserved single-turn evaluation fields:

```text
gt_semantic_similarity
emotion_understanding
relevance
naturalness
engagement
over_support
under_support
overall_appropriateness
```

Lexical metrics such as BLEU or ROUGE should be secondary. ED GT is one possible reply rather than the unique correct reply.

## Multi-turn output

Recommended file: `outputs/<run_id>/multi_turn_responses.jsonl`

Use the same operational fields as single-turn, except:

- `messages` contains the full fixed history and current user message.
- `constructed_user_2` is the current input.
- There is no `ed_ground_truth` for the generated final turn.
- The primary deliverable is `model_response`.

Reserved multi-turn evaluation fields:

```text
history_need
current_need
transition_type
switch_success
cp_appropriateness
es_intensity
over_support
under_support
topic_following
naturalness
overall_appropriateness
```

These fields may remain empty during the first generation-only run.

