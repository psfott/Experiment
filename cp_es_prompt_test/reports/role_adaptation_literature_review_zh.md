# 固定角色下的 CP/ES 自适应：定向文献调研

检索日期：2026-10-27。优先 ACL、NAACL、EMNLP，明确标注 Findings、Industry 及补充会议。本文是定向综述，不是穷尽性系统综述；核查深度区分 PDF 指定段落与 Anthology 摘要，未声称全部精读或运行代码。

## 最需要更新的判断

1. 不能宣称已有角色评测只关心知识、风格、不关心用户：CharacterEval 有共情与交流能力，ChatAnime 有两轮对话与需求匹配。
2. 不能把“保持 persona 的同时适应情境”作为全新问题：PersonaArena 已明确包含此项。
3. 更可检验的候选贡献是：固定角色，控制双向 CP/ES 需求轨迹和历史证据，分别评价话题跟随、支持强度及角色一致性，并给出人类验证。其新颖性仍须与近邻论文数据和rubric逐项比对。
4. “跨越默认模式”不应等于“违反角色”。同一朋友可以认真倾听，同一支持型角色可以参与玩笑；核心是策略灵活性，不能把 CP/ES 当互斥人格。

## 优先级

P0：设计前必须精读；P1：方法与baseline重点参考；P2：背景或相关边界。具体以每条核查深度为准。

## 角色一致性

### [CharacterEval: A Chinese Benchmark for Role-Playing Conversational Agent Evaluation](https://aclanthology.org/2024.acl-long.638/)

**会议**：ACL 2024 主会；**优先级**：P1；**核查深度**：PDF §5及指标定义核查。

**已核实**：多轮角色对话，四维十三指标，CharacterRM；已有共情与交流能力评价。

**对你的设计**：复用多维角色评价思路及人工标注训练评价器。

**边界**：不能称其只评价知识；你的增量需是受控需求轨迹和支持强度适切性。

### [InCharacter: Evaluating Personality Fidelity in Role-Playing Agents through Psychological Interviews](https://aclanthology.org/2024.acl-long.102/)

**会议**：ACL 2024 主会；**优先级**：P1；**核查深度**：Anthology 摘要核查。

**已核实**：通过心理访谈与量表评价人格忠实度。

**对你的设计**：在独立探针上验证角色诱导是否生效。

**边界**：人格量表分数不是某次回复是否适合当前用户的金标准。

### [RoleLLM: Benchmarking, Eliciting, and Enhancing Role-Playing Abilities of Large Language Models](https://aclanthology.org/2024.findings-acl.878/)

**会议**：ACL 2024 Findings；**优先级**：P2；**核查深度**：Anthology 摘要核查。

**已核实**：构建角色画像、角色知识指令与说话风格数据 RoleBench。

**对你的设计**：角色卡组织及角色相关指令基线。

**边界**：主要是角色能力构建，不能直接代替 CP/ES 调节评价。

### [Spotting Out-of-Character Behavior: Atomic-Level Evaluation of Persona Fidelity in Open-Ended Generation](https://aclanthology.org/2025.findings-acl.1349/)

**会议**：ACL 2025 Findings；**优先级**：P1；**核查深度**：Anthology 摘要核查。

**已核实**：以细粒度单元诊断角色不一致，减少整段单分数的遮蔽。

**对你的设计**：给问题片段标证据；分别标角色偏离和需求偏离。

**边界**：把原子评估迁移为支持残留检测是本研究设计建议，不是该文已验证的结果。

### [CharacterGPT: A Persona Reconstruction Framework for Role-Playing Agents](https://aclanthology.org/2025.naacl-industry.24/)

**会议**：NAACL 2025 Industry；**优先级**：P2；**核查深度**：Anthology 摘要核查。

**已核实**：根据小说章节增量重建 persona，以人格与创作任务评价。

**对你的设计**：区分角色设定更新与固定角色下的策略调节。

**边界**：动态 persona 重建不是固定角色适应用户需求。

## 角色适配与冲突

### [When Harry Meets Superman: The Role of The Interlocutor in Persona-Based Dialogue Generation](https://aclanthology.org/2025.acl-long.879/)

**会议**：ACL 2025 主会；**优先级**：P0；**核查深度**：PDF 摘要及§5人工评价核查。

**已核实**：研究目标角色与交谈对象信息的影响，以身份识别及人工评价测量；对交谈对象信息进行显示/遮蔽。

**对你的设计**：借鉴上下文控制，但评估端应提供相同信息，避免仅因裁判线索增加而分数提高。

