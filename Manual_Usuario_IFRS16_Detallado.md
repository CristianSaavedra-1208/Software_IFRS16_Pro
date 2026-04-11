# Manual de Usuario Integral: Sistema IFRS 16 Pro

¡Bienvenido al **Sistema IFRS 16 Pro**! La solución tecnológica corporativa para la gestión de arrendamientos bajo la Norma Internacional de Información Financiera 16 (NIIF 16), ahora con identidad visual corporativa avanzada (Estilo Mundo) y capacidades de integración nativas.

Este manual está diseñado **paso a paso**, para guiar tanto al usuario principiante como al analista o ingeniero que requiere explotar todo el potencial analítico y contable del sistema.

---

## 🌟 1. ¿Qué hace el software y cuál es su lógica? (Arquitectura Multi-Compañía)

El **Sistema IFRS 16 Pro** es un motor diseñado para operar bajo una arquitectura **multi-compañía**, permitiendo gestionar el portafolio de un holding con decenas de filiales en un solo lugar.

**Capacidades Clave:**
- **Consolidación vs Detalle:** Emita reportes resumidos que sumen todas las filiales ("Todas"), o filtre para auditar una sola compañía (ej. "Holdco" o "Pacifico").
- **Motor Financiero Acelerado Cache-V21:** El cerebro del software proyecta el futuro y reconstruye el pasado. Al darle los datos, el sistema construirá la tabla inmutable de **amortización, pago y devengo** en fracciones de segundo, gracias a su nuevo sistema de procesamiento masivo en memoria (Caché O(1)).
- **Contabilidad Multimoneda en Tiempo Real (NIC 21):** Valora sus pasivos al cierre de cada mes, generando automáticamente los ajustes de tipo de cambio contra la moneda funcional.
- **Interfaz Corporativa "Mundo":** La plataforma ha sido diseñada con ergonomía visual corporativa (tipografía Montserrat, tabs tipo toggle y un esquema de sombreado de tarjetas) para una experiencia premium.

---

## 🛑 2. REGLA DE ORO OPERATIVA: EL ORDEN DE CARGA

Si no sigue este orden estricto de pasos 1-2-3, los cálculos matemáticos contendrán errores por saltos de tipo de cambio.

**Secuencia de Uso Paso a Paso:**
1. **Paso 1:** Configurar en el "Módulo Configuración" empresas, parámetros, credenciales de ERP y la auditoría.
2. **Paso 2:** Cargar en el "Módulo Monedas" los tipos de cambio de la divisa de sus contratos.
3. **Paso 3:** Ingresar al "Módulo Contratos" y crear o cargar su base de datos de arrendamientos.
4. **Paso 4:** Generar asientos contables y transferirlos directo a su ERP.

---

## 🧩 3. Guía Paso a Paso de Todos los Módulos

### ⚙️ Módulo A: Configuración del Sistema (Centro de Mando)
Este módulo es utilizado por Administradores y/o el **Ingeniero IT** (rol restringido). Posee pestañas críticas:

* **Usuarios:** Creación de accesos con roles estrictos (Administrador, Analista, Auditor Lector, Ingeniero IT). *Nota: El Ing. IT solo tiene acceso a las Integraciones ERP.*
* **Empresas, Monedas y Clases:** Parametrización básica de las listas desplegables.
* **Campos Extra y Frecuencias:** Agregue frecuencias personalizadas (ej. `"Cuatrimestral-4"`) o columnas adicionales de información a los contratos (ej. "Centro de Costo").
* **Cuentas Contables:** Ruté todo el plan de cuentas IFRS 16 según los códigos internos de su contabilidad corporativa.
* **Integraciones ERP (Avanzado):** **¡Nueva Funcionalidad!** Conecte el sistema a **Odoo** (vía XML-RPC) o configure SAP S/4HANA / Dynamics 365. El sistema guardará la URL, base de datos y llaves de acceso encriptadas para empujar asientos de forma automatizada.
* **Bitácora de Auditoría:** Permite al Administrador encender el rastreo perpetuo del sistema. Si está activo, el sistema anotará cada vez que un usuario Ingrese, Elimine, o Remedie (modifique) un contrato, generando un visor de Logs estricto para revisión.
* **Mantenimiento BD:** Botones destructivos para borrar contratos o monedas.

