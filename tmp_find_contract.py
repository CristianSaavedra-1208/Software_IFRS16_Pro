import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import motor_financiero_v21, obtener_tc_cache
from core import simular_libro_mayor

rems_grupos = cargar_remediciones_todas_agrupadas()
lista_c = cargar_contratos()
a = 2026
meses = [1, 2, 3]

for m_idx in meses:
    f_act = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
    f_ant = f_act - relativedelta(months=1, day=31)
    
    for c in lista_c:
        if c['Empresa'] != 'Pacifico': continue
        
        f_ini = pd.to_datetime(c['Inicio'])
        if f_act < f_ini.replace(day=1): continue
        
        # Exclusión de bajas anteriores
        if c.get('Fecha_Baja') and c.get('Estado') in ['Baja', 'Remedido']:
            f_baja = pd.to_datetime(c['Fecha_Baja'])
            if f_baja.year < a or (f_baja.year == a and f_baja.month < m_idx):
                continue

        tab, vp, rou = motor_financiero_v21(c, rems_grupos.get(c['Codigo_Interno'], []))
        if tab.empty: continue
        
        tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
        if tc_ini_hist <= 0: tc_ini_hist = 1.0
        
        # --- RECONCILIACION MOVEMENT ---
        rb_t, aa_t, p_t = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
        net_t = rb_t - aa_t
        rb_t1, aa_t1, p_t1 = simular_libro_mayor(c, tab, f_ant, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
        net_t1 = rb_t1 - aa_t1
        
        mov_recon = net_t - net_t1
        
        # --- ASIENTOS MOVEMENT ---
        mov_asientos = 0
        fila = tab[(tab['Fecha'].dt.month == m_idx) & (tab['Fecha'].dt.year == a)]
        if not fila.empty:
            it = fila.iloc[0]
            tc_act = obtener_tc_cache(c['Moneda'], f_act)
            if it['Mes'] == 1: tc_ant_val = tc_ini_hist
            else: tc_ant_val = obtener_tc_cache(c['Moneda'], f_ant)
            
            tc_act_amo = tc_act if tc_act > 0 else 1.0
            tc_amo_rou = tc_act_amo if c['Moneda'] in ['UF', 'CLP'] else tc_ini_hist
            
            amort = it['Dep_Orig'] * tc_amo_rou
            mov_asientos -= amort
            
            flujo_pasivo = (it['Int_Orig'] - it['Pago_Orig']) * tc_act
            
            for r in rems_grupos.get(c['Codigo_Interno'], []):
                f_r = pd.to_datetime(r['Fecha_Remedicion'])
                if f_r.month == m_idx and f_r.year == a:
                    past_tab = tab[tab['Fecha'] < f_r]
                    fut_tab = tab[tab['Fecha'] >= f_r]
                    old_pasivo = past_tab.iloc[-1]['S_Fin_Orig'] if not past_tab.empty else vp
                    new_pasivo = fut_tab.iloc[0]['S_Ini_Orig'] if not fut_tab.empty else 0.0
                    tc_rem = obtener_tc_cache(c['Moneda'], f_r)
                    if tc_rem == 0: tc_rem = 1.0
                    
                    baja_p = float(r.get('Baja_Pasivo', 0.0))
                    baja_r = float(r.get('Baja_ROU', 0.0))
                    if baja_p > 0 or baja_r > 0:
                        tc_rou_rem = tc_rem if c['Moneda'] in ['UF', 'CLP'] else tc_ini_hist
                        bp_clp = baja_p * tc_rem
                        br_clp = baja_r * tc_rou_rem
                        mov_asientos -= br_clp
                        old_pasivo -= baja_p
                        flujo_pasivo -= bp_clp
                        
                    aj = (new_pasivo - old_pasivo) * tc_rem
                    if abs(aj) > 0.01:
                        mov_asientos += aj
                        flujo_pasivo += aj
            
            target_balance = it['S_Fin_Orig'] * tc_act
            paso_baja_manual = False
            if c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido']:
                f_baja = pd.to_datetime(c['Fecha_Baja'])
                if f_baja.month == m_idx and f_baja.year == a:
                    paso_baja_manual = True
            paso_terminacion_parcial = False
            for r in rems_grupos.get(c['Codigo_Interno'], []):
                f_r = pd.to_datetime(r['Fecha_Remedicion'])
                if f_r.month == m_idx and f_r.year == a and r.get('Baja_Pasivo', 0.0) > 0:
                    paso_terminacion_parcial = True
                    break
                    
            if paso_baja_manual:
                target_balance = 0.0
            elif not paso_baja_manual and not paso_terminacion_parcial and c['Estado'] == 'Activo':
                f_fin_c = pd.to_datetime(c['Fin'])
                if f_fin_c.month == m_idx and f_fin_c.year == a:
                    target_balance = 0.0
                    
            if it['Mes'] == 1:
                last_target_balance = 0.0
            else:
                past_ant = tab[tab['Fecha'] <= f_ant]
                last_uf = past_ant.iloc[-1]['S_Fin_Orig'] if not past_ant.empty else 0.0
                last_target_balance = last_uf * tc_ant_val
                
            saldo_libro = last_target_balance + flujo_pasivo
            reajuste = target_balance - saldo_libro
            
            if abs(reajuste) > 1.0:
                if c['Moneda'] in ['UF', 'CLP']:
                    mov_asientos += reajuste
                    
            es_baja = False
            if c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido']:
                f_baja = pd.to_datetime(c['Fecha_Baja'])
                if f_baja.month == m_idx and f_baja.year == a:
                    es_baja = True
            elif not paso_terminacion_parcial and c['Estado'] == 'Activo':
                f_fin_c = pd.to_datetime(c['Fin'])
                if f_fin_c.month == m_idx and f_fin_c.year == a:
                    es_baja = True
                    
            if es_baja:
                rb_hist, aa_hist, p_hist = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou, ignore_baja=True)
                s_fin_pasivo = p_hist
                amort_acum = aa_hist
                s_fin_rou = rb_hist - aa_hist
                r_neto = rb_hist
                if s_fin_pasivo > 0.01 or abs(r_neto) > 0.01:
                    mov_asientos -= r_neto
                    mov_asientos += amort_acum
        
        diff = mov_recon - mov_asientos
        if abs(diff) > 1.0:
            print(f"Mes {m_idx} - Contrato {c['Codigo_Interno']} - Diff: {diff:.2f} (Recon: {mov_recon:.2f}, Asiento: {mov_asientos:.2f})")
