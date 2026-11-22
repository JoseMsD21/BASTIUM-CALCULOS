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
- Wiring a `AreaStrategy`, modelo `Obligacion`, UI y reportes.

## Pruebas
`tests/engine/civil/test_fruto_civil.py` (valores calculados a mano con la serie IPC mensual real).
