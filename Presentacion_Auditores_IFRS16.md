# Validación Técnica del Motor Financiero IFRS 16
**Documento dirigido a Auditores Externos y Revisores de Cumplimiento Normativo**

Este documento detalla la arquitectura, metodología de cálculo y el entorno de control interno implementado en el sistema *Mundo 16*, demostrando su estricto apego y cumplimiento a la normativa contable **NIIF 16 (Arrendamientos)** y su interacción con la **NIC 21 (Efectos de las Variaciones en las Tasas de Cambio de la Moneda Extranjera)**.

---

## 1. Alcance y Objetivos de la Plataforma
El software automatiza el ciclo de vida contable completo de los arrendamientos donde la compañía actúa como arrendatario:
- **Reconocimiento y Medición Inicial.**
- **Medición Posterior (Devengo de intereses, pagos de capital y amortización).**
- **Remediciones, Modificaciones y Terminos Anticipados de Contrato.**
- **Manejo Multidivisa (CLP, UF, USD, EUR) y Cuadratura Contable Dúplex.**

---

## 2. Metodología de Cálculo y Reconocimiento Inicial
El motor financiero (implementado vectorialmente vía Pandas/NumPy para exactitud al céntimo) construye el pasivo y el activo por derecho de uso al inicio del contrato.

### A. Reconocimiento del Pasivo por Arrendamiento (NIIF 16 - Párrafo 26)
El sistema calcula el Valor Presente (VP) de los pagos de arrendamiento no pagados en la fecha de comienzo.
- **Fórmula Base (Flujo de Caja Descontado):** Utiliza la tasa incremental por préstamos (Tasa Mensual Equivalente) ingresada por el usuario.
- **Pagos Fijos y en Esencia Fijos:** Proyectados sobre el Plazo de Arrendamiento (incluyendo opciones de prolongación o terminación con certeza razonable).
- **Periodicidad y Modelamiento:** Evalúa cuotas bajo modalidad lógica de *Pago Anticipado* (descuento $t$) o *Pago Vencido* (descuento $t-1$).

### B. Reconocimiento del Activo por Derecho de Uso (ROU) (NIIF 16 - Párrafo 24)
La medición inicial de la partida del activo (ROU) incorpora los componentes requeridos:
> **Costo ROU** = *Valor Presente del Pasivo* + *Pagos de Arrendamientos Anticipados* + *Costos Directos Iniciales* + *Costos de Desmantelamiento y Restauración* - *Incentivos Recibidos* + *Ajustes Manuales de ROU (si aplica)*

---

## 3. Medición Posterior
La proyección a lo largo del tiempo se genera mensualmente usando el método del interés efectivo.

### A. Pasivo por Arrendamiento
Se mide incrementando el valor en libros para reflejar el interés y reduciendo el saldo por los cánones o cuotas de arrendamiento realizadas.
- **Ecuación Contable:** `Saldo_Final = Saldo_Inicial + Interés - Pago_Período`
- **Ajuste Centesimal Obligatorio (Plug):** En la última cuota, el algoritmo empuja el delta o residuo decimal contra la cuota de capital, forzando matemáticamente que el valor residual del pasivo sea exactamente `0.00`. Este blindaje evita descuadraturas residuales arrastradas al cierre.

### B. Depreciación del Activo ROU
El activo se amortiza de manera sistemática:
- **Modelo Base:** El sistema amortiza en *línea recta* durante el plazo de arrendamiento (desde el mes 1 hasta la fecha de fin o de ejercer la opción).
- **Cálculo de Cuota:** `Valor Neto a Amortizar / Plazo Restante Vigente`.

---

## 4. Remediciones y Modificaciones de Contratos (NIIF 16 - Párrafos 39 a 46)
Cualquier evento que altere la estructura original (Renegociaciones, prórrogas, ajustes por IPC superior al esperado, aumentos/disminuciones de metraje) se traza como un bloque de Remedición, originando correcciones prospectivas (hacia adelante).

