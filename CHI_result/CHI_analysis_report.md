# CHI 分析结果包（MIST-stress-test）

本文件夹汇总了基于 `data/` 与 `combined_analysis.csv` 的 **CHI/HCI 风格定量+定性**分析输出（含图表、统计表、定性主题、以及用于对齐相关工作的PDF摘录）。

## 1. 实验设计与条件说明
- **被试**：6名（SubjectID 1–6），组内设计。
- **条件**（来自 `data/实验顺序.txt`）：
  - **A**：自己右手做思考姿势
  - **B**：强制不做思考姿势
  - **C**：控制机械臂做思考姿势（无衣服）
  - **D**：控制穿衣服机械臂做思考姿势
- **量化指标**（来自 `combined_analysis.csv`）：
  - **行为表现**：Word_Recall_Correct（单词记忆记对数量）, MIST_ResponseTime, MIST_Timeouts
  - **生理**：Bio_EDA_Mean, Bio_BVP_Mean, Bio_RESP_Mean（其中 C 条件有 1 名缺失，因此相关检验以完整被试为准）
  - **主观量表**：NASA_TLX_Score, NASA_Mental, NASA_Frustration
  - **力传感**：Force_Total_*（仅 C/D 有数据；Thumb+Index 合并后的总力）

## 2. 定量分析说明（Quant）
- **描述统计**：按条件输出 mean/sd/median/iqr。
- **总体组内差异**：对 A/B/C/D 进行 Friedman 检验，并报告 Kendall’s W（效应量）。
- **关键对比（配对）**：
  - A vs B（允许姿势 vs 禁止姿势）
  - D vs C（穿衣机械臂 vs 裸机械臂）
  - HasArm vs NoArm（(C,D)均值 vs (A,B)均值）
  使用 Wilcoxon signed-rank，并报告 rank-biserial correlation (RBC) 作为方向性效应量。

> 备注：样本量（n=6）较小，且同一被试在 4 条件下为重复测量设计；当前结果更适合以“趋势+效应量+机制解释（配合定性主题）”方式呈现，并作为后续扩大样本/更严格生理预处理与基线控制的依据。

### 2.1 定量统计结果（可直接用于论文 Results）
统计表详见：
- `tables/descriptives_by_condition.csv`
- `tables/friedman_ABCD.csv`
- `tables/paired_t_tests.csv`（配对 t，含 95%CI 与 Cohen’s dz）
- `tables/paired_wilcoxon_tests.csv`（配对 Wilcoxon，含 RBC）

#### (1) 描述统计（均值±SD）
（从 `tables/descriptives_by_condition.csv` 汇总）
- **单词记忆记对数量**：A 6.333±1.033；B 7.167±1.941；C 6.000±2.000；D 7.500±1.871
- **MIST反应时(s)**：A 4.855±1.983；B 4.636±1.351；C 4.790±1.387；D 4.625±0.861
- **MIST超时数**：A 1.167±1.472；B 2.167±2.787；C 1.833±1.835；D 1.667±1.862
- **NASA-TLX**：A 9.608±1.509；B 9.244±3.323；C 10.147±2.702；D 10.681±2.393
- **NASA心理需求**：A 12.000±4.944；B 10.500±5.416；C 13.067±5.916；D 13.700±4.833
- **NASA挫败感**：A 10.233±5.370；B 6.433±2.679；C 10.150±6.413；D 8.750±4.858
- **EDA均值**：A 6.289±4.598；B 6.683±3.518；C 5.043±2.526（n=5）；D 5.494±2.555

#### (2) 总体组内差异（Friedman，A/B/C/D）
（完整被试数：行为/量表 n=6；生理均值 n=5）
- **单词记忆记对数量**：χ²=5.706，p=0.127，Kendall’s W=0.317
- **MIST反应时**：χ²=1.400，p=0.706，W=0.078
- **MIST超时数**：χ²=3.364，p=0.339，W=0.187
- **NASA-TLX**：χ²=4.017，p=0.260，W=0.223
- **NASA心理需求**：χ²=6.051，p=0.109，W=0.336（最接近显著的一项：提示“条件”可能影响主观心理需求）
- **NASA挫败感**：χ²=1.000，p=0.801，W=0.056

#### (3) 关键配对对比（t 与 p）
以下为**配对 t 检验**（见 `tables/paired_t_tests.csv`），与非参数 Wilcoxon（见 `tables/paired_wilcoxon_tests.csv`）方向基本一致：
- **A vs B（允许姿势 vs 禁止姿势）**
  - MIST超时数：t(5)=-1.581，p=0.175，均值差(A-B)=-1.000（趋势：禁止姿势更易超时）
  - 单词记忆记对数量：t(5)=-1.185，p=0.289，均值差(A-B)=-0.833（趋势：B 更高，但不显著）
  - 其余指标差异不显著
- **D vs C（穿衣机械臂 vs 裸机械臂）**
  - NASA-TLX：t(5)=1.567，p=0.178，均值差(D-C)=+0.533（趋势：穿衣条件主观负荷更高）
  - 单词记忆记对数量：t(5)=2.423，p=0.060，均值差(D-C)=+1.500（趋势：D 更高，接近显著）
  - 其余指标差异不显著
- **HasArm vs NoArm（(C,D) vs (A,B)）**
  - NASA心理需求：t(5)=1.841，p=0.125，均值差=+2.133（趋势：引入机械臂交互增加心理需求）
  - 单词记忆记对数量：t(5)=0.000，p=1.000，均值差=0.000（两侧平均相同）
  - 其余指标差异不显著

> 解释建议（CHI写作）：在 n=6 的小样本下，当前更适合报告“方向性趋势 + 效应量（dz 或 RBC）+ 定性机制”，并将显著性作为探索性结论而非强因果结论。

