import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import obtener_motor_financiero, obtener_tc_cache

a = 2025
m_idx = 12
f_t = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
emp_sel = "Holdco"

lista_c = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()

print(f"{'Contrato':<15} | {'Pasivo Total':<15} | {'Corriente (App)':<15} | {'Corriente (Rec)':<15} | {'Diff'}")

for c in lista_c:
    if c['Empresa'] != emp_sel: continue
    if f_t < pd.to_datetime(c['Inicio']).replace(day=1): continue
    
    es_baja = False
    if c.get('Fecha_Baja') and c['Estado'] == 'Baja':
        f_baja = pd.to_datetime(c['Fecha_Baja'])
        if f_baja <= f_t: es_baja = True
        
    tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
    if tab.empty or 'Fecha' not in tab.columns: continue
    
    past = tab[tab['Fecha'] <= f_t]
    if past.empty or es_baja: continue
    
    tc = obtener_tc_cache(c['Moneda'], f_t)
    v_act = past.iloc[-1]['S_Fin_Orig']
    
    futuros_app = tab[tab['Fecha'] > f_t].copy()
    futuros_rec = tab[tab['Fecha'] > f_t].copy()
    
    # APP LOGIC
    v_cor_app = 0
    if not futuros_app.empty:
        limite_12_dash = f_t + relativedelta(months=12)
        futuros_app['Capital'] = futuros_app['S_Ini_Orig'] - futuros_app['S_Fin_Orig']
        futuros_app.iloc[-1, futuros_app.columns.get_loc('Capital')] += futuros_app.iloc[-1]['S_Fin_Orig']
        dias_al_pago = (futuros_app['Fecha'] - f_t).dt.days
        es_corriente_mask = (dias_al_pago <= 90) | (futuros_app['Fecha'] <= limite_12_dash)
        v_cor_app = futuros_app.loc[es_corriente_mask, 'Capital'].sum()
        
    # REC LOGIC
    v_cor_rec = 0
    if not futuros_rec.empty:
        limite_12 = f_t + relativedelta(months=12)
        futuros_rec['Capital'] = futuros_rec['S_Ini_Orig'] - futuros_rec['S_Fin_Orig']
        futuros_rec.iloc[-1, futuros_rec.columns.get_loc('Capital')] += futuros_rec.iloc[-1]['S_Fin_Orig']
        es_corriente = (futuros_rec['Fecha'] - f_t).dt.days <= 90
        es_corriente = es_corriente | (futuros_rec['Fecha'] <= limite_12)
        v_cor_rec = futuros_rec.loc[es_corriente, 'Capital'].sum()
        
    val_app = v_cor_app * tc
    val_rec = v_cor_rec * tc
    
    if abs(val_app - val_rec) > 1:
        print(f"{c['Codigo_Interno']:<15} | {v_act*tc:15.0f} | {val_app:15.0f} | {val_rec:15.0f} | {val_app - val_rec:15.0f}")
