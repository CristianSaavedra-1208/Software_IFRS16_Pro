# Manual de Usuario Integral: Sistema IFRS 16 Pro

¡Bienvenido al **Sistema IFRS 16 Pro**! La solución tecnológica definitiva y de vanguardia para la gestión corporativa de arrendamientos bajo la Norma Internacional de Información Financiera 16 (NIIF 16).

Este manual está diseñado **paso a paso**, para guiar tanto al usuario principiante sin conocimientos previos del software, como al analista financiero avanzado que requiere explotar todo el potencial analítico y contable del sistema.

---

## 🌟 1. ¿Qué hace el software y cuál es su lógica? (Arquitectura Multi-Compañía)

El **Sistema IFRS 16 Pro** no es solo una calculadora; es un motor diseñado para operar bajo una arquitectura **multi-compañía**. Esto significa que puede gestionar el portafolio completo de arrendamientos de un **grupo empresarial holding** con decenas de filiales en un solo lugar.

**Capacidades Clave:**
- **Consolidación vs Detalle:** Podrá emitir reportes resumidos que sumen los pasivos de todas las filiales ("Todas"), o filtrar los reportes dinámicamente para auditar el estado de los arriendos de una sola compañía (ej. "Holdco" o "Pacifico") a la fecha exacta que usted desee.
- **Motor Financiero V21.0:** El cerebro del software proyecta el futuro y reconstruye el pasado. Al darle el valor del contrato, el plazo y la tasa de interés, el sistema descontará todos los flujos a su **Valor Presente (Pasivo)**, calculará el **Activo por Derecho de Uso (ROU)**, y construirá la tabla inmutable de **amortización, pago y devengo por intereses** para la vida completa de cientos de contratos simultáneos en pocos segundos.
- **Contabilidad Multimoneda en Tiempo Real (NIC 21):** El motor lee diariamente los tipos de cambio (UF, USD, EUR) y valora sus pasivos al cierre de cada mes, generando automáticamente los ajustes y diferencias de cambio contra la moneda funcional.

---

## 🛑 2. REGLA DE ORO OPERATIVA: EL ORDEN DE CARGA

Si no sigue este orden estricto de pasos 1-2-3, los cálculos matemáticos contendrán errores. Un contrato recién firmado necesita saber a cuánto equivale su moneda en la fecha que nació.

**Secuencia de Uso Paso a Paso:**
1. **Paso 1:** Configurar en el "Módulo Configuración" las empresas, nuevas monedas extra, y campos libres que su negocio requiera (ej. El número de Patente de los vehículos).
2. **Paso 2:** Cargar en el "Módulo Monedas" el tipo de cambio del mes en curso y de los meses anteriores necesarios de la divisa de sus contratos.
3. **Paso 3:** Una vez la moneda está cargada, ingresar al "Módulo Contratos" y crear su base de datos de arrendamientos.
4. **Paso 4:** Generar asientos contables, paneles de control y notas a los estados financieros.

---

## 🧩 3. Guía Paso a Paso de Todos los Módulos

Descubra cada área de trabajo a la que podrá acceder desde el menú principal del sistema.

### ⚙️ Módulo A: Configuración del Sistema (El Centro de Mando)
Este módulo se encuentra en el área de `"Configuración del Sistema"` y es utilizado al momento de arrancar el software por primera vez o ante cambios estructurales en el Holding. Solo el **Administrador o Ing. IT** deberían manipularlo frecuentemente. Posee varias pestañas internas:

* **Usuarios:** Creación de accesos al sistema con roles estrictos (Lectura, Edición, Admin).
* **Empresas:** Cuadro de texto donde puede escribir "Empresa XYZ Holding" y presionar "Agregar Empresa". Esto le activará el filtro de buscar a esa empresa en todos los reportes del sistema.
* **Monedas:** Puede digitar cualquier moneda internacional (ej. "GBP", "JPY", "MXN") y el sistema la registrará globalmente.
* **Campos Extra y Frecuencias:** ¡El software es completamente flexible! 
  * ¿En su empresa arriendan cosas que se pagan cada 4 meses? Escriba `"Cuatrimestral-4"` en "Nueva Frecuencia" para enseñarle al motor esa lógica financiera.
  * ¿Necesita llevar control de las patentes o de los centros de costo en sus reportes? En "*Campos Adicionales*", digite "Centro de Costo" y presione "Crear Campo". Automáticamente el módulo de Contratos empezará a solicitar este campo cada vez que agregue un nuevo alquiler.
