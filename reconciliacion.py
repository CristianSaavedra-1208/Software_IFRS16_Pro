import pandas as pd # Reload trigger v21
from datetime import date
from dateutil.relativedelta import relativedelta

# Asumiendo que MESES_LISTA está definido en app.py, lo re-declaramos aquí por simplicidad o lo importamos
MESES_LISTA = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def generar_reconciliacion_rollforward(empresa_sel, a, mes_fin_nom, lista_c, rems_grupos):
    """
    Genera un DataFrame de Reconciliación (Roll-Forward) iterando mes a mes
    para calcular los deltas orgánicos de cada mes de forma independiente.
    """
    from app import obtener_motor_financiero, obtener_tc_cache
    
    # Diciembre del año anterior
    f_dic = pd.to_datetime(date(a - 1, 12, 31))
    m_idx_fin = MESES_LISTA.index(mes_fin_nom) + 1
    
    df_c = pd.DataFrame(lista_c)
    if df_c.empty: return pd.DataFrame()
    
    if empresa_sel != "Todas":
        df_c = df_c[df_c['Empresa'] == empresa_sel]
        
    # Vamos a calcular los saldos exactos (la foto) para Diciembre y para cada mes del año actual
    fechas_corte = [(f'Saldo inicial (Diciembre {a - 1})', f_dic)]
    for i in range(1, m_idx_fin + 1):
        f_t = pd.to_datetime(date(a, i, 1)) + relativedelta(day=31)
        fechas_corte.append((f'Saldos {MESES_LISTA[i-1]} {a}', f_t))
        
    resultados_fotos = []
    
    for nombre_mes, f_t in fechas_corte:
        rou_bruto_tot = 0
        amort_acum_tot = 0
        pasivo_tot = 0
        pasivo_corr_tot = 0
        pasivo_nocorr_tot = 0
        
        for _, c in df_c.iterrows():
            if f_t < pd.to_datetime(c['Inicio']).replace(day=1): continue
            
            # 1. Identificar si existe baja anticipada o vencimiento
            es_baja = False
            f_baja_efectiva = None
            if c.get('Fecha_Baja') and c.get('Estado') == 'Baja':
                f_baja = pd.to_datetime(c['Fecha_Baja'])
                if f_baja <= f_t: f_baja_efectiva = f_baja
            
            f_fin_c = pd.to_datetime(c['Fin'])
            if f_t.year > f_fin_c.year or (f_t.year == f_fin_c.year and f_t.month >= f_fin_c.month):
                if not f_baja_efectiva or f_fin_c < f_baja_efectiva:
                    f_baja_efectiva = f_fin_c
                    
            if f_baja_efectiva:
                if f_baja_efectiva.year < f_t.year:
                    continue # Excluir categóricamente si murió antes del año de la foto
                elif f_baja_efectiva.year == f_t.year and f_baja_efectiva.month <= f_t.month:
                    es_baja = True
                    
            tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
            if tab.empty or 'Fecha' not in tab.columns: continue
            
            past = tab[tab['Fecha'] <= f_t]
            if not past.empty and not es_baja:
                tc = obtener_tc_cache(c['Moneda'], f_t)
                v_act = past.iloc[-1]['S_Fin_Orig']
                
                futuros = tab[tab['Fecha'] > f_t].copy()
                v_cor_sum = 0
                if not futuros.empty:
                    limite_12 = f_t + relativedelta(months=12)
                    futuros['Capital'] = futuros['S_Ini_Orig'] - futuros['S_Fin_Orig']
                    futuros.iloc[-1, futuros.columns.get_loc('Capital')] += futuros.iloc[-1]['S_Fin_Orig']
                    es_corriente = (futuros['Fecha'] - f_t).dt.days <= 90
                    es_corriente = es_corriente | (futuros['Fecha'] <= limite_12)
                    v_cor_sum = futuros.loc[es_corriente, 'Capital'].sum()
                    
                v12 = v_act - v_cor_sum
                tc_ini = float(c['Valor_Moneda_Inicio']) if float(c.get('Valor_Moneda_Inicio', 1)) > 0 else 1.0
                r_bruto = rou * tc_ini
                
                rems = rems_grupos.get(c['Codigo_Interno'], [])
                for r in rems:
                    f_r = pd.to_datetime(r['Fecha_Remedicion'])
                    if f_r <= f_t:
                        tc_rem = obtener_tc_cache(c['Moneda'], f_r)
                        if tc_rem == 0: tc_rem = 1.0
                        
                        past_r = tab[tab['Fecha'] < f_r]
                        fut_r = tab[tab['Fecha'] >= f_r]
                        old_pasivo = past_r.iloc[-1]['S_Fin_Orig'] if not past_r.empty else vp
                        new_pasivo = fut_r.iloc[0]['S_Ini_Orig'] if not fut_r.empty else 0.0
                        baja_p = r.get('Baja_Pasivo', 0.0)
                        baja_r = r.get('Baja_ROU', 0.0)
                        
                        jump_rou_uf = new_pasivo - (old_pasivo - baja_p)
                        if baja_r > 0: r_bruto -= (baja_r * tc_ini)
                        if abs(jump_rou_uf) > 0.01: r_bruto += (jump_rou_uf * tc_rem)
                        
                a_acum = past['Dep_Orig'].sum() * tc_ini
                
                rou_bruto_tot += r_bruto
                amort_acum_tot += a_acum
                pasivo_tot += v_act * tc
                pasivo_corr_tot += v_cor_sum * tc
                pasivo_nocorr_tot += v12 * tc
                
        resultados_fotos.append({
            'Periodo': nombre_mes,
            'ROU Bruto': rou_bruto_tot,
            'Amortizacion Acumulada': amort_acum_tot,
            'Rou Neto': rou_bruto_tot - amort_acum_tot,
            'Pasivo total': pasivo_tot,
            'Pasivo Corriente': pasivo_corr_tot,
            'Pasivo no corriente': pasivo_nocorr_tot
        })
        
    df_fotos = pd.DataFrame(resultados_fotos)
    
    # Calcular los movimientos (Registros por mes)
    movimientos = []
    
    # La primera fila es el Saldo Inicial exacto
    movimientos.append({
        'Periodo': df_fotos.iloc[0]['Periodo'],
        'ROU Bruto': df_fotos.iloc[0]['ROU Bruto'],
        'Amortizacion Acumulada': df_fotos.iloc[0]['Amortizacion Acumulada'],
        'Rou Neto': df_fotos.iloc[0]['Rou Neto'],
        'Pasivo total': df_fotos.iloc[0]['Pasivo total'],
        'Pasivo Corriente': df_fotos.iloc[0]['Pasivo Corriente'],
        'Pasivo no corriente': df_fotos.iloc[0]['Pasivo no corriente']
    })
    
    # Iterar desde Enero para sacar las diferencias (que son los movimientos del mes)
    for i in range(1, len(df_fotos)):
        prev = df_fotos.iloc[i-1]
        curr = df_fotos.iloc[i]
        mes_nom = curr['Periodo'].replace('Saldos ', '')
        
        movimientos.append({
            'Periodo': f'Registros {mes_nom}',
            'ROU Bruto': curr['ROU Bruto'] - prev['ROU Bruto'],
            'Amortizacion Acumulada': curr['Amortizacion Acumulada'] - prev['Amortizacion Acumulada'],
            'Rou Neto': curr['Rou Neto'] - prev['Rou Neto'],
            'Pasivo total': curr['Pasivo total'] - prev['Pasivo total'],
            'Pasivo Corriente': curr['Pasivo Corriente'] - prev['Pasivo Corriente'],
            'Pasivo no corriente': curr['Pasivo no corriente'] - prev['Pasivo no corriente']
        })
        
    # Totales (que equivale matemáticamente a la última foto del mes objetivo)
    totales = df_fotos.iloc[-1].copy()
    totales['Periodo'] = 'Totales'
    movimientos.append(totales.to_dict())
    
    df_final = pd.DataFrame(movimientos)
    return df_final
