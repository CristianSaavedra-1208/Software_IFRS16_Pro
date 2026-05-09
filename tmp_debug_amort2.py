import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import sys

sys.path.append('c:\\Users\\cfsaa\\OneDrive\\Desktop\\Software_IFRS16_Pro')
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import obtener_motor_financiero

lista_c = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()

a = 2026
m_idx = 1
f_act = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
f_ant = pd.to_datetime(date(a - 1, 12, 31))

diff_total = 0

for c in lista_c:
    f_ini = pd.to_datetime(c['Inicio'])
    if f_act < f_ini.replace(day=1): continue

    tc_ini_hist = float(c.get('Valor_Moneda_Inicio', 1))
    if tc_ini_hist == 0: tc_ini_hist = 1.0

    tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
    if tab.empty or 'Fecha' not in tab.columns: continue

    fila = tab[(tab['Fecha'].dt.month == m_idx) & (tab['Fecha'].dt.year == a)]
    amort_jan = fila.iloc[0]['Dep_Orig'] * tc_ini_hist if not fila.empty else 0
    
    paso_baja_manual = False
    is_terminated_jan = False
    amort_baja = 0
    
    if c.get('Fecha_Baja') and c['Estado'] in ['Baja', 'Remedido']:
        f_baja = pd.to_datetime(c['Fecha_Baja'])
        if f_baja.month == m_idx and f_baja.year == a:
            paso_baja_manual = True
            is_terminated_jan = True
            pasado = tab[tab['Fecha'] <= f_baja]
            amort_baja = pasado['Dep_Orig'].sum() * tc_ini_hist
            
    paso_terminacion_parcial = False
    rems = rems_grupos.get(c['Codigo_Interno'], [])
    for r in rems:
        f_r = pd.to_datetime(r['Fecha_Remedicion'])
        if f_r.month == m_idx and f_r.year == a and r.get('Baja_Pasivo', 0.0) > 0:
            paso_terminacion_parcial = True
            break
            
    f_fin_c = pd.to_datetime(c['Fin'])
    if not paso_baja_manual and not paso_terminacion_parcial and c['Estado'] == 'Activo':
        if f_fin_c.month == m_idx and f_fin_c.year == a:
            is_terminated_jan = True
            pasado = tab[tab['Fecha'] <= f_fin_c]
            amort_baja = pasado['Dep_Orig'].sum() * tc_ini_hist
            
    if is_terminated_jan:
        pasado_dic = tab[tab['Fecha'] <= f_ant]
        amort_dic = pasado_dic['Dep_Orig'].sum() * tc_ini_hist if not pasado_dic.empty else 0
        
        # Recon net decrease is amort_dic
        recon_net_decrease = amort_dic
        # Accounting net decrease is amort_baja - amort_jan
        acc_net_decrease = amort_baja - amort_jan
        
        if abs(recon_net_decrease - acc_net_decrease) > 0.1:
            print(f"[{c['Codigo_Interno']}] Recon Decrease: {recon_net_decrease:,.2f} | Acc Decrease: {acc_net_decrease:,.2f} | Diff: {recon_net_decrease - acc_net_decrease:,.2f}")
            diff_total += (recon_net_decrease - acc_net_decrease)

print(f"\nTotal Difference: {diff_total:,.2f}")