* **Clases de Activo:** Para ordenar en sus reportes, agregue agrupaciones como "Flota de Buses", "Sucursales Norte", "Datacenters".
* **Cuentas Contables:** Aquí usted asigna cómo contablemente se reconoce el activo/pasivo. Escriba el _N° de Cuenta_ y _Nombre de Cuenta_ según su Plan de Cuentas interno corporativo (Ej: Cuenta Banco Pago -> "1102 - Cta. Corriente Santander"). Cada "Asiento" usará exactamente las cuentas que registre aquí.
* **Integraciones ERP (Avanzado):** Permite conectar y guardar credenciales directas a las APIs contables de SAP S/4HANA, Odoo, Dynamics 365 o Oracle NetSuite.
* **Mantenimiento BD:** **¡Boton de Peligro!** Incluye botones rojos destructivos para borrar todos los contratos o borrar todas las monedas de un solo golpe. Úselo si cometió un error masivo durante el primer uso.

---

### 💱 Módulo B: Monedas (Alimentando el Tipo de Cambio)
El motor necesita los valores diarios. Sin esto, todo valdrá 1 CLP.

**Paso a Paso - Pestaña Carga Manual:**
1. Seleccione en el calendario la *"Fecha"* que desea guardar.
2. En la lista *"Moneda"*, elija "UF", "USD", u otra.
3. En el cuadro numérico *"Valor CLP"*, ingrese el equivalente en pesos, por ejemplo: `39450.50`, y presione **"Guardar Moneda"**.

**Paso a Paso - Pestaña Carga Masiva (Recomendado):**
1. Haga clic en **"Descargar Plantilla"**. Se guardará un Excel llamado *plantilla_monedas.xlsx*.
2. Ábralo, y rellene las tres columnas hacia abajo para mil o más días (Fecha, Moneda, Valor). Use formato `YYYY-MM-DD` para las fechas (ej. `2026-03-31`).
3. Arrastre ese Excel de vuelta al bloque de pantalla y presione **"Cargar Tipos de Cambio"**. El software asimilará todo el historial en un segundo.

**Ver Todos los Datos:** Pestaña auditable para revisar lista, con opción a descarga.

---

### 📝 Módulo C: Contratos (Dando Vida a los Activos)
Usted ingresa aquí los términos comerciales.

**Paso a Paso - Pestaña Carga Manual:**
Aparecerá un formulario completo. ¿Para qué sirve cada cuadro?
* **Empresa / Clase:** Seleccione a qué filial del holding pertenece el contrato y bajo qué grupo (Oficinas, Bodegas).
* **Nombre / ID / Proveedor:** Digite la identificación de su proveedor, su RUT y un nombre que le de la pista de lo que arrendó (Ej. "Arriendo Planta Cerrillos").
* **Canon:** El valor de "la cuota" pactada en el contrato. Por ejemplo `150.5`.
* **Moneda:** En qué divisa se paga el Canon (ej. UF o USD).
* **Frecuencia Pagos:** Especifique si el canon acordado se debe tributar de forma Mensual, Semestral, Anual, etc.
* **Tasa Anual %:** Tasa de Descuento comercial pactada o Tasa Incremental de Endeudamiento (IBR) del arrendatario. Debe ser un número (Ej. `6.5`).
* **Fechas (Inicio y Fin):** Escoja el día en que la empresa pudo empezar a utilizar el activo (Inicio) y el día donde por escrito se debe devolver (Fin).
* **Tipo de Pago:** *Vencido* (paga al final de cada periodo). *Anticipado* (paga al primer día hábil del inicio del periodo). Esto cambia drásticamente la matemática de los intereses.
* Botón **"Registrar"**: El sistema creará internamente de manera perpetua cada amortización e interés al cliquear aquí.

