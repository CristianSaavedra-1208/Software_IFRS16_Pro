import sqlite3
import pandas as pd
conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
df = pd.read_sql("SELECT * FROM contratos WHERE Codigo_Interno = 'CNT-HOL-0008'", conn)
for col in df.columns:
    print(f'{col}: {df[col].iloc[0]}')
conn.close()
