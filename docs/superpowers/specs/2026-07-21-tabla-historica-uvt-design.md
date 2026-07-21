# Diseño: Tabla histórica de UVT (DIAN) — Sprint 14

**Fecha:** 2026-07-21
**Origen:** Sprint 14 de `Pendientes.md`. Desbloqueador de dos piezas pendientes: la conversión
SMLMV→UVT del Sprint 4 (`resolver_base_sancion` lanza `UVTNoDisponibleError` para hechos posteriores a
2020-01-01 por falta de serie) y el Sprint 15 (Tributario 11b), que necesita UVT para la sanción mínima
(10 UVT) y para expresar cuantías.

## El bloqueador real: la fuente

El PDF de requisitos (`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`) describe el mecanismo
de la UVT (págs. 8, 21, 38, 53: se fija anualmente por resolución DIAN en nov/dic, rige desde el 1 de
enero, se ajusta según variación IPC oct-oct) pero **no trae una tabla año por año** — solo un valor
aislado en la página 69 ("UVT 2023 ≈ $38.004", que en realidad corresponde al valor oficial de **2022**,
no 2023; probablemente una referencia a la UVT aplicable a la declaración de renta presentada en 2023
sobre ingresos de 2022, o un error de transcripción del PDF fuente — de cualquier forma, no es una fuente
confiable por sí sola).

Como el criterio explícito de este sprint es "no inventar valores", la serie se obtuvo de fuentes externas
(no del PDF) y se verificó cruzando 3 fuentes independientes antes de transcribirla:

- https://www.gerencie.com/uvt.html (tabla completa 2006-2026)
- https://siemprealdia.co/colombia/impuestos/uvt-historico/ (tabla completa 2006-2026 + resolución DIAN
  por año)
- Búsqueda web adicional para confirmar el valor y la resolución de 2025 específicamente (la tabla de
  siemprealdia.co repetía por error la resolución de 2026 para 2025; se confirmó por separado que el valor
  de 2025 corresponde a la Resolución DIAN 000193 del 4-dic-2024, no a la 000238).

Las 3 fuentes coinciden en los 21 valores. Tabla verificada:

| Año  | UVT       | Resolución DIAN                  |
|------|-----------|-----------------------------------|
| 2006 | $20.000   | Res. 15652/2005                   |
| 2007 | $20.974   | Res. 15013/2007                   |
| 2008 | $22.054   | Res. 01063/2008                   |
| 2009 | $23.763   | Res. 12115/2009                   |
| 2010 | $24.555   | Res. 12066/2010                   |
| 2011 | $25.132   | Res. 11963/2011                   |
| 2012 | $26.049   | Res. 000219/2012                  |
| 2013 | $26.841   | Res. 000227/2013                  |
| 2014 | $27.485   | Res. 000228/2014                  |
| 2015 | $28.279   | Res. 000004/2016                  |
| 2016 | $29.753   | Res. 000071/2016                  |
| 2017 | $31.859   | Res. 000062/2017                  |
| 2018 | $33.156   | Res. 000063/2018                  |
| 2019 | $34.270   | Res. 000084/2019                  |
| 2020 | $35.607   | Res. 000111/2020                  |
| 2021 | $36.308   | Res. 000140/2021                  |
| 2022 | $38.004   | Res. 001264/2022                  |
| 2023 | $42.412   | Res. 000187/2023                  |
| 2024 | $47.065   | Res. 000193/2024                  |
| 2025 | $49.799   | Res. 000193 del 4-dic-2024        |
| 2026 | $52.374   | Res. 000238 del 15-dic-2025        |

## Decisión tomada con el usuario durante el brainstorming

- **Rango de la serie: 2006-2026 completo** (creación de la UVT por Ley 1111 de 2006 hasta el año vigente
  hoy), no solo desde 2020. El usuario prefirió esto sobre el alcance mínimo (solo 2020+) porque la serie
  completa ya estaba verificada y sigue el mismo patrón que SMLMV/IPC (que también arrancan en su año de
  origen, no en el año donde un motor específico empezó a necesitarlos).
