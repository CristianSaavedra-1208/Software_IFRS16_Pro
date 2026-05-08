import pandas as pd
from datetime import date
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from reconciliacion import generar_reconciliacion_rollforward
from app import MESES_LISTA, obtener_motor_financiero, obtener_tc_cache
from dateutil.relativedelta import relativedelta

emp_sel = "Holdco"
a = 2026
m_saved = "Abril"

lista_c = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()

df_recon = generar_reconciliacion_rollforward(emp_sel, a, m_saved, lista_c, rems_grupos)
print("Recon Saldo Inicial:")
print(df_recon.iloc[0])

# Dashboard logic for Dec 2025
a_dash = 2025
m_dash = 12
f_t = pd.to_datetime(date(a_dash, m_dash, 1)) + relativedelta(day=31)

res = []
for c in lista_c:
    if c['Empresa'] != emp_sel: continue
    if f_t < pd.to_datetime(c['Inicio']).replace(day=1): continue
    
    es_baja_ejercicio = False
    f_baja_efectiva = None
    
    if c.get('Fecha_Baja') and c['Estado'] == 'Baja':
        f_baja = pd.to_datetime(c['Fecha_Baja'])
        if f_baja <= f_t: f_baja_efectiva = f_baja
            
    f_fin_c = pd.to_datetime(c['Fin'])
    if f_t.year > f_fin_c.year or (f_t.year == f_fin_c.year and f_t.month >= f_fin_c.month):
        if not f_baja_efectiva or f_fin_c < f_baja_efectiva:
            f_baja_efectiva = f_fin_c
            
    if f_baja_efectiva:
        if f_baja_efectiva.year < a_dash: continue
        elif f_baja_efectiva.year == a_dash and f_baja_efectiva.month <= f_t.month:
            es_baja_ejercicio = True
            
    tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
    if tab.empty or 'Fecha' not in tab.columns: continue
    past = tab[tab['Fecha'] <= f_t]
    if not past.empty:
        tc = obtener_tc_cache(c['Moneda'], f_t); ratio_pasivo = tc
        v_act = past.iloc[-1]['S_Fin_Orig']
        futuros = tab[tab['Fecha'] > f_t].copy()
        v_cor_sum = 0
        if not futuros.empty:
            limite_12_dash = f_t + relativedelta(months=12)
            futuros['Capital'] = futuros['S_Ini_Orig'] - futuros['S_Fin_Orig']
            futuros.iloc[-1, futuros.columns.get_loc('Capital')] += futuros.iloc[-1]['S_Fin_Orig']
            dias_al_pago = (futuros['Fecha'] - f_t).dt.days
            es_corriente_mask = (dias_al_pago <= 90) | (futuros['Fecha'] <= limite_12_dash)
            v_cor_sum = futuros.loc[es_corriente_mask, 'Capital'].sum()
        v12 = v_act - v_cor_sum 
        
        if es_baja_ejercicio:
            v_act = 0; v_cor_sum = 0; v12 = 0
            
        res.append({
            'Codigo_Interno': c['Codigo_Interno'],
            'Pasivo Total': v_act * ratio_pasivo,
            'Pasivo Corriente': v_cor_sum * ratio_pasivo,
            'Pasivo No Corr': v12 * ratio_pasivo
        })

df_dash = pd.DataFrame(res)
print("\nDashboard Totals:")
print(df_dash[['Pasivo Total', 'Pasivo Corriente', 'Pasivo No Corr']].sum())

