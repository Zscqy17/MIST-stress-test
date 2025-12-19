import pandas as pd

try:
    df = pd.read_excel("data/NASA-TLX_6_6.xlsx")
    print("Columns:", df.columns.tolist())
    
    # Check range of values for the first few dimension columns
    dims = ['心理需求 Mental Demand', '身体需求 Physical Demand', '时间压力 Temporal Demand', 
            '个人表现 Performance', '努力程度 Effort', '挫败感 Frustration Level']
            
    print("\nValue ranges (All Rounds):")
    for i in range(4):
        suffix = "" if i == 0 else f".{i}"
        print(f"--- Round {i+1} ---")
        for d in dims:
            col = f"{d}{suffix}"
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                print(f"{col}: {min_val} - {max_val}")
            
except Exception as e:
    print(e)
