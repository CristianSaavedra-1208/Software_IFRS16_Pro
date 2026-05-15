import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock

# Simulate UI state
st.session_state.auth = True

captured_df = None

def mock_to_excel(self, *args, **kwargs):
    global captured_df
    captured_df = self.copy()
    return None

def run_asientos_mes(m_idx, a=2026):
    global captured_df
    captured_df = None
    
    from app import modulo_asientos
    
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

# 1. Sum up all Asientos for Q1
total_rou_asientos = 0.0
total_aa_asientos = 0.0

for m in [1, 2, 3]:
    df = run_asientos_mes(m)
    if df is not None and not df.empty:
        for idx, r in df.iterrows():
            if r['Empresa'] == 'TOTALES': continue
            cta_num = str(r['N° Cuenta']).strip()
            debe = float(r['Debe']) if pd.notnull(r['Debe']) else 0
            haber = float(r['Haber']) if pd.notnull(r['Haber']) else 0
            
            # ROU
            if cta_num in ['1401', '1208104', '1208114']:
                total_rou_asientos += (debe - haber)
            # Amortizacion Acumulada
            elif cta_num in ['1402', '1208105', '1208115']:
                total_aa_asientos += (haber - debe)

net_asientos = total_rou_asientos - total_aa_asientos

# 2. Get Reconciliacion Data
from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from app import motor_financiero_v21
from core import simular_libro_mayor

lista_c_todas = [c for c in cargar_contratos() if c['Empresa'] == 'Pacifico']
rems_grupos = cargar_remediciones_todas_agrupadas()

rou_2025 = 0.0
aa_2025 = 0.0
rou_2026 = 0.0
aa_2026 = 0.0

f_ant = pd.to_datetime(date(2025, 12, 31))
f_act = pd.to_datetime(date(2026, 3, 31))

for c in lista_c_todas:
    tab, vp, rou = motor_financiero_v21(c, rems=rems_grupos.get(c['Codigo_Interno'], []))
    tc_ini_hist = float(c.get('Valor_Moneda_Inicio') or 1.0)
    if tc_ini_hist <= 0: tc_ini_hist = 1.0
    
    rb_1, aa_1, p_1 = simular_libro_mayor(c, tab, f_ant, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
    rou_2025 += rb_1
    aa_2025 += aa_1
    
    rb_2, aa_2, p_2 = simular_libro_mayor(c, tab, f_act, rems_grupos.get(c['Codigo_Interno'], []), tc_ini_hist, vp, rou)
    rou_2026 += rb_2
    aa_2026 += aa_2

net_2025 = rou_2025 - aa_2025
net_2026 = rou_2026 - aa_2026
mov_recon_rou = rou_2026 - rou_2025
mov_recon_aa = aa_2026 - aa_2025
mov_recon_net = net_2026 - net_2025

print("--- RESULTADOS Q1 2026 PACIFICO ---")
print(f"Saldo Inicial Recon (31-Dic-2025): Activos Netos = {net_2025:,.0f} (ROU: {rou_2025:,.0f}, AA: {aa_2025:,.0f})")
print(f"Saldo Final Recon   (31-Mar-2026): Activos Netos = {net_2026:,.0f} (ROU: {rou_2026:,.0f}, AA: {aa_2026:,.0f})")
print(f"Movimiento Recon Q1 2026:          Activos Netos = {mov_recon_net:,.0f} (ROU: {mov_recon_rou:,.0f}, AA: {mov_recon_aa:,.0f})")
print("-----------------------------------")
print(f"Suma de Asientos Q1 2026:          Activos Netos = {net_asientos:,.0f} (ROU: {total_rou_asientos:,.0f}, AA: {total_aa_asientos:,.0f})")
print("-----------------------------------")
diff_net = mov_recon_net - net_asientos
print(f"Diferencia (Recon Mov - Asientos): {diff_net:,.0f}")
print(f"Diferencia ROU: {mov_recon_rou - total_rou_asientos:,.0f}")
print(f"Diferencia AA:  {mov_recon_aa - total_aa_asientos:,.0f}")

