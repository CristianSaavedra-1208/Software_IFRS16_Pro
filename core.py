import pandas as pd
import streamlit as st
import io

@st.cache_data
def obtener_df_monedas_cache():
    from db import cargar_monedas
    return cargar_monedas()

from functools import lru_cache

@lru_cache(maxsize=4096)
def _obtener_tc_cache_interno(moneda, f_s):
    if moneda == "CLP": return 1.0
    df = obtener_df_monedas_cache()
    if df.empty: return 0.0
    try:
        res = df[(df['moneda'] == moneda) & (df['fecha'] <= f_s)]
        return float(res.iloc[0]['valor']) if not res.empty else 0.0
    except: return 0.0

def obtener_tc_cache(moneda, fecha):
    if moneda == "CLP": return 1.0
    try:
        f_s = pd.to_datetime(fecha).strftime('%Y-%m-%d')
        return _obtener_tc_cache_interno(moneda, f_s)
    except: return 0.0

def __calc_vp(can, p, t_m, tipo, f_meses=1):
    if p <= 0: return 0.0
    
    arr_cf = np.zeros(p)
    for i in range(p):
        if tipo == "Anticipado":
            if i % f_meses == 0: arr_cf[i] = can
        else:
            if (i+1) % f_meses == 0: arr_cf[i] = can
            
    if t_m > 0:
        vp = 0.0
        for i in range(p):
            if tipo == "Anticipado":
                vp += arr_cf[i] / ((1 + t_m)**i)
            else:
                vp += arr_cf[i] / ((1 + t_m)**(i+1))
        return vp
    else: 
        return sum(arr_cf)

import numpy as np