- **Trazabilidad de la fuente:** como el PDF no tiene esta tabla (a diferencia de SMLMV/IPC, que citan
  páginas específicas), el spec documenta la tabla completa con resolución DIAN por año y las URLs
  consultadas; el código solo referencia este documento (mismo patrón de cita corta que el resto de
  `historical_index.py`).

## Código nuevo

**`app/engine/indexation/historical_index.py`:**
- `_UVT_POR_ANIO: Dict[int, Decimal]` — los 21 valores de la tabla de arriba.
- `get_uvt_for_year(anio: int) -> Decimal`, mismo contrato que `get_smlmv_for_year` (línea 79): consulta
  `get_parametro("UVT", date(anio, 1, 1))`, captura `ParametroNoDisponibleError` y relanza `ValueError`
  con el rango disponible.

**`app/services/parametro_service.py`:**
- Entrada `"UVT"` en `CATALOGO_PARAMETROS`: modo `ANUAL_EXACTO` (mismo modo que `SMLMV` e
  `IPC_INDICE_ACUMULADO` — un valor por 1 de enero, no requiere modo nuevo), fuente legal `"DIAN,
  resolución anual (Ley 1111 de 2006)"`.

**`scripts/migrate_parametros_legales.py`:**
- Bloque de siembra para `"UVT"` desde `_UVT_POR_ANIO`, mismo patrón idempotente
  (`if not _clave_ya_sembrada(...)`) que `SMLMV`/`IPC_INDICE_ACUMULADO`.

**`app/engine/indexation/smlmv_to_uvt.py` (`resolver_base_sancion`):**
- Para `fecha_hecho >= FECHA_CORTE_SMLMV_A_UVT` (2020-01-01): en vez de lanzar `UVTNoDisponibleError`
  incondicionalmente, llama `get_uvt_for_year(fecha_hecho.year)` y convierte con
  `SMMLVCalculator.to_pesos(cantidad, uvt_del_anio)` — se reutiliza esta clase sin cambios porque su lógica
  (cantidad × valor unitario, redondeado a moneda) no tiene nada específico de SMLMV; no hace falta una
  clase `UVTCalculator` nueva.
- Si `get_uvt_for_year` lanza `ValueError` (año no cargado, ej. 2027+ aún no publicado por la DIAN), se
  captura y se relanza `UVTNoDisponibleError` — se preserva esta excepción para años genuinamente
  faltantes, de la que ya depende el manejo de errores de la GUI en `app/views/expediente_detalle.py:180`.

## Pruebas a actualizar (no solo agregar)

Dos pruebas existentes hoy afirman `UVTNoDisponibleError` para fechas ≥ 2020-01-01; tras este sprint esas
fechas sí resuelven, así que las pruebas quedan obsoletas y deben cambiar para afirmar el peso correcto:

- `tests/engine/test_smlmv_to_uvt.py`: `test_hecho_exactamente_2020_01_01_ya_requiere_uvt_y_lanza_error` y
  `test_hecho_posterior_a_2020_lanza_uvt_no_disponible_error`.
- `tests/services/test_area_strategy.py`: `test_liquida_multa_posterior_a_2020_lanza_uvt_no_disponible_error`.

Pruebas nuevas:
- `get_uvt_for_year` para un par de años conocidos (ej. 2020 → 35607.00, 2026 → 52374.00).
- `resolver_base_sancion` con una fecha posterior a 2020-01-01, verificando el valor en pesos correcto.
- Un año aún no cargado (ej. 2027) sigue lanzando `UVTNoDisponibleError` — confirma que la excepción no
  desapareció, solo dejó de dispararse para el rango ya cubierto.

## Alcance explícitamente excluido

- Automatización de actualización anual vía scraping DIAN (mismo criterio que el resto de series del
  Sprint 5/14).
- El Sprint 15 en sí — este sprint solo entrega el dato y desbloquea `resolver_base_sancion`, no el motor
  de sanciones tributarias que lo consumirá.

## Definición de Hecho

- `get_uvt_for_year` retorna valores verificables contra la tabla de este spec para 2006-2026.
- `resolver_base_sancion` liquida correctamente un caso con fecha posterior a 2020-01-01 sin lanzar
  `UVTNoDisponibleError`.
- Las 2 pruebas que asumían el bloqueo (sección "Pruebas a actualizar") quedan corregidas, no borradas.
- Suite completa en verde.
