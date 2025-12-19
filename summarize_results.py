import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def main():
    df = pd.read_csv("combined_analysis.csv")
    
    # Define metric groups
    # 不再统计“计算准确率”，改为统计“单词记忆记对数量”
    mist_metrics = ['Word_Recall_Correct', 'MIST_ResponseTime', 'MIST_Timeouts']
    bio_metrics = ['Bio_HR_Mean', 'Bio_HRV_RMSSD', 'Bio_HRV_LFHF', 'Bio_SCL_Mean', 'Bio_SCR_Freq', 'Bio_EDA_MeanFreq', 'Bio_EDA_Power005', 'Bio_RESP_Rate']
    force_metrics = ['Force_Total_Mean']
    avatar_metrics = ['Avatar_Embodiment_Mean', 'Avatar_Q1_Ownership', 'Avatar_Q6_Control', 'Avatar_Q25_HarmConcern']
    nasa_metrics = ['NASA_TLX_Score', 'NASA_Mental', 'NASA_Frustration']
    
    # 1. Group by Condition (A, B, C, D)
    print("=== Mean Values by Condition ===")
    grouped = df.groupby('Condition')[mist_metrics + bio_metrics + nasa_metrics + avatar_metrics].mean(numeric_only=True)
    print(grouped)
    print("\n")
    
    # 2. Specific Comparisons
    print("=== Comparison: Robotic Arm (C+D) vs No Arm (A+B) ===")
    df['HasArm'] = df['Condition'].isin(['C', 'D'])
    arm_comp = df.groupby('HasArm')[mist_metrics + bio_metrics + nasa_metrics + avatar_metrics].mean(numeric_only=True)
    print(arm_comp)
    print("\n")
    
    print("=== Comparison: Clothed (D) vs Naked Robot (C) ===")
    robot_df = df[df['Condition'].isin(['C', 'D'])]
    robot_comp = robot_df.groupby('Condition')[mist_metrics + bio_metrics + nasa_metrics + force_metrics + avatar_metrics].mean(numeric_only=True)
    print(robot_comp)
    print("\n")
    
    # 3. Save Summary
    grouped.to_csv("summary_by_condition.csv")
    print("Summary saved to summary_by_condition.csv")

if __name__ == "__main__":
    main()

