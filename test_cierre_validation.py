"""
test_cierre_validation.py
=========================
Suite de pruebas de control de calidad financiera y validación de baseline para el
módulo de Cierre de Períodos Contables (Candado IFRS 16).
"""

import sys
import os
import types

# 1. Configurar Mock de Streamlit ANTES de importar cualquier módulo del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if "streamlit" not in sys.modules:
    mock_st = types.ModuleType("streamlit")
    mock_st.cache_data = lambda f=None, **kw: (f if f else lambda fn: fn)
    mock_st.session_state = {}
    sys.modules["streamlit"] = mock_st

import json
import hashlib
import sqlite3
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from db import cargar_contratos, cargar_remediciones_todas_agrupadas
from core import motor_financiero_v21, simular_libro_mayor

# Periodos de prueba clave para evaluar integridad
PERIODOS_TEST = [
    (2025, 5),   # Mayo 2025
    (2025, 12),  # Diciembre 2025
    (2026, 1),   # Enero 2026
    (2026, 7),   # Julio 2026
    (2026, 8),   # Agosto 2026
]

BASELINE_CIERRE_FILE = "baseline_cierre_numeros.json"
TOLERANCIA_CLP = 0.01

def df_hash(df):
    if df is None or df.empty:
        return "EMPTY"
    try:
        return hashlib.sha256(
            pd.util.hash_pandas_object(df, index=True).values.tobytes()
        ).hexdigest()[:16]
    except Exception:
        return "HASH_ERROR"

def round2(v):
    try:
        return round(float(v), 2)
    except Exception:
        return 0.0

def calcular_foto_periodos_todos():
    lista_c = cargar_contratos()
    rems_grupos = cargar_remediciones_todas_agrupadas()
    
    # Precomputar tablas financieras una sola vez
    print(f"Precomputando tablas financieras para {len(lista_c)} contratos...", flush=True)
    tablas_cache = {}
    for c in lista_c:
        cid = c["Codigo_Interno"]
        rems = rems_grupos.get(cid, [])
        try:
            tab, vp, rou = motor_financiero_v21(c, rems)
        except Exception:
            tab, vp, rou = motor_financiero_v21(c)
        tablas_cache[cid] = (tab, vp, rou)
        
    resultado_periodos = {}
    
    for anio, mes in PERIODOS_TEST:
        tag = f"{anio}-{mes:02d}"
        f_ref = pd.to_datetime(date(anio, mes, 1)) + relativedelta(day=31)
        print(f" -> Procesando período {tag}...", flush=True)
        
        datos_periodo = {
            "contratos": {},
            "totales": {
                "rou_bruto_total": 0.0,
                "amort_acum_total": 0.0,
                "pasivo_total": 0.0,
                "vp_total": 0.0
            }
        }
        
        rb_tot, aa_tot, pas_tot, vp_tot = 0.0, 0.0, 0.0, 0.0
        
        for c in lista_c:
            cid = c["Codigo_Interno"]
            tab, vp, rou = tablas_cache[cid]
            rems = rems_grupos.get(cid, [])
            
            tc_ini = float(c.get("Valor_Moneda_Inicio") or 1.0)
            if tc_ini <= 0: tc_ini = 1.0
            
            rb, aa, pasivo = simular_libro_mayor(c, tab, f_ref, rems, tc_ini, vp, rou)
            
            rb_tot += rb
            aa_tot += aa
            pas_tot += pasivo
            vp_tot += vp
            
            datos_periodo["contratos"][cid] = {
                "vp": round2(vp),
                "rou": round2(rou),
                "tabla_hash": df_hash(tab),
                "rou_bruto": round2(rb),
                "amort_acum": round2(aa),
                "pasivo": round2(pasivo)
            }
            
        datos_periodo["totales"]["rou_bruto_total"] = round2(rb_tot)
        datos_periodo["totales"]["amort_acum_total"] = round2(aa_tot)
        datos_periodo["totales"]["pasivo_total"] = round2(pas_tot)
        datos_periodo["totales"]["vp_total"] = round2(vp_tot)
        
        print(f"    Pasivo: ${datos_periodo['totales']['pasivo_total']:,.0f} | ROU Bruto: ${datos_periodo['totales']['rou_bruto_total']:,.0f}", flush=True)
        resultado_periodos[tag] = datos_periodo
        
    return resultado_periodos

