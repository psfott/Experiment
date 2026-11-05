# Support inertia pilot: ES role vs no role

本目录测试一个特定问题：在相同的既往情绪支持对话和隐含陪伴需求下，固定的 Emotional Support Assistant 角色是否增加不必要的支持性回复。当前只有 `no_role` 与 `es_role` 两个条件，不含 CP role、提示词优化或历史消融。

## 材料与消息结构

`data/implicit_cp_scenarios_en.json` 和 `data/implicit_cp_scenarios.json` 各有 10 条样例。每条包括 `user_profile`、`situation`、`history`、`query`、`GT`。默认运行英文版；用 `--language zh` 选择中文版。样例 ID 依文件顺序为 `case_001` 到 `case_010`。

同一模型、样例、重复次数下，两组只改变 system 消息中的角色句。共同指令、背景、两轮 seeker/supporter 历史、最终 query、采样参数均相同：

```text
System: [ES role sentence, if es_role] + common instruction + user profile + situation
User: history[0].seeker
Assistant: history[0].supporter
User: history[1].seeker
Assistant: history[1].supporter
User: query
Assistant: generated response
```

`GT` **不发送给模型**，只作为参考文本保存在结果中；它不是唯一正确答案，也不能直接用于计算过度支持率。角色模板在 `prompt_template/prompts.json`。当前模板故意不提示模型“需求已转向陪伴”，也不强制“每轮必须安慰”。

## 安装与配置

在 PowerShell 中运行：

```powershell
cd G:\ps\llm\experiment\Experiment_repo\support_interia_test
Copy-Item models.example.json models.local.json
```

编辑 `models.local.json` 中的准确 `model_id`、`base_url`、`api_key_env`；可在 `models` 列表中配置多个模型。`base_url` 应为 API 前缀，例如 `https://host/v1`，**不要**包含 `/chat/completions`。本脚本只支持 OpenAI-compatible Chat Completions，不直接支持原生 Anthropic/Gemini API。可通过环境变量设置密钥；也可在本地 JSON 的模型条目中填写 `api_key`，但不要写入 `models.example.json`。`models.local.json` 和 `results/` 由 `.gitignore` 排除。脚本只使用 Python 标准库，无需安装额外依赖。

## 预览和运行

```powershell
# 使用示例模型配置预览；不需要密钥、不访问 API
python scripts/run_experiment.py --dry-run --run-id preview_en

# 检查 results/preview_en/run_snapshot.json 内的完整消息

# 配置好 models.local.json 后，先做一个成对 smoke test（两次请求）
python scripts/run_experiment.py --run-id smoke --model example --case case_001

# 全量：每个启用模型 × 10 样例 × 2 角色 × repeats
python scripts/run_experiment.py --run-id pilot_en_v1

# 失败续跑；成功请求跳过，保持相同配置与运行参数
python scripts/run_experiment.py --run-id pilot_en_v1 --resume

# 中文数据：需要独立 run-id
python scripts/run_experiment.py --language zh --run-id pilot_zh_v1

# 仅重建横向对比 CSV，不访问 API
python scripts/run_experiment.py --export-comparison results/pilot_en_v1

# 本地测试，不访问 API
python -m unittest discover -s scripts -p 'test_*.py' -v
```

`--model`、`--case`、`--condition` 均可指定一个或多个值。若只选择一个条件，就不是成对比较。可设置 `--repeats`、`--temperature`、`--top-p`、`--max-tokens`；所有条件共享这些参数。默认请求顺序按固定种子打乱，降低时间顺序与条件混淆。运行目录存在时必须使用 `--resume`，且计划指纹必须一致。续跑若在请求已计费但结果尚未写入时中断，可能重新发送该请求。

每次运行写入 `results/<run-id>/`：`run_snapshot.json` 保存完整无密钥的请求计划；`responses.jsonl` 保存每次调用、失败及重试记录；`comparison.csv` 按模型、样例和重复次数横向列出两组回复。网络错误与 HTTP 408/429/5xx 会按设定重试；HTTP 400/401 等配置错误不会自动修改参数。修改模型参数需要新 run-id。

## 解释边界

这 10 条都是隐含 CP 转换，适合先做 pilot。当前对比估计的是**在相同支持历史之上，额外加入固定 ES role 的效应**；不能单凭它分离历史本身的影响。若要正式回答 RQ1，后续还需持续 ES、稳定 CP 等对照样本，以及独立于候选回复的人工需求标注。建议盲评“是否接住当前互动意图”“是否不必要地重提旧困扰／追问／建议”“回复自然度”，不要把与 GT 不同直接记为错误。