### A. Ajuste de Cánones o Modificación en Plazos
Se recalcula un Nuevo Valor Presente para los flujos restantes desde la "Fecha de Remedición" a la nueva tasa de descuento.
- **Ajuste ROU:** La diferencia entre el `Nuevo Pasivo` vs `Antiguo Pasivo` en CLP se carga o abona exactamente al Activo ROU correspondiente (No pasa por Estado de Resultados P&L).

### B. Terminaciones Parciales y Modificaciones Decrecientes
Si el espacio arrendado o el plazo original son reducidos abruptamente debido a una cancelación sobre porciones del ROU:
1. Se decrementan equitativamente el Pasivo Arrendamiento y el Activo ROU.
2. Si el cálculo en Moneda Base (ej. CLP a la fecha de modificación) revela un diferencial entre los montos reducidos de Pasivos y Activos ROU, **el diferencial es reconocido en Estado de Resultados P&L** explícitamente a través del generador automático de asientos contables.

---

## 5. Exigencias Multimoneda e Interacciones Transversales NIC 21
Para evitar distorsiones con divisas fluctuantes (USD, EUR) y la unidad de fomento (UF), se asegura la división contable en **Activos No Monetarios** contra **Pasivos Monetarios**.

- **Cuentas de Pasivos Monetarios (Obligación de pago):** El saldo acreedor se actualiza y consolida mes a mes con la **Tasa de Cierre (spot)** de la fecha actual de los estados financieros. Esta evolución monetaria liquida el ajuste como "Diferencia de Cambio" o "Restatement de Indexación" al P&L (Cuenta Resultado).
- **Activo ROU No Monetario (Costo Histórico Bloqueado):** El momento del alta inicial fija la valoración usando la tasa "TC Inicial" del contrato. La amortización y del saldo en libros continúan reflejándose irrevocablemente a **valor costo histórico**, en la moneda funcional, sin sufrir el vaivén del TC.

*(El sistema previene errores de offset del Tipo de Cambio usando el TC exacto correlacionado al mes de arranque en la primera cuota amortizada).*

---

## 6. Generación de Cierres Contables e Integridad Relacional
El módulo de "Asientos Contables" procesa mensualmente la información para volcarla al ERP, validando una *Estructura Doble (Partida Doble)* en todos sus asientos. El set de asientos es el siguiente:
- **1. Reconocimiento Inicial:** `ROU (Debe) contra Pasivo (Haber) + Plug Cuenta Ajuste/Banco`
- **2. Depreciación:** `Gasto Amortización ROU (Debe) contra Amortización Acumulada ROU (Haber)` *medida enteramente al Costo Histórico*.
- **3. Pagos / Intereses:** `Pasivo / Interés Financiero (Debe) contra Bancos, Acreedores o Caja (Haber)`. *Calculado a la spot TC actual*.
- **4. Diferencia de Variación Cambiaria (IFRS/NIC21):** El algoritmo cuadra las diferencias y ubica el diferencial contable a cuentas de ganancia por TC o perdidas por TC mes a mes de forma consolidada, sumando o restando el Pasivo.

---

## 7. Módulo de Trazabilidad y Bitácora de Auditoría Fuerte
Finalmente, la plataforma ha sido estructurada a nivel back-end con un sistema Opt-in de auditorías para asegurar el control de cambios en la matriz financiera.
- **Log Inmutable SQLite:** Toda alteración a los parámetros bases (Inicio, Fin, Tasas, montos, plazos) es serializada, indexada por usuario local o PC subyacente y con timbraje de hora `Timestamp`. 
- **Verificabilidad Ex-Post (Test of Controls):** Los auditores e inspectores podrán auditar directamente en el panel histórico cualquier rastro desde la modificación de valores base hasta el borrado de contratos o la creación de notas finales.

---
*Fin Documento Orientativo*
