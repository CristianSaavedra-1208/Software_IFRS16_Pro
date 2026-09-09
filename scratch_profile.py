import sys, os, time
import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta

from db import cargar_contratos, cargar_remediciones_todas_agrupadas, obtener_parametros
from core import motor_financiero_v21, simular_libro_mayor, obtener_tc_cache

def profile_dashboard_optimizado(a=2025, m_idx=12, emp_sel="Todas"):
    f_t = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
    
    t0 = time.time()
    df_c = pd.DataFrame(cargar_contratos())
    rems_grupos = cargar_remediciones_todas_agrupadas()
    
    res = []
    t_start = time.time()
    
    # Pre-cache TC for year a
    fechas_anio = [pd.to_datetime(date(a, m, 1)) + relativedelta(day=31) for m in range(1, m_idx + 1)]
    tc_cache_uf = {f: obtener_tc_cache('UF', f) for f in fechas_anio}
    tc_cache_usd = {f: obtener_tc_cache('USD', f) for f in fechas_anio}
    tc_cache_utm = {f: obtener_tc_cache('UTM', f) for f in fechas_anio}
    
    tc_map_by_currency = {'UF': tc_cache_uf, 'USD': tc_cache_usd, 'UTM': tc_cache_utm, 'CLP': {f: 1.0 for f in fechas_anio}}
    
    for _, c in df_c.iterrows():
        if emp_sel != "Todas" and c['Empresa'] != emp_sel: continue
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
            if f_baja_efectiva.year < a: continue
            elif f_baja_efectiva.year == a and f_baja_efectiva.month <= f_t.month:
                es_baja_ejercicio = True
                
        tab, vp, rou = motor_financiero_v21(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
        if tab.empty or 'Fecha' not in tab.columns: continue
        
        mask_past = tab['Fecha'] <= f_t
        past = tab[mask_past]
        if not past.empty:
            tc = obtener_tc_cache(c['Moneda'], f_t); ratio_pasivo = tc
            v_act = past['S_Fin_Orig'].iloc[-1]
            
            # Fast vectorized calculation of future capital
            futuros = tab[~mask_past]
            v_cor_sum = 0.0
            if not futuros.empty:
                limite_12_dash = f_t + relativedelta(months=12)
                caps = (futuros['S_Ini_Orig'] - futuros['S_Fin_Orig']).to_numpy(copy=True)
                caps[-1] += futuros['S_Fin_Orig'].iloc[-1]
                fechas_fut = futuros['Fecha'].values
                
                dias_al_pago = (fechas_fut - np.datetime64(f_t)).astype('timedelta64[D]').astype(int)
                es_corriente_mask = (dias_al_pago <= 90) | (fechas_fut <= np.datetime64(limite_12_dash))
                v_cor_sum = caps[es_corriente_mask].sum()
            v12 = v_act - v_cor_sum
            
            tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
            if tc_ini_hist <= 0: tc_ini_hist = 1.0
            
            rems = rems_grupos.get(c['Codigo_Interno'], [])
            rou_bruto, amort_clp, pasivo_total_clp = simular_libro_mayor(c, tab, f_t, rems, tc_ini_hist, vp, rou)
            
            # Fast vectorized dep_ejercicio_clp
            past_ejercicio = past[past['Fecha'].dt.year == a]
            if not past_ejercicio.empty:
                dep_origs = past_ejercicio['Dep_Orig'].values
                fechas_dep = past_ejercicio['Fecha'].values
                moneda = c['Moneda']
                tc_dict = tc_map_by_currency.get(moneda, {})
                
                dep_ejercicio_clp = 0.0
                for d_val, f_val in zip(dep_origs, fechas_dep):
                    f_dt = pd.to_datetime(f_val)
                    f_mes_dep = pd.to_datetime(date(f_dt.year, f_dt.month, 1)) + relativedelta(day=31)
                    if f_baja_efectiva:
                        if f_mes_dep.year > f_baja_efectiva.year or (f_mes_dep.year == f_baja_efectiva.year and f_mes_dep.month > f_baja_efectiva.month):
                            continue
                    tc_mes_dep = tc_dict.get(f_mes_dep) or obtener_tc_cache(moneda, f_mes_dep) or 1.0
                    tc_amo_rou = tc_mes_dep if (moneda in ['UF', 'CLP'] or (moneda == 'UTM' and a >= 2026)) else tc_ini_hist
                    dep_ejercicio_clp += d_val * tc_amo_rou
            else:
                dep_ejercicio_clp = 0.0
                
    t_tot = time.time() - t_start
    print(f"\nTiempo Total Calculo Dashboard OPTIMIZADO: {t_tot:.2f} s")

if __name__ == "__main__":
    profile_dashboard_optimizado(2025, 12)
