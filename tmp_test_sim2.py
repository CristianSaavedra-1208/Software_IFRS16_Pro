import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import obtener_motor_financiero, obtener_tc_cache

def simular_libro_mayor(c, tab, f_t, rems, tc_ini_hist, vp, rou):
    if tab.empty or 'Fecha' not in tab.columns:
        return 0.0, 0.0, 0.0
        
    past = tab[tab['Fecha'] <= f_t]
    if past.empty:
        return 0.0, 0.0, 0.0

    es_uf_clp = c['Moneda'] in ['UF', 'CLP']
    tc_ini = float(c['Valor_Moneda_Inicio']) if c.get('Valor_Moneda_Inicio') and float(c['Valor_Moneda_Inicio']) > 0 else 1.0
    
    rou_bruto_clp = rou * tc_ini
    pasivo_clp = vp * tc_ini
    amort_acum_clp = 0.0
    
    rems_por_mes = {}
    for r in rems:
        f_r = pd.to_datetime(r['Fecha_Remedicion'])
        if f_r <= f_t:
            k = (f_r.year, f_r.month)
            if k not in rems_por_mes: rems_por_mes[k] = []
            rems_por_mes[k].append(r)

    for idx, row in past.iterrows():
        f_mes = pd.to_datetime(date(row['Fecha'].year, row['Fecha'].month, 1)) + relativedelta(day=31)
        tc_act = obtener_tc_cache(c['Moneda'], f_mes)
        if tc_act == 0: tc_act = 1.0
        
        tc_amo_rou = tc_act if es_uf_clp else tc_ini_hist
        
        # 1. Amortizacion
        amort_acum_clp += row['Dep_Orig'] * tc_amo_rou
        
        # 2. Flujos del mes
        int_clp = row['Int_Orig'] * tc_act
        pago_clp = row['Pago_Orig'] * tc_act
        pasivo_clp += int_clp - pago_clp
        
        # 3. Remediciones (Bajas y Saltos)
        k = (row['Fecha'].year, row['Fecha'].month)
        if k in rems_por_mes:
            for r in rems_por_mes[k]:
                f_r = pd.to_datetime(r['Fecha_Remedicion'])
                tc_rem = obtener_tc_cache(c['Moneda'], f_r)
                if tc_rem == 0: tc_rem = 1.0
                tc_rou_rem = tc_rem if es_uf_clp else tc_ini_hist
                
                baja_p = r.get('Baja_Pasivo', 0.0)
                baja_r = r.get('Baja_ROU', 0.0)
                
                if baja_p > 0 or baja_r > 0:
                    bp_clp = baja_p * tc_rem
                    br_clp = baja_r * tc_rou_rem
                    pasivo_clp -= bp_clp
                    rou_bruto_clp -= br_clp
                
                past_tab = tab[tab['Fecha'] < f_r]
                fut_tab = tab[tab['Fecha'] >= f_r]
                old_p = past_tab.iloc[-1]['S_Fin_Orig'] if not past_tab.empty else vp
                new_p = fut_tab.iloc[0]['S_Ini_Orig'] if not fut_tab.empty else 0.0
                
                aj = (new_p - (old_p - baja_p)) * tc_rem
                pasivo_clp += aj
                rou_bruto_clp += aj
                
        # 4. Reajuste UF
        target_balance = row['S_Fin_Orig'] * tc_act
        if c.get('Fecha_Baja') and c['Estado'] == 'Baja':
            fb = pd.to_datetime(c['Fecha_Baja'])
            if fb.year == row['Fecha'].year and fb.month == row['Fecha'].month:
                target_balance = 0.0
        
        reajuste = target_balance - pasivo_clp
        if abs(reajuste) > 1.0:
            pasivo_clp += reajuste
            if es_uf_clp:
                rou_bruto_clp += reajuste

    if c.get('Fecha_Baja') and c['Estado'] == 'Baja':
        fb = pd.to_datetime(c['Fecha_Baja'])
        if fb <= f_t:
            rou_bruto_clp = 0.0
            amort_acum_clp = 0.0
            pasivo_clp = 0.0

    # Ensure termination logic correctly zeroes everything
    f_fin = pd.to_datetime(c['Fin'])
    # f_t is the end of the month
    if f_fin.year < f_t.year or (f_fin.year == f_t.year and f_fin.month <= f_t.month):
        if not (c.get('Fecha_Baja') and c['Estado'] == 'Baja' and pd.to_datetime(c['Fecha_Baja']) <= f_t):
            rou_bruto_clp = 0.0
            amort_acum_clp = 0.0
            pasivo_clp = 0.0

    return rou_bruto_clp, amort_acum_clp, pasivo_clp

lista_c = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()
for c in lista_c:
    if c['Codigo_Interno'] == 'CNT-PAC-0495': # Example from Pacifico
        tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
        f_t = pd.to_datetime('2025-12-31')
        tc_ini_hist = float(c['Valor_Moneda_Inicio']) if c.get('Valor_Moneda_Inicio') and float(c['Valor_Moneda_Inicio']) > 0 else 1.0
        rb, aa, p = simular_libro_mayor(c, tab, f_t, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
        print("Dic 2025:", rb, aa, p)
        
        f_t2 = pd.to_datetime('2026-03-31')
        rb2, aa2, p2 = simular_libro_mayor(c, tab, f_t2, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
        print("Marzo 2026:", rb2, aa2, p2)
        break
