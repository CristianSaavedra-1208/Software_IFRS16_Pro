import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import sys

sys.path.append('c:\\Users\\cfsaa\\OneDrive\\Desktop\\Software_IFRS16_Pro')
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import obtener_motor_financiero

lista_c = cargar_contratos()
rems_grupos = cargar_remediciones_todas_agrupadas()

for c in lista_c:
    if c['Codigo_Interno'] == 'CNT-PAC-0081':
        tab, vp, rou = obtener_motor_financiero(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
        print(tab[['Fecha', 'S_Ini_Orig', 'Dep_Orig', 'Pago_Orig', 'Int_Orig', 'S_Fin_Orig']].tail(5))
        print("Fin:", c['Fin'], "Fecha_Baja:", c.get('Fecha_Baja'))