@st.cache_data(show_spinner=False)
def motor_financiero_v21(c, rems=None):
    if rems is None:
        from db import cargar_remediciones
        rems = cargar_remediciones(c['Codigo_Interno'])
    
    # Hito 1: Parámetros del contrato Original (antes de cualquier remedición)
    f_i = pd.to_datetime(c['Inicio'])
    tipo = c.get('Tipo_Pago', 'Vencido')
    
    # Calcular ROU Inicial Original
    cd = float(c.get('Costos_Directos', 0.0))
    pa = float(c.get('Pagos_Anticipados', 0.0))
    cdesm = float(c.get('Costos_Desmantelamiento', 0.0))
    inc = float(c.get('Incentivos', 0.0))
    ajuste_orig = float(c.get('Ajuste_ROU', 0.0))
    
    # Cargar Frecuencia del contrato original
    frec_str = c.get('Frecuencia_Pago', 'Mensual')
    from db import obtener_parametros
    frecs = obtener_parametros('FRECUENCIA_PAGO')
    map_frec = {'Mensual': 1}
    for fr in frecs:
        parts = fr.split('-')
        if len(parts) == 2 and parts[1].strip().isdigit():
            map_frec[parts[0].strip()] = int(parts[1].strip())
            
    f_meses = map_frec.get(frec_str.strip(), 1)
    
    vp_orig = __calc_vp(float(c['Canon']), int(c['Plazo']), float(c['Tasa_Mensual']), tipo, f_meses)
    rou_orig = vp_orig + cd + pa + cdesm - inc + ajuste_orig
    
    tramos = []
    tramos.append({
        'Fecha_Inicio': f_i,
        'Canon': float(c['Canon']),
        'Tasa_Mensual': float(c['Tasa_Mensual']),
        'Plazo': int(c['Plazo']),
        'Ajuste_ROU': ajuste_orig,
        'Es_Remedicion': False,
        'Frec_Meses': f_meses
    })
    
    for r in rems:
        tramos.append({
            'Fecha_Inicio': pd.to_datetime(r['Fecha_Remedicion']),
            'Canon': float(r['Canon']),
            'Tasa_Mensual': float(r['Tasa_Mensual']),
            'Plazo': int(r['Plazo']),
            'Ajuste_ROU': float(r['Ajuste_ROU']),
            'Es_Remedicion': True,
            'Frec_Meses': f_meses # Mantenemos la frecuencia original
        })
        
    f_baja_final = pd.to_datetime(c['Fecha_Baja']) if c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido'] else None
    
    dfs = []
    mes_global = 1
    
    # Aunque iteramos los Tramos (suele ser 1, rara vez > 2), vectorizamos **dentro** del tramo.
    s_ini_pasivo = vp_orig
    s_ini_rou_net = rou_orig
    
    for idx, t in enumerate(tramos):
        f_tramo_ini = t['Fecha_Inicio']
        f_tramo_fin = tramos[idx+1]['Fecha_Inicio'] if idx+1 < len(tramos) else None
        
        if t['Es_Remedicion']:
            s_ini_pasivo = __calc_vp(t['Canon'], t['Plazo'], t['Tasa_Mensual'], tipo, t['Frec_Meses'])
            s_ini_rou_net = s_ini_pasivo + t['Ajuste_ROU']
            
        plazo = t['Plazo']
        if plazo <= 0: continue
            
        dep_tramo = s_ini_rou_net / plazo
        
        # 1. Crear el array de índices (0 hasta plazo-1)
        periodos = np.arange(plazo)
        
        # 2. Generar Fechas Vectorizadas
        # date_range es sumamente eficiente en pandas
        fechas_reales = pd.date_range(start=f_tramo_ini, periods=plazo, freq=pd.DateOffset(months=1))
        
        # 3. Filtrar fechas según tramos de remedición o bajas
        mask = np.ones(plazo, dtype=bool)
        if f_tramo_fin:
            # Eliminar periodos >= Fecha del siguiente tramo
            mask = mask & ((fechas_reales.year < f_tramo_fin.year) | ((fechas_reales.year == f_tramo_fin.year) & (fechas_reales.month < f_tramo_fin.month)))
        # La tabla debe generarse hasta el Fin natural (o próxima remedición) para no corromper la distribución Corto/Largo plazo de meses anteriores.
        # Las bajas (write-offs) se aplican lógicamente en app.py, reconciliacion.py y asientos.py evaluando f_baja_efectiva.            
        valid_idx = np.where(mask)[0]
        if len(valid_idx) == 0: continue
        
        periodos_validos = periodos[valid_idx]
        fechas_validas = fechas_reales[valid_idx]
        n_meses = len(valid_idx)
        
        # 4. Matemáticas Financieras - Soporte DCF Múltiples Frecuencias
        t_m = t['Tasa_Mensual']
        c_an = t['Canon']
        f_meses = t['Frec_Meses']
        
        all_s_inis = np.zeros(plazo)
        all_ints = np.zeros(plazo)
        all_caps = np.zeros(plazo)
        all_s_fins = np.zeros(plazo)
        pagos_proyectados = np.zeros(plazo)
        
        # Distribuir canon de acuerdo a la frecuencia de pago
        for i in range(plazo):
            if tipo == "Anticipado":
                if i % f_meses == 0: pagos_proyectados[i] = c_an
            else:
                if (i+1) % f_meses == 0: pagos_proyectados[i] = c_an
                
        saldo_actual = __calc_vp(c_an, plazo, t_m, tipo, f_meses)
        
        if t_m > 0:
            for i in range(plazo):
                pago_mes = pagos_proyectados[i]
                all_s_inis[i] = saldo_actual
                if tipo == "Anticipado":
                    saldo_base = max(0.0, saldo_actual - pago_mes)
                    interes = saldo_base * t_m
                    amort = pago_mes - interes
                    saldo_final = saldo_actual - amort
                else: # Vencido
                    interes = saldo_actual * t_m
                    amort = pago_mes - interes
                    saldo_final = saldo_actual - amort
                
                # Ajuste centesimal obligatoria final
                if i == plazo - 1:
                    amort = saldo_actual
                    interes = max(0.0, pago_mes - amort)
                    saldo_final = 0.0
                    
                all_ints[i] = interes
                all_caps[i] = amort
                all_s_fins[i] = saldo_final
                
                saldo_actual = saldo_final
        else:
            for i in range(plazo):
                pago_mes = pagos_proyectados[i]
                all_s_inis[i] = saldo_actual
                interes = 0.0
                amort = pago_mes
                saldo_final = saldo_actual - amort
                
                if i == plazo - 1:
                    amort = saldo_actual
                    saldo_final = 0.0
                    
                all_ints[i] = interes
                all_caps[i] = amort
                all_s_fins[i] = saldo_final
                saldo_actual = saldo_final
                
        # Extraer ventana de tiempo para el tramo actual
        s_inis = all_s_inis[valid_idx]
        ints = all_ints[valid_idx]
        caps = all_caps[valid_idx]
        s_fins = all_s_fins[valid_idx]
        pagos_tramo = pagos_proyectados[valid_idx]
        
        # 5. Ensamblar DataFrame del tramo
        df_tramo = pd.DataFrame({
            'Mes': mes_global + np.arange(n_meses),
            'Fecha': fechas_validas,
            'S_Ini_Orig': np.round(s_inis, 4),
            'Int_Orig': np.round(ints, 4),
            'Pago_Orig': np.round(pagos_tramo, 4),
            'Dep_Orig': np.round(np.full(n_meses, dep_tramo), 4),
            'S_Fin_Orig': np.round(s_fins, 4)
        })
        
        dfs.append(df_tramo)
        mes_global += n_meses
        
        # El saldo inicial (si hubiera otro tramo o se quisiera auditar de fuera) sería el fin de este tramo
        s_ini_pasivo = s_fins[-1] if n_meses > 0 else s_ini_pasivo
        
    if not dfs:
        return pd.DataFrame(), vp_orig, rou_orig
        
    final_df = pd.concat(dfs, ignore_index=True)
    return final_df, vp_orig, rou_orig

