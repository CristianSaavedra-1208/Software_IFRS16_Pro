import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import motor_financiero_v21, obtener_tc_cache
from core import simular_libro_mayor

rems_grupos = cargar_remediciones_todas_agrupadas()
lista_c = cargar_contratos()

c = next(c for c in lista_c if c['Codigo_Interno'] == 'CNT-PAC-0014')
print('rems:', rems_grupos.get(c['Codigo_Interno'], []))
tab, vp, rou = motor_financiero_v21(c, rems_grupos.get(c['Codigo_Interno'], []))

f_act = pd.to_datetime(date(2026, 1, 1)) + relativedelta(day=31)
f_ant = f_act - relativedelta(months=1, day=31)

tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
rb_t, aa_t, p_t = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
net_t = rb_t - aa_t
rb_t1, aa_t1, p_t1 = simular_libro_mayor(c, tab, f_ant, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
net_t1 = rb_t1 - aa_t1

mov_recon = net_t - net_t1
print('rb_t:', rb_t, 'aa_t:', aa_t, 'net_t:', net_t)
print('rb_t1:', rb_t1, 'aa_t1:', aa_t1, 'net_t1:', net_t1)
print('mov_recon:', mov_recon)
