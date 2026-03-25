import sqlite3
import pandas as pd
conn = sqlite3.connect('C:/Users/cfsaa/OneDrive/Desktop/Software_IFRS16_Pro/ifrs16_platinum.db')

q = "SELECT Valor FROM monedas WHERE Moneda='UF' AND Fecha='2024-10-31'"
print("tc_ini", conn.cursor().execute(q).fetchone())

q2 = "SELECT Valor FROM monedas WHERE Moneda='UF' AND Fecha='2026-02-14'"
print("tc_rem", conn.cursor().execute(q2).fetchone())

q3 = "SELECT Valor FROM monedas WHERE Moneda='UF' AND (Fecha LIKE '2026-02-%' OR Fecha LIKE '2026-01-%') ORDER BY Fecha DESC LIMIT 5"
print("tc_rem_fallback", conn.cursor().execute(q3).fetchall())