def generar_codigo_correlativo(empresa, lista_existente):
    prefix = str(empresa).strip()[:3].upper()
    max_num = 0
    pattern = f"CNT-{prefix}-"
    
    for c in lista_existente:
        cod = c.get('Codigo_Interno', '')
        if cod.startswith(pattern):
            try:
                num = int(cod.split('-')[-1])
                if num > max_num: max_num = num
            except: pass
            
    count = max_num + 1
    return f"CNT-{prefix}-{count:04d}"

def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df.to_excel(wr, index=False)
    return out.getvalue()

def to_excel_formatted(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df.to_excel(wr, index=False)
        workbook = wr.book
        worksheet = wr.sheets['Sheet1']
        num_fmt = workbook.add_format({'num_format': '#,##0'})
        for i, col in enumerate(df.columns):
            if pd.api.types.is_numeric_dtype(df[col]):
                worksheet.set_column(i, i, 18, num_fmt)
            else:
                worksheet.set_column(i, i, 20)
    return out.getvalue()

def simular_libro_mayor(c, tab, f_t, rems, tc_ini_hist, vp, rou, ignore_baja=False):
    from dateutil.relativedelta import relativedelta
    from datetime import date
    import pandas as pd
    
    if tab is None or tab.empty or 'Fecha' not in tab.columns:
        return 0.0, 0.0, 0.0
        
    past = tab[tab['Fecha'] <= f_t]
    if past.empty:
        return 0.0, 0.0, 0.0

    es_uf_clp = c['Moneda'] in ['UF', 'CLP']
    tc_ini = float(c.get('Valor_Moneda_Inicio') or 1.0)
    if tc_ini <= 0: tc_ini = 1.0
    
    rou_bruto_clp = rou * tc_ini
    pasivo_clp = vp * tc_ini
    amort_acum_clp = 0.0
    
    rems_por_mes = {}
    if rems:
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
                
                baja_p = float(r.get('Baja_Pasivo') or 0.0)
                baja_r = float(r.get('Baja_ROU') or 0.0)
                
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
        if not ignore_baja:
            if c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido']:
                fb = pd.to_datetime(c['Fecha_Baja'])
                if fb.year == row['Fecha'].year and fb.month == row['Fecha'].month:
                    target_balance = 0.0
        
        reajuste = target_balance - pasivo_clp
        if abs(reajuste) > 1.0:
            pasivo_clp += reajuste
            if es_uf_clp:
                rou_bruto_clp += reajuste

    if not ignore_baja:
        # Ensure termination logic correctly zeroes everything
        f_fin = pd.to_datetime(c['Fin'])
        if f_fin.year < f_t.year or (f_fin.year == f_t.year and f_fin.month <= f_t.month):
            if not (c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido'] and pd.to_datetime(c['Fecha_Baja']) > f_t):
                rou_bruto_clp = 0.0
                amort_acum_clp = 0.0
                pasivo_clp = 0.0
                
        if c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido']:
            fb = pd.to_datetime(c['Fecha_Baja'])
            if fb.year < f_t.year or (fb.year == f_t.year and fb.month <= f_t.month):
                rou_bruto_clp = 0.0
                amort_acum_clp = 0.0
                pasivo_clp = 0.0

    return rou_bruto_clp, amort_acum_clp, pasivo_clp