import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas, obtener_parametros
from app import obtener_motor_financiero, obtener_tc_cache

a = 2026
m_idx = 4
f_t = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
emp_sel = "Pacifico"

lista_c = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()

res = []
for c in lista_c:
    if c['Empresa'] != emp_sel: continue
    if f_t < pd.to_datetime(c['Inicio']).replace(day=1): continue
    
    es_baja_ejercicio = False
    f_baja_efectiva = None
    
    if c.get('Fecha_Baja') and c['Estado'] == 'Baja':
        f_baja = pd.to_datetime(c['Fecha_Baja'])
        if f_baja <= f_t:
            f_baja_efectiva = f_baja
            
    f_fin_c = pd.to_datetime(c['Fin'])
    if f_t.year > f_fin_c.year or (f_t.year == f_fin_c.year and f_t.month >= f_fin_c.month):
        if not f_baja_efectiva or f_fin_c < f_baja_efectiva:
            f_baja_efectiva = f_fin_c
            
    if f_baja_efectiva:
        if f_baja_efectiva.year < a:
            continue
        elif f_baja_efectiva.year == a and f_baja_efectiva.month <= f_t.month:
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
        tc_ini = float(c['Valor_Moneda_Inicio']) if float(c['Valor_Moneda_Inicio']) > 0 else 1.0
        rou_bruto = rou * tc_ini
        
        amort_acum = past['Dep_Orig'].sum()
        amort_clp = amort_acum * tc_ini

        past_ejercicio = past[past['Fecha'].dt.year == a]
        dep_ejercicio_clp = past_ejercicio['Dep_Orig'].sum() * tc_ini
        
        if es_baja_ejercicio:
            v_act = 0
            v_cor_sum = 0
            v12 = 0
            rou_bruto = 0
            amort_clp = 0
            rou = 0
            
        item_dict = {}
        item_dict["Codigo_Interno"] = c['Codigo_Interno']
        item_dict["Estado_Vigencia"] = "Dado de Baja" if es_baja_ejercicio else "Activo"
        item_dict["ROU Bruto"] = rou_bruto
        item_dict["Amort. Acum"] = amort_clp
        item_dict["ROU Neto"] = rou_bruto - amort_clp
        item_dict["Pasivo Total"] = v_act * ratio_pasivo
        res.append(item_dict)

df = pd.DataFrame(res)
print("Row for CNT-PAC-0495 in April 2026:")
print(df[df['Codigo_Interno'] == 'CNT-PAC-0495'].to_dict('records'))

