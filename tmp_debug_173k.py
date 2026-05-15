import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import motor_financiero_v21, obtener_tc_cache
from core import simular_libro_mayor
import unicodedata

def norm_str(s):
    if not isinstance(s, str): return ""
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8').strip().upper()

def get_cta(tipo_cta, c_cls):
    return (tipo_cta, tipo_cta)

def add_asiento(detalles, emp, cod1, t, cta_num, cta_nom, debe, haber):
    if abs(debe) > 0.01:
        detalles.append({"Cod1": cod1, "Cuenta": cta_num, "Tipo": "Debe", "Debe": round(debe,0), "Haber": 0})
    if abs(haber) > 0.01:
        detalles.append({"Cod1": cod1, "Cuenta": cta_num, "Tipo": "Haber", "Debe": 0, "Haber": round(haber,0)})

def calc_mes(a, m_idx, c, rems_grupos, tab, vp, rou):
    detalles = []
    f_act = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
    f_ant = f_act - relativedelta(months=1, day=31)
    
    f_ini = pd.to_datetime(c['Inicio'])
    if f_act < f_ini.replace(day=1): return 0.0
    
    if c.get('Fecha_Baja') and c.get('Estado') in ['Baja', 'Remedido']:
        f_baja = pd.to_datetime(c['Fecha_Baja'])
        if f_baja.year < a or (f_baja.year == a and f_baja.month < m_idx):
            return 0.0
            
    f_fin_c = pd.to_datetime(c['Fin'])
    if f_fin_c.year < a or (f_fin_c.year == a and f_fin_c.month < m_idx):
        return 0.0
        
    c_cls = c.get('Clase_Activo', 'Otros')
    if f_ini.month == m_idx and f_ini.year == a:
        tc_ini = float(c['Valor_Moneda_Inicio']) if c['Valor_Moneda_Inicio'] > 0 else 1.0
        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "1", *get_cta('ROU', c_cls), rou * tc_ini, 0)
        
    fila = tab[(tab['Fecha'].dt.month == m_idx) & (tab['Fecha'].dt.year == a)]
    if not fila.empty:
        it = fila.iloc[0]
        tc_act = obtener_tc_cache(c['Moneda'], f_act)
        
        tc_ini_hist = float(c['Valor_Moneda_Inicio']) if c.get('Valor_Moneda_Inicio') and float(c['Valor_Moneda_Inicio']) > 0 else 1.0
        tc_act_amo = tc_act if tc_act > 0 else 1.0
        tc_amo_rou = tc_act_amo if c['Moneda'] in ['UF', 'CLP'] else tc_ini_hist
        
        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "2", *get_cta('AmortAcum', c_cls), 0, it['Dep_Orig'] * tc_amo_rou)

    tc_ini_hist = float(c['Valor_Moneda_Inicio']) if c.get('Valor_Moneda_Inicio') and float(c['Valor_Moneda_Inicio']) > 0 else 1.0
    paso_baja_manual = False
    if c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido']:
        f_baja = pd.to_datetime(c['Fecha_Baja'])
        if f_baja.month == m_idx and f_baja.year == a:
            paso_baja_manual = True
            rb_hist, aa_hist, p_hist = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou, ignore_baja=True)
            r_neto = rb_hist
            if p_hist > 0.01 or abs(r_neto) > 0.01:
                add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Baja", *get_cta('ROU', c_cls), 0, r_neto)
                add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Baja", *get_cta('AmortAcum', c_cls), aa_hist, 0)

    paso_terminacion_parcial = False
    rems = rems_grupos.get(c['Codigo_Interno'], [])
    for r in rems:
        f_r = pd.to_datetime(r['Fecha_Remedicion'])
        if f_r.month == m_idx and f_r.year == a and r.get('Baja_Pasivo', 0.0) > 0:
            paso_terminacion_parcial = True
            break
            
    if not paso_baja_manual and not paso_terminacion_parcial and c['Estado'] == 'Activo':
        if f_fin_c.month == m_idx and f_fin_c.year == a:
            rb_hist, aa_hist, p_hist = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou, ignore_baja=True)
            r_neto = rb_hist
            if p_hist > 0.01 or abs(r_neto) > 0.01:
                add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Baja", *get_cta('ROU', c_cls), 0, r_neto)
                add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Baja", *get_cta('AmortAcum', c_cls), aa_hist, 0)

    for r in rems:
        f_r = pd.to_datetime(r['Fecha_Remedicion'])
        if f_r.month == m_idx and f_r.year == a:
            tc_rem = obtener_tc_cache(c['Moneda'], f_r)
            if tc_rem == 0: tc_rem = 1.0
            
            baja_p = r.get('Baja_Pasivo', 0.0)
            baja_r = r.get('Baja_ROU', 0.0)
            if baja_p > 0 or baja_r > 0:
                tc_rou_rem = tc_rem if c['Moneda'] in ['UF', 'CLP'] else tc_ini_hist
                br_clp = baja_r * tc_rou_rem
                add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Baja", *get_cta('ROU', c_cls), 0, br_clp)
                
            past_tab = tab[tab['Fecha'] < f_r]
            fut_tab = tab[tab['Fecha'] >= f_r]
            old_p = past_tab.iloc[-1]['S_Fin_Orig'] if not past_tab.empty else vp
            new_p = fut_tab.iloc[0]['S_Ini_Orig'] if not fut_tab.empty else 0.0
            old_p -= baja_p
            aj = (new_p - old_p) * tc_rem
            if abs(aj) > 0.01:
                if aj > 0: add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Rem", *get_cta('ROU', c_cls), aj, 0)
                elif aj < 0: add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Rem", *get_cta('ROU', c_cls), 0, abs(aj))

    if not fila.empty:
        it = fila.iloc[0]
        tc_act = obtener_tc_cache(c['Moneda'], f_act)
        if it['Mes'] == 1:
            tc_ant = float(c['Valor_Moneda_Inicio']) if c.get('Valor_Moneda_Inicio') and float(c['Valor_Moneda_Inicio']) > 0 else 1.0
            last_target_balance = 0.0
        else:
            tc_ant = obtener_tc_cache(c['Moneda'], f_ant)
            past_ant = tab[tab['Fecha'] <= f_ant]
            last_uf = past_ant.iloc[-1]['S_Fin_Orig'] if not past_ant.empty else 0.0
            last_target_balance = last_uf * tc_ant
            
        ratio_act = tc_act
        target_balance = it['S_Fin_Orig'] * ratio_act
        
        if (c.get('Fecha_Baja') and c['Estado'] == 'Baja' and pd.to_datetime(c['Fecha_Baja']).month == m_idx and pd.to_datetime(c['Fecha_Baja']).year == a):
            target_balance = 0.0
        elif not paso_baja_manual and not paso_terminacion_parcial and c['Estado'] == 'Activo':
            if f_fin_c.month == m_idx and f_fin_c.year == a:
                target_balance = 0.0
                
        # To get pasivo flujo, we must compute it
        flujo_pasivo_mes = 0.0
        if f_ini.month == m_idx and f_ini.year == a:
            flujo_pasivo_mes += vp * (float(c['Valor_Moneda_Inicio']) if c['Valor_Moneda_Inicio']>0 else 1.0)
        
        flujo_pasivo_mes += (it['Pago_Orig'] * tc_act) * -1
        flujo_pasivo_mes += (it['Int_Orig'] * tc_act)
        
        for r in rems:
            f_r = pd.to_datetime(r['Fecha_Remedicion'])
            if f_r.month == m_idx and f_r.year == a:
                tc_rem = obtener_tc_cache(c['Moneda'], f_r)
                if tc_rem == 0: tc_rem = 1.0
                baja_p = r.get('Baja_Pasivo', 0.0)
                flujo_pasivo_mes -= (baja_p * tc_rem)
                past_tab = tab[tab['Fecha'] < f_r]
                fut_tab = tab[tab['Fecha'] >= f_r]
                old_p = past_tab.iloc[-1]['S_Fin_Orig'] if not past_tab.empty else vp
                new_p = fut_tab.iloc[0]['S_Ini_Orig'] if not fut_tab.empty else 0.0
                old_p -= baja_p
                flujo_pasivo_mes += (new_p - old_p) * tc_rem
                
        if paso_baja_manual or (not paso_terminacion_parcial and c['Estado'] == 'Activo' and f_fin_c.month == m_idx and f_fin_c.year == a):
            rb_hist, aa_hist, p_hist = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou, ignore_baja=True)
            if p_hist > 0:
                flujo_pasivo_mes -= p_hist
                
        saldo_libro = last_target_balance + flujo_pasivo_mes
        reajuste = target_balance - saldo_libro
        
        if abs(reajuste) > 1.0:
            if c['Moneda'] in ['UF', 'CLP']:
                if reajuste > 0: add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Rea", *get_cta('ROU', c_cls), reajuste, 0)
                else: add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "Rea", *get_cta('ROU', c_cls), 0, abs(reajuste))

    neto_mes = 0.0
    for d in detalles:
        if d['Cuenta'] == 'ROU':
            neto_mes += (d['Debe'] - d['Haber'])
        elif d['Cuenta'] == 'AmortAcum':
            neto_mes -= (d['Haber'] - d['Debe'])
    return neto_mes

lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Pacifico']
rems_grupos = cargar_remediciones_todas_agrupadas()

print("Buscando diferencias Q1 2026...")
for c in lista_c_todas:
    tab, vp, rou = motor_financiero_v21(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
    tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
    if tc_ini_hist <= 0: tc_ini_hist = 1.0
    
    # 2025
    f_ant = pd.to_datetime('2025-12-31')
    rb_t1, aa_t1, p_t1 = simular_libro_mayor(c, tab, f_ant, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
    net_2025 = rb_t1 - aa_t1
    
    # Mar 2026
    f_act = pd.to_datetime('2026-03-31')
    rb_t, aa_t, p_t = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
    net_2026 = rb_t - aa_t
    
    mov_recon = net_2026 - net_2025
    
    mov_asie = 0.0
    for m_idx in [1, 2, 3]:
        mov_asie += calc_mes(2026, m_idx, c, rems_grupos, tab, vp, rou)
        
    diff = mov_recon - mov_asie
    if abs(diff) > 1.0:
        print(f"Contract {c['Codigo_Interno']}: diff={diff:.2f} (recon={mov_recon:.2f}, asie={mov_asie:.2f})")
