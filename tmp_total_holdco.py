import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import modulo_asientos, obtener_motor_financiero
from core import simular_libro_mayor
from unittest.mock import patch, MagicMock
import logging

logging.getLogger().setLevel(logging.ERROR)

rems_grupos = cargar_remediciones_todas_agrupadas()
lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Holdco']

captured_df = None

def mock_to_excel(self, *args, **kwargs):
    global captured_df
    captured_df = self.copy()
    return None

def get_asientos_totales(m_idx=1, a=2026):
    global captured_df
    captured_df = None
    with patch('streamlit.selectbox') as mock_sb, \
         patch('streamlit.number_input') as mock_ni, \
         patch('streamlit.button') as mock_btn, \
         patch('streamlit.dataframe'), \
         patch('streamlit.download_button'), \
         patch('streamlit.header'), \
         patch('pandas.DataFrame.to_excel', new=mock_to_excel), \
         patch('streamlit.columns') as mock_cols:
         
        c1, c2, c3 = MagicMock(), MagicMock(), MagicMock()
        mock_cols.return_value = [c1, c2, c3]
        mock_sb.side_effect = lambda *args, **kwargs: 'Holdco' if args[0] == 'Empresa' else ['Enero', 'Febrero', 'Marzo'][m_idx-1]
        c1.selectbox.return_value = 'Holdco'
        c2.selectbox.return_value = ['Enero', 'Febrero', 'Marzo'][m_idx-1]
        c3.number_input.return_value = a
        mock_btn.return_value = True
        
        modulo_asientos()
        
    mov_asientos_rou = 0.0
    mov_asientos_amort = 0.0
    if captured_df is not None and not captured_df.empty:
        df = captured_df
        for idx, r in df.iterrows():
            cta_num = str(r['N° Cuenta']).strip()
            debe = float(r['Debe']) if pd.notnull(r['Debe']) else 0
            haber = float(r['Haber']) if pd.notnull(r['Haber']) else 0
            
            if cta_num in ['1208104', '1208105', '1401', '1402']:
                mov_asientos_rou += (debe - haber)
            elif cta_num in ['1208114', '1208115']:
                mov_asientos_amort += (haber - debe)
    
    return mov_asientos_rou, mov_asientos_amort

print("Calculando Asientos Holdco Febrero 2026...")
a_rou, a_amort = get_asientos_totales(2, 2026)

print(f"Total Asientos Mov ROU Bruto: {a_rou}")
print(f"Total Asientos Mov Amort Acum: {a_amort}")
print(f"Total Asientos Net ROU: {a_rou - a_amort}")

print("\nCalculando Recon Holdco Febrero 2026...")
f_act = pd.to_datetime(date(2026, 2, 28))
f_ant = f_act - relativedelta(months=1, day=31)

r_rou = 0.0
r_amort = 0.0

for c in lista_c_todas:
    rems = rems_grupos.get(c['Codigo_Interno'], [])
    tab, vp, rou = obtener_motor_financiero(c, rems=rems)
    tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
    if tc_ini_hist <= 0: tc_ini_hist = 1.0
    
    rb_t, aa_t, p_t = simular_libro_mayor(c, tab, f_act, rems, tc_ini_hist, vp, rou)
    rb_t1, aa_t1, p_t1 = simular_libro_mayor(c, tab, f_ant, rems, tc_ini_hist, vp, rou)
    
    r_rou += (rb_t - rb_t1)
    r_amort += (aa_t - aa_t1)

print(f"Total Recon Mov ROU Bruto: {r_rou}")
print(f"Total Recon Mov Amort Acum: {r_amort}")
print(f"Total Recon Net ROU: {r_rou - r_amort}")

print(f"\nDiferencia Total ROU Bruto: {r_rou - a_rou}")
print(f"Diferencia Total Amort Acum: {r_amort - a_amort}")
print(f"Diferencia ROU Neto: {(r_rou - r_amort) - (a_rou - a_amort)}")
