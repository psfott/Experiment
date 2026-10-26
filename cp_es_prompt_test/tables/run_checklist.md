# Run checklist

## Before API integration

- [ ] Confirm whether the final experiment uses four or five models.
- [ ] Fill in the exact provider and model ID for every enabled model.
- [ ] Clarify which model `flash` refers to.
- [ ] Confirm that all providers accept an omitted/empty system message.
- [ ] Confirm generation parameters supported by every provider.
- [ ] Manually verify `history_need` and `transition_type` in `cases_master.csv`.
- [ ] Freeze `dataset_version` and `prompt_version` before the main run.

## Request construction checks

- [ ] Every case has all six experimental conditions.
- [ ] Every enabled model receives the same cases.
- [ ] Single-turn requests do not contain ED Assistant 1.
- [ ] Single-turn requests do not contain emotion or target labels.
- [ ] Multi-turn requests preserve the order User 1 → Assistant 1 → User 2.
- [ ] Simple Prompt does not explicitly mention CP or ES.
- [ ] Actual messages sent to APIs are saved with the output.

## Output checks

- [ ] No missing model-condition combinations.
- [ ] No duplicate `request_id` values.
- [ ] Empty and refused responses are marked rather than silently discarded.
- [ ] Truncated outputs are marked using `finish_reason`.
- [ ] Failed requests are recorded separately and can be resumed.
- [ ] A blinded export hides model and condition identities for human evaluation.

