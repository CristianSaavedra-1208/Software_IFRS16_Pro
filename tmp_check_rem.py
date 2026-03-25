import sqlite3
import pandas as pd
conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
c = conn.cursor().execute('SELECT Codigo_Interno, Fecha_Remedicion, Fin FROM remediciones WHERE Codigo_Interno IN ("CNT-PAC-0017", "CNT-PAC-0018", "CNT-PAC-0047")').fetchall()
df = pd.DataFrame(c, columns=['Codigo_Interno', 'Fecha_Remedicion', 'Fin'])
print(df.to_string())