---

### 💱 Módulo B: Monedas (Alimentando el Tipo de Cambio)
Para evitar que se calcule 1 a 1, cargue los valores UF o USD históricos.
* Recomendamos usar **"Descargar Plantilla"** en la carga Masiva, rellenar el histórico `YYYY-MM-DD` y cargar los cientos de días en menos de un segundo.

---

### 📝 Módulo C: Contratos (Dando Vida a los Activos)
Ingrese los términos comerciales. Las cuotas, la Tasa de Descuento (IBR) y las frecuencias de pago.
* **Baja:** Cese un contrato antes de la fecha final original y detenga todos los flujos.
* **Modificación/Remedición Individual o Masiva:** Reajuste el Canon por inflación o varíe la duración. El sistema calculará el delta (Ajuste ROU / Pasivo) inyectando la corrección contable sin arruinar los registros del pasado. Puede descargar la *Plantilla de Modificaciones Masivas* para actualizar 500 contratos en un solo clic.

---

### 🧮 Generación de Reportes Financieros

#### D: Panel de Saldos (Dashboard)
Responde: *¿Cuánta deuda y activos tengo hoy?* Generado a velocidades sub-segundo. Separa automáticamente la porción Corriente (12 meses) de la No Corriente basándose en los flujos matemáticos futuros. 

#### E: Registros Contables (Asientos) y Conexión Automática a Odoo
El gran Libro Diario.
* Cruza toda la información del ROU, Intereses, Amortizaciones y Diferencias de Cambio (NIC 21 purificada) en **7 transacciones estándar**.
* Cuenta con los símbolos algebraicos correctos (negativos para pagos de pasivo) permitiendo una fácil lectura de T-Accounts.
* **Conexión ERP Activa:** Si el módulo de Integraciones ERP (Odoo) fue configurado, aparecerá un botón clave: **"Enviar a [Nombre ERP] mediante API"**. Al presionarlo, el sistema conectará por XML-RPC, validará las cuentas contables, y empujará todos los registros generados mes a mes como un **Borrador Contable Original** en el software contable destino.

#### F: Movimientos de Saldos (Estructura en cascada)
Muestra visualmente la formula YTD: `[Saldo Inicial] + [Adiciones] + [Intereses] - [Pago Pagos Capital/Intereses] + [Ajustes FX] = Saldos Finales`. Ideal para cuadrar la "variación" del balance de comprobación.

#### G: Notas a los Estados Financieros (Liquidez)
Exigencia de la norma NIIF 7. Organiza todos los flujos nominales (sin tasa de descuento) según su exigibilidad ("Menos de 90 Días", "1 a 3 Años", etc.). Su motor optimizado agrupa las remediciones para procesar enormes portafolios sin cuellos de botella (N+1 queries eliminadas).

---

### 🔍 Módulos Analíticos Avanzados

#### H: Auditoría y Transparencia
* Descargue el archivo de base de datos `.db` puro, o investigue las fórmulas teóricas oficiales de cálculo de devengo e IFRS 16. La "Caja Negra" no existe en este software.

#### I: Asistente de Cálculos de Tasas (IBR / Implícita)
¿No sabe qué tasa ponerle a un nuevo contrato? 
* **Calculadora de Tasa Implícita:** Ingrese el Valor Razonable, la Cuota y Valores Residuales. El sistema hallará la iteración matemática exacta, emitiendo una **Memoria de Cálculo Formal en Word** para sus archivos legales.
* **Calculadora IBR:** Cargue la deuda histórica de su empresa usando bonos del Banco Central o US Treasury como base, y el sistema descubrirá su **Spread Ponderado de Riesgo**, revelando científicamente la tasa de descuento óptima y justificable bajo NIIF 16.
* **Calculadora Valor Presente:** Simule cualquier cuota en forma Vencida o Anticipada, y exporte el cuadro de pago a Excel al instante.

---

> **Soporte y Garantía:** Este manual ha sido actualizado para reflejar la versión definitiva del IFRS 16 Pro (Conexiones API, Optimización Caché, Identidad Mundo y Control de Auditoría Activos). Ante cualquier duda funcional, refiérase a su consultor financiero interno.
