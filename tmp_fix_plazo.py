import sqlite3
import pandas as pd
from dateutil.relativedelta import relativedelta

conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
cursor = conn.cursor()

# 1. Select all contracts
cursor.execute("SELECT Codigo_Interno, Inicio, Fin FROM contratos")
rows = cursor.fetchall()
updated = 0

for cod, ini, fin in rows:
    f_i = pd.to_datetime(ini)
    f_f = pd.to_datetime(fin)
    
    diff = relativedelta(f_f, f_i)
    p = diff.years * 12 + diff.months
    if diff.days > 0:
        p += 1
        
    cursor.execute("UPDATE contratos SET Plazo=? WHERE Codigo_Interno=?", (p, cod))
    updated += 1

# Update remediciones if any
cursor.execute("SELECT id, Fecha_Remedicion, Fin FROM remediciones")
rems = cursor.fetchall()
for r_id, f_rem, fin in rems:
    f_i = pd.to_datetime(f_rem)
    f_f = pd.to_datetime(fin)
    
    diff = relativedelta(f_f, f_i)
    p = diff.years * 12 + diff.months
    if diff.days > 0:
        p += 1
        
    cursor.execute("UPDATE remediciones SET Plazo=? WHERE id=?", (p, r_id))

conn.commit()
conn.close()
print(f"Updated {updated} contratos with true Plazo formula.")
