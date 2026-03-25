import sqlite3
import pandas as pd
conn=sqlite3.connect('ifrs16_platinum.db')
q = "SELECT c.Codigo_Interno, r.Fecha_Remedicion, r.Baja_Pasivo, r.Baja_ROU FROM contratos c JOIN remediciones r ON c.Codigo_Interno = r.Codigo_Interno WHERE c.Empresa='Pacifico' AND r.Fecha_Remedicion LIKE '2026-02-%'"
print(pd.DataFrame(conn.cursor().execute(q).fetchall(), columns=['Codigo', 'Fecha', 'Baja_P', 'Baja_R']).to_string())
