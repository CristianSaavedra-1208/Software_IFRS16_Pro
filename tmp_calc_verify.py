import sqlite3
import copy
from core import motor_financiero_v20, __calc_vp

conn = sqlite3.connect('ifrs16_platinum.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM contratos WHERE Codigo_Interno='CNT-HOL-0275'")
row = cursor.fetchone()
cols = [description[0] for description in cursor.description]
c_dict = dict(zip(cols, row))
conn.close()

# Currently Plazo is 181 in DB
# Let's see what core.py returns
df181, vp181, rou181 = motor_financiero_v20(c_dict)

print("--- ACTUAL (Plazo = 181) ---")
print(f"VP = {vp181:,.2f}")
print(f"ROU = {rou181:,.2f}")
print(f"Check sum of payments in VP calculation = {df181['Pago_Orig'].sum():,.2f}")
cuotas181 = df181[df181['Pago_Orig'] > 0]
print(f"Number of payments = {len(cuotas181)}")

# Now let's calculate for 180 (correct 15 years)
c_dict_180 = copy.deepcopy(c_dict)
c_dict_180['Plazo'] = 180
df180, vp180, rou180 = motor_financiero_v20(c_dict_180)

print("\\n--- CORRECTED (Plazo = 180) ---")
print(f"VP = {vp180:,.2f}")
print(f"ROU = {rou180:,.2f}")
print(f"Check sum of payments in VP calculation = {df180['Pago_Orig'].sum():,.2f}")
cuotas180 = df180[df180['Pago_Orig'] > 0]
print(f"Number of payments = {len(cuotas180)}")

print("\\nDifference in VP:", vp181 - vp180)
