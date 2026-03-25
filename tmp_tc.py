import sqlite3
conn=sqlite3.connect('ifrs16_platinum.db')
print(conn.cursor().execute('SELECT Valor_Moneda_Inicio FROM contratos WHERE Codigo_Interno="CNT-PAC-0013"').fetchone())
