# 事件标签与 hard cases

## Report 同步

`selective_es_14_cases_zh.json` 为 14 条案例的结构化数据，保留较新的原审阅报告中的对话、D 标签与行为评价，事件编号统一映射到本目录的六大类。家人健康归 E3、工作汇报归 E1、考试归 E5；搬家案例的核心是关系联结不足，归 E2。这 14 条并不覆盖所有六类事件。未提供原始用户画像的案例使用简短背景描述，不补写个人经历。

报告已与当前 JSON 数据同步：`data/hard_cases_zh.md`、`report/selective_es_10_paired_cases.md`、`report/14_cases.md` 和 `report/selective_es_14_case_review.md`。配对报告保留原文件名，正文为 6 组、18 条。后续修改数据时需对应更新报告。旧 `report/14_cases.pdf` 是尚未更新的历史导出。

14 条案例可使用 `--dataset data/selective_es_14_cases_zh.json --language zh` 运行。配对 hard cases 仍不含 GT 与 design_source。

本次采用用户最初提出的六大类，定义见 `event_categories.json`：E1 职业发展、E2 人际关系、E3 婚姻家庭、E4 个体不适、E5 自我成长、E6 社会环境。**不是** `14_cases_修改版.pdf` 中同编号的六种具体生活事件。

## 现有案例

`implicit_cp_scenarios.json` 和 `implicit_cp_scenarios_en.json` 各保留原来的 10 条案例、原文和顺序，新增 `event_category`、`event_category_name`、`event_rationale`。两种语言按位置配对，标签相同。事件标签描述背景中的主要困扰，不描述最后一轮的闲聊主题。

原案例 4 只明确长期居家导致低落，外部限制证据不足，因此标 E4；原案例 6 的 situation 明确提到疫情，因此标 E6。原案例 8 主要是对朋友丧亲的情绪和关系回应，标 E2；疫情作为背景不自动令所有案例都归 E6。主标签存在研究判断，正式使用前需人工复核。

## 新增 hard cases

`hard_cases_zh.json`：18 条中文案例，六类各一组，每组 A/B/C 三条。借鉴 `hard_cases.pdf` 的固定历史配对设计，以及 `14_cases_修改版.pdf` 中当前目标与边界的判断原则。新案例为自行构造，未声称逐字来自参考文档。

| 事件 | 具体背景 | A | B | C |
| --- | --- | --- | --- | --- |
| E1 | 求职等待 | D2 | D3 | D5 |
| E2 | 朋友疏远 | D2 | D3 | D5 |
| E3 | 婚姻结束及子女适应 | D2 | D3 | D5 |
| E4 | 睡眠不佳及其担忧 | D2 | D3 | D5 |
| E5 | 写诗学习受挫 | D2 | D3 | D5 |
| E6 | 社区公共设施持续暂停 | D2 | D3 | D5 |

- A：继续表达困扰，适度支持；B：当前困扰与日常分享并存，简短关心后接话；C：隐含陪伴，自然接话。
- 同一 `pair_id` 内 `user_profile`、`situation`、`history` 完全相同，仅当前 query 与评估元数据变化。B/C 复用日常话题，减少主题差异。
- `variant` 是需求输入变体，实验脚本的 `condition` 仍表示 no_role/es_role，二者不是同一个因素。
- Hard cases 不设置 `GT` 或标准回复文本；`expected_behavior` 和 `failure_modes` 仅用于后续行为盲评。所有新标签为待人工复核草稿，尤其 D2 与 D3 不代表已确认的心理状态。
- 不将当前情绪存在自动等同于请求深入处理；C 允许自然温暖，但不要求冷淡。六组不能代表每个大类的全部子情境，也尚未覆盖 D1/D4/D6/D7。

## 运行

在实验根目录运行（只预览，不访问 API）：

```powershell
python scripts/run_experiment.py --dataset data/hard_cases_zh.json --language zh --dry-run --run-id hard_cases_preview_v1
```

真实运行时去掉 `--dry-run` 并使用新 run-id。18 案例 × 2 角色 = 每模型每次重复 36 个请求。自定义数据集必须指定单一语言，不能使用 `both`；本次新增材料仅提供中文。

`case_metadata` 在运行记录中保存事件和评估标签，但不进入 API 的 `messages`。原数据补标签会改变数据指纹，不能续跑旧 run-id；历史结果不修改。
