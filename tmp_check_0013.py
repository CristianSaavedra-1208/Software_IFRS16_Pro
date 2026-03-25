import sqlite3
import pandas as pd
conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
c = conn.cursor().execute('SELECT Codigo_Interno, Estado, Fecha_Baja, Inicio, Fin, Plazo FROM contratos WHERE Codigo_Interno="CNT-PAC-0013"').fetchall()
df = pd.DataFrame(c, columns=['Codigo_Interno', 'Estado', 'Fecha_Baja', 'Inicio', 'Fin', 'Plazo'])
print("--- CONTRATO ---")
print(df.to_string())

r = conn.cursor().execute('SELECT Codigo_Interno, Fecha_Remedicion, Canon, Plazo, Baja_Pasivo, Baja_ROU, P_L_Efecto FROM remediciones WHERE Codigo_Interno="CNT-PAC-0013"').fetchall()
df_r = pd.DataFrame(r, columns=['Codigo_Interno', 'Fecha_Remedicion', 'Canon', 'Plazo', 'Baja_Pasivo', 'Baja_ROU', 'P_L_Efecto'])
print("\n--- REMEDICIONES ---")
print(df_r.to_string())