### 2.2 Avatar Embodiment Questionnaire（C/D 条件）
数据来源：`data/avatar_scale/*.xlsx`。量表包含 Q1–Q25，并在问卷中出现两段（默认段与 `.1` 段）。我们将默认段映射为 **C（Naked Robot）**、`.1` 段映射为 **D（Clothed Robot）**；若 `Serial Number` 包含“相反”，则交换 C/D 映射。  
对 Q22/Q23 的重复列（两种英文版本）做合并（同题取均值，忽略不可转数值）。  

为便于分析，我们在 `combined_analysis.csv` 中构建了以下指标（仅在 C/D 存在）：  
- `Avatar_Embodiment_Mean`：Q1–Q25 的均值（原始方向）  
- `Avatar_Ownership_Score`：Ownership（含对“someone else”题项的反向计分；对称刻度下用取负号近似反向）  
- `Avatar_Agency_Score`：Agency/Control（Q6/Q7/Q8 与反向后的 Q9）  
- `Avatar_Touch_Score`：触觉/触觉归因（Q10–Q13）  
- `Avatar_Q25_HarmConcern`：安全/伤害担忧（原始分）  

统计输出：  
- `tables/avatar_C_vs_D_tests.csv`：C vs D 的配对 t 与 Wilcoxon 对比  
- 图：`figures/plots/boxplot_Avatar_*_C_vs_D.png`（箱线图+散点）  

本次样本（n=6）下，C vs D 的 Avatar 总体/Ownership/Agency 未观察到显著差异；Touch 分量表呈上升趋势（D 高于 C，n=5，t=2.282，p=0.0846）。  

## 3. 定性分析说明（Qual）
数据来源：`data/interviews/1.txt`–`6.txt` 半结构访谈转写。
输出采用 CHI 常见写法：**主题（Theme）—证据摘录（Quote）—机制解释（Mechanism）**。
当前数据中较一致的主题包括：
- 低身体归属感：机械臂更像“支架/异物”，而非身体延伸
- 交互成本/分心：控制、声音、不可见轨迹与主任务竞争
- 可预测性与信任：更希望可见轨迹/更可控/更即时的启动反馈
- 微调与协同适配：缺少头-手协调，用户需要“迎合它”
- 外观/衣服的边界：可见时影响可接受性；不可见时弱
- 触感与双向触觉：硬/硌与缺少触觉反馈削弱“情感性自触摸”
- 减轻压力/认知负担：更放松、更稳定、更集中/更“来得及答题”

### 3.1 定性结论（可直接用于论文 Results）
（详见 `qual/qual_themes_and_quotes.txt`）
- **机械臂多被体验为“支架/异物”而非身体延伸**：多数被试给出极低的“像自己手”评分（0/1），并强调其更像“固定支撑物”。  
- **主任务优先导致“运动过程/外观”常被忽略**：多名被试表示做题时几乎不关注轨迹或衣服变化，只有在可见/注意到时外观才影响可接受性。  
- **影响体验的关键机制**集中在：可预测性（何时到达/是否可见）、可控性（是否一键触发且稳定）、微调协同（是否随头部微动适配）、触感与双向触觉反馈（软硬与触觉回路）。  

## 4. 与相关工作（PDF）对齐
`pdf/` 下保存了PDF文本抽取与关键词片段，主要用于对齐“embodiment/agency/predictability/appearance/clothing/trust/stress/workload”等概念框架。

## 5. 统计结论（简版）
综合定量与定性，当前数据支持以下更稳健的结论（适合写在 CHI 的 Findings/Discussion）：  
- **结论1（交互成本 vs 认知卸载的张力）**：机械臂要想提供“思考姿势/自触摸”带来的认知卸载，前提是不能引入额外的注意占用；访谈中“分心/等待/迎合位置/噪声”会把辅助变成负担，这也解释了总体量化差异不显著。  
- **结论2（姿势限制可能影响超时）**：A 相比 B 在 MIST 超时数上呈降低趋势（A-B=-1.000；t(5)=-1.581；p=0.175；Wilcoxon p=0.25，RBC=-1.0），提示“允许自发姿势/支撑”可能帮助在高压时间限制下维持作答节奏。  
- **结论3（机械臂条件可能提高主观心理需求/负荷）**：HasArm 相比 NoArm 在 NASA心理需求上呈上升趋势（+2.133；t(5)=1.841；p=0.125；Friedman p=0.109），与访谈中“需要贴合/额外控制/可预测性不足”一致。  
- **结论4（外观不是首要变量）**：D vs C 的差异整体较小；访谈显示外观的效应被“是否可见/是否注意”强烈调节，优先级低于可预测性与微调协同。  
- **结论5（记忆任务在穿衣机械臂条件更好，趋势接近显著）**：单词记忆记对数量在 D 相比 C 更高（D-C=+1.5；t(5)=2.423；p=0.060），提示“穿衣外观/更可接受的形态线索”可能在不显著打断主任务的情况下帮助记忆表现；该结论需更大样本验证。  

## 6. 文件清单
- `figures/plots/`：现有图表（箱线图、折线图、相关热图、力对比、性能vs负荷等）
- `tables/descriptives_by_condition.csv`：按条件描述统计
- `tables/friedman_ABCD.csv`：A/B/C/D 的 Friedman 检验 + Kendall’s W
- `tables/paired_t_tests.csv`：关键配对对比（配对 t，含 t/p/CI/dz）
- `tables/paired_wilcoxon_tests.csv`：关键配对对比（含 RBC）
- `qual/qual_themes_and_quotes.txt`：定性主题与代表性引文
- `pdf/Social_Robot_Related_Work_extracted.txt`：PDF文本抽取（用于检索）
- `pdf/key_snippets.txt`：关键词片段摘录
