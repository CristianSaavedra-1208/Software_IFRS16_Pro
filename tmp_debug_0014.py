import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import motor_financiero_v21, obtener_tc_cache
from core import simular_libro_mayor

rems_grupos = cargar_remediciones_todas_agrupadas()
lista_c = cargar_contratos()
c = next(c for c in lista_c if c['Codigo_Interno'] == 'CNT-PAC-0014')

a = 2026
m_idx = 1
f_act = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
f_ant = f_act - relativedelta(months=1, day=31)

tab, vp, rou = motor_financiero_v21(c, [])
tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)

rb_t, aa_t, p_t = simular_libro_mayor(c, tab, f_act, [], tc_ini_hist, vp, rou)
net_t = rb_t - aa_t
rb_t1, aa_t1, p_t1 = simular_libro_mayor(c, tab, f_ant, [], tc_ini_hist, vp, rou)
net_t1 = rb_t1 - aa_t1
mov_recon = net_t - net_t1

mov_asientos = 0
fila = tab[(tab['Fecha'].dt.month == m_idx) & (tab['Fecha'].dt.year == a)]
print('Fila empty:', fila.empty)
if not fila.empty:
    it = fila.iloc[0]
    tc_act = obtener_tc_cache(c['Moneda'], f_act)
    if it['Mes'] == 1: tc_ant_val = tc_ini_hist
    else: tc_ant_val = obtener_tc_cache(c['Moneda'], f_ant)
    
    tc_act_amo = tc_act if tc_act > 0 else 1.0
    tc_amo_rou = tc_act_amo if c['Moneda'] in ['UF', 'CLP'] else tc_ini_hist
    
    amort = it['Dep_Orig'] * tc_amo_rou
    mov_asientos -= amort
    print('After amort:', mov_asientos)
    
    flujo_pasivo = (it['Int_Orig'] - it['Pago_Orig']) * tc_act
    
    target_balance = it['S_Fin_Orig'] * tc_act
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
    print('After reajuste:', mov_asientos, 'reajuste:', reajuste)
