# Diseño — Sprint 12: TRM y obligaciones en moneda extranjera

**Fecha:** 2026-07-20
**Origen:** `Pendientes.md`, sección "Sprint 12 — TRM y obligaciones en moneda extranjera".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

El PDF (`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`) menciona la TRM en dos lugares:

- Página 8 (tabla "INDICADORES DE CÁLCULO"): la TRM la certifica el Banco de la República/SFC,
  periodicidad diaria, "Liquidación de obligaciones pactadas en moneda extranjera (Art. 874 C.Co)".
- Página 21 (sección "E. TRM"): "Funciona como mecanismo de revalorización de la moneda cuando el pago
  se hace en el equivalente en pesos de curso legal según la tasa de la fecha de la obligación o del
  pago."

A diferencia de SMLMV/IPC/IBC-Usura (Sprint 5), **el PDF no trae una serie histórica de TRM diaria** —
verificado extrayendo el texto completo de las páginas 8 y 21 (`pdftotext -layout`). No hay datos que
transcribir como se hizo con `historical_index.py`. Confirmado con el usuario: hay casos reales próximos
que requieren esto, pero la fuente de datos para la TRM tendrá que ser manual por ahora (el usuario
puede pasar una serie histórica del Banco de la República más adelante).

El código existente no tiene ninguna coincidencia de "TRM" ni "moneda extranjera" (`Pendientes.md` línea
730). El punto de entrada natural es `ComercialStrategy` (`app/services/area_strategy.py`), la única
área que trabaja con títulos valores comerciales — el Sprint 2 dejó esto explícitamente excluido de su
alcance (`Pendientes.md` línea 82).

## Decisiones tomadas con el usuario

1. **Alcance: solo área Comercial, solo USD.** El PDF ata la TRM a obligaciones en moneda extranjera de
   títulos valores comerciales (Art. 874 C.Co.); no hay indicio de que otras áreas (Civil/Familia,
   Laboral, Sancionatorio, Honorarios) necesiten esto. Una sola moneda extranjera (USD) cubre los casos
   reales actuales — el modelo deja espacio para agregar otras monedas después sin rediseño (campo
   `moneda: str`, no un booleano "es_extranjera").

2. **TRM de carga manual por obligación, con capa reemplazable.** Sin serie histórica en el PDF, el
   abogado ingresa directamente la TRM aplicable a cada obligación en moneda extranjera (en vez de que
   el sistema la busque). Para no cerrar la puerta a una fuente histórica futura, la conversión se
   encapsula detrás de una interfaz `TRMProvider` — mismo patrón que `RateProvider`/`MemoryRateProvider`
   (`app/engine/interest/provider.py`) ya usa para tasas de interés. Hoy solo existe
   `ManualTRMProvider`; el día que el usuario entregue una serie histórica real, se agrega un
   `HistoricalTRMProvider` sin tocar `ComercialStrategy`.