*Nota Comercial:* En `"Carga Masiva"` se sigue exactamente la misma lógica de campos, con un Excel. ¡El sistema filtrará matemáticamente los Excel mal rellenados para proteger su Base de Datos de errores!

**Pestañas: Modificación de Contrato, Baja Anticipada y Modificación Masiva:**
* **Baja:** Si devuelve un vehículo a la automotora 2 años antes, selecciónelo del menú, marque la "Fecha Efectiva de Baja", y la matemática futura de ese arriendo cesará por completo para siempre.
* **Modificación Individual:** Si le reajustaron el Canon a medio camino, escoja la "Fecha de Renegociación", ponga la nueva cuota, nueva tasa y nueva fecha fin, y el motor hará toda la reversa y cuadratura correspondiente mediante una "Remedición o Ajuste ROU" sin alterar la historia que ya contabilizó el año pasado.
* **Modificación Masiva:** Diseñada para ajustar docenas o cientos de contratos simultáneamente (ej. reajuste corporativo por IPC o renovación en bloque de flota).
  1. Vaya a la pestaña "Modificación Masiva" y haga clic en **"📥 Descargar Plantilla M.Masivas"**.
  2. Abra el Excel descargado. Encontrará una tabla estructurada; llene *obligatoriamente* estas 5 columnas por cada contrato que desee recalcular:
     - *ID Contrato*: El código interno exacto (Ej: `CNT-PAC-0001`).
     - *Fecha Efectiva de Registro (Modificación)*: El día exacto en que entran en rigor los nuevos valores (Ej: `2026-03-01`).
     - *Nuevo Canon*: El monto actualizado de la cuota.
     - *Nueva Tasa Anual %*: La tasa vigente al día de hoy (Ej: `6.5`).
     - *Nuevo Plazo Residual*: Cuántos meses en total le restan al contrato a partir de esta nueva Fecha Efectiva.
  3. *(Opcional)* Si su modificación es una "Reducción de Alcance" (ej. devolvió la mitad de la oficina), puede llenar opcionalmente las columnas de *Reducción de Activo ROU* y *Reducción de Pasivo Bruto* (proporcionadas en la funcionalidad de baja del sistema). El motor las calculará para cuadrar el descarte.
  4. Guarde el Excel modificado en su computador, regrese a la plataforma, arrastre el archivo al recuadro "Subir Archivo de Modificaciones" y espere la confirmación verde. ¡El sistema inyectará la remedición simultáneamente en todos los contratos y reconstruirá sus activos al instante!

---

### 🧮 Módulos de Generación de Reportes: ¿Cómo buscar la información?
Todos los siguientes módulos (Dashboard, Registros Contables, Notas a E.F. y Movimientos) comparten el mismo **Filtro Avanzado Superior** que es potentísimo:
* **Filtro de Empresa:** Desplegable donde dice "Empresa". Si elige **"Todas"**, los números se sumarán globalmente haciendo la consolidación del grupo empresarial. Si elige **"Pacifico Holding"**, sólo saldrán pasivos y activos de ella.
* **Filtro de Periodo (Mes y Año):** Seleccioné *Abril* y *2026*. El motor viajará en el tiempo; descartará mágicamente cualquier contrato nacido en *Mayo 2026*, e incluirá sólo activos vivos en la foto congelada hasta el día *30 de Abril 2026*.

#### D: Panel de Saldos (Dashboard)
Responde la pregunta: *¿Cuánta deuda y activos tengo al día hoy?*
* Al **Generar Resumen de Saldos**, visualizará la pestaña de **Resumen**. Esta presentará sumas agrupadas: separando la deuda urgente del año (Pasivo Corriente) y el de los próximos años (Pasivo No Corriente).
* La pestaña de **Detalle** revela la "vida secreta" que no ve a simple vista: *¿Cuántas cuotas he pagado a la fecha?*, *¿Cuántas cuotas reales desembolsables (VA) quedan?*, *¿Cuánto llevo Amortizado del equipo?*.