**边界**：交谈对象 persona 与同一用户逐轮 CP/ES 需求不同；不能宣称此前没有交谈对象适配研究。

### [PersonaArena: Dynamic Simulation for Evaluating and Enhancing Persona-Level Role-Playing in Large Language Models](https://aclanthology.org/2026.findings-acl.471/)

**会议**：ACL 2026 Findings；**优先级**：P0；**核查深度**：PDF §2.3及附录A.1核查。

**已核实**：动态社会模拟；八维指标中已有 Adaptability，定义包含在维持 persona 时适应变化情境。

**对你的设计**：把总体适应能力拆为需求识别、支持强度、话题跟随；比较通用 Adaptability 与你的指标。

**边界**：不能把角色一致性+适应性本身宣称为首次；多裁判共识不等于人类一致性。

### [RoleConflictBench: A Benchmark of Role Conflict Scenarios for Evaluating LLMs’ Contextual Sensitivity](https://aclanthology.org/2026.findings-acl.1695/)

**会议**：ACL 2026 Findings；**优先级**：P0；**核查深度**：PDF §3.3及附录A.6核查。

**已核实**：控制角色冲突场景的情境紧迫度，评价决策对情境的敏感性。

**对你的设计**：同一背景改变需求线索，另设无关线索不变对照；先独立验证线索标签。

**边界**：在用户多社会角色间作优先级建议，不等于 assistant 保持角色时调节支持策略。

### [RoleCDE: Benchmarking and Mitigating Role–Alignment Trade-offs in Role-Playing Agents](https://aclanthology.org/2026.findings-acl.106/)

**会议**：ACL 2026 Findings；**优先级**：P2；**核查深度**：Anthology 摘要核查。

**已核实**：结构化角色价值与对齐约束冲突。

**对你的设计**：区分价值/身份约束与互动策略偏好。

**边界**：你的 CP/ES 通常可以兼容，不应强行表述为不可同时满足的价值冲突；规模存在摘要与PDF片段不一致，需读全文再引用数字。

### [CPO: Addressing Reward Ambiguity in Role-playing Dialogue via Comparative Policy Optimization](https://aclanthology.org/2025.findings-emnlp.18/)

**会议**：EMNLP 2025 Findings；**优先级**：P1；**核查深度**：PDF §1及评价框架核查。

**已核实**：CharacterArena 采用上下文化多轮模拟及轨迹相对比较。

**对你的设计**：抽取子集作配对人工偏好，与分维等级分互证；增加自生成历史测试。

**边界**：相对比较不是客观金标准证明；固定历史对照与真实轨迹测试各有用途。

### [REMP: A Structured Event-Probing Benchmark for Long-Horizon Role-Playing Dialogue](https://aclanthology.org/2026.findings-emnlp.602/)

**会议**：EMNLP 2026 Findings；**优先级**：P1；**核查深度**：Anthology 摘要核查，PDF未能访问。

**已核实**：长程事件探针，评价人格、情绪、记忆与关系连续性。

**对你的设计**：设置需求变化事件，比较变化前后行为；短历史与长历史分层。

**边界**：已核实事件触发评价；具体是否覆盖 CP/ES 转换需检查数据和完整指标，不能推断没有。

## 角色与情绪需求

### [ChatAnime: Towards User-Centered Emotional Support in LLM-based Virtual Character Chat](https://aclanthology.org/2026.acl-long.2179/)

**会议**：ACL 2026 主会；**优先级**：P0；**核查深度**：PDF §3、§4、附录A/E核查。

**已核实**：真实日常情境、两轮角色对话；评价角色与支持，包含 Demand Matching。

**对你的设计**：直接对比其需求匹配 rubric；检查二轮用户话语，复用标注组织思路。

**边界**：最接近的角色+支持评测之一；两轮和需求匹配已有，差异不能只写成多轮或以用户为中心。

## 语用与需求

### [Grounding Gaps in Language Model Generations](https://aclanthology.org/2024.naacl-long.348/)

**会议**：NAACL 2024 主会；**优先级**：P0；**核查深度**：Anthology及PDF摘要/背景核查。

**已核实**：模型可能默认已理解用户而缺少必要的共同理解建立。

**对你的设计**：标上下文证据是否足够；模糊需求允许合适澄清。

**边界**：不能用问句数量表示好坏；多问也可能打断用户或持续治疗框架。

### [Understanding Client Reactions in Online Mental Health Counseling](https://aclanthology.org/2023.acl-long.577/)

**会议**：ACL 2023 主会；**优先级**：P0；**核查深度**：PDF §3、标注类别核查。

