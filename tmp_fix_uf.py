import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from core import obtener_tc_cache

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
cursor = conn.cursor()

# Get all contracts where Valor_Moneda_Inicio is 0 or 1.0 (some UFs might have been defaulted to 1.0)
cursor.execute("SELECT Codigo_Interno, Moneda, Inicio FROM contratos WHERE Moneda != 'CLP' AND Valor_Moneda_Inicio IN (0, 1.0)")
rows = cursor.fetchall()
updated = 0

for cod, mon, ini in rows:
    tc_correcto = obtener_tc_cache(mon, ini)
    if tc_correcto > 0:
        cursor.execute("UPDATE contratos SET Valor_Moneda_Inicio=? WHERE Codigo_Interno=?", (tc_correcto, cod))
        updated += 1

conn.commit()
conn.close()
print(f"Updated {updated} contratos con el Valor de Moneda correcto.")
