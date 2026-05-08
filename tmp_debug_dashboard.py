import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos
from app import obtener_motor_financiero

lista_c = cargar_contratos()
c = next((x for x in lista_c if x['Codigo_Interno'] == 'CNT-PAC-0495'), None)
if not c:
    print("Contract not found")
    exit()

print(f"Estado: {c['Estado']}, Fecha_Baja: {c.get('Fecha_Baja')}, Fin: {c['Fin']}")

a = 2026
m_idx = 4
f_t = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)

es_baja_ejercicio = False
f_baja_efectiva = None

# 1. Identificar si existe baja anticipada
if c.get('Fecha_Baja') and c['Estado'] == 'Baja':
    f_baja = pd.to_datetime(c['Fecha_Baja'])
    if f_baja <= f_t:
        f_baja_efectiva = f_baja
        print(f"Baja anticipada detectada: {f_baja_efectiva}")

# 2. Identificar si expiró naturalmente
f_fin_c = pd.to_datetime(c['Fin'])
if f_t.year > f_fin_c.year or (f_t.year == f_fin_c.year and f_t.month >= f_fin_c.month):
    if not f_baja_efectiva or f_fin_c < f_baja_efectiva:
        f_baja_efectiva = f_fin_c
        print(f"Expiración natural detectada: {f_baja_efectiva}")

if f_baja_efectiva:
    if f_baja_efectiva.year < a:
        print(f"Excluido porque murió en {f_baja_efectiva.year} < {a}")
    elif f_baja_efectiva.year == a and f_baja_efectiva.month <= f_t.month:
        es_baja_ejercicio = True
        print(f"Es baja ejercicio = True")

tab, vp, rou = obtener_motor_financiero(c, rems=[])
past = tab[tab['Fecha'] <= f_t]
print(f"Past empty: {past.empty}")
if not past.empty:
    v_act = past.iloc[-1]['S_Fin_Orig']
    print(f"v_act before: {v_act}")
    if es_baja_ejercicio:
        v_act = 0
        rou_bruto = 0
        amort_clp = 0
        print("Set to 0 because es_baja_ejercicio is True")
    print(f"v_act after: {v_act}")