**已核实**：联合咨询师策略与来访者反应；Changing Topics 在该咨询语境下可表现为消极反应。

**对你的设计**：区分普通换话题、拒绝继续、回避、纠正；按上下文标注。

**边界**：临床咨询中的换话题含义不能直接移植为日常陪伴的需求标签。

### [EmoDynamiX: Emotional Support Dialogue Strategy Prediction by Modelling MiXed Emotions and Discourse Dynamics](https://aclanthology.org/2025.naacl-long.81/)

**会议**：NAACL 2025 主会；**优先级**：P1；**核查深度**：Anthology 摘要核查。

**已核实**：用混合情绪及话语动态预测支持策略，关注策略偏好偏差。

**对你的设计**：分开需求判断和策略选择；检验模型是否只偏爱少数支持策略。

**边界**：支持内策略选择与退出支持并不相同；不能写成已有工作全是静态。

### [Facilitating Multi-turn Emotional Support Conversation with Positive Emotion Elicitation: A Reinforcement Learning Approach](https://aclanthology.org/2023.acl-long.96/)

**会议**：ACL 2023 主会；**优先级**：P2；**核查深度**：Anthology 摘要核查。

**已核实**：动态调整积极情绪引导强度并兼顾连贯性。

**对你的设计**：作为支持强度调节的已有工作对比。

**边界**：减少痛苦/引导积极情绪与尊重当前陪伴邀请是不同评价目标。

## Judge

### [LLMs instead of Human Judges? A Large Scale Empirical Study across 20 NLP Evaluation Tasks](https://aclanthology.org/2025.acl-short.20/)

**会议**：ACL 2025 主会短文；**优先级**：P0；**核查深度**：PDF主结论及人工一致性附录核查。

**已核实**：JUDGE-BENCH 显示人机一致性依赖任务、属性和数据来源；CoT 不保证更好。

**对你的设计**：你的任务须有独立人工金标准；报告人-人及Judge-人一致性。

**边界**：其他任务的相关性不能替代 CSTM 任务内验证。

### [G-Eval: NLG Evaluation using Gpt-4 with Better Human Alignment](https://aclanthology.org/2023.emnlp-main.153/)

**会议**：EMNLP 2023 主会；**优先级**：P1；**核查深度**：Anthology 摘要核查。

**已核实**：以评价标准及结构化表单组织 LLM 评价，讨论人类对齐及偏差。

**对你的设计**：建立标准、证据片段与结构化分数的 prompting baseline。

**边界**：无参考评价可做，但不能把流畅度或泛化共情分当需求适配分。

### [Prometheus 2: An Open Source Language Model Specialized in Evaluating Other Language Models](https://aclanthology.org/2024.emnlp-main.248/)

**会议**：EMNLP 2024 主会；**优先级**：P1；**核查深度**：Anthology 摘要核查。

**已核实**：支持用户指定评价准则、直接评分及配对排名的开放评价模型。

**对你的设计**：专用 LoRA 需与强 prompting 和现有开放Judge对比；核查输入格式要求。

**边界**：模型在其他基准的强表现不保证理解你的新构念。

### [Humans or LLMs as the Judge? A Study on Judgement Bias](https://aclanthology.org/2024.emnlp-main.474/)

**会议**：EMNLP 2024 主会；**优先级**：P1；**核查深度**：Anthology 摘要核查。

**已核实**：研究人类和 LLM 评价中的多种偏差及扰动脆弱性。

**对你的设计**：做控制内容的表面表达扰动测试，人工也需盲评。

**边界**：不能假设人类无偏；需要清晰rubric及分歧记录。

### [Are LLM-Judges Robust to Expressions of Uncertainty? Investigating the effect of Epistemic Markers on LLM-based Evaluation](https://aclanthology.org/2025.naacl-long.452/)

**会议**：NAACL 2025 主会；**优先级**：P0；**核查深度**：Anthology 摘要核查。

**已核实**：EMBER 测试不确定性表达对单项及配对评价的影响。

**对你的设计**：比较保留语义的笃定/谨慎表达，防止把克制支持或合适澄清误判低质。

**边界**：在本任务中缓和措辞也可能改变真实适切性，不能未经人工确认就当等价扰动。

## 补充Judge

### [Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge](https://aclanthology.org/2025.ijcnlp-long.18/)

**会议**：IJCNLP-AACL 2025，非ACL/NAACL/EMNLP；**优先级**：P2；**核查深度**：Anthology 摘要核查。

**已核实**：系统研究位置偏差、重复稳定性与位置一致性。

