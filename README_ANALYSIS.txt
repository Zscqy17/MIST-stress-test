Analysis Results for MIST Stress Test
===================================

Files Generated:
1. combined_analysis.csv: Master dataset containing row-by-row data for each Subject and Condition.
2. summary_by_condition.csv: Aggregated mean values for each Condition (A, B, C, D).

Column Descriptions:
- Condition A: Self right hand thinking pose
- Condition B: Forced no thinking pose
- Condition C: Control robotic arm thinking pose (Naked)
- Condition D: Control clothed robotic arm thinking pose (Clothed)

Key Findings:

1. Performance (MIST Accuracy):
   - Condition A & D (0.81) > C (0.76) > B (0.75)
   - Participants performed best in the Self-Think (A) and Clothed Robot (D) conditions.
   - Forced No-Think (B) had the worst performance.

2. Physiological Stress (EDA - Skin Conductance):
   - B (6.68) > A (6.28) > D (5.49) > C (5.04)
   - Surprisingly, Robot conditions (C & D) showed LOWER physiological arousal compared to Human conditions (A & B).
   - Among robots, the Clothed Robot (D) elicited higher arousal than the Naked Robot (C).

3. Subjective Workload (NASA TLX):
   - D (10.68) > C (10.14) > A (9.60) > B (9.24)
   - Participants reported the HIGHEST workload/stress for the Clothed Robot (D), followed by Naked Robot (C).
   - This contrasts with the physiological data (lower EDA for robots), suggesting a dissociation between perceived and physiological stress.

4. Force Sensor (Interaction Force):
   - Thumb Force was higher in Condition D (0.74) vs C (0.42).
   - Indicates stronger interaction or grip with the Clothed Robot.

Methodology:
- Data matched based on 'data/实验顺序.txt' and timestamps.
- Bio data aligned using file start times.
- NASA TLX mapped assuming sequential order (Round 1-4).

