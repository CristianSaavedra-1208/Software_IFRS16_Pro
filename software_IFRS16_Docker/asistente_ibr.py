import datetime
import os

def mostrar_definiciones():
    print("="*60)
    print(" ASISTENTE DE CÁLCULO DE TASA DE DESCUENTO (IFRS 16)")
    print("="*60)
    print("Definiciones y Enlaces de Referencia:")
    print("- Tasa IBR: Incremental Borrowing Rate (Tasa incremental por préstamos).")
    print("- BCU (UF): bcentral.cl")
    print("- BCP (Pesos): bcentral.cl")
    print("- Treasury Yield (USD): treasurydirect.gov")
    print("- Bunds (EUR - Alemania): deutsche-finanzagentur.de")
    print("="*60)

def obtener_float(mensaje):
    while True:
        valor = input(mensaje)
        if valor.strip() == "":
            return None
        try:
            return float(valor)
        except ValueError:
            print("Por favor, ingrese un número válido o deje en blanco si no tiene el dato.")

def diagnostico_inicial():
    print("\n--- DIAGNÓSTICO INICIAL (Jerarquía IFRS 16) ---")
    print("¿Desea intentar calcular la Tasa Implícita o pasar directamente a la IBR?")
    print("1. Tasa Implícita en el arrendamiento")
    print("2. IBR (Incremental Borrowing Rate)")
    
    opcion = input("Seleccione (1 o 2): ").strip()
    
    if opcion == "1":
        print("\nPara calcular la Tasa Implícita, ingrese los siguientes datos (deje en blanco si no lo conoce):")
        vr = obtener_float("Valor Razonable del activo subyacente: ")
        oc = obtener_float("Opción de Compra (o pagos de arrendamiento): ")
        vrng = obtener_float("Valor Residual No Garantizado: ")
        ca = obtener_float("Costos Iniciales Directos del Arrendador: ")
        
        if vr is None or oc is None or vrng is None or ca is None:
            print("\n[!] ADVERTENCIA TÉCNICA: ")
            print("No se cuenta con toda la información necesaria (específicamente datos del arrendador).")
            print("Según la normativa NIIF 16 (párrafo 26), si la tasa implícita no puede determinarse fácilmente, ")
            print("el arrendatario utilizará su Tasa Incremental por Préstamos (IBR).")
            print("Procediendo al cálculo de la IBR...")
            return "IBR"
        else:
            print("\nSe han ingresado todos los parámetros. Sin embargo, en la práctica habitual sin acceso")
            print("interno a la contabilidad del arrendador, se recomienda el uso de IBR.")
            print("Procederemos al cálculo de IBR como alternativa de respaldo.")
            return "IBR"
    else:
        return "IBR"

def calcular_ibr():
    print("\n--- CÁLCULO DE IBR PERSONALIZADO ---")
    moneda = input("Ingrese la Moneda del contrato (Ej. UF, CLP, USD, EUR): ").strip().upper()
    
    req_inter = input("¿La Tasa Base de Referencia requiere ser calculada mediante interpolación lineal? (s/n): ").strip().lower()
    datos_interpolacion = None
    
    if req_inter == 's':
        plazo_obj = float(input("  Ingrese el plazo objetivo a interpolar (Ej. 3 para 3 años): "))
        p1 = float(input("  Ingrese el plazo inferior más cercano disponible (Ej. 2): "))
        t1 = float(input(f"  Ingrese la tasa para el plazo de {p1} años (%): "))
        p2 = float(input("  Ingrese el plazo superior más cercano disponible (Ej. 5): "))
        t2 = float(input(f"  Ingrese la tasa para el plazo de {p2} años (%): "))
        
        tasa_base = t1 + (plazo_obj - p1) * ((t2 - t1) / (p2 - p1))
        print(f"\n=> Tasa interpolada calculada a {plazo_obj} años: {tasa_base:.4f}%")
        datos_interpolacion = {
            "plazo_obj": plazo_obj, "p1": p1, "t1": t1, "p2": p2, "t2": t2
        }
    else:
        tasa_base = None
        while tasa_base is None:
            try:
                tasa_base = float(input(f"Ingrese la Tasa Base de Referencia actual en {moneda} (%) [Ej. 5.5]: "))
            except ValueError:
                print("Ingrese un número válido.")
            
    try:
        num_deudas = int(input("¿Cuántas deudas vigentes desea utilizar para calcular el Spread de Riesgo Ponderado?: "))
    except ValueError:
        num_deudas = 0
        
    deudas = []
    suma_capital = 0.0
    suma_ponderada = 0.0
    
    for i in range(num_deudas):
        print(f"\nDeuda {i+1}:")
        try:
            capital = float(input("  Monto Capital: "))
            tasa_deuda = float(input("  Tasa de la Deuda (%) [Ej. 6.0]: "))
            tasa_ref_hist = float(input("  Tasa Ref. Histórica al momento de tomar la deuda (%) [Ej. 4.0]: "))
            
            deudas.append({
                "capital": capital,
                "tasa_deuda": tasa_deuda,
                "tasa_ref_hist": tasa_ref_hist
            })
            
            spread_individual = tasa_deuda - tasa_ref_hist
            suma_capital += capital
            suma_ponderada += (spread_individual * capital)
            
        except ValueError:
            print("Error en los datos ingresados. Saltando esta deuda...")
            
    spread_ponderado = 0.0
    if suma_capital > 0:
        spread_ponderado = suma_ponderada / suma_capital
        
    ibr_final = tasa_base + spread_ponderado
    
    print("\n" + "="*60)
    print(" RESULTADOS ")
    print("="*60)
    print(f"Moneda: {moneda}")
    print(f"Tasa Base de Referencia: {tasa_base:.4f}%")
    print(f"Spread de Riesgo Ponderado: {spread_ponderado:.4f}%")
    print(f"Tasa IBR Anual Final: {ibr_final:.4f}%")
    print("="*60)
    
    generar_reporte(moneda, tasa_base, deudas, spread_ponderado, ibr_final, suma_capital, datos_interpolacion)

