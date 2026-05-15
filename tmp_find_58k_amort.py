import pandas as pd
from db import cargar_contratos
from app import motor_financiero_v21

lista_c = [c for c in cargar_contratos() if c['Empresa'] == 'Pacifico']
for c in lista_c:
    tab, _, _ = motor_financiero_v21(c, [])
    if tab.empty: continue
    fila = tab[(tab['Fecha'].dt.year == 2026) & (tab['Fecha'].dt.month == 1)]
    if not fila.empty:
        amort = fila.iloc[0]['Dep_Orig']
        tc_ini = float(c.get('Valor_Moneda_Inicio') or 1.0)
        tc_amo = 1.0 if c['Moneda'] in ['UF', 'CLP'] else tc_ini
        amort_clp = amort * tc_amo
        if 57000 < amort_clp < 59000:
            print(f"{c['Codigo_Interno']} - Amort: {amort_clp}")
