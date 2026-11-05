# API 运行说明

## 按六个条件整理 CSV

运行结束后执行（将运行名替换为实际 outputs 子目录名）：

```powershell
python organize_results.py deepseek_all_v1
python organize_results.py qwen38_all_v1
```

结果写入该运行目录的 `classified_csv/`：`No_no_prompt.csv`、`No_with_prompt.csv`、`CP_no_prompt.csv`、`CP_with_prompt.csv`、`ES_no_prompt.csv`、`ES_with_prompt.csv`，另有 `summary.csv` 汇总数量。每个条件文件包含单轮和多轮，使用 task 列区分；多个模型使用 model_alias 列区分。

同时生成按输入横向对比的 `by_input.csv`，以及分任务的 `single_turn_by_input.csv` 和 `multi_turn_by_input.csv`。每行对应同一样本、模型、重复次数及可见历史，六种条件的回复各占一列（如 CP_with_prompt_output），附带各条件的 status、error、finish_reason。尚未生成的条件标为 missing；失败回复保留原文及错误状态。available_conditions 与 successful_conditions 用于检查是否收齐六条件。不同历史不会仅因最后一句相同而合并。

默认保留 error，避免遗漏失败请求；使用 `--success-only` 仅导出成功记录。续跑记录按 task + request_id 取文件最后一条，attempt_records 是保存的记录数量（不含单次调用内的 HTTP 重试）。CSV 使用 UTF-8 BOM，支持 Excel 中文及多行文本；它们含模型和条件信息，不是匿名标注表。重复执行覆盖分类 CSV，不修改原始 JSONL。运行中也可导出当前已完成部分，结束后重新执行即可；若 JSONL 正在写入出现残行，等待写完再导出。

在 PowerShell 中进入目录：

```powershell
cd D:\Companion\Experiment\cp_es_prompt_test
python -m pip install -r requirements.txt
Copy-Item models.example.yaml models.local.yaml
```

编辑 `models.local.yaml`，填写准确的 `model_id`、`base_url`（到 `/v1` 等 API 前缀，不含 `/chat/completions`）、`api_key_env`。多个模型在 models 列表追加配置，alias 对应 deepseek、flash、qwen3_8b、doubao、gpt。只有本地配置中的 enabled 模型参与运行；manifest 中 TBD 模型列表是设计清单，不用于 API 连接。不要猜测 flash 的实际模型。

也可以直接在 `models.local.yaml` 的每个模型下填写 `api_key: "你的密钥"`。非空 `api_key` 优先；留空则读取 `api_key_env` 指定的环境变量。密钥不进入请求计划、快照或结果文件，更换密钥不影响续跑。

如果选择环境变量方式，可用隐藏输入：

```powershell
$secureKey = Read-Host 'API key' -AsSecureString
$env:DEEPSEEK_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
```

按各模型的 api_key_env 分别设置变量；同一兼容服务可以共用一个环境变量。直接填写密钥时使用本地的 models.local.yaml，不要填写到示例模板。models.local.yaml 和运行输出已被 gitignore 排除。

## 先检查，再小批运行

```powershell
# 不需要密钥，不访问 API；检查完整消息和预计请求数
python run_experiment.py --dry-run --run-id preview

# 一个模型、一个样本、一个条件、一个任务：仅一次请求
python run_experiment.py --run-id smoke --model deepseek --case sad_dog_001 --condition NR_NP --task single_turn

# 正式实验：已启用模型 × 10 样本 × 6 条件 × 2 任务 × repeats
python run_experiment.py --run-id phase1_v1

# 原配置、原 run-id 失败续跑；成功项跳过，失败项保留并追加新尝试
python run_experiment.py --run-id phase1_v1 --resume
```

dry-run 同样创建运行目录。可在配置不变时用同一 run-id 加 `--resume` 正式执行；配置修改后必须换 run-id。续跑时保留原来的筛选参数、order-seed、timeout、retries 等配置。程序拒绝将不同配置混入同一运行。

`--task`、`--model`、`--case`、`--condition` 都可指定多个值。运行顺序按 `--order-seed`（默认 42）打乱；该种子只控制请求顺序。生成 seed 在 manifest 的 generation 中配置，模型是否支持需自行确认。重复次数、temperature、top_p 和 token 上限也在 manifest 中配置。

## 参数兼容与错误

默认发送 temperature、top_p、max_tokens；配置中的 extra_body 可显式覆盖参数，值为 null 时移除该参数。不同模型对思考开关、token 参数和 seed 的支持不同，请根据所使用 API 的说明填写。脚本不会在报错后悄悄降低约束或修改实验参数。不要通过 extra_body 添加标签或目标需求。

系统代理默认生效；仅在确认代理不可用并需要直连时使用 `--ignore-proxy`。超时默认 120 秒，自动重试默认 3 次，仅对网络错误和 HTTP 408/429/500/502/503/504 重试。HTTP 400/401 等需要修正配置。错误日志仅保存 HTTP 状态码，不保存可能回显敏感信息的原始错误体。

拒答、空回复和 token 截断均记为 error，保留已有文本、finish_reason 和用量。截断不是适切性错误，评价前应检查。持续截断需要新 run-id 和新 token 设置；重复续跑仍可能产生费用。Ctrl+C 停止后可续跑；若中断发生在请求已计费但尚未落盘时，该请求可能需要重新发送。

同一 run-id 同时只启动一个进程。若写入时发生系统崩溃导致 JSONL 最后一行不完整，应备份文件并修复残行后再续跑，脚本不会静默丢弃损坏记录。

## 结果与人工标注

`outputs/<run_id>/` 包含：

- `run_snapshot.json`：配置指纹、完整请求计划、原始消息与生成参数，不含密钥值。
- `single_turn_responses.jsonl`、`multi_turn_responses.jsonl`：每次请求的结果、用量、延迟和错误；续跑追加记录，分析时每个 request_id 取最后一条。
- `blinded.csv`：打乱后的有效回复、可见历史、当前输入及空评分列；不含角色 Prompt、模型或条件标签。
- `blinded_key.json`：标注 ID 对照表，仅研究者保存，不能发给标注者。

重新导出：

```powershell
python run_experiment.py --export-blind outputs\phase1_v1
python -m unittest -v test_runner.py
```

匿名导出只包括最后一次记录为 success 的请求。继续运行后重新导出会改变 blind_id，必须在完成生成后冻结标注文件。需求标注应另用不含候选回复的材料开展，避免候选污染需求判断。

本实现保持仓库现有单轮/多轮任务及六条件；没有加入新的实验样本或历史消融。尚未进行真实服务调用，先用 smoke 确认具体服务兼容性，再运行完整批次。
