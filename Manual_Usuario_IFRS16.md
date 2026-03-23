# Manual de Usuario: Sistema IFRS 16 Pro

¡Bienvenido al **Sistema IFRS 16 Pro**! Este manual está diseñado paso a paso para que cualquier persona, sin importar su experiencia técnica, pueda cargar contratos, gestionar tipos de cambio y generar los reportes financieros exigidos por la norma NIIF 16 (IFRS 16).

---

## 🛑 REGLA DE ORO ANTES DE EMPEZAR
**NUNCA cargues un contrato sin haber cargado antes las monedas (UF, USD, EUR, etc.).** 
El sistema necesita saber cuánto vale la moneda **exactamente el día que inicia tu contrato**. Si subes el contrato y el sistema no encuentra la moneda de ese día, registrará un valor de cero y el cálculo fallará. 

**Orden estricto de uso:**
1. Cargar Monedas.
2. Cargar Contratos.
3. Generar Reportes.

---

## Módulo 1: 💱 Monedas (Tipos de Cambio)
Aquí le enseñamos al sistema a cuánto estaban las divisas en el pasado y en el presente.

1. Ve a la pestaña **Monedas**.
2. Tienes dos opciones principales:
   - **Carga Manual:** Útil para agregar el valor de la UF o el Dólar de un solo día en particular. Solo eliges la fecha, la moneda y escribes su valor en pesos (CLP).
   - **Carga Masiva (Recomendado):** Útil para subir toda la historia.
     * Haz clic en **"Descargar Plantilla"**.
     * Abre el Excel y pega tus fechas, la moneda (ej. "UF") y el valor.
     * Guarda el archivo, arrástralo al recuadro de la pantalla.
     * Presiona **"Cargar Tipos de Cambio"**.
3. Revisa en la pestaña **"Ver Todos los Datos"** que tu historial de monedas esté correctamente listado.

---

## Módulo 2: 📝 Contratos (Arrendamientos)
Aquí es donde registras todos los alquileres de oficinas, vehículos, maquinaria, etc.

1. Ve a la pestaña **Contratos**.
2. Elige cómo subir tu información:
   - **Carga Manual:** Para ingresar un solo contrato rápido. Llenas el formulario (Empresa, Nombre, Canon mensual/semestral, Tasa Anual, Fechas, Frecuencia, etc.) y guardas.
   - **Carga Masiva (Recomendado para todo tu portafolio):**
     * Descarga la **"Plantilla con Ejemplos"**.
     * Llena el Excel respetando EXACTAMENTE las palabras que el sistema espera (ejemplo: escribe `Vencido` o `Anticipado` sin espacios en blanco al final. En frecuencia usa `Mensual`, `Semestral`, `Anual`, etc.).
     * La **Tasa Anual %** debe ir en número decimal o entero puro (ej. Si es 6%, en el Excel pones `6` o `0.06` según el formato).
     * Arrastra el Excel al sistema y presiona procesar. El sistema verificará que no haya errores matemáticos antes de guardar nada.
3. **Modificación de Contrato:** Si renegociaste un canon o el plazo cambió, usa esta pestaña. Eliges la nueva fecha y tasa, y el sistema cerrará el cálculo viejo y creará automáticamente el asiento de "Remedición" IFRS 16.
4. **Baja Anticipada:** Si devuelves la oficina o vehículo antes de tiempo, usa esta opción para detener la depreciación y los intereses para los siguientes meses.

---

## Módulo 3: 🧮 Panel de Saldos (Dashboard)
El corazón del sistema. Aquí ves los resultados financieros mes a mes, listos para tu Centralización Contable.

1. Entra a **Panel de Saldos**.
2. Filtra por la **Empresa** que quieres analizar, el **Mes** y el **Año** de cierre.
3. Haz clic en **"Generar Resumen de Saldos"**.
4. ¡Magia! El sistema procesará las fórmulas complejas de valor presente y devengo para todos tus activos en segundos.
5. Verás dos pestañas:
   - **Resumen Consolidado:** Los totales agrupados por empresa listos para tu Balance General (Activo ROU, Pasivo Corriente y Pasivo No Corriente, Depreciación Acumulada ROU). 
   - **Detalle por Contrato:** Muestra línea por línea cada contrato. Aquí auditarás el **Valor Presente** exacto, tu **Tasa Anual %** real, e incluye una columna llamada **"Cuotas de Pago (VA)"** que te confirmará exactamente cuántos desembolsos físicos de caja proyectó el motor (ej. 30 cuotas semestrales para 15 años).
6. **Boton de Descarga:** Genera Excel consolidado o detallado para armar tus asientos contables en tu ERP.

---

## Módulo 4: 📊 Notas a los Estados Financieros (Vencimientos)
Los auditores o la gerencia siempre piden la nota de "Riesgo de Liquidez" exigida por IFRS 7. Este módulo la genera lista para imprimir.

1. Ve a **Notas a los Estados Financieros**.
2. Elige el mes y año de cierre, además de la empresa.
3. Haz clic en **Generar Pasivos No Descontados**.
4. El sistema agrupará toda la plata bruta (flujos nominales de caja reales sin contar Tasa de Descuento ni Valor Presente) que vas a tener que pagar en los próximos meses y años.
5. Los distribuirá matemáticamente en baldes de tiempo requeridos por norma: *Menos de 90 días, Entre 90 días y 1 año, 2 a 3 años, 4 a 7 años, etc.*
6. Úsalo directamente para pegar la tabla (que está en Millones de Pesos - M$) en tu estado financiero dictaminado.

---

## Anexo: Preguntas Frecuentes (FAQ)

**¿Qué pasa si mi frecuencia no es mensual?**
El sistema es inteligente. Si tu contrato dice "Semestral" y "Anticipado", el motor solo aplicará pagos de salida de caja cada 6 meses (justo al inicio de tu semestre). Sin embargo, mes a mes SÍ devengará y registrará la porción exigible de "gasto de interés" para tu contabilidad en sus 180 meses teóricos.

**¿Qué hago si me equivoqué de Tasa o Canon al subir el Excel?**
Ve a "Modificación de Contrato" y registra la fecha de inicio histórica original, luego coloca la nueva tasa o canon. El sistema hará el empalme matemático perfecto. No uses esto si el contrato aún no ha arrancado (en ese caso es mejor darlo de baja o pedir a soporte eliminarlo para cargarlo de nuevo limpio).

**Mis Tasas aparecían como 0 en el panel final, ¿se borraron?**
No, el sistema visual de reportes a veces resume los decimales por estética, pero en tu descarga de Excel todas tus tasas de `0.045%` aparecerán intactas para tu escuadre.

---
*Fin del Manual.*
