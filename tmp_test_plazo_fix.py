import sqlite3
import pandas as pd

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
cursor = conn.cursor()

cursor.execute("SELECT Codigo_Interno, SUM(Plazo) as total_n_p FROM remediciones GROUP BY Codigo_Interno")
rems = cursor.fetchall()

for r in rems:
    cod = r[0]
    total_np = r[1]
    cursor.execute("SELECT Plazo, Inicio, Fin, Canon FROM contratos WHERE Codigo_Interno=?", (cod,))
    c = cursor.fetchone()
    if c:
        current_plazo = c[0]
        ini = c[1]
        
        orig_1 = current_plazo - total_np
        print(f"[{cod}] Current_Plazo: {current_plazo} | Sum_Rems_Plazo: {total_np}  ==>  Proposed Orig Plazo: {orig_1}")

conn.close()
