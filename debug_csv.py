import pandas as pd
import os

csv_path = 'assets/data/BTC-USD_data.csv'
if not os.path.exists(csv_path):
    print("File not found")
else:
    df = pd.read_csv(csv_path)
    print("Columns:", df.columns.tolist())
    print("First 3 rows raw:")
    print(df.head(3))
    
    # Try parsing with skiprows
    print("\n--- Try skipping 2 rows (header=0) ---")
    df2 = pd.read_csv(csv_path, header=0, skiprows=[1,2])
    print("Columns:", df2.columns.tolist())
    print(df2.head(2))
