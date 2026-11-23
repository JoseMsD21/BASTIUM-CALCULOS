# Motor Civil: Beneficio dejado de percibir como fruto civil (Sprint 100)

## Que hace
Liquida mes a mes el fruto civil que el propietario dejo de percibir durante un periodo de privacion del
activo (acciones reivindicatorias, resolucion de contratos), segun la regla del despacho (respuesta al
"Sprint 97 (seguimiento)"): rendimiento real del activo (p. ej. canon de arrendamiento de mercado),
indexado mes a mes por IPC, menos solo los gastos ordinarios de conservacion (Art. 964 C.C.).

**No** usa la mecanica de cuota recurrente pensional (IBL x tasa de reemplazo), ni la tasa 0,0048676 de
las formulas actuariales del Sprint 97, ni el "Incremento Anual" de la plantilla X6: el despacho califico
esa mecanica como un error de derecho sustancial para esta figura.

## Componentes
- `app/engine/civil/fruto_civil.py`:
  - `calcular_fruto_civil(canon_mensual, fecha_referencia, fecha_inicial, fecha_final,
    gasto_conservacion_mensual=0, gastos_conservacion=None) -> ResultadoFrutoCivil`.
  - `GastoConservacion(fecha, monto, concepto="")`: gasto puntual por fecha.
  - `FrutoCivilMes`: detalle por mes (tramo `desde`/`hasta`, `dias`/`dias_mes`, `ipc_mes`,
    `canon_indexado_mes`, `canon_periodo`, `gastos_conservacion`, `fruto_neto`).
  - `ResultadoFrutoCivil`: `ipc_referencia`, `serie_ipc` (`MENSUAL`/`ANUAL`), `meses`, `total_canon`,
    `total_gastos_conservacion`, `total_fruto_civil`.

## Convenciones
1. **Indexacion:** `canon_mes = canon_mensual x IPC(mes) / IPC(fecha_referencia)`. `IPC(mes)` es el indice
   mensual DANE del mes (= interpolado al ultimo dia del mes); `IPC(fecha_referencia)` se interpola por
   dias dentro del mes (`get_ipc_interpolado_mensual_for_date`, Sprint 8/80). Razon pura, sin piso de
   deflacion: si la referencia es posterior a un mes del periodo, ese mes queda por debajo del canon de
   referencia.
2. **Serie:** si alguna fecha es anterior a ene-2003, todas pasan a la interpolacion anual
   (`get_ipc_interpolado_for_date`); nunca se mezclan series (criterio del Sprint 80).
3. **Periodo y prorrateo:** `fecha_inicial` y `fecha_final` inclusive; primer/ultimo mes incompletos se
   prorratean por dias calendario (`dias_privados / dias_del_mes`).
4. **Gastos de conservacion:** gasto mensual fijo (prorrateado con la misma fraccion) y/o gastos
   puntuales por fecha (completos en su mes, dentro del periodo). Valor nominal, sin indexar.
5. **Redondeo:** a centavos por mes (canon indexado del mes, canon del periodo, gastos, neto); los totales
   suman los valores redondeados. El neto mensual puede ser negativo y se muestra tal cual.

## Fuera de alcance (pendiente de confirmacion del despacho)
- Intereses sobre los frutos.
- Distincion poseedor de buena/mala fe del Art. 964 C.C. (desde cuando se deben los frutos, frutos que el
  dueno "hubiera podido percibir"): hoy el usuario fija el periodo de privacion.
- Actualizacion de cada fruto mensual a una fecha de corte posterior (segunda indexacion).
- Gastos de conservacion puntuales por fecha: el motor los soporta (`GastoConservacion`), pero la UI
  solo captura el gasto mensual fijo.

## Integracion en el area Civil/Familia (Sprint 100, wiring)
- **Modelo:** nueva categoria `FRUTO_CIVIL` ("Fruto civil (beneficio dejado de percibir)") en
  `CATEGORIAS_CIVIL_FAMILIA`, siempre `TipoObligacion.PUNTUAL`. Reutiliza columnas existentes y agrega
  dos nuevas (`scripts/migrate_fruto_civil_sprint100.py`, registrada en
  `aplicar_migraciones_pendientes()`):
  - `valor` = canon mensual del activo; `fecha_origen` = inicio del periodo de privacion;
    `fecha_fin` = final del periodo (ambas inclusive);
  - `fecha_referencia_canon` (nueva, `Date`) = fecha a cuyos precios esta el canon;
  - `gasto_conservacion_mensual` (nueva, `Numeric(18,2)`, opcional) = gasto ordinario de conservacion fijo.
- **Liquidacion:** `CivilFamiliaStrategy._eventos_fruto_civil` llama a `calcular_fruto_civil` y emite un
  evento de capital `FRUTO_CIVIL` por mes (fechado el ultimo dia privado del mes, monto = fruto neto, etiqueta
  con mes/año, dias, canon y gasto). El periodo se topa en la fecha de corte, con alerta no bloqueante.
- **Sin intereses (decision por defecto):** el despacho NO confirmo que el fruto civil genere el interes civil
  del 6 % despues de causado; la obligacion corre con tasa 0 (fuente "Fruto civil: sin intereses (no
  confirmado por el despacho)") y se suma en seco. La indexacion IPC de la obligacion se ignora en esta
  categoria (el canon ya se indexa mes a mes; no hay segunda actualizacion a la fecha de corte). Los abonos
  se imputan normalmente contra el capital.
- **Resultados y reportes:** cada mes es una fila de la tabla (pantalla, PDF y Word); el resumen agrega el rubro
  "Fruto Civil Causado (Art. 964 C.C., sin intereses)" (`ReportSummaryBuilder`, clave `total_fruto_civil`,
  calculado con `LiquidationResult.total_fruto_civil()`), que discrimina la parte del capital que es fruto.
- **UI:** `ObligacionFormDialog` (area Civil/Familia) muestra, al elegir la categoria, "Canon mensual del
  activo", "Fecha de referencia del canon", "Inicio/Fin del periodo de privación" y "Gasto de conservación
  mensual (opcional)", y oculta tipo, tasas/indexacion y beneficiario.

## Pruebas
`tests/engine/civil/test_fruto_civil.py` (valores calculados a mano con la serie IPC mensual real);
`tests/services/test_civil_fruto_civil.py` (liquidacion Civil/Familia), `tests/views/test_obligaciones.py`,
`tests/views/test_liquidaciones.py`, `tests/reports/test_pdf.py`, `tests/reports/test_word.py`,
`tests/database/test_migrations.py`.