**对你的设计**：配对结果交换顺序；报告翻转、平局与不一致。

**边界**：角色资料属于角色一致性评价所需输入；应隐藏模型来源，不是删掉全部角色信息。

## 从文献落实到实验

以下是针对你任务的设计建议，不是原论文已经验证的结论。

| 模块 | 建议 | 来源线索 |
|---|---|---|
| 角色操纵检查 | 用独立样本检查 CP/ES 提示是否真的产生不同默认倾向，另测角色知识/风格保持 | InCharacter、CharacterEval |
| 角色与策略分层 | 明确身份/知识/价值等较稳定约束，与可调节的幽默、探询、建议强度 | RoleCDE、Spotting OOC |
| 受控情境 | 同一角色、同一背景，仅改当前需求线索；无关线索作为不变对照 | RoleConflictBench |
| 用户侧适配 | 固定评价端可见信息，仅改变生成端历史/用户线索，防止裁判信息量混杂 | When Harry Meets Superman 的显示/遮蔽设计启发 |
| 需求轨迹 | 四类轨迹，隐含/显式，短/长历史，需求不确定样本 | ChatAnime、REMP、EmoDynamiX |
| 评价分解 | 角色一致性、当前需求回应、话题跟随、支持强度匹配、证据依据分开评分 | PersonaArena、ChatAnime、CharacterEval |
| 标注单位 | 在回复中标出过度探询、旧困扰回访、无依据推断等片段，而非只给总分 | Spotting OOC、Client Reactions |
| 历史协议 | 固定历史适合配对控制；另加自生成历史子集，检验角色延续及错误恢复 | CharacterArena |
| Judge 校验 | 人工金标准、各维度一致性、长度/格式/来源/位置扰动、未见角色与生成模型留出 | JUDGE-BENCH、EMBER、Prometheus 2 |

## 角色一致性与需求适配的联合判断

| | 当前需求匹配高 | 当前需求匹配低 |
|---|---|---|
| 角色一致性高 | 理想的角色内适配 | 角色僵化候选，须排除有意设计的强角色约束 |
| 角色一致性低 | 可能靠退出角色完成适配 | 两个目标均未满足 |

角色一致性评价必须提供角色卡；需求评价可独立进行以免被角色标签诱导。对刻意冷漠、恶意或拒绝支持的角色，不宜默认所有情境都有兼顾两个目标的答案。首版可选择具有基本合作意愿、但互动倾向不同的角色。

## 需要首先精读的顺序

1. ChatAnime §3/§4、附录A/E：逐项对照二轮输入与 Demand Matching，核查是否已包含支持退出。
2. PersonaArena §2.3、附录A.1：对照 Adaptability 的输入、分数锚点和人类验证。
3. RoleConflictBench §3及附录A.6：参考如何验证情境线索，避免把构造者意图当金标准。
4. When Harry Meets Superman 方法与§5：区分生成端条件与评价端可见线索。
5. Grounding Gaps 与 Client Reactions：形成不确定需求、换话题、拒绝与回避的边界例。
6. JUDGE-BENCH 与 EMBER：设计任务内人机一致性与表面风格鲁棒性测试。

## 投稿前必须回答的近邻比较问题

- ChatAnime 的需求匹配指标是否已惩罚不必要支持？必须看rubric和样本，不能从标题推断没有。
- PersonaArena 的 Adaptability 能否直接识别支持残留？用同一组人工确认的对照回复测试。
- REMP 的情绪事件是否包含用户从支持转为日常互动？目前仅摘要核实，未读到全部数据。
- 短功能型角色提示是否足以支持 role-play 的论域？加入多种人格/关系角色，或收窄主张为 role-conditioned assistants。
- 专用Judge的改进是否只是迎合长度或温柔措辞？训练与测试应按情境家族划分，并留出生成模型。

## 可用的暂定定位

已有工作研究角色忠实度、交谈对象适配、动态情境及情绪支持质量。本研究拟在固定角色条件下，通过受控的陪伴—支持需求轨迹，评估模型能否随上下文增加或降低支持强度，并将这种需求适配与角色保持、话题跟随分开验证。

这是一项待通过近邻基准对比验证的定位，不是“首次”声明。

## 自检

- 贡献：不把通用角色适配、多轮或需求匹配本身当空白。
- 清晰性：区分角色更新、角色切换、固定角色下的策略调节。
- 实验：每项新主张都对应受控样本与人工证据。
- 评价：多模型共识不能取代任务内人工校验。
- 方法：拟人化经验共享在虚构角色中与普通AI助手中的含义不同，需按角色卡分别判断。
