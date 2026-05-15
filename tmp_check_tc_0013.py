import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import motor_financiero_v21, modulo_asientos
from core import simular_libro_mayor

st.session_state.auth = True

captured_df = None

def mock_to_excel(self, *args, **kwargs):
    global captured_df
    captured_df = self.copy()
    return None

def run_asientos_mes(m_idx, a=2026):
    global captured_df
    captured_df = None
    
    with patch('streamlit.selectbox') as mock_sb, \
         patch('streamlit.number_input') as mock_ni, \
         patch('streamlit.button') as mock_btn, \
         patch('streamlit.dataframe'), \
         patch('streamlit.download_button'), \
         patch('streamlit.header'), \
         patch('streamlit.tabs') as mock_tabs, \
         patch('streamlit.expander'), \
         patch('streamlit.info'), \
         patch('pandas.DataFrame.to_excel', new=mock_to_excel), \
         patch('streamlit.columns') as mock_cols:
         
        c1, c2, c3 = MagicMock(), MagicMock(), MagicMock()
        mock_cols.return_value = [c1, c2, c3]
        
        mock_sb.side_effect = lambda *args, **kwargs: 'Pacifico' if args[0] == 'Empresa' else ['Enero', 'Febrero', 'Marzo'][m_idx-1]
        c1.selectbox.return_value = 'Pacifico'
        c2.selectbox.return_value = ['Enero', 'Febrero', 'Marzo'][m_idx-1]
        c3.number_input.return_value = a
        mock_btn.return_value = True
        
        t1, t2 = MagicMock(), MagicMock()
        mock_tabs.return_value = [t1, t2]
        t1.__enter__.return_value = t1
        t1.__exit__.return_value = False
        t2.__enter__.return_value = t2
        t2.__exit__.return_value = False
        
        modulo_asientos()
        
    return captured_df

asientos_per_contract = {}

for m in [1, 2, 3]:
    df = run_asientos_mes(m)
    if df is not None and not df.empty:
        for idx, r in df.iterrows():
            if r['Empresa'] == 'TOTALES': continue
            c_code = None
            for col in r.keys():
                if 'Contrato' in str(col):
                    c_code = str(r[col]).strip()
                    break
            if not c_code: c_code = str(r.iloc[1]).strip()
            
            if c_code not in asientos_per_contract:
                asientos_per_contract[c_code] = {'rou': 0.0, 'aa': 0.0}
                
            cta_num = None
            for col in r.keys():
                if 'Cuenta' in str(col):
                    cta_num = str(r[col]).strip()
                    break
            if not cta_num: cta_num = str(r.iloc[3]).strip()
            
            debe = float(r['Debe']) if pd.notnull(r['Debe']) else 0
            haber = float(r['Haber']) if pd.notnull(r['Haber']) else 0
            
            # ROU
            if cta_num in ['1401', '1208104', '1208114']:
                asientos_per_contract[c_code]['rou'] += (debe - haber)
            # Amortizacion Acumulada
            elif cta_num in ['1402', '1208105', '1208115']:
                asientos_per_contract[c_code]['aa'] += (haber - debe)

lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Pacifico']
rems_grupos = cargar_remediciones_todas_agrupadas()

f_ant = pd.to_datetime(date(2025, 12, 31))
f_act = pd.to_datetime(date(2026, 3, 31))

for c in lista_c_todas:
    c_code = c['Codigo_Interno']
    tab, vp, rou = motor_financiero_v21(c, rems=rems_grupos.get(c_code, []))
    tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
    if tc_ini_hist <= 0: tc_ini_hist = 1.0
    
    rb_1, aa_1, p_1 = simular_libro_mayor(c, tab, f_ant, rems_grupos.get(c_code, []), tc_ini_hist, vp, rou)
    rb_2, aa_2, p_2 = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c_code, []), tc_ini_hist, vp, rou)
    
    mov_recon_rou = rb_2 - rb_1
    mov_recon_aa = aa_2 - aa_1
    
    asiento_rou = asientos_per_contract.get(c_code, {}).get('rou', 0.0)
    asiento_aa = asientos_per_contract.get(c_code, {}).get('aa', 0.0)
    
    diff_rou = mov_recon_rou - asiento_rou
    diff_aa = mov_recon_aa - asiento_aa
    
    if abs(diff_rou) > 700000000 or abs(diff_aa) > 700000000:
        print(f"!!! FOUND IT !!! [{c_code}] Diff ROU: {diff_rou:,.0f} | Diff AA: {diff_aa:,.0f} | Mov Recon ROU: {mov_recon_rou:,.0f} | Asiento ROU: {asiento_rou:,.0f} | Mov Recon AA: {mov_recon_aa:,.0f} | Asiento AA: {asiento_aa:,.0f} | Estado: {c['Estado']}")
