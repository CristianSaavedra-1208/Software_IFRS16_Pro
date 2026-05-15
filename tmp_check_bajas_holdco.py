import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import obtener_motor_financiero
from core import simular_libro_mayor
import logging

logging.getLogger().setLevel(logging.ERROR)

lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Holdco']
rems_grupos = cargar_remediciones_todas_agrupadas()

print("Bajas y Remediciones Holdco Enero 2026:")
for c in lista_c_todas:
    rems = rems_grupos.get(c['Codigo_Interno'], [])
    is_baja_jan = False
    is_rem_jan = False
    
    if c.get('Estado') == 'Baja':
        fb = pd.to_datetime(c.get('Fecha_Baja'))
        if fb.year == 2026 and fb.month == 1:
            is_baja_jan = True
            
    for r in rems:
        fr = pd.to_datetime(r.get('Fecha_Remedicion'))
        if fr.year == 2026 and fr.month == 1:
            is_rem_jan = True
            
    if is_baja_jan or is_rem_jan:
        print(f"Contract {c['Codigo_Interno']} - Baja: {is_baja_jan}, Rem: {is_rem_jan}")
        f_act = pd.to_datetime(date(2026, 1, 31))
        f_ant = f_act - relativedelta(months=1, day=31)
        
        tab, vp, rou = obtener_motor_financiero(c, rems=rems)
        tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
        if tc_ini_hist <= 0: tc_ini_hist = 1.0
        
        rb_t, aa_t, p_t = simular_libro_mayor(c, tab, f_act, rems, tc_ini_hist, vp, rou)
        rb_t1, aa_t1, p_t1 = simular_libro_mayor(c, tab, f_ant, rems, tc_ini_hist, vp, rou)
        
        mov_rb = rb_t - rb_t1
        mov_aa = aa_t - aa_t1
        mov_net = mov_rb - mov_aa
        print(f"  Recon Mov: ROU Bruto={mov_rb:.2f}, Amort Acum={mov_aa:.2f}, ROU Neto={mov_net:.2f}")
