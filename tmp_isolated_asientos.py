import sqlite3
import pandas as pd
from datetime import date
from core import motor_financiero_v20
from db import cargar_contratos, obtener_tc, cargar_remediciones

lista_c = [c for c in cargar_contratos() if c['Codigo_Interno'] == 'CNT-PAC-0013']
c = lista_c[0]

tab, vp, rou = motor_financiero_v20(c)
rems = cargar_remediciones(c['Codigo_Interno'])

tc_ini = float(c['Valor_Moneda_Inicio']) if c['Valor_Moneda_Inicio'] > 0 else 1.0
print(f"tc_ini={tc_ini}")

for r in rems:
    f_r = pd.to_datetime(r['Fecha_Remedicion'])
    if f_r.month == 2 and f_r.year == 2026:
        tc_rem = obtener_tc(c['Moneda'], f_r.strftime('%Y-%m-%d'))
        print(f"tc_rem={tc_rem}")
        
        baja_p = r.get('Baja_Pasivo', 0.0)
        baja_r = r.get('Baja_ROU', 0.0)
        pl_efecto_clp = r.get('P_L_Efecto', 0.0)
        
        bp_clp = baja_p * tc_rem
        br_clp = baja_r * tc_ini
        print(f"Baja_Pasivo(UF)={baja_p}, Baja_ROU(UF)={baja_r}")
        print(f"bp_clp={bp_clp}, br_clp={br_clp}")
        print(f"pl_efecto_clp={pl_efecto_clp}")
        
        diff = bp_clp - br_clp
        print(f"Expected PL Effect (CLP) if simple math: {diff}")
        print(f"Actual PL Effect (CLP) stored in DB: {pl_efecto_clp}")
        print(f"Does it balance? Debe(bp_clp) {bp_clp} == Haber(br_clp + pl) {br_clp + pl_efecto_clp} : {bp_clp == (br_clp + pl_efecto_clp)}")
