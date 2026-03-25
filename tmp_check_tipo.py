import sqlite3
import pandas as pd
conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')
c = conn.cursor().execute('SELECT Codigo_Interno, Inicio, Plazo, Tipo_Pago FROM contratos WHERE Codigo_Interno IN ("CNT-PAC-0017", "CNT-PAC-0018", "CNT-PAC-0047")').fetchall()
df = pd.DataFrame(c, columns=['Codigo_Interno', 'Inicio', 'Plazo', 'Tipo_Pago'])
print(df.to_string())