#### E: Registros Contables (Asientos)
Generador contable oficial (Libro Diario Centralizado).
* Hace crujiente la NIIF 16 por usted. Si revisa la pantalla, le dirá exactamente cuánto cargar a la Izquierda (Debe) y cuánto abonar a la Derecha (Haber).
* El sistema es detalladísimo y clasifica los movimientos de las cuentas bajo **7 transacciones puras** (ej. "Reconocimiento Inicial", "Amortización", "Pérdida por Riesgo Cambiario NIC 21", "Salida a Banco de Pago de Canon").
* Contiene botones de exportación a Excel en un formato estructurado y con cuadratura de columna "Total Pasivos", o bien cuenta con la capacidad para despachar esto por cable a su ERP.

#### F: Movimiento de Saldos (Roll-Forward de Activos y Pasivos)
Responde la pregunta del auditor: *¿Cómo pasamos de $100 de deuda en enero, a $250 en abril?*
* En la pantalla consolidada o por contrato se muestra la ruta (YTD/Acumulativa):
  `Saldo de Inicio` + `Nuevas Adiciones de Contratos` + `Intereses Producidos` - `Pagos hechos a proveedores` + `Efectos de Tipo de Cambio en Contra` = `[Saldo de Deuda Final en el Balance]`.
* Tiene un sub-tab avanzado de **"Estado de Resultados"** donde puede vaciar todo el gasto en la plantilla ER Clasificada corporativa.

#### G: Notas a los Estados Financieros (Liquidez)
Es el desglose mandatario por Ley (NIIF 7 Riesgo de Liquidez).
* Al hacer clic en **"Generar Pasivos No Descontados"**, el sistema evalúa toda la plata en la calle (flujo bruto nominal) que la compañía va a deber en toda la historia futura y la encajona ordenadamente bajo las columnas exigibles por la norma: "Hasta 90 Días", "90 días a 1 Año", "2 a 3 años", "4 a 7 años", "Más de 7 años".

---

### 🔍 Módulo H: Auditoría y Transparencia
El software rompe el paradigma de "Caja Negra" abarcando dos sub-pestañas:
1. **Fórmulas y Criterios:** Permite que cualquier analista financiero o socio auditor lea de frente en plataforma las fórmulas determinísticas (despeje de valor presente vencido vs anticipado, etc.) que fundamentan la cifra del balance.
2. **Descarga de Datos Crudos (Dumping):** Apriete el botón *"Descargar Base Completa"*. Este botón extrae todo el archivo matriz SQLite puro de manera inalterada a su computador, entregándole la verdad sagrada de su base de datos. Sirve de salvoconducto para los modelos internos de auditoría.

---

### 🧮 Módulo I: Asistente IBR (Incremental Borrowing Rate)
Es el "consultorio" técnico externo a la BD principal. Cuando la Gerencia no sabe *Qué tasa de interés Anual poner en la casilla al cargar el contrato* puede consultar esto.

**Paso a paso en Pestaña "Determinar Tasa Implícita":**
1. Recopile data extra: Exija el Valor Razonable ('Valor de Mercado del Auto/Suficiencia'), Costos de cierre, Cuota Mensual y Opción o Valor Residual estipulado legalmente por el dueño.
2. Dígite estos 4 números pesados en la pantalla en los cuadros designados.
3. Presione el potente botón de cálculo: El motor iterativo se obligará por iteraciones tipo TIR-Bisección a ubicar exactamente a qué tasa intrínseca ocultó la rentabilidad su Proveedor u Arrendador en el canon cobrado.
4. ¿Obtuvo un resultado favorable? La plataforma arrojará una Memoria Legal del Cálculo en formato físico `(*.docx)` para ser adjuntada automáticamente a las carpetas legales de su arrendamiento demostrando que bajo normativa es imposible impugnar legalmente el uso de la tasa matemática subyacente de descuento.
5. ¿Da un error por carecer de Valor residual conjeturable? Consulte inmediatamente la pestaña 2 "Determinar Tasa IBR", indicándole apoyarse en un cálculo escalable de WACC generalizado para la cartera corporativa.

---

¡Disfrute explorando esta potente solución corporativa! Ante cualquier incidente operativo que detenga los procesos, comuníquese asiduamente con su equipo de soporte IT local asignado para la herramienta.
