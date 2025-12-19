import pandas as pd

try:
    df = pd.read_excel("data/NASA-TLX_6_6.xlsx")
    print("Columns:", df.columns.tolist())
    print(df.head())
except Exception as e:
    print(e)

