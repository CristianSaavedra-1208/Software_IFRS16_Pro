import sqlite3
import pandas as pd

db_path = r'c:\Users\cfsaa\OneDrive\Desktop\Software_IFRS16_Pro\ifrs16_platinum.db'
conn = sqlite3.connect(db_path)

print('--- Contrato CNT-HOL-0178 ---')
df_c = pd.read_sql_query("SELECT Codigo_Interno, Inicio, Moneda, Valor_Moneda_Inicio FROM contratos WHERE Codigo_Interno = 'CNT-HOL-0178'", conn)
print(df_c)

print('\n--- UF el 2022-01-27 ---')
df_uf_date = pd.read_sql_query("SELECT * FROM monedas WHERE moneda = 'UF' AND fecha = '2022-01-27'", conn)
print(df_uf_date)

print('\n--- Buscar fecha del valor 35273.86 ---')
df_uf_val = pd.read_sql_query("SELECT * FROM monedas WHERE moneda = 'UF' AND valor >= 35273 AND valor <= 35274", conn)
print(df_uf_val)

print('\n--- Verificar otros contratos ---')
query = """
    SELECT c.Codigo_Interno, c.Inicio, c.Moneda, c.Valor_Moneda_Inicio, tc.valor as TipoCambio_Inicio
    FROM contratos c
    LEFT JOIN monedas tc ON c.Moneda = tc.moneda AND c.Inicio = tc.fecha
    WHERE c.Moneda = 'UF'
"""
df_all = pd.read_sql_query(query, conn)
df_diff = df_all[abs(df_all['Valor_Moneda_Inicio'] - df_all['TipoCambio_Inicio']) > 0.1].copy()
df_diff.dropna(subset=['Valor_Moneda_Inicio'], inplace=True)

print(f'Contratos con diferencias (UF Inicio != Valor_Moneda_Inicio): {len(df_diff)}')
if len(df_diff) > 0:
    print(df_diff[['Codigo_Interno', 'Inicio', 'Valor_Moneda_Inicio', 'TipoCambio_Inicio']].head(15))

conn.close()
