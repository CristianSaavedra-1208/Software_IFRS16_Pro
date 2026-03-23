import sqlite3
c = sqlite3.connect('ifrs16_platinum.db')
c.row_factory = sqlite3.Row
res = c.execute('SELECT * FROM contratos WHERE Codigo_Interno="CNT-PAC-0001"').fetchone()
if res:
    print(dict(res))
else:
    print("Not found")
