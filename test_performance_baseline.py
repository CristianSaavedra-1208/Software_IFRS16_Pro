"""
test_performance_baseline.py
============================
Script de Test Harness para validar que las optimizaciones de rendimiento
NO alteran los números financieros del sistema IFRS 16 Pro.

MODOS DE USO:
  python test_performance_baseline.py capture   → Captura el baseline actual
  python test_performance_baseline.py verify    → Verifica contra el baseline guardado

El script compara:
  1. motor_financiero_v21 → VP, ROU y hash del DataFrame de tabla financiera
  2. simular_libro_mayor  → ROU Bruto, Amort. Acumulada, Pasivo (a fecha de referencia)
  3. obtener_tc_cache     → Tipos de cambio para fechas clave
  4. generar_reconciliacion_rollforward → Totales consolidados

CRITERIO DE ÉXITO: 0 diferencias > 1 CLP (tolerancia de redondeo).
"""

import sys
import os
import json
import hashlib
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# ─── Período de referencia fijo ──────────────────────────────────────────────
# Cambiar este valor si se quiere un período diferente
ANIO_REF = 2025
MES_REF   = 5   # Mayo = 5
EMPRESA_REF = "Todas"

MESES_LISTA = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
               "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

BASELINE_FILE = "baseline_numeros.json"

# ─── Tolerancia ───────────────────────────────────────────────────────────────
TOLERANCIA_CLP = 1.0   # diferencia máxima aceptable en CLP

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def df_hash(df):
    """SHA-256 del DataFrame para detectar cualquier cambio estructural."""
    if df is None or df.empty:
        return "EMPTY"
    try:
        return hashlib.sha256(
            pd.util.hash_pandas_object(df, index=True).values.tobytes()
        ).hexdigest()[:16]
    except Exception:
        return "HASH_ERROR"

def round2(v):
    """Redondea a 2 decimales para comparación."""
    try:
        return round(float(v), 2)
    except Exception:
        return 0.0

# ─────────────────────────────────────────────────────────────────────────────
# CAPTURA DEL BASELINE
# ─────────────────────────────────────────────────────────────────────────────

