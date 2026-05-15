import streamlit as st
from unittest.mock import patch, MagicMock
import pandas as pd
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import modulo_asientos, obtener_motor_financiero
from core import simular_libro_mayor
from datetime import date
from dateutil.relativedelta import relativedelta

st.session_state.auth = True

lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Pacifico']
rems_grupos = cargar_remediciones_todas_agrupadas()

diffs = []
captured_df = None

original_to_excel = pd.DataFrame.to_excel

def mock_to_excel(self, *args, **kwargs):
    global captured_df
    captured_df = self.copy()
    return None

def run_for_contract(c_target, m_idx, a=2026):
    global captured_df
    captured_df = None
    
    def mock_cargar_contratos():
        return [c_target]
        
    with patch('app.cargar_contratos', side_effect=mock_cargar_contratos), \
         patch('streamlit.selectbox') as mock_sb, \
         patch('streamlit.number_input') as mock_ni, \
         patch('streamlit.button') as mock_btn, \
         patch('streamlit.dataframe'), \
         patch('streamlit.download_button'), \
         patch('streamlit.header'), \
         patch('pandas.DataFrame.to_excel', new=mock_to_excel), \
         patch('streamlit.columns') as mock_cols:
         
        c1, c2, c3 = MagicMock(), MagicMock(), MagicMock()
        mock_cols.return_value = [c1, c2, c3]
        mock_sb.side_effect = lambda *args, **kwargs: 'Pacifico' if args[0] == 'Empresa' else ['Enero', 'Febrero', 'Marzo'][m_idx-1]
        c1.selectbox.return_value = 'Pacifico'
        c2.selectbox.return_value = ['Enero', 'Febrero', 'Marzo'][m_idx-1]
        c3.number_input.return_value = a
        mock_btn.return_value = True
        
        modulo_asientos()
        
    mov_asientos = 0.0
    if captured_df is not None and not captured_df.empty:
        df = captured_df
        for idx, r in df.iterrows():
            cta_num = str(r['N° Cuenta']).strip()
            debe = float(r['Debe']) if pd.notnull(r['Debe']) else 0
            haber = float(r['Haber']) if pd.notnull(r['Haber']) else 0
            
            if cta_num in ['1401', '1208104', '1208114']:
                mov_asientos += (debe - haber)
            elif cta_num in ['1402', '1208105', '1208115']:
                mov_asientos -= (haber - debe)
                
    # Recon
    f_act = pd.to_datetime(date(a, m_idx, 1)) + relativedelta(day=31)
    f_ant = f_act - relativedelta(months=1, day=31)
    
    tab, vp, rou = obtener_motor_financiero(c_target, rems=rems_grupos.get(c_target['Codigo_Interno'], []))
    tc_ini_hist = float(c_target.get('Valor_Moneda_Inicio') or 1.0)
    if tc_ini_hist <= 0: tc_ini_hist = 1.0
    
    rb_t, aa_t, p_t = simular_libro_mayor(c_target, tab, f_act, rems_grupos.get(c_target['Codigo_Interno'], []), tc_ini_hist, vp, rou)
    net_t = rb_t - aa_t
    rb_t1, aa_t1, p_t1 = simular_libro_mayor(c_target, tab, f_ant, rems_grupos.get(c_target['Codigo_Interno'], []), tc_ini_hist, vp, rou)
    net_t1 = rb_t1 - aa_t1
    
    mov_recon = net_t - net_t1
    
    diff = mov_recon - mov_asientos
    if abs(diff) > 1.0:
        return diff, mov_recon, mov_asientos
    return 0, 0, 0

print("Buscando diferencias en Enero 2026...")
for c in lista_c_todas:
    d, r, a_val = run_for_contract(c, 1)
    if abs(d) > 1.0:
        print(f"Jan - {c['Codigo_Interno']}: diff={d:.2f} (recon={r:.2f}, asie={a_val:.2f})")
