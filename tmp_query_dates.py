import sqlite3
conn = sqlite3.connect('ifrs16_platinum.db')
c = conn.cursor()
c.execute("SELECT Inicio, Fin, Plazo FROM contratos WHERE Codigo_Interno='CNT-PAC-0495'")
print(c.fetchone())
conn.close()
