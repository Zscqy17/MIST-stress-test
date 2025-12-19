import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # For Chinese characters support on MacOS if needed, or just generic sans-serif
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = "plots"

def save_plot(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Saved {path}")

def main():
    df = pd.read_csv("combined_analysis.csv")
    
    # Map Condition codes to descriptive names for better legends
    condition_map = {
        'A': 'A: Self Gesture',
        'B': 'B: No Gesture',
        'C': 'C: Naked Robot',
        'D': 'D: Clothed Robot'
    }
    df['Condition_Name'] = df['Condition'].map(condition_map)
    
    # Sort order
    order = ['A', 'B', 'C', 'D']
    order_names = [condition_map[x] for x in order]

    # --- 1. Box Plots for Main Metrics (Condition Comparison) ---
    metrics = [
        ('Word_Recall_Correct', 'Word Recall Correct (#)', (0, 10)),
        ('MIST_ResponseTime', 'Response Time (s)', None),
        ('Bio_HR_Mean', 'Heart Rate (BPM)', None),
        ('Bio_HRV_RMSSD', 'HRV (RMSSD) (ms)', None),
        ('Bio_HRV_LFHF', 'HRV LF/HF Ratio', None),
        ('Bio_SCL_Mean', 'Skin Conductance Level (uS)', None),
        ('Bio_SCR_Freq', 'SCR Frequency (peaks/min)', None),
        ('Bio_EDA_MeanFreq', 'EDA Gradient Mean Freq (Hz)', None),
        ('Bio_EDA_Power005', 'EDA Gradient Power @ 0.05Hz', None),
        ('Bio_RESP_Rate', 'Respiration Rate (breaths/min)', None),
        ('NASA_TLX_Score', 'NASA TLX Workload', (0, 20)), # Assuming raw scale, adjust if needed
        ('NASA_Frustration', 'Frustration Level', None)
    ]

    for col, title, ylim in metrics:
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='Condition', y=col, hue='Condition', data=df, order=order, palette="Set2", legend=False)
        sns.swarmplot(x='Condition', y=col, data=df, order=order, color=".25", size=6) # Add individual points
        plt.title(f"{title} by Condition", fontsize=16)
        plt.xlabel("Condition")
        plt.ylabel(title)
        if ylim:
            plt.ylim(ylim)
        save_plot(f"boxplot_{col}.png")

    # --- 2. Line Plots (Subject Trends) ---
    # Show how each subject changed across conditions. 
    # Since conditions are categorical, this is a parallel coordinate-like plot.
    
    # Pivot for parallel coordinates is tricky if order varies, 
    # so we just plot lines grouping by SubjectID
    
    for col, title, _ in metrics:
        plt.figure(figsize=(10, 6))
        sns.pointplot(x='Condition', y=col, hue='SubjectID', data=df, order=order, palette="tab10", markers='o')
        plt.title(f"Individual Subject Trends: {title}", fontsize=16)
        plt.legend(title='Subject ID', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.ylabel(title)
        save_plot(f"lineplot_subject_{col}.png")

    # --- 3. Force Comparison (C vs D) ---
    force_df = df[df['Condition'].isin(['C', 'D'])]
    if not force_df.empty:
        # 仅一个力传感器：将 Thumb/Index 合并为总力（在 process_data.py 中已生成 Force_Total_*）
        if 'Force_Total_Mean' in force_df.columns:
            plt.figure(figsize=(7, 6))
            sns.barplot(
                x='Condition',
                y='Force_Total_Mean',
                data=force_df,
                order=['C', 'D'],
                palette="viridis",
                errorbar='sd'
            )
            plt.title("Interaction Force (Total): Naked (C) vs Clothed (D)", fontsize=16)
            plt.xlabel("Condition")
            plt.ylabel("Mean Total Force Magnitude (Thumb + Index)")
            save_plot("barplot_force_comparison.png")

    # --- 4. Bio-Psych Correlation Matrix ---
    # Select relevant columns
    corr_cols = [
        'Word_Recall_Correct', 'MIST_ResponseTime', 
        'Bio_HR_Mean', 'Bio_HRV_RMSSD', 'Bio_HRV_LFHF',
        'Bio_SCL_Mean', 'Bio_SCR_Freq', 'Bio_EDA_MeanFreq', 'Bio_EDA_Power005',
        'NASA_TLX_Score', 'NASA_Mental', 'NASA_Frustration'
    ]
    corr_matrix = df[corr_cols].corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0, fmt=".2f")
    plt.title("Correlation Matrix of Metrics", fontsize=16)
    save_plot("heatmap_correlation.png")

    # --- 5. Grouped Bar Plot: Word Recall & NASA TLX ---
    # To compare performance vs perceived workload side by side
    # Normalize or just plot on dual axis? Dual axis is messy. 
    # Let's just do two subplots.
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    sns.barplot(x='Condition', y='Word_Recall_Correct', data=df, order=order, ax=axes[0], palette="Blues_d", errorbar='se')
    axes[0].set_title("Word Recall Correct (Higher is Better)")
    axes[0].set_ylim(0, 10)
    
    sns.barplot(x='Condition', y='NASA_TLX_Score', data=df, order=order, ax=axes[1], palette="Reds_d", errorbar='se')
    axes[1].set_title("NASA TLX Workload (Lower is Better)")
    
    plt.suptitle("Performance vs Workload Comparison", fontsize=16)
    save_plot("comparison_perf_workload.png")

    print("All plots generated in 'plots' directory.")

if __name__ == "__main__":
    main()

