import sqlite3
conn = sqlite3.connect('ifrs16_platinum.db')
c = conn.cursor()
c.execute("SELECT Codigo_Interno, Estado, Fecha_Baja FROM contratos WHERE Codigo_Interno IN ('CNT-PAC-0063', 'CNT-PAC-0081', 'CNT-PAC-0151', 'CNT-PAC-0495', 'CNT-PAC-0510')")
print("Contratos:")
for r in c.fetchall():
    print(r)
conn.close()
