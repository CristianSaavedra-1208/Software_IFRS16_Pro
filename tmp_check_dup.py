import sqlite3
import pandas as pd

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
df = pd.read_sql("SELECT Codigo_Interno, Inicio, Valor_Moneda_Inicio FROM contratos WHERE Nombre LIKE '%Tucapel%' ORDER BY Codigo_Interno DESC LIMIT 5", conn)
print(df)
conn.close()