def generar_reporte(moneda, tasa_base, deudas, spread_ponderado, ibr_final, suma_capital, datos_interpolacion):
    nombre_analisis = input("\nIngrese un nombre o identificador para este análisis (ej. Contrato Oficina Central): ").strip()
    if not nombre_analisis:
        nombre_analisis = "Analisis_IBR"
        
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nombre_archivo = f"Reporte_IBR_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write("====================================================\n")
        f.write(" MEMORIA DE CÁLCULO - TASA DE DESCUENTO (IFRS 16)\n")
        f.write("====================================================\n")
        f.write(f"Nombre del Análisis: {nombre_analisis}\n")
        f.write(f"Fecha de Generación: {fecha_actual}\n\n")
        
        f.write("--- JUSTIFICACIÓN TÉCNICA ---\n")
        f.write("De acuerdo con la NIIF 16 (párrafo 26), al no poder determinarse fácilmente la tasa de interés\n")
        f.write("implícita en el arrendamiento (debido a la carencia de datos exactos del arrendador como su valor\n")
        f.write("residual no garantizado y costos directos iniciales), el arrendatario debe utilizar de forma mandataria\n")
        f.write("su Tasa Incremental por Préstamos (Incremental Borrowing Rate - IBR).\n\n")
        
        f.write("--- CÁLCULO DE TASA BASE (LIBRE DE RIESGO) ---\n")
        f.write(f"Moneda: {moneda}\n")
        if datos_interpolacion:
            di = datos_interpolacion
            f.write(f"Descripción Metodológica: Se utilizó el método de Interpolación Lineal para determinar la tasa exacta a {di['plazo_obj']} años,\n")
            f.write("dado que no existía una tasa de mercado observable para ese plazo exacto en la curva de rendimientos del mercado.\n")
            f.write("Fórmula aplicada:\n")
            f.write("  Tasa Interpolada (Y) = Y1 + (X - X1) * [ (Y2 - Y1) / (X2 - X1) ]\n")
            f.write("Donde:\n")
            f.write(f"  - X  (Plazo Objetivo) = {di['plazo_obj']} años\n")
            f.write(f"  - X1 (Plazo Inferior) = {di['p1']} años  -> Y1 (Tasa Inferior) = {di['t1']:.4f}%\n")
            f.write(f"  - X2 (Plazo Superior) = {di['p2']} años  -> Y2 (Tasa Superior) = {di['t2']:.4f}%\n")
            f.write(f"Desarrollo Matemático:\n")
            f.write(f"  Tasa = {di['t1']:.4f} + ({di['plazo_obj']} - {di['p1']}) * [ ({di['t2']:.4f} - {di['t1']:.4f}) / ({di['p2']} - {di['p1']}) ]\n")
            f.write(f"Tasa Base Resultante: {tasa_base:.4f}%\n\n")
        else:
            f.write(f"Tasa Libre de Riesgo / Referencia Actual: {tasa_base:.4f}%\n")
            f.write("Descripción: Tasa de referencia observable directamente en el mercado para el plazo del contrato.\n\n")
        
        f.write("--- CÁLCULO DE SPREAD DE RIESGO PONDERADO ---\n")
        if not deudas:
            f.write("No se ingresaron deudas referenciales. El spread asumido es 0.0000%.\n")
        else:
            f.write(f"Capital Total Ponderado: {suma_capital:,.2f}\n")
            f.write("Detalle de Deudas Vigentes:\n")
            for i, d in enumerate(deudas):
                f.write(f"  Deuda {i+1}:\n")
                f.write(f"    - Capital: {d['capital']:,.2f}\n")
                f.write(f"    - Tasa de la Deuda: {d['tasa_deuda']:.4f}%\n")
                f.write(f"    - Tasa de Referencia Histórica: {d['tasa_ref_hist']:.4f}%\n")
                f.write(f"    => Spread Individual: {(d['tasa_deuda'] - d['tasa_ref_hist']):.4f}%\n\n")
                
            f.write("Descripción Metodológica:\n")
            f.write("El Spread de Riesgo Ponderado refleja la prima de riesgo crediticio (Credit Spread) específica de la entidad.\n")
            f.write("Se calcula determinando el diferencial histórico de las deudas vigentes (Tasa de Deuda vs. Tasa Libre de\n")
            f.write("Riesgo a la fecha de emisión) y ponderando dicho diferencial por la proporción de capital de cada deuda sobre el total.\n\n")
            f.write("Fórmula aplicada:\n")
            f.write("Spread Ponderado = Σ [ (Tasa Deuda_i - Tasa Ref Histórica_i) * (Capital_i / Capital Total) ]\n\n")
            f.write(f"Resultado Spread Ponderado: {spread_ponderado:.4f}%\n\n")
            
        f.write("--- TASA FINAL APLICABLE ---\n")
        f.write("Fórmula: Tasa IBR = Tasa Base Actual + Spread Ponderado\n")
        f.write(f"TASA IBR ANUAL FINAL: {ibr_final:.4f}%\n")
        f.write("====================================================\n")
        f.write("Fin del Reporte.\n")
        
    print(f"\n[OK] Reporte generado exitosamente: {os.path.abspath(nombre_archivo)}")

if __name__ == '__main__':
    mostrar_definiciones()
    diagnostico_inicial()
    calcular_ibr()
