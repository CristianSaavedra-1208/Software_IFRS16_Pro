import sqlite3
import pandas as pd
conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
c = conn.cursor().execute('SELECT Codigo_Interno, Estado, Fecha_Baja, Inicio, Fin, Plazo FROM contratos WHERE Codigo_Interno IN ("CNT-PAC-0017", "CNT-PAC-0018", "CNT-PAC-0047")').fetchall()
df = pd.DataFrame(c, columns=['Codigo_Interno', 'Estado', 'Fecha_Baja', 'Inicio', 'Fin', 'Plazo'])
print(df.to_string())