3. **Conversión única al inicio de la liquidación, no por abono.** Art. 874 C.Co. permite elegir entre
   la TRM de la fecha de la obligación o la del pago — pero eso es una elección de **qué número usar**,
   no una relicitación continua. El capital se convierte a pesos **una sola vez**, antes de construir los
   eventos de causación, exactamente como ya anticipaba `Pendientes.md` ("el capital se convierta a
   pesos antes de aplicar interés"). A partir de ahí, `UniversalLiquidationService` opera 100% en pesos,
   sin ningún cambio al motor de interés/mora/usura. Los abonos (`Abono.monto`) ya se registran en pesos
   hoy — no requieren conversión.
   - El campo `trm_fecha_referencia` es metadato de auditoría (qué fecha sustenta la TRM ingresada,
     útil si alguien audita el expediente después) — el motor no lo usa para buscar nada, ya que la TRM
     viene dada directamente por `trm_aplicable`.

4. **Migración manual de esquema, mismo patrón que Sprint 8.** Igual que
   `scripts/migrate_aplica_indexacion_ipc.py`: script idempotente en `scripts/`, `ALTER TABLE`
   verificado contra `PRAGMA table_info`, ejecutado una vez contra `bastium.db` preservando los datos
   existentes (que quedan con `moneda="COP"`, comportamiento idéntico al actual).

## Componentes técnicos

### 1. `database/models.py` → `Obligacion`

```python
moneda: Mapped[str] = mapped_column(String(3), default="COP")
trm_aplicable: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
trm_fecha_referencia: Mapped[date | None] = mapped_column(Date, nullable=True)
```

Todas las obligaciones existentes y de áreas distintas a Comercial quedan con `moneda="COP"` —
comportamiento idéntico al actual, cero impacto.

### 2. `scripts/migrate_moneda_trm.py` (nuevo, ejecución única)

Mismo patrón que `migrate_aplica_indexacion_ipc.py`: tres `ALTER TABLE` (uno por columna), verificados
individualmente contra `PRAGMA table_info(obligaciones)` para poder correr más de una vez sin error.

### 3. `app/engine/currency/trm_provider.py` (nuevo módulo)

```python
class TRMProvider(ABC):
    @abstractmethod
    def get_trm(self, fecha_referencia: date) -> Decimal: ...

class ManualTRMProvider(TRMProvider):
    """La TRM viene decidida por el abogado (Obligacion.trm_aplicable) -- no se
    busca en ninguna serie historica. Reemplazable por un HistoricalTRMProvider
    sin tocar ComercialStrategy el dia que exista una serie real."""
    def __init__(self, trm: Decimal):
        self._trm = trm

    def get_trm(self, fecha_referencia: date) -> Decimal:
        return self._trm
```

### 4. `app/engine/currency/converter.py` (nuevo módulo)

```python
def convertir_a_pesos(
    valor: Decimal,
    moneda: str,
    provider: TRMProvider | None,
    fecha_referencia: date,
) -> Decimal:
    if moneda == "COP":
        return valor
    if provider is None:
        raise ValueError(f"Obligación en {moneda} requiere una TRM aplicable.")
    return valor * provider.get_trm(fecha_referencia)
```

Función pura, sin estado — fácil de testear de forma aislada.

### 5. `app/services/area_strategy.py` → `ComercialStrategy`

- `_validar_obligacion_comercial` se extiende: si `obligacion.moneda != "COP"`, exige `trm_aplicable` y
  `trm_fecha_referencia` (mismo estilo que la validación ya existente de
  `tasa_efectiva_anual`/`tasa_moratoria_anual`/`fecha_vencimiento`/`ibc_vigente_anual`).
- `_eventos_de_obligacion` (o un paso previo en `liquidar()`) convierte `obligacion.valor` a pesos con
  `convertir_a_pesos(...)` antes de construir el `Event` de capital — usando `ManualTRMProvider` sembrado
  con `obligacion.trm_aplicable` cuando `moneda != "COP"`.
- El resto de `ComercialStrategy.liquidar()` no cambia: interés remuneratorio/moratorio, usura y
  allocation siguen operando sobre el monto ya convertido a pesos.

### 6. GUI — `app/views/obligaciones.py` (`ObligacionDialog`)

Mismo patrón condicional que ya usan los campos específicos de Comercial (`campo_fecha_vencimiento`,
`.setVisible(es_comercial)`):

- `combo_moneda` (QComboBox: "COP", "USD"), visible solo cuando `es_comercial`.
- `campo_trm_aplicable` (QLineEdit) y `campo_trm_fecha_referencia` (QDateEdit), visibles solo cuando
  `es_comercial` **y** `combo_moneda.currentText() == "USD"` (listener sobre el combo, análogo a los
  listeners ya existentes que alternan visibilidad por área/tipo).
- Validación en el diálogo antes de guardar: moneda USD sin TRM aplicable o sin fecha de referencia →
  mensaje de error, igual que las validaciones ya existentes de campos comerciales requeridos.

## Fuera de alcance (explícito)

- Otras monedas extranjeras además de USD (EUR, etc.) — el campo `moneda: str` no lo impide a futuro,
  pero no se carga ningún dato ni se valida ninguna otra moneda en este sprint.
- Serie histórica de TRM precargada (no existe en el PDF fuente) o conexión a una API del Banco de la
  República — solo `ManualTRMProvider`.
- Conversión de abonos individuales a/desde moneda extranjera — los abonos ya se registran en pesos.
- Reconversión continua del capital pendiente a la TRM vigente en cada fecha de pago — la conversión es
  única, al inicio de la liquidación (ver decisión 3).
- Áreas distintas a Comercial.

## Testing

- `convertir_a_pesos`: caso `moneda="COP"` (retorna el valor sin tocar, sin requerir provider), caso
  `moneda="USD"` con provider (multiplica correctamente por la TRM), caso `moneda="USD"` sin provider
  (`ValueError`).
- `ManualTRMProvider.get_trm`: retorna siempre el mismo valor sembrado, para cualquier fecha.
- `ComercialStrategy`: obligación en USD con TRM conocida → el capital que entra al motor de
  interés/mora/usura es el convertido a pesos (comparar contra el mismo caso armado manualmente en COP
  con el valor ya convertido). Validación: obligación en USD sin `trm_aplicable` lanza `ValueError` antes
  de liquidar.
- Regresión: obligaciones existentes (`moneda` default `"COP"`) liquidan exactamente igual que antes de
  este sprint.
- Migración: test que corre `scripts/migrate_moneda_trm.py` dos veces sobre una base de datos temporal y
  confirma idempotencia, y que las columnas quedan con los defaults esperados.
- Suite completa (hoy en verde) sigue pasando.

## Definición de hecho

- `ComercialStrategy` liquida obligaciones en USD convirtiendo el capital a pesos con la TRM ingresada
  por el abogado, antes de aplicar interés/mora/usura.
- Formulario de obligación operable end-to-end desde la GUI para el flujo Comercial + USD (smoke test
  manual: crear obligación en USD con TRM, liquidar, confirmar que el resultado coincide con el cálculo
  manual en pesos).
- `bastium.db` migrado con las tres columnas nuevas sin perder los datos existentes.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados (regla obligatoria de `Pendientes.md` al cerrar
  cualquier sprint) — quitar la mención de TRM de "Fuera de alcance" en `GUIA_USUARIO.md` línea 199.
- Suite completa en verde.
