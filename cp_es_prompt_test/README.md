# CP–ES Prompt Test（第一阶段）

本目录保存单轮和多轮实验的固定材料、实验条件与输出规范。本阶段不包含任何模型 API 调用代码。

## 1. 任务划分

### 单轮任务（single-turn）

- 模型输入：`ED User 1`
- 参考回复：`ED Assistant 1`
- `ED Assistant 1` 只用于生成后的对比，不发送给模型。
- 后续比较应同时保留“与 ED GT 的语义接近程度”和“独立回复适切性”。ED GT 是参考回复，不应被视为唯一正确答案。

消息结构：

```text
System: role_prompt + task_prompt（按实验条件组合）
User: ED User 1
Assistant: model output
```

### 多轮任务（multi-turn）

- 固定历史：`ED User 1 → ED Assistant 1`
- 当前输入：`Constructed User 2`
- 模型只生成针对当前输入的自然回复。
- 不提供或比较唯一 GT。

消息结构：

```text
System: role_prompt + task_prompt（按实验条件组合）
User: ED User 1
Assistant: ED Assistant 1
User: Constructed User 2
Assistant: model output
```

## 2. 实验因素

- 模型标签：`deepseek`、`flash`、`qwen3_8b`、`doubao`、`gpt`
- Role：`no_role`、`cp_role`、`es_role`
- Prompt：`no_prompt`、`simple_prompt`
- 情绪：`sad`、`surprised`、`proud`、`confident`、`joyful`
- 当前样本：每类情绪 2 条，共 10 条
- 默认重复次数：1（正式稳定性实验可调整为 3）

当前材料按 5 个模型标签计算，每个任务的预计调用量为：

```text
10 cases × 5 models × 3 roles × 2 prompt levels = 300
```

单轮和多轮合计 600 次。如果最终只启用 4 个模型，则合计为 480 次。

## 3. 文件说明

```text
cp_es_prompt_test/
├── README.md
├── experiment_manifest.yaml
├── data/
│   ├── cases_master.csv
│   ├── single_turn_cases.csv
│   └── multi_turn_cases.jsonl
├── prompts/
│   └── prompt_templates.yaml
├── tables/
│   ├── condition_matrix.csv
│   ├── experiment_overview.csv
│   ├── model_condition_matrix.csv
│   ├── sample_distribution.csv
│   └── run_checklist.md
├── schemas/
│   └── output_schema.md
└── outputs/
    └── .gitkeep
```

## 4. 重要控制项

1. 所有模型必须接收完全相同的原始用户文本和历史文本。
2. Role 只改变角色内容；Simple Prompt 只增加中性回复要求，不泄漏 CP/ES 目标。
3. 单轮请求不得包含 `situation`、`ED Assistant 1`、情绪标签或目标需求。
4. 多轮请求使用固定的 ED Assistant 1，避免不同模型生成的历史成为混淆变量。
5. 保存实际发送的完整消息，而不只保存 Prompt 模板名称。
6. `flash` 目前只是模型别名，正式运行前需要填写准确 provider 和 model ID。
7. 当前多轮样本的当前需求均为 CP；历史需求和转换类型仍需人工确认，不能仅凭 ED emotion 推断。

