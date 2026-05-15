import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import motor_financiero_v21, obtener_tc_cache
from core import simular_libro_mayor

rems_grupos = cargar_remediciones_todas_agrupadas()
lista_c = cargar_contratos()
meses = [1, 2, 3]
a = 2026

resultados = []

for m_idx in meses:
    f_act = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
    f_ant = f_act - relativedelta(months=1, day=31)
    
    detalles = []
    
    # --- SIMULAR MODULO ASIENTOS ---
    # Copiar lógica exacta de modulo_asientos para ver los totales
    def add_asiento(lista, emp, cod1, transaccion, n_cta, cuenta, debe, haber):
        if abs(debe) > 0.01:
            lista.append({"N_Cuenta": str(n_cta), "Debe": round(debe,0), "Haber": 0})
        if abs(haber) > 0.01:
            lista.append({"N_Cuenta": str(n_cta), "Debe": 0, "Haber": round(haber,0)})

    for c in lista_c:
        if c['Empresa'] != 'Pacifico': continue
        f_ini = pd.to_datetime(c['Inicio'])
        if f_act < f_ini.replace(day=1): continue
        if c.get('Fecha_Baja') and c.get('Estado') in ['Baja', 'Remedido']:
            f_baja = pd.to_datetime(c['Fecha_Baja'])
            if f_baja.year < a or (f_baja.year == a and f_baja.month < m_idx):
                continue
                
        tab, vp, rou = motor_financiero_v21(c, rems_grupos.get(c['Codigo_Interno'], []))
        if tab.empty: continue
        
        tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
        if tc_ini_hist <= 0: tc_ini_hist = 1.0
        
        fila = tab[(tab['Fecha'].dt.month == m_idx) & (tab['Fecha'].dt.year == a)]
        if not fila.empty:
            it = fila.iloc[0]
            tc_act = obtener_tc_cache(c['Moneda'], f_act)
            if it['Mes'] == 1:
                tc_ant_val = tc_ini_hist
            else:
                tc_ant_val = obtener_tc_cache(c['Moneda'], f_ant)
            
            tc_act_amo = tc_act if tc_act > 0 else 1.0
            tc_amo_rou = tc_act_amo if c['Moneda'] in ['UF', 'CLP'] else tc_ini_hist
            
            # Amort
            add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "2", 'Amort', 'Amort', it['Dep_Orig'] * tc_amo_rou, 0)
            add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "2", 'AmortAcum', 'AmortAcum', 0, it['Dep_Orig'] * tc_amo_rou)
            
            # Pago
            add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "3", 'Pasivo', 'Pasivo', it['Pago_Orig'] * tc_act, 0)
            add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "3", 'Banco', 'Banco', 0, it['Pago_Orig'] * tc_act)
            
            # Int
            add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "4", 'Interes', 'Interes', it['Int_Orig'] * tc_act, 0)
            add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "4", 'Pasivo', 'Pasivo', 0, it['Int_Orig'] * tc_act)
            
        paso_baja_manual = False
        if c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido']:
            f_baja = pd.to_datetime(c['Fecha_Baja'])
            if f_baja.month == m_idx and f_baja.year == a:
                paso_baja_manual = True
                rb_hist, aa_hist, p_hist = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou, ignore_baja=True)
                s_fin_pasivo = p_hist
                amort_acum = aa_hist
                s_fin_rou = rb_hist - aa_hist
                r_neto = rb_hist
                if s_fin_pasivo > 0.01 or abs(r_neto) > 0.01:
                    if s_fin_pasivo > 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'Pasivo', 'Pasivo', s_fin_pasivo, 0)
                    add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'ROU', 'ROU', 0, r_neto)
                    add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'AmortAcum', 'AmortAcum', amort_acum, 0)
                    dif_baja = s_fin_pasivo - s_fin_rou
                    if dif_baja > 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'GananciaBaja', 'G', 0, dif_baja)
                    elif dif_baja < 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'PerdidaBaja', 'P', abs(dif_baja), 0)

        paso_terminacion_parcial = False
        rems = rems_grupos.get(c['Codigo_Interno'], [])
        for r in rems:
            f_r = pd.to_datetime(r['Fecha_Remedicion'])
            if f_r.month == m_idx and f_r.year == a and r.get('Baja_Pasivo', 0.0) > 0:
                paso_terminacion_parcial = True
                break
                
        if not paso_baja_manual and not paso_terminacion_parcial and c['Estado'] == 'Activo':
            f_fin_c = pd.to_datetime(c['Fin'])
            if f_fin_c.month == m_idx and f_fin_c.year == a:
                rb_hist, aa_hist, p_hist = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou, ignore_baja=True)
                s_fin_pasivo = p_hist
                amort_acum = aa_hist
                s_fin_rou = rb_hist - aa_hist
                r_neto = rb_hist
                if s_fin_pasivo > 0.01 or abs(r_neto) > 0.01:
                    if s_fin_pasivo > 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'Pasivo', 'Pasivo', s_fin_pasivo, 0)
                    add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'ROU', 'ROU', 0, r_neto)
                    add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'AmortAcum', 'AmortAcum', amort_acum, 0)
                    dif_baja = s_fin_pasivo - s_fin_rou
                    if dif_baja > 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'GananciaBaja', 'G', 0, dif_baja)
                    elif dif_baja < 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "6", 'PerdidaBaja', 'P', abs(dif_baja), 0)

        for r in rems:
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
                    pl = bp_clp - br_clp
                    add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "7", 'Pasivo', 'Pasivo', bp_clp, 0)
                    add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "7", 'ROU', 'ROU', 0, br_clp)
                    if pl > 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "7", 'GananciaBaja', 'G', 0, pl)
                    elif pl < 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "7", 'PerdidaBaja', 'P', abs(pl), 0)
                    old_pasivo -= baja_p
                
                aj = (new_pasivo - old_pasivo) * tc_rem
                if abs(aj) > 0.01:
                    if aj > 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "7", 'ROU', 'ROU', aj, 0)
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "7", 'Pasivo', 'Pasivo', 0, aj)
                    else:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "7", 'Pasivo', 'Pasivo', abs(aj), 0)
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "7", 'ROU', 'ROU', 0, abs(aj))

        if not fila.empty:
            target_balance = it['S_Fin_Orig'] * tc_act
            if (c.get('Fecha_Baja') and c['Estado'] == 'Baja' and pd.to_datetime(c['Fecha_Baja']).month == m_idx and pd.to_datetime(c['Fecha_Baja']).year == a):
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
                
            flujo_pasivo_mes = sum((d['Haber'] - d['Debe']) for d in detalles if d['N_Cuenta'] == 'Pasivo')
            saldo_libro = last_target_balance + flujo_pasivo_mes
            reajuste = target_balance - saldo_libro
            
            if abs(reajuste) > 1.0:
                if c['Moneda'] in ['UF', 'CLP']:
                    if reajuste > 0:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "5", 'ROU', 'ROU', reajuste, 0)
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "5", 'Pasivo', 'Pasivo', 0, reajuste)
                    else:
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "5", 'Pasivo', 'Pasivo', abs(reajuste), 0)
                        add_asiento(detalles, c['Empresa'], c['Codigo_Interno'], "5", 'ROU', 'ROU', 0, abs(reajuste))

    df = pd.DataFrame(detalles)
    df_res = df.groupby('N_Cuenta').sum().reset_index()
    
    # Net flow ROU = Debe ROU - Haber ROU
    # Net flow AmortAcum = Debe AmortAcum - Haber AmortAcum (actually AmortAcum increases with Haber, so Haber - Debe)
    
    debe_rou = df_res[df_res['N_Cuenta'] == 'ROU']['Debe'].sum() if not df_res[df_res['N_Cuenta'] == 'ROU'].empty else 0
    haber_rou = df_res[df_res['N_Cuenta'] == 'ROU']['Haber'].sum() if not df_res[df_res['N_Cuenta'] == 'ROU'].empty else 0
    mov_rou = debe_rou - haber_rou
    
    debe_aa = df_res[df_res['N_Cuenta'] == 'AmortAcum']['Debe'].sum() if not df_res[df_res['N_Cuenta'] == 'AmortAcum'].empty else 0
    haber_aa = df_res[df_res['N_Cuenta'] == 'AmortAcum']['Haber'].sum() if not df_res[df_res['N_Cuenta'] == 'AmortAcum'].empty else 0
    mov_aa = haber_aa - debe_aa
    
    mov_neto = mov_rou - mov_aa
    
    resultados.append({
        'Mes': m_idx,
        'Mov_ROU': mov_rou,
        'Mov_AA': mov_aa,
        'Mov_Neto': mov_neto
    })

print(pd.DataFrame(resultados))
