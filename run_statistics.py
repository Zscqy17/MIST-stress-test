import pandas as pd
import numpy as np
from scipy import stats
import scikit_posthocs as sp

def interpret_effect_size_kendall(w):
    if w < 0.1: return "Very Weak"
    if w < 0.3: return "Weak"
    if w < 0.5: return "Moderate"
    if w < 0.7: return "Strong"
    return "Very Strong"

def main():
    df = pd.read_csv("combined_analysis.csv")
    
    # Metrics to analyze
    metrics = [
        # Performance
        'Word_Recall_Correct', 'MIST_ResponseTime',
        # Physio - Heart
        'Bio_HR_Mean', 'Bio_HRV_RMSSD', 'Bio_HRV_LFHF',
        # Physio - EDA
        'Bio_SCL_Mean', 'Bio_SCR_Freq', 'Bio_EDA_MeanFreq', 'Bio_EDA_Power005',
        # Physio - Resp
        'Bio_RESP_Rate',
        # Subjective
        'NASA_TLX_Score', 'NASA_Mental', 'NASA_Frustration'
    ]
    
    results = []
    
    print("=== Statistical Analysis Report ===\n")
    
    for metric in metrics:
        # Pivot data: Rows=Subject, Cols=Condition
        # We need complete cases for repeated measures
        pivot = df.pivot(index='SubjectID', columns='Condition', values=metric)
        
        # Check for missing values
        if pivot.isnull().values.any():
            # print(f"Warning: Missing values for {metric}. Dropping incomplete subjects.")
            pivot = pivot.dropna()
            
        if pivot.shape[0] < 2:
            print(f"Skipping {metric}: Not enough data points after dropping NaNs.")
            continue
            
        # 1. Friedman Test (Non-parametric repeated measures ANOVA)
        # Conditions: A, B, C, D
        try:
            stat, p_val = stats.friedmanchisquare(
                pivot['A'], pivot['B'], pivot['C'], pivot['D']
            )
        except ValueError as e:
            print(f"Error calculating Friedman for {metric}: {e}")
            continue

        # 2. Kendall's W (Effect Size for Friedman)
        # W = Chi2 / (N * (k-1))
        # N = number of subjects, k = number of conditions (4)
        N = pivot.shape[0]
        k = 4
        kendalls_w = stat / (N * (k - 1))
        w_interp = interpret_effect_size_kendall(kendalls_w)
        
        row = {
            "Metric": metric,
            "N": N,
            "Friedman_Chi2": stat,
            "p_value": p_val,
            "Significance": "**" if p_val < 0.01 else ("*" if p_val < 0.05 else "ns"),
            "Kendalls_W": kendalls_w,
            "W_Interpretation": w_interp
        }
        results.append(row)
        
        print(f"--- {metric} ---")
        print(f"N={N}, Friedman p={p_val:.4f} ({row['Significance']})")
        print(f"Kendall's W={kendalls_w:.3f} ({w_interp})")
        
        # 3. Post-hoc Analysis (Nemenyi test) if significant
        if p_val < 0.05:
            print("  > Post-hoc (Nemenyi):")
            # Melt for posthoc
            melted = pivot.reset_index().melt(id_vars='SubjectID', var_name='Condition', value_name='Value')
            ph = sp.posthoc_nemenyi_friedman(melted, y_col='Value', group_col='Condition', block_col='SubjectID')
            
            # Print significant pairs
            found_sig = False
            conditions = ['A', 'B', 'C', 'D']
            for i in range(len(conditions)):
                for j in range(i+1, len(conditions)):
                    c1, c2 = conditions[i], conditions[j]
                    pval_ph = ph.loc[c1, c2]
                    if pval_ph < 0.05:
                        print(f"    {c1} vs {c2}: p={pval_ph:.4f} *")
                        found_sig = True
            if not found_sig:
                print("    No specific pairs significant despite global test.")
        print("")

    # Save results table
    res_df = pd.DataFrame(results)
    res_df.to_csv("statistical_analysis_results.csv", index=False)
    print("Full statistical table saved to 'statistical_analysis_results.csv'")

    # --- Explanation of Metrics ---
    print("\n=== 指标解释 (Metric Explanations) ===")
    print("1. Word_Recall_Correct (单词记忆正确数):")
    print("   - 反映短期记忆能力和认知负荷。负荷越高，通常记忆成绩越差。")
    
    print("\n2. MIST_ResponseTime (平均反应时间):")
    print("   - 反映处理速度。时间越长可能代表任务越难或犹豫不决。")
    
    print("\n3. Bio_HR_Mean (平均心率):")
    print("   - 反映生理唤醒水平(Arousal)。压力或情绪激动时通常升高。")
    
    print("\n4. Bio_HRV_RMSSD (心率变异性 - 时域):")
    print("   - 反映副交感神经活性。数值越低，通常代表压力越大或精神越紧张。")
    
    print("\n5. Bio_HRV_LFHF (心率变异性 - 频域 LF/HF比率):")
    print("   - 反映交感神经与副交感神经的平衡。比率越高，代表交感神经占主导，压力/警戒水平越高。")
    
    print("\n6. Bio_SCL_Mean (皮电水平均值 - Tonic):")
    print("   - 反映持续性的生理唤醒或紧张水平。")
    
    print("\n7. Bio_SCR_Freq (皮电反应频率 - Phasic):")
    print("   - 反映对特定刺激的瞬时压力反应频率。频率越高，代表受到的刺激或压力事件越多。")
    
    print("\n8. Bio_EDA_Power005 (EDA梯度 0.05Hz功率):")
    print("   - 论文特有指标。研究表明该频段的能量与认知负荷呈正相关。")
    
    print("\n9. NASA_TLX_Score (NASA任务负荷指数 - 均值):")
    print("   - 6个维度的平均分(1-21分)。分数越高代表感觉任务越累/越难。")

if __name__ == "__main__":
    main()
