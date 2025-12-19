import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# Set style
sns.set_theme(style="whitegrid")
# Try to set a font that supports Chinese if available, otherwise fallback
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = "plots"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def save_plot(fig, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"Saved {path}")

def main():
    if not os.path.exists("combined_analysis.csv"):
        print("Error: combined_analysis.csv not found.")
        return

    df = pd.read_csv("combined_analysis.csv")
    
    # Condition mapping/order
    order = ['A', 'B', 'C', 'D']
    
    # --- Plot 1: Physiological & Force ---
    # Grouping
    # 1. Force
    force_metrics = ['Force_Total_Mean']
    # 2. BVP (Heart)
    bvp_metrics = ['Bio_HR_Mean', 'Bio_HRV_RMSSD', 'Bio_HRV_LFHF']
    # 3. EDA (GSR)
    eda_metrics = ['Bio_SCL_Mean', 'Bio_SCR_Freq', 'Bio_EDA_MeanFreq', 'Bio_EDA_Power005']
    # 4. RESP
    resp_metrics = ['Bio_RESP_Rate']
    
    # Flatten list for iteration
    all_metrics = force_metrics + bvp_metrics + eda_metrics + resp_metrics
    
    # Titles map for better readability
    titles = {
        'Force_Total_Mean': 'Force (Total Mean) [N]',
        'Bio_HR_Mean': 'Heart Rate [BPM]',
        'Bio_HRV_RMSSD': 'HRV (RMSSD) [ms]',
        'Bio_HRV_LFHF': 'HRV (LF/HF Ratio)',
        'Bio_SCL_Mean': 'SCL (Mean) [uS]',
        'Bio_SCR_Freq': 'SCR Freq [peaks/min]',
        'Bio_EDA_MeanFreq': 'EDA Gradient Mean Freq [Hz]',
        'Bio_EDA_Power005': 'EDA Gradient Power @ 0.05Hz',
        'Bio_RESP_Rate': 'Resp Rate [breaths/min]'
    }
    
    # Layout: 3 rows x 3 columns = 9 plots
    fig, axes = plt.subplots(3, 3, figsize=(18, 15))
    axes = axes.flatten()
    
    for i, metric in enumerate(all_metrics):
        ax = axes[i]
        
        # Check if metric exists in df
        if metric in df.columns:
            # Use barplot to show Mean + SE (Standard Error)
            sns.barplot(x='Condition', y=metric, data=df, order=order, ax=ax, palette='viridis', errorbar='se', capsize=.1)
            ax.set_title(titles.get(metric, metric), fontsize=14, fontweight='bold')
            ax.set_xlabel('')
            ax.set_ylabel('')
            
            # Add value labels on top of bars (optional, but helpful for summary)
            # means = df.groupby('Condition')[metric].mean()
            # for j, cond in enumerate(order):
            #     if cond in means:
            #         val = means[cond]
            #         if not pd.isna(val):
            #             ax.text(j, val, f'{val:.2f}', ha='center', va='bottom')
        else:
            ax.text(0.5, 0.5, f"Metric {metric} not found", ha='center', va='center')
            
    fig.suptitle('Physiological & Force Metrics by Condition', fontsize=20, y=0.99)
    save_plot(fig, "summary_physio_force_combined.png")
    
    # --- Plot 2: NASA TLX ---
    # Only plot Total Score as requested ("不用放子表格")
    nasa_metrics = ['NASA_TLX_Score']
    nasa_titles = {
        'NASA_TLX_Score': 'NASA TLX (Mean Score)',
    }
    
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    
    metric = 'NASA_TLX_Score'
    if metric in df.columns:
        sns.barplot(x='Condition', y=metric, data=df, order=order, ax=ax2, palette='magma', errorbar='se', capsize=.1)
        ax2.set_title(nasa_titles.get(metric, metric), fontsize=14, fontweight='bold')
        ax2.set_xlabel('Condition')
        ax2.set_ylabel('')
    
    fig2.suptitle('NASA TLX Score by Condition', fontsize=20, y=0.95)
    save_plot(fig2, "summary_nasa_tlx_combined.png")

if __name__ == "__main__":
    main()
