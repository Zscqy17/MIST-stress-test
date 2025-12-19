# MIST Stress Test & HRI Analysis Project

这是一个包含 Montreal Image Stress Test (MIST) 实验程序以及相关人机交互 (HRI) 生理与心理数据分析的完整项目。

## 核心代码说明

本项目主要包含以下核心脚本：

### 1. 实验程序
*   **`mist_test.py`**
    *   **功能**：运行 MIST 压力测试实验的 GUI 程序。
    *   **特点**：包含倒计时、算术题生成、自动记录反应时与正确率。
    *   **运行**：`python mist_test.py`

### 2. 数据分析流水线
*   **`process_data.py`**
    *   **功能**：数据预处理与融合。
    *   **描述**：读取 `data/` 目录下的 MIST 行为数据、PhysioLAB 生理数据 (EDA, HR等)、NASA-TLX 问卷数据及 Force Sensor 数据，进行时间戳对齐和清洗，生成 `combined_analysis.csv`。

*   **`run_statistics.py`**
    *   **功能**：统计分析。
    *   **描述**：对清洗后的数据进行统计检验（如 ANOVA, t-test, Friedman test），分析不同实验条件（A: Self-Think, B: No-Think, C: Naked Robot, D: Clothed Robot）下的显著性差异。

*   **`visualize_results.py`**
    *   **功能**：数据可视化。
    *   **描述**：基于统计结果绘制箱线图、折线图和相关性热力图，可视化生理指标、任务表现和主观问卷评分的差异。

*   **`summarize_results.py`**
    *   **功能**：生成报告。
    *   **描述**：汇总所有分析结果，生成 Markdown 格式的分析报告。

## 实验条件说明

*   **Condition A**: Self right hand thinking pose (人类右手思考姿态)
*   **Condition B**: Forced no thinking pose (强制无思考姿态)
*   **Condition C**: Control robotic arm thinking pose (Naked) (裸机机械臂思考姿态)
*   **Condition D**: Control clothed robotic arm thinking pose (Clothed) (穿衣机械臂思考姿态)

## 快速开始

1.  **运行实验**：
    ```bash
    python mist_test.py
    ```
2.  **运行完整分析**：
    ```bash
    # 1. 处理数据
    python process_data.py
    # 2. 运行统计
    python run_statistics.py
    # 3. 生成图表
    python visualize_results.py
    ```

## 依赖库

*   `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `pingouin`
*   `tkinter` (用于实验程序)
