# Diseño — Sprint 17: Módulo pensional (IBL, tasa de reemplazo, densidad de semanas)

**Fecha:** 2026-07-26
**Origen:** `Pendientes.md`, sección "Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, densidad de
semanas)".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

El PDF de requerimientos (pág. 52, "5. Liquidaciones Especiales: IBL y Pensiones" y "7. Indicador Crítico
de Tiempo: El Calendario") exige 4 piezas separadas del régimen pensional de Prima Media:

1. IBL (Ingreso Base de Liquidación) = promedio de los salarios cotizados en los últimos 10 años,
   actualizados año a año con IPC.
2. Tasa de Reemplazo (Fórmula R) = `r = 65.5 − 0.5·s`, donde `s` es el número de SMLMV contenidos en el
   IBL.
3. Densidad de semanas, contada en días **calendario reales** (365/366) desde la Sentencia SL138-2024 de
   la Corte Suprema (Sala Laboral) — no en días hábiles (`dias_habiles_entre`, Sprint 6) ni en el año
   comercial de 360 usado antes de esa sentencia.
4. Actualización IPC del historial salarial (pieza compartida por el IBL, no una función aparte).

Es el sprint de mayor incertidumbre de dominio de todo el backlog: el PDF da la fórmula base pero no un
caso numérico completo para verificar, y no menciona el piso/techo/bono reales de la tasa de reemplazo
(Ley 100 art. 34) que sí existen en la práctica. Antes de codificar se investigó jurisprudencia y fuentes
externas para poder cerrar esas dos brechas sin inventar valores — ver "Decisiones tomadas con el usuario"
y `Preguntas-Para-Abogado.md` (sección Sprint 17) para lo que sigue sin confirmación jurídica formal.

## Decisiones tomadas con el usuario

1. **Granularidad del IBL: mensual (hasta 120 registros)**, no un valor representativo por año. Es la
   lectura real de la ley (promedio de las 120 cotizaciones mensuales de los últimos 10 años, cada una
   indexada por IPC antes de promediar), y el usuario confirmó que va a capturar el historial mes a mes.
2. **Densidad de semanas: unión de periodos solapados antes de contar días.** Si la persona tuvo dos
   contratos simultáneos, los días de la superposición cuentan una sola vez — no se puede cotizar "doble"
   el mismo día calendario.
3. **Fórmula de tasa de reemplazo: completa real, no solo la línea literal del PDF.** El PDF solo trae
   `r = 65.5 − 0.5·s`, pero la práctica real (Ley 100 art. 34, verificada cruzando fuentes externas durante
   este sprint — ver Sources al final) agrega: piso 65%, techo 80%, y un bono de `+1.5%` por cada 50 semanas
   cotizadas por encima de 1.300. El usuario decidió implementar la fórmula completa ahora (más útil de
   inmediato porque coincide con cómo Colpensiones calcula pensiones reales) en vez de solo la línea del
   PDF, y pidió que el hueco entre "lo que dice el PDF de BASTIUM" y "lo que se implementó" quede
   documentado en `Preguntas-Para-Abogado.md` para que el despacho lo confirme o corrija.
4. **Caso de validación real: Sentencia SL138-2024**, no un caso aportado directamente por el usuario (no
   tenía uno a la mano). Se investigó y se encontró el caso citado en la propia sentencia: 348 días
   calendario cotizados → 49,71 semanas → redondeadas a 50, usado como test de aceptación de
   `calcular_densidad_semanas` en vez de solo datos sintéticos.
5. **Convención de conteo de días: no inclusiva** (`(fecha_fin - fecha_inicio).days`, sin sumar 1), igual
   que el resto del código (`LaboralStrategy.dias_trabajados`, ver Sprint 30). El propio Sprint 30 dejó
   abierta la pregunta de si esa convención es la jurídicamente correcta o si debería ser inclusiva — no se
   introduce una segunda convención distinta solo para este módulo; la ambigüedad se documenta una vez y se
   agrega como pregunta compartida en `Preguntas-Para-Abogado.md`.
6. **Alcance: solo motores de cálculo puros**, sin `PensionalStrategy` ni wiring de GUI — igual patrón que
   `IPCIndexation` (huérfano hasta el Sprint 8) o `app/engine/tax/*` de Sprint 11a. `Pendientes.md` no pide
   una estrategia de área nueva para este sprint, solo las 4 piezas de cálculo.

## Funciones nuevas (`app/engine/labor/ibl.py`, paquete existente)

Funciones libres (no una clase estática), siguiendo la firma exacta sugerida por `Pendientes.md` — no hay
estado compartido entre ellas que justifique agruparlas en una clase.

```python
def calcular_ibl(
    historial_salarios: list[tuple[date, Decimal]],
    fecha_calculo: date,
) -> Decimal:
    """Promedio de los salarios cotizados, cada uno indexado por IPC desde su
    fecha hasta fecha_calculo (PDF pag. 52). El historial ya debe venir acotado
    a los ultimos 10 anios cotizados -- esta funcion no filtra por fecha, solo
    indexa y promedia lo que reciba (mismo criterio que
    SeguridadSocialCalculator: los calculadores no resuelven que datos son
    relevantes, eso es responsabilidad de quien arma el historial)."""
    if not historial_salarios:
        raise ValueError("El historial de salarios no puede estar vacio.")

    indice_final = get_ipc_interpolado_for_date(fecha_calculo)
    total = Decimal("0.00")
    for fecha, salario in historial_salarios:
        indice_inicial = get_ipc_interpolado_for_date(fecha)
        total += salario + IPCIndexation.calculate(salario, indice_inicial, indice_final)

    return Rounding.money(total / len(historial_salarios))


def calcular_tasa_reemplazo(
    ibl: Decimal,
    smlmv_vigente: Decimal,
    semanas_cotizadas: int,
) -> Decimal:
    """Formula R completa (Ley 100 art. 34; el PDF de BASTIUM solo trae la
    linea base r = 65.5 - 0.5*s, ver Preguntas-Para-Abogado.md, Sprint 17):
    piso 65%, techo 80%, bono +1.5% por cada 50 semanas sobre 1300."""
    if smlmv_vigente <= Decimal("0.00"):
        raise ValueError("El SMLMV vigente debe ser positivo.")

    s = ibl / smlmv_vigente
    r = Decimal("65.5") - Decimal("0.5") * s

    if semanas_cotizadas > 1300:
        bloques_50_semanas = (semanas_cotizadas - 1300) // 50
        r += Decimal(bloques_50_semanas) * Decimal("1.5")

    r = max(Decimal("65"), min(Decimal("80"), r))
    return Rounding.money(r)  # 2 decimales, ROUND_HALF_UP -- mismo quantize que money, reutilizado para puntos porcentuales


def calcular_densidad_semanas(periodos_cotizados: list[tuple[date, date]]) -> int:
    """Semanas de cotizacion en dias calendario reales (365/366), no dias
    habiles ni ano comercial de 360 (Sentencia SL138-2024). Los periodos
    solapados se unen antes de contar, para no cotizar "doble" el mismo dia
    calendario."""
    if not periodos_cotizados:
        return 0
    for inicio, fin in periodos_cotizados:
        if fin < inicio:
            raise ValueError(f"Periodo invalido: fin ({fin}) es anterior a inicio ({inicio}).")

    periodos_ordenados = sorted(periodos_cotizados)
    fusionados: list[tuple[date, date]] = [periodos_ordenados[0]]
    for inicio, fin in periodos_ordenados[1:]:
        ultimo_inicio, ultimo_fin = fusionados[-1]
        if inicio <= ultimo_fin:
            fusionados[-1] = (ultimo_inicio, max(ultimo_fin, fin))
        else:
            fusionados.append((inicio, fin))

    dias_totales = sum((fin - inicio).days for inicio, fin in fusionados)
    semanas = (Decimal(dias_totales) / Decimal("7")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(semanas)
```

Notas de diseño:
- `calcular_ibl` reutiliza `get_ipc_interpolado_for_date` (`app/engine/indexation/historical_index.py`,
  ya usada por el wiring de Sprint 8) en vez de `get_ipc_for_date`, porque las fechas de cotización mensual
  no van a coincidir siempre con un 31 de diciembre.
- `calcular_tasa_reemplazo` recibe `smlmv_vigente` como parámetro (no lo resuelve internamente), igual
  patrón que `IncapacidadCalculator.calcular` recibe `ibc_mensual` ya resuelto — mantiene la función pura y
  testeable sin tocar `parametro_service`.
- Ninguna de las tres funciones toca `dias_habiles_entre` (Sprint 6): confirmado que esa función no aplica
  aquí (conteo en días hábiles ~250/año, no calendario ~365/año), como ya advertía la sección "Depende de"
  de `Pendientes.md`.

## Testing (`tests/engine/labor/test_ibl.py`, paquete existente)

1. **`calcular_ibl`**: historial sintético de 120 meses con IPC variable (usa
   `_IPC_VARIACION_ANUAL`/`_construir_indice_ipc_acumulado` real de `historical_index.py`, no un IPC
   inventado); verifica el promedio indexado contra un cálculo manual. Caso adicional: historial vacío →
   `ValueError`.
2. **`calcular_tasa_reemplazo`**: al menos 3 valores de `s` (bajo, medio, alto) sin bono; caso con bono
   (semanas > 1300, verificando el bloque de 50 en 50); caso de piso (s muy alto sin bono suficiente,
   confirmar que no baja de 65%); caso de techo (bono grande, confirmar que no sube de 80%).
3. **`calcular_densidad_semanas`**:
   - Comparación explícita: mismo periodo de 13 meses cruzando un año bisiesto, calculado con días
     calendario reales vs. con la convención comercial de 360 (13×30 días) — documentar la diferencia
     exacta de semanas entre ambos métodos (requisito literal de la Definición de Hecho del sprint).
   - **Caso real SL138-2024**: periodo que suma 348 días calendario → 49,71 semanas → redondea a 50
     (fuente: sentencia de la Corte Suprema, Sala Laboral, 31-ene-2024).
   - Periodos solapados: dos periodos que se cruzan, verificar que el solape no se cuenta dos veces.
   - Periodo vacío → 0. `fin < inicio` → `ValueError`.

## Fuera de alcance (explícito)

- `PensionalStrategy` / wiring a `area_strategy.py` / GUI — no lo pide `Pendientes.md` para este sprint;
  estas 3 funciones quedan como motores puros standalone, mismo patrón que `app/engine/tax/*` (Sprint 11a).
- RAIS (Régimen de Ahorro Individual con Solidaridad) — el PDF solo describe Prima Media.
- Integración con Colpensiones/AFP para traer el historial real de cotizaciones — el input es manual.
- Resolver de forma definitiva si el conteo de días debe ser inclusivo o no (decisión 5 arriba) — queda
  como pregunta compartida con el Sprint 30 en `Preguntas-Para-Abogado.md`, no se decide unilateralmente
  aquí ni allá.

## Definición de hecho

- Tests de IBL con historial sintético de 10 años con IPC variable (en verde).
- Tests de tasa de reemplazo con al menos 3 valores de `s` distintos, más piso/techo/bono (en verde).
- Test de densidad de semanas que compara explícitamente calendario vs. año comercial de 360, y el caso
  real SL138-2024 (en verde).
- Suite completa en verde.
- `Preguntas-Para-Abogado.md` creado con la sección Sprint 17 (fórmula completa vs. PDF, convención de días)
  y las secciones de sprints 2-16, 18 (ver documento aparte).
- `Pendientes.md`: marcar Sprint 17 como completado, con nota de Estado igual que los sprints anteriores.

## Fuentes externas verificadas (no vienen del PDF de BASTIUM)

- Sentencia SL138-2024, Corte Suprema de Justicia, Sala de Casación Laboral (31-ene-2024) —
  `https://cortesuprema.gov.co/corte/wp-content/uploads/2024/02/SL138-2024.pdf` y nota de prensa oficial
  `https://cortesuprema.gov.co/semanas-de-cotizacion-a-pension-se-deben-contabilizar-con-dias-calendario-no-con-meses-de-30-dias/`.
- Fórmula completa de tasa de reemplazo (piso 65%, techo 80%, bono +1.5%/50 semanas), Ley 100 de 1993 art.
  34 — verificada con ejemplo numérico de referencia en fuentes secundarias (Gerencie.com, tupensioncolombia.com);
  sin confirmación directa de un despacho jurídico todavía, ver `Preguntas-Para-Abogado.md`.
