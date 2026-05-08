import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import obtener_motor_financiero, obtener_tc_cache

a = 2025
m_idx = 12
f_t = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
emp_sel = "Pacifico"

lista_c = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()

res = []
for c in lista_c:
    if c['Empresa'] != emp_sel: continue
    if f_t < pd.to_datetime(c['Inicio']).replace(day=1): continue
    if c['Codigo_Interno'] != 'CNT-PAC-0495': continue

    tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
    print("Length of tab:", len(tab))
    print("Max date in tab:", tab['Fecha'].max() if not tab.empty else None)
    
    past = tab[tab['Fecha'] <= f_t]
    futuros = tab[tab['Fecha'] > f_t].copy()
    
    print("Length of futuros:", len(futuros))
    print("Max date in futuros:", futuros['Fecha'].max() if not futuros.empty else None)

    v_act = past.iloc[-1]['S_Fin_Orig']
    v_cor_sum = 0
    if not futuros.empty:
        limite_12_dash = f_t + relativedelta(months=12)
        futuros['Capital'] = futuros['S_Ini_Orig'] - futuros['S_Fin_Orig']
        futuros.iloc[-1, futuros.columns.get_loc('Capital')] += futuros.iloc[-1]['S_Fin_Orig']
        dias_al_pago = (futuros['Fecha'] - f_t).dt.days
        es_corriente_mask = (dias_al_pago <= 90) | (futuros['Fecha'] <= limite_12_dash)
        v_cor_sum = futuros.loc[es_corriente_mask, 'Capital'].sum()
                
    v12 = v_act - v_cor_sum 
    print(f"v_act: {v_act}, v_cor_sum: {v_cor_sum}, v12: {v12}")

