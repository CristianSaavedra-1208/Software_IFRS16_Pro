import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from core import obtener_tc_cache, motor_financiero_v20

print("Testing obtener_tc_cache for UF on 2013-07-01")
val = obtener_tc_cache("UF", "2013-07-01")
print("Response:", val)

print("Checking db for contracts with Valor_Moneda_Inicio = 0")
conn = sqlite3.connect('ifrs16_platinum.db')
df = pd.read_sql("SELECT Codigo_Interno, Moneda, Inicio, Valor_Moneda_Inicio FROM contratos WHERE Valor_Moneda_Inicio = 0 LIMIT 5;", conn)
print(df)
conn.close()