def capturar_baseline():
    print("=" * 70, flush=True)
    print("  CAPTURA DE BASELINE FINANCIERO PRE-CIERRE (TOLERANCIA CERO)", flush=True)
    print("=" * 70, flush=True)
    
    periodos = calcular_foto_periodos_todos()
    resultado = {
        "fecha_captura": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "periodos": periodos
    }
    
    with open(BASELINE_CIERRE_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
        
    print(f"\n [OK] Baseline guardado exitosamente en: {BASELINE_CIERRE_FILE}", flush=True)

def verificar_baseline():
    print("=" * 70, flush=True)
    print("  VERIFICACIÓN CONTRA BASELINE PRE-CIERRE", flush=True)
    print("=" * 70, flush=True)
    
    if not os.path.exists(BASELINE_CIERRE_FILE):
        print(f" [ERROR] No existe el archivo {BASELINE_CIERRE_FILE}. Ejecute capture primero.", flush=True)
        sys.exit(1)
        
    with open(BASELINE_CIERRE_FILE, "r", encoding="utf-8") as f:
        baseline = json.load(f)
        
    diferencias = []
    actual_periodos = calcular_foto_periodos_todos()
    
    for anio, mes in PERIODOS_TEST:
        tag = f"{anio}-{mes:02d}"
        print(f" -> Verificando período {tag}...", flush=True)
        actual = actual_periodos.get(tag)
        esperado = baseline["periodos"].get(tag)
        
        if not esperado or not actual:
            diferencias.append(f"Período {tag} faltante")
            continue
            
        # Comparar totales
        for k, v_esp in esperado["totales"].items():
            v_act = actual["totales"].get(k, 0.0)
            diff = abs(v_act - v_esp)
            if diff > TOLERANCIA_CLP:
                diferencias.append(f"[{tag}] Total {k}: Esperado={v_esp}, Actual={v_act}, Dif={diff}")
                
        # Comparar contratos
        for cid, vals_esp in esperado["contratos"].items():
            if cid not in actual["contratos"]:
                diferencias.append(f"[{tag}] Contrato {cid} falta en versión actual")
                continue
            vals_act = actual["contratos"][cid]
            
            for campo in ["vp", "rou", "rou_bruto", "amort_acum", "pasivo"]:
                ve = vals_esp.get(campo, 0.0)
                va = vals_act.get(campo, 0.0)
                diff = abs(va - ve)
                if diff > TOLERANCIA_CLP:
                    diferencias.append(f"[{tag}][{cid}] Campo {campo}: Esperado={ve}, Actual={va}, Dif={diff}")
                    
            if vals_esp.get("tabla_hash") != vals_act.get("tabla_hash"):
                diferencias.append(f"[{tag}][{cid}] Hash de tabla amortización difiere")
                
    print("\n" + "=" * 70, flush=True)
    if not diferencias:
        print(" [ÉXITO TOTAL] 0 DIFERENCIAS DETECTADAS. 100% DE SALDOS IDÉNTICOS.", flush=True)
        print("=" * 70, flush=True)
        return True
    else:
        print(f" [ALERTA] SE ENCONTRARON {len(diferencias)} DIFERENCIAS:", flush=True)
        for d in diferencias[:20]:
            print(f"   - {d}", flush=True)
        if len(diferencias) > 20:
            print(f"   ... y {len(diferencias) - 20} más.", flush=True)
        print("=" * 70, flush=True)
        return False

def test_candados():
    from db import (
        inicializar_db, cerrar_periodo_contable, reabrir_periodo_contable,
        es_periodo_cerrado, obtener_ultimo_periodo_cerrado, conectar
    )
    print("=" * 70, flush=True)
    print("  TEST UNITARIO DE FUNCIONES DE CANDADO Y CIERRE", flush=True)
    print("=" * 70, flush=True)
    
    inicializar_db()
    
    # 0. Limpiar registros de prueba para test aislado
    conn = conectar()
    conn.execute("DELETE FROM periodos_contables WHERE motivo LIKE '%test%' OR motivo LIKE '%auditor%'")
    conn.execute("DELETE FROM saldos_cierre_periodo WHERE periodo_cierre >= '2026-01-01'")
    conn.commit()
    conn.close()
    
    # 1. Probar cierre de periodo Mayo 2026
    ok, msg = cerrar_periodo_contable(2026, 5, "Todas", "admin", "Cierre mensual auditoria test")
    print(f" -> Cierre Mayo 2026: {ok} ({msg})", flush=True)
    assert ok, f"Fallo al cerrar periodo: {msg}"
    
    # 2. Verificar que fechas <= 2026-05-31 estén cerradas y posteriores abiertas
    assert es_periodo_cerrado("2026-05-15", "Todas") == True, "Error: 2026-05-15 debiera estar cerrada"
    assert es_periodo_cerrado("2026-01-01", "Todas") == True, "Error: 2026-01-01 debiera estar cerrada"
    assert es_periodo_cerrado("2026-06-01", "Todas") == False, "Error: 2026-06-01 debiera estar abierta"
    print(" -> Verificaciones de fechas cerradas/abiertas: CORRECTAS", flush=True)
    
    # 3. Probar reapertura de Mayo 2026
    ok_reabrir, msg_reabrir = reabrir_periodo_contable(2026, 5, "Todas", "admin", "Reapertura para test")
    print(f" -> Reapertura Mayo 2026: {ok_reabrir} ({msg_reabrir})", flush=True)
    assert ok_reabrir, f"Fallo al reabrir periodo: {msg_reabrir}"
    
    # Limpiar
    conn = conectar()
    conn.execute("DELETE FROM periodos_contables WHERE motivo LIKE '%test%'")
    conn.commit()
    conn.close()
    
    print("\n [OK] Todos los tests de candado pasaron con éxito.", flush=True)
    return True

def test_benchmark_snapshots():
    import time
    from db import (
        inicializar_db, cerrar_periodo_contable, reabrir_periodo_contable
    )
    from core import limpiar_caches_financieros
    
    print("=" * 70, flush=True)
    print("  BENCHMARK & INTEGRIDAD CON SNAPSHOTS DE CIERRE", flush=True)
    print("=" * 70, flush=True)
    
    inicializar_db()
    
    # 1. Medir tiempo sin snapshot para Agosto 2026 (1784 contratos)
    print("\n[1/4] Calculando Agosto 2026 SIN snapshots (desde 2019/origen)...", flush=True)
    t0 = time.time()
    res_sin_snap = calcular_foto_periodos_todos()
    t_sin = time.time() - t0
    print(f" -> Tiempo total sin snapshots: {t_sin:.2f} s", flush=True)
    
    # 2. Cerrar Julio 2026 (generará snapshot al 2026-07-31)
    print("\n[2/4] Cerrando período 2026-07 para generar snapshots...", flush=True)
    ok_c, msg_c = cerrar_periodo_contable(2026, 7, "Todas", "admin", "Benchmark test snapshot")
    print(f" -> Cierre 2026-07: {ok_c} ({msg_c})", flush=True)
    limpiar_caches_financieros()
    
    # 3. Medir tiempo CON snapshot para Agosto 2026
    print("\n[3/4] Calculando periodos CON snapshot activo al 2026-07...", flush=True)
    t0 = time.time()
    res_con_snap = calcular_foto_periodos_todos()
    t_con = time.time() - t0
    print(f" -> Tiempo total con snapshots: {t_con:.2f} s", flush=True)
    
    # 4. Validar que los números de Agosto 2026 sean 100% IDÉNTICOS
    print("\n[4/4] Verificando tolerancia cero en saldos entre ambas ejecuciones...", flush=True)
    tag = "2026-08"
    tot_sin = res_sin_snap[tag]["totales"]
    tot_con = res_con_snap[tag]["totales"]
    
    difs = []
    for k in tot_sin:
        diff = abs(tot_sin[k] - tot_con[k])
        if diff > TOLERANCIA_CLP:
            difs.append(f"Total {k}: SinSnap={tot_sin[k]}, ConSnap={tot_con[k]}, Dif={diff}")
            
    for cid in res_sin_snap[tag]["contratos"]:
        vs = res_sin_snap[tag]["contratos"][cid]
        vc = res_con_snap[tag]["contratos"][cid]
        for campo in ["pasivo", "rou_bruto", "amort_acum"]:
            diff = abs(vs[campo] - vc[campo])
            if diff > TOLERANCIA_CLP:
                difs.append(f"[{cid}] {campo}: SinSnap={vs[campo]}, ConSnap={vc[campo]}, Dif={diff}")
                
    # Reabrir el período para dejar la base de datos limpia
    reabrir_periodo_contable(2026, 7, "Todas", "admin", "Limpieza post-benchmark")
    limpiar_caches_financieros()
    
    if not difs:
        print(f"\n [ÉXITO TOTAL] 0 DIFERENCIAS DETECTADAS.")
        print(f" -> Saldo Pasivo 2026-08: ${tot_con['pasivo_total']:,.0f}")
        print(f" -> Saldo ROU 2026-08:    ${tot_con['rou_bruto_total']:,.0f}")
        return True
    else:
        print(f"\n [ALERTA] Se encontraron {len(difs)} diferencias:")
        for d in difs[:20]:
            print(f"   - {d}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "capture":
        capturar_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == "verify":
        ok = verificar_baseline()
        sys.exit(0 if ok else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "test-lock":
        ok = test_candados()
        sys.exit(0 if ok else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        ok = test_benchmark_snapshots()
        sys.exit(0 if ok else 1)
    else:
        print("Uso: python test_cierre_validation.py [capture|verify|test-lock|benchmark]")
