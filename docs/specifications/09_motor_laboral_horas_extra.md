# Motor Laboral: horas extra HED/HEN/HEFD/HEFN en la liquidacion (Sprint 95)

## Que hace
Permite registrar horas extra en una liquidacion Laboral ("Liquidacion de contrato laboral") y las suma como
rubro propio (evento `HORAS_EXTRA`) con el factor legal vigente en la fecha de causacion, segun la respuesta
del despacho (Sprint 95, seguimiento): HED 1,25 y HEN 1,75 en cualquier fecha; HEFD/HEFN por tramo de la
Ley 2466 de 2025.

| Concepto | Antes del 01/07/2025 | 01/07/2025 - 30/06/2026 | 01/07/2026 - 30/06/2027 | Desde 01/07/2027 |
|---|---|---|---|---|
| HED | 1,25 | 1,25 | 1,25 | 1,25 |
| HEN | 1,75 | 1,75 | 1,75 | 1,75 |
| HEFD | porcentaje digitado | 2,05 | 2,15 | 2,25 |
| HEFN | porcentaje digitado | 2,55 | 2,65 | 2,75 |

Monto de cada fila = `horas x valor hora ordinaria x factor`, redondeado a centavos (`Rounding.money`).
Con porcentaje digitado: `factor = 1 + porcentaje / 100` (`calcular_hora_extra`).

## Modelo de captura
- Tabla nueva `horas_extra_laborales` (`database.models.HoraExtraLaboral`), hija de la obligacion Laboral,
  mismo patron que `descuentos_laborales`: `concepto` (HED/HEN/HEFD/HEFN), `fecha_causacion`,
  `numero_horas`, `valor_hora` y `porcentaje_manual` (NULL salvo HEFD/HEFN antes del 01/07/2025). Columnas
  numericas en `DecimalExacto` (TEXT, sin `float`).
- No es una categoria de obligacion nueva: `LaboralStrategy` liquida una sola obligacion por expediente, y
  las horas extra pertenecen al mismo contrato.
- Tabla nueva, no columna: la crea `Base.metadata.create_all()` (`init_db()`) en cualquier `bastium.db`,
  sin script de migracion (prueba en `tests/database/test_migrations.py`).
- UI: grupo "Horas extra" en el Detalle del expediente (solo area Laboral) y dialogo
  `app/views/horas_extra_laborales.py::HoraExtraLaboralFormDialog`, que muestra el factor vigente y pide el
  porcentaje (con la explicacion) solo cuando el motor no tiene factor confirmado.
- Valor hora: digitado. El codigo no tiene conversion salario mensual -> valor hora (depende de la jornada
  maxima legal vigente, no parametrizada).

## Componentes
- `app/engine/labor/horas_extra.py`: `requiere_porcentaje_manual(concepto, fecha)` y
  `liquidar_hora_extra_con_porcentaje_manual(concepto, horas, valor_hora, fecha, porcentaje_manual)` ->
  `(monto, factor)`, sobre `factor_hora_extra`/`liquidar_hora_extra`/`calcular_hora_extra` (PR #41).
- `LaboralStrategy._eventos_horas_extra`: un evento `HORAS_EXTRA` por fila, en su fecha de causacion, con
  etiqueta `Horas extra HED (10 h x valor hora $10,000.00 x factor 1.25, causadas el 15/03/2020)`.
- `LiquidationCore._capital_concepts` incluye `HORAS_EXTRA`.

## Reglas y validaciones
1. HEFD/HEFN antes del 01/07/2025 sin porcentaje: `HoraExtraFestivaSinFactorConfirmadoError` (el dialogo no
   deja guardar la fila sin el porcentaje).
2. Si el motor tiene factor, el porcentaje digitado se ignora (y el dialogo no lo guarda).
3. `fecha_causacion` debe estar dentro del contrato (`fecha_inicio` a `fecha_fin`).
4. La categoria "Salarios y prestaciones dejadas de percibir" no admite horas extra.
5. No cambia ningun otro rubro: las horas extra no entran en la base de prestaciones, de la moratoria del
   Art. 65 CST, de la indexacion IPC ni de las costas.

## Fuera de alcance / pendiente de confirmar
- Factor de HEFD/HEFN antes del 01/07/2025 (repreguntado en el Sprint 119).
- Si las horas extra habituales deben integrar la base salarial de prestaciones/moratoria (Art. 127 CST).
- Topes de la Ley 2466 (2 h/dia, 12 h/semana, `validar_limite_horas_extra_ley_2466`): una fila puede
  agrupar horas de varios dias, asi que no se validan por fila.
- Recargos (nocturno, dominical/festivo diurno/nocturno) siguen sin conectar a la UI.
