import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from core import motor_financiero_v20

conn = sqlite3.connect('ifrs16_platinum.db')
cursor = conn.cursor()

# 1. Print config params
cursor.execute("SELECT valor FROM config_params WHERE tipo='FRECUENCIA_PAGO'")
print("Config Params for FRECUENCIA_PAGO:")
for row in cursor.fetchall():
    print(row[0])

# 2. Update specific contracts to Semestral
cnts_to_update = ['CNT-HOL-0139', 'CNT-HOL-0189', 'CNT-HOL-0200', 'CNT-HOL-0215', 'CNT-HOL-0216', 'CNT-HOL-0260', 'CNT-HOL-0263', 'CNT-HOL-0275', 'CNT-HOL-0293', 'CNT-HOL-0296', 'CNT-HOL-0301', 'CNT-HOL-0302', 'CNT-HOL-0321', 'CNT-HOL-0353']

placeholders = ', '.join(['?'] * len(cnts_to_update))
cursor.execute(f"UPDATE contratos SET Frecuencia_Pago='Semestral' WHERE Codigo_Interno IN ({placeholders})", cnts_to_update)
conn.commit()
print(f"\\nUpdated {cursor.rowcount} contracts to Semestral.\\n")

# 3. Test calculation for CNT-HOL-0275
cursor.execute("SELECT * FROM contratos WHERE Codigo_Interno='CNT-HOL-0275'")
row = cursor.fetchone()
cols = [description[0] for description in cursor.description]
c_dict = dict(zip(cols, row))

print("Contract dict for CNT-HOL-0275:")
print(f"Inicio: {c_dict['Inicio']}, Fin: {c_dict['Fin']}, Frecuencia: {c_dict['Frecuencia_Pago']}, Tipo_Pago: {c_dict['Tipo_Pago']}")

try:
    df_calc, vp, rou = motor_financiero_v20(c_dict)
    print(f"\\nTotal Cuotas Generadas (meses) = {len(df_calc)}")
    if not df_calc.empty:
        cuotas_con_pago = df_calc[df_calc['Pago_Orig'] > 0]
        print(f"Cuotas con desembolso de Pago > 0 = {len(cuotas_con_pago)}")
        print("\\nDetalle de pagos mayores a 0:")
        print(cuotas_con_pago[['Mes', 'Fecha', 'Pago_Orig']].to_string())
    else:
        print("Empty table generated")
except Exception as e:
    import traceback
    traceback.print_exc()

conn.close()
