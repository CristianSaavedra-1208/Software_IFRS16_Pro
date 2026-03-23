import sys
import os
import pandas as pd

sys.path.append(os.getcwd())
from core import motor_financiero_v20

# 12-month contract, semiannual payment of 1000, 6% annual rate
c_ant = {
    'Codigo_Interno': 'TEST-ANT',
    'Inicio': '2023-01-01',
    'Fin': '2023-12-31',
    'Plazo': 12,
    'Canon': 1000,
    'Tasa_Mensual': pow(1+0.06, 1/12) - 1,
    'Frecuencia_Pago': 'Semestral',
    'Tipo_Pago': 'Anticipado',
    'Costos_Directos': 0, 'Pagos_Anticipados': 0, 'Costos_Desmantelamiento': 0, 'Incentivos': 0, 'Ajuste_ROU': 0
}

c_ven = {
    'Codigo_Interno': 'TEST-VEN',
    'Inicio': '2023-01-01',
    'Fin': '2023-12-31',
    'Plazo': 12,
    'Canon': 1000,
    'Tasa_Mensual': pow(1+0.06, 1/12) - 1,
    'Frecuencia_Pago': 'Semestral',
    'Tipo_Pago': 'Vencido',
    'Costos_Directos': 0, 'Pagos_Anticipados': 0, 'Costos_Desmantelamiento': 0, 'Incentivos': 0, 'Ajuste_ROU': 0
}

df_ant, vp_ant, _ = motor_financiero_v20(c_ant)
df_ven, vp_ven, _ = motor_financiero_v20(c_ven)

print("--- PAGO ANTICIPADO SEMESTRAL ---")
print(f"VP = {vp_ant:,.2f}")
print(df_ant[['Mes', 'S_Ini_Orig', 'Int_Orig', 'Pago_Orig', 'S_Fin_Orig']].to_string())

print("\\n--- PAGO VENCIDO SEMESTRAL ---")
print(f"VP = {vp_ven:,.2f}")
print(df_ven[['Mes', 'S_Ini_Orig', 'Int_Orig', 'Pago_Orig', 'S_Fin_Orig']].to_string())
