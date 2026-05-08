import sqlite3
import pandas as pd
conn = sqlite3.connect('ifrs16_platinum.db')
c = conn.cursor()
c.execute("SELECT Codigo_Interno, Estado, Fecha_Baja FROM contratos WHERE Codigo_Interno='CNT-PAC-0495'")
print(c.fetchone())

c.execute("SELECT * FROM remediciones WHERE Codigo_Interno='CNT-PAC-0495'")
for r in c.fetchall():
    print(r)
conn.close()
