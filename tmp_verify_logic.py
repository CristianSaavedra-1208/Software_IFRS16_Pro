import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from core import motor_financiero_v20

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM contratos WHERE Codigo_Interno='CNT-PAC-0001'")
rc = cursor.fetchone()

if rc:
    c = dict(zip([col[0] for col in cursor.description], rc))
    tab, vp_orig, rou_orig = motor_financiero_v20(c)
    
    # We display the initial values and the last 3 rows of the table
    print("Original VP:", vp_orig)
    print("Original ROU:", rou_orig)
    print("\nUltimos 5 meses del flujo:")
    if not tab.empty:
        print(tab[['Mes', 'Fecha', 'S_Ini_Orig', 'Int_Orig', 'Pago_Orig', 'Dep_Orig', 'S_Fin_Orig']].tail(5).to_string(index=False))
    else:
        print("Flujo vacio.")

conn.close()
