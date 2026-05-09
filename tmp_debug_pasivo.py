import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import sys

sys.path.append('c:\\Users\\cfsaa\\OneDrive\\Desktop\\Software_IFRS16_Pro')
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import obtener_motor_financiero, obtener_tc_cache

lista_c = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()

a = 2026
m_idx = 1
f_act = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
f_ant = pd.to_datetime(date(a - 1, 12, 31))

diff_total = 0

print("Verificando Pasivo para Enero 2026...")

for c in lista_c:
    f_ini = pd.to_datetime(c['Inicio'])
    if f_act < f_ini.replace(day=1): continue

    tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
    if tab.empty or 'Fecha' not in tab.columns: continue

    tc_act = obtener_tc_cache(c['Moneda'], f_act)
    tc_ant = obtener_tc_cache(c['Moneda'], f_ant)

    # --- 1. RECONCILIATION LOGIC ---
    es_baja = False
    f_baja_efectiva = None
    if c.get('Fecha_Baja') and c.get('Estado') == 'Baja':
        f_baja = pd.to_datetime(c['Fecha_Baja'])
        if f_baja <= f_act: f_baja_efectiva = f_baja
    
    f_fin_c = pd.to_datetime(c['Fin'])
    if f_act.year > f_fin_c.year or (f_act.year == f_fin_c.year and f_act.month >= f_fin_c.month):
        if not f_baja_efectiva or f_fin_c < f_baja_efectiva:
            f_baja_efectiva = f_fin_c
            
    if f_baja_efectiva:
        if f_baja_efectiva.year == f_act.year and f_baja_efectiva.month <= f_act.month:
            es_baja = True

    past_jan = tab[tab['Fecha'] <= f_act]
    recon_pasivo_jan = 0
    if not past_jan.empty and not es_baja:
        recon_pasivo_jan = past_jan.iloc[-1]['S_Fin_Orig'] * tc_act

    es_baja_dic = False
    if f_baja_efectiva:
        if f_baja_efectiva.year < f_ant.year or (f_baja_efectiva.year == f_ant.year and f_baja_efectiva.month <= f_ant.month):
            es_baja_dic = True

    past_dic = tab[tab['Fecha'] <= f_ant]
    recon_pasivo_dic = 0
    if not past_dic.empty and not es_baja_dic:
        recon_pasivo_dic = past_dic.iloc[-1]['S_Fin_Orig'] * tc_ant
        if f_ini.year == a: # Reconocimiento ocurre en el año, saldo inicial es 0
            recon_pasivo_dic = 0

    recon_net_movement = recon_pasivo_jan - recon_pasivo_dic

    # --- 2. ACCOUNTING LOGIC (Simulated FX Plug target) ---
    # The Accounting module explicitly forces the Ending Balance to equal 'target_balance'
    target_balance = 0
    fila = tab[(tab['Fecha'].dt.month == m_idx) & (tab['Fecha'].dt.year == a)]
    if not fila.empty:
        target_balance = fila.iloc[0]['S_Fin_Orig'] * tc_act
        
        # Exceptions for Baja
        if (c.get('Fecha_Baja') and c['Estado'] == 'Baja' and pd.to_datetime(c['Fecha_Baja']).month == m_idx and pd.to_datetime(c['Fecha_Baja']).year == a):
            target_balance = 0.0
        elif c['Estado'] == 'Activo':
            if f_fin_c.month == m_idx and f_fin_c.year == a:
                target_balance = 0.0
    elif es_baja:
        target_balance = 0.0

    # The starting balance for the accounting is what was left at the end of December
    if f_ini.month == m_idx and f_ini.year == a:
        last_target_balance = 0.0 # Reconocimiento inicial
    else:
        last_uf = past_dic.iloc[-1]['S_Fin_Orig'] if not past_dic.empty else 0.0
        last_target_balance = last_uf * tc_ant

    acc_net_movement = target_balance - last_target_balance

    diff = round(abs(recon_net_movement - acc_net_movement), 0)
    if diff > 1.0:
        print(f"[{c['Codigo_Interno']}] Mismatch! Recon: {recon_net_movement:,.0f} | Acc: {acc_net_movement:,.0f} | Diff: {diff:,.0f}")
        diff_total += diff

print(f"\nDiferencia Total de Pasivos: {diff_total:,.0f}")
