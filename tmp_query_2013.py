import sqlite3
import pandas as pd

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')

print('--- Monedas Table 2013-09-01 ---')
df_m = pd.read_sql("SELECT * FROM monedas WHERE fecha = '2013-09-01'", conn)
print(df_m)

print('\n--- Contratos Table CNT-HOL-0008 ---')
df_c = pd.read_sql("SELECT Codigo_Interno, Inicio, Valor_Moneda_Inicio FROM contratos WHERE Codigo_Interno = 'CNT-HOL-0008'", conn)
print(df_c)

conn.close()
