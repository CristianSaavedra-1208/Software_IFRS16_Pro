import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from app import obtener_motor_financiero
from db import cargar_contratos, cargar_remediciones

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
cursor = conn.cursor()

ids = ['CNT-PAC-0017', 'CNT-PAC-0018', 'CNT-PAC-0047']

for cid in ids:
    print(f"\n======================================")
    print(f"Investigando {cid}")
    cursor.execute("SELECT * FROM contratos WHERE Codigo_Interno=?", (cid,))
    rc = cursor.fetchone()
    if not rc:
        print("Contrato no encontrado.")
        continue
        
    c = dict(zip([col[0] for col in cursor.description], rc))
    print(f"Inicio original: {c.get('Inicio')}, Fin actual en header: {c.get('Fin')}, Plazo en header: {c.get('Plazo')}")
    
    rems = cargar_remediciones(cid)
    print(f"Remediciones encontradas: {len(rems)}")
    for r in rems:
        print(f"  -> Fecha: {r.get('Fecha_Remedicion')}, Plazo rem: {r.get('Plazo')}, Ajuste_ROU: {r.get('Ajuste_ROU')}, Nuevo Fin: {r.get('Fin')}")
        
    tab, vp, rou = obtener_motor_financiero(c)
    if tab.empty:
        print("Flujo vacio.")
        continue
        
    target_date = pd.to_datetime('2026-02-28')
    past = tab[tab['Fecha'] <= target_date]
    if past.empty:
        print("No hay fechas pasadas.")
    else:
        print(f"Ultima fila al {target_date.date()}:")
        print(past[['Mes', 'Fecha', 'S_Ini_Orig', 'Pago_Orig', 'Dep_Orig', 'S_Fin_Orig']].tail(5).to_string(index=False))

conn.close()