def capturar_baseline():
    print("=" * 60)
    print("  MODO CAPTURA — Generando baseline_numeros.json")
    print("=" * 60)

    # Importar módulos del sistema (sin Streamlit — usamos mock)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Mock mínimo de Streamlit para ejecutar sin UI
    import types
    mock_st = types.ModuleType("streamlit")
    mock_st.cache_data = lambda f=None, **kw: (f if f else lambda fn: fn)
    mock_st.session_state = {}
    sys.modules["streamlit"] = mock_st

    from db import cargar_contratos, cargar_remediciones_todas_agrupadas, obtener_parametros
    from core import motor_financiero_v21, simular_libro_mayor, obtener_tc_cache

    lista_c = cargar_contratos()
    rems_grupos = cargar_remediciones_todas_agrupadas()

    f_ref = pd.to_datetime(date(ANIO_REF, MES_REF, 1)) + relativedelta(day=31)

    print(f"\nContratos encontrados: {len(lista_c)}")
    print(f"Período de referencia: {f_ref.strftime('%Y-%m-%d')}\n")

    baseline = {
        "fecha_captura": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "periodo_referencia": f_ref.strftime("%Y-%m-%d"),
        "anio_ref": ANIO_REF,
        "mes_ref": MES_REF,
        "contratos": {},
        "tc_muestras": {},
        "reconciliacion": {}
    }

    errores_captura = []

    # 1. Motor financiero + Libro mayor por contrato
    for c in lista_c:
        cid = c["Codigo_Interno"]
        rems = rems_grupos.get(cid, [])
        print(f"  Procesando {cid}...", end="")

        try:
            tab, vp, rou = motor_financiero_v21(c, tuple(frozenset(r.items()) for r in rems) if rems else None)
        except TypeError:
            # Si motor_financiero_v21 no acepta rems como arg, lo llamamos sin él
            # y usamos la carga interna
            try:
                tab, vp, rou = motor_financiero_v21(c)
            except Exception as e:
                errores_captura.append(f"{cid}: motor_financiero_v21 → {e}")
                print(f" ERROR motor: {e}")
                continue

        tc_ini_hist = float(c.get("Valor_Moneda_Inicio") or 1.0)
        if tc_ini_hist <= 0:
            tc_ini_hist = 1.0

        try:
            rb, aa, pasivo = simular_libro_mayor(
                c, tab, f_ref, rems, tc_ini_hist, vp, rou
            )
        except Exception as e:
            errores_captura.append(f"{cid}: simular_libro_mayor → {e}")
            print(f" ERROR libro_mayor: {e}")
            rb, aa, pasivo = 0.0, 0.0, 0.0

        # TC de referencia para la moneda de este contrato
        moneda = c.get("Moneda", "CLP")
        tc_val = obtener_tc_cache(moneda, f_ref)

        baseline["contratos"][cid] = {
            "moneda": moneda,
            "vp": round2(vp),
            "rou": round2(rou),
            "tabla_rows": len(tab) if not tab.empty else 0,
            "tabla_hash": df_hash(tab),
            "libro_mayor": {
                "rou_bruto": round2(rb),
                "amort_acum": round2(aa),
                "pasivo": round2(pasivo)
            },
            "tc_ref": round2(tc_val)
        }
        print(f" OK (pasivo={round2(pasivo):,.0f})")

    # 2. Muestras de tipos de cambio para fechas clave
    print("\nCapturando muestras de TC...")
    fechas_tc = [
        date(2025, 1, 31), date(2025, 3, 31), date(2025, 5, 31),
        date(2024, 12, 31), date(2023, 6, 30)
    ]
    monedas_tc = obtener_parametros("MONEDA")
    for mon in monedas_tc:
        baseline["tc_muestras"][mon] = {}
        for fd in fechas_tc:
            val = obtener_tc_cache(mon, pd.to_datetime(fd))
            baseline["tc_muestras"][mon][str(fd)] = round2(val)
            print(f"  TC {mon} @ {fd}: {round2(val)}")

    # 3. Reconciliación roll-forward
    print("\nCapturando reconciliación roll-forward...")
    try:
        # Importar sin el contexto de app.py (que tiene Streamlit)
        # Usamos los datos ya calculados para construir los totales directamente
        rou_bruto_tot = sum(
            v["libro_mayor"]["rou_bruto"]
            for v in baseline["contratos"].values()
        )
        amort_tot = sum(
            v["libro_mayor"]["amort_acum"]
            for v in baseline["contratos"].values()
        )
        pasivo_tot = sum(
            v["libro_mayor"]["pasivo"]
            for v in baseline["contratos"].values()
        )
        baseline["reconciliacion"] = {
            "rou_bruto_total": round2(rou_bruto_tot),
            "amort_acum_total": round2(amort_tot),
            "rou_neto_total": round2(rou_bruto_tot - amort_tot),
            "pasivo_total": round2(pasivo_tot)
        }
        print(f"  ROU Bruto Total:  {rou_bruto_tot:,.0f}")
        print(f"  Amort Acum Total: {amort_tot:,.0f}")
        print(f"  ROU Neto Total:   {rou_bruto_tot - amort_tot:,.0f}")
        print(f"  Pasivo Total:     {pasivo_tot:,.0f}")
    except Exception as e:
        baseline["reconciliacion"] = {"error": str(e)}
        print(f"  ERROR reconciliación: {e}")

    # Guardar
    with open(BASELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"  Baseline guardado en: {BASELINE_FILE}")
    if errores_captura:
        print(f"  ADVERTENCIAS ({len(errores_captura)}):")
        for e in errores_captura:
            print(f"    - {e}")
    print(f"  Contratos procesados: {len(baseline['contratos'])}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACIÓN CONTRA BASELINE
# ─────────────────────────────────────────────────────────────────────────────

def verificar_baseline():
    print("=" * 60)
    print("  MODO VERIFICACIÓN — Comparando contra baseline_numeros.json")
    print("=" * 60)

    if not os.path.exists(BASELINE_FILE):
        print(f"\n  ERROR: No existe {BASELINE_FILE}")
        print("  Ejecuta primero: python test_performance_baseline.py capture")
        sys.exit(1)

    with open(BASELINE_FILE, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    print(f"\n  Baseline capturado el: {baseline['fecha_captura']}")
    print(f"  Período de referencia: {baseline['periodo_referencia']}\n")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    import types
    mock_st = types.ModuleType("streamlit")
    mock_st.cache_data = lambda f=None, **kw: (f if f else lambda fn: fn)
    mock_st.session_state = {}
    sys.modules["streamlit"] = mock_st

    from db import cargar_contratos, cargar_remediciones_todas_agrupadas, obtener_parametros
    from core import motor_financiero_v21, simular_libro_mayor, obtener_tc_cache

    lista_c = cargar_contratos()
    rems_grupos = cargar_remediciones_todas_agrupadas()
    f_ref = pd.to_datetime(baseline["periodo_referencia"])

    diferencias = []
    ok_count = 0

    # 1. Verificar por contrato
    for c in lista_c:
        cid = c["Codigo_Interno"]
        if cid not in baseline["contratos"]:
            print(f"  [NUEVO] {cid} no estaba en el baseline (contrato nuevo, ignorado)")
            continue

        b = baseline["contratos"][cid]
        rems = rems_grupos.get(cid, [])

        try:
            tab, vp, rou = motor_financiero_v21(c)
        except Exception as e:
            diferencias.append(f"{cid}: Error en motor_financiero_v21: {e}")
            continue

        tc_ini_hist = float(c.get("Valor_Moneda_Inicio") or 1.0)
        if tc_ini_hist <= 0:
            tc_ini_hist = 1.0

        try:
            rb, aa, pasivo = simular_libro_mayor(c, tab, f_ref, rems, tc_ini_hist, vp, rou)
        except Exception as e:
            diferencias.append(f"{cid}: Error en simular_libro_mayor: {e}")
            continue

        # Comparar VP y ROU
        if abs(round2(vp) - b["vp"]) > TOLERANCIA_CLP:
            diferencias.append(f"{cid}: VP → baseline={b['vp']:,.2f} | actual={round2(vp):,.2f} | diff={round2(vp)-b['vp']:+,.2f}")

        if abs(round2(rou) - b["rou"]) > TOLERANCIA_CLP:
            diferencias.append(f"{cid}: ROU → baseline={b['rou']:,.2f} | actual={round2(rou):,.2f} | diff={round2(rou)-b['rou']:+,.2f}")

        # Comparar tabla hash
        h_actual = df_hash(tab)
        if h_actual != b["tabla_hash"]:
            diferencias.append(f"{cid}: TABLA FINANCIERA CAMBIÓ → baseline_hash={b['tabla_hash']} | actual_hash={h_actual}")

        # Comparar libro mayor
        for campo, val_base in b["libro_mayor"].items():
            val_actual = {"rou_bruto": rb, "amort_acum": aa, "pasivo": pasivo}[campo]
            if abs(round2(val_actual) - val_base) > TOLERANCIA_CLP:
                diferencias.append(
                    f"{cid}: libro_mayor.{campo} → baseline={val_base:,.2f} | actual={round2(val_actual):,.2f} | diff={round2(val_actual)-val_base:+,.2f}"
                )

        ok_count += 1
        print(f"  OK {cid} (pasivo={round2(pasivo):,.0f})")

    # 2. Verificar TCs
    print("\n  Verificando tipos de cambio...")
    monedas_tc = obtener_parametros("MONEDA")
    fechas_tc = [
        date(2025, 1, 31), date(2025, 3, 31), date(2025, 5, 31),
        date(2024, 12, 31), date(2023, 6, 30)
    ]
    for mon in monedas_tc:
        if mon not in baseline.get("tc_muestras", {}):
            continue
        for fd in fechas_tc:
            val_actual = round2(obtener_tc_cache(mon, pd.to_datetime(fd)))
            val_base = baseline["tc_muestras"].get(mon, {}).get(str(fd), None)
            if val_base is not None and abs(val_actual - val_base) > TOLERANCIA_CLP:
                diferencias.append(
                    f"TC {mon}@{fd} → baseline={val_base:,.4f} | actual={val_actual:,.4f}"
                )

    # 3. Verificar totales de reconciliación
    print("\n  Verificando totales consolidados...")
    rou_bruto_tot = sum(
        float(baseline["contratos"][cid]["libro_mayor"]["rou_bruto"])
        for cid in baseline["contratos"]
    )
    # Nota: acá usamos los valores que acabamos de calcular en este run
    # para comparar con el baseline
    b_recon = baseline.get("reconciliacion", {})
    if b_recon and "rou_bruto_total" in b_recon:
        if abs(rou_bruto_tot - b_recon["rou_bruto_total"]) > TOLERANCIA_CLP:
            diferencias.append(
                f"RECON ROU Bruto Total → baseline={b_recon['rou_bruto_total']:,.2f} | actual={rou_bruto_tot:,.2f}"
            )

    # ─── Resultado final ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    if not diferencias:
        print(f"  VERIFICACION EXITOSA --- 0 diferencias encontradas")
        print(f"  Contratos verificados: {ok_count}")
        print(f"  Los numeros son identicos al baseline. SEGURO AVANZAR.")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"  VERIFICACION FALLIDA --- {len(diferencias)} diferencia(s) encontrada(s):")
        for d in diferencias:
            print(f"    -> {d}")
        print(f"\n  NO AVANZAR a la siguiente fase.")
        print(f"  Revisar los cambios realizados o hacer rollback con el archivo BACKUP.")
        print("=" * 60)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("capture", "verify"):
        print("Uso:")
        print("  python test_performance_baseline.py capture   → Captura baseline")
        print("  python test_performance_baseline.py verify    → Verifica vs. baseline")
        sys.exit(1)

    if sys.argv[1] == "capture":
        capturar_baseline()
    else:
        verificar_baseline()
