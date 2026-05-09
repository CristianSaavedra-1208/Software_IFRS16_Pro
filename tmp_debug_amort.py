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

# Let's find exactly which contracts are terminated in January
terminados = []

for c in lista_c:
    # Check if terminated in Jan 2026
    es_baja = False
    f_baja_efectiva = None
    if c.get('Fecha_Baja') and c.get('Estado') in ['Baja', 'Remedido']:
        f_baja = pd.to_datetime(c['Fecha_Baja'])
        if f_baja.year == a and f_baja.month == m_idx:
            es_baja = True
            
    f_fin_c = pd.to_datetime(c['Fin'])
    if f_fin_c.year == a and f_fin_c.month == m_idx and c['Estado'] == 'Activo':
        es_baja = True
        
    if es_baja:
        terminados.append(c)
        
print("Contracts terminated in Jan 2026:")
for c in terminados:
    tc_ini = float(c.get('Valor_Moneda_Inicio', 1))
    if tc_ini == 0: tc_ini = 1.0
    
    tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
    
    f_baja_val = pd.to_datetime(c['Fecha_Baja']) if c.get('Fecha_Baja') and c.get('Estado') in ['Baja', 'Remedido'] else pd.to_datetime(c['Fin'])
    pasado_baja = tab[tab['Fecha'] <= f_baja_val]
    amort_baja = pasado_baja['Dep_Orig'].sum() * tc_ini
    
    pasado_dic = tab[tab['Fecha'] <= f_ant]
    amort_dic = pasado_dic['Dep_Orig'].sum() * tc_ini if not pasado_dic.empty else 0
    
    fila_jan = tab[(tab['Fecha'].dt.year == a) & (tab['Fecha'].dt.month == m_idx)]
    amort_jan = fila_jan.iloc[0]['Dep_Orig'] * tc_ini if not fila_jan.empty else 0
    
    print(f"[{c['Codigo_Interno']}] {c['Nombre']} - Amort_Dic: {amort_dic:,.0f}, Amort_Jan: {amort_jan:,.0f}, Amort_Baja_Total: {amort_baja:,.0f}")
    
    # Difference Check
    # In Excel: Net movement = Amort_Baja_Total (Debe) - Amort_Jan (Haber) = Amort_Dic (Net Debe)
    # In Recon: Net movement = - Amort_Dic (Decrease of Amort_Dic)
    
