import pandas as pd
import streamlit as st
import io

@st.cache_data
def obtener_df_monedas_cache():
    from db import cargar_monedas
    return cargar_monedas()

def obtener_tc_cache(moneda, fecha):
    if moneda == "CLP": return 1.0
    df = obtener_df_monedas_cache()
    if df.empty: return 0.0
    try:
        f_s = pd.to_datetime(fecha).strftime('%Y-%m-%d')
        res = df[(df['moneda'] == moneda) & (df['fecha'] <= f_s)]
        return res.iloc[0]['valor'] if not res.empty else 0.0
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

@st.cache_data
def motor_financiero_v20(c):
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
        
    f_baja_final = pd.to_datetime(c['Fecha_Baja']) if c.get('Fecha_Baja') and c['Estado'] == 'Baja' else None
    
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
        if f_baja_final:
            # Eliminar periodos > Fecha de baja
            mask = mask & ((fechas_reales.year < f_baja_final.year) | ((fechas_reales.year == f_baja_final.year) & (fechas_reales.month <= f_baja_final.month)))
            
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
    prefix = empresa[:3].upper()
    count = len([c for c in lista_existente if c['Empresa'] == empresa]) + 1
    return f"CNT-{prefix}-{count:04d}"

def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df.to_excel(wr, index=False)
    return out.getvalue()