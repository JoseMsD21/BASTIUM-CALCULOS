# Sprint 24 — Validación de Datos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ObligacionFormDialog` (`app/views/obligaciones.py`) y `parametro_service.agregar_valor()`
(`app/services/parametro_service.py`) dejan de aceptar datos absurdos (tasas/porcentajes negativos o
descabelladamente altos, fechas invertidas, tramos de parámetros solapados, conceptos vacíos) sin ningún
aviso — cada regla lanza `ValueError` al momento de guardar, no solo al liquidar.

**Architecture:** Validaciones puras de sentido común, sin catálogo EFDJ nuevo. Tres helpers privados
nuevos en `ObligacionFormDialog` (`_validar_rango`, `_validar_concepto_no_vacio`,
`_validar_fecha_no_posterior_a_corte`) reutilizados desde las 3 rutas de guardado existentes
(`guardar()`, `_guardar_laboral()`, `_guardar_tributario()`) y desde los `_parse_campos_*` por área.
`agregar_valor()` gana 3 checks nuevos (signo de `valor`, orden de fechas movido desde la GUI, solapamiento
de tramos `TRAMO_CERRADO`) antes de insertar la fila.

**Tech Stack:** Python, PySide6 (Qt), SQLAlchemy, pytest + pytest-qt.

**Spec:** `docs/superpowers/specs/2026-08-01-sprint24-validacion-datos-design.md`

---

### Task 1: Rango de tasa y concepto no vacío en la ruta genérica de `guardar()`

**Files:**
- Modify: `app/views/obligaciones.py:363-370` (agregar helpers después de `_parse_decimales`)
- Modify: `app/views/obligaciones.py:1-27` (import de `Expediente`)
- Modify: `app/views/obligaciones.py:305-361` (`guardar()`)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_obligaciones.py`:

```python
def test_tasa_efectiva_negativa_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("100000.00")
    dialog.campo_tasa.setText("-1.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_tasa_efectiva_absurdamente_alta_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("100000.00")
    dialog.campo_tasa.setText("99999.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_concepto_vacio_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("   ")
    dialog.campo_valor.setText("100000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_fecha_origen_posterior_a_fecha_de_corte_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)  # fecha_corte_default = 2026-06-01

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("100000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2026, 7, 1))  # posterior al corte

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_fecha_inicio_recurrente_posterior_a_fecha_de_corte_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)  # fecha_corte_default = 2026-06-01

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    dialog.campo_concepto.setText("Cuota alimentaria")
    dialog.campo_valor.setText("500000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_inicio.setDate(date(2026, 7, 1))  # posterior al corte
    dialog.campo_dia_pago.setValue(5)

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `pytest tests/views/test_obligaciones.py -k "tasa_efectiva or concepto_vacio or fecha_origen_posterior or fecha_inicio_recurrente_posterior" -v`
Expected: 5 tests FAIL (hoy no existe ninguna de estas validaciones — el guardado tiene éxito o falla por
una razón distinta, así que `pytest.raises(ValueError)` no se cumple).

- [ ] **Step 3: Agregar el import de `Expediente`**

En `app/views/obligaciones.py`, línea 27, cambiar:

```python
from database.models import Obligacion, TipoObligacion
```

por:

```python
from database.models import Expediente, Obligacion, TipoObligacion
```

- [ ] **Step 4: Agregar los 3 helpers privados**

En `app/views/obligaciones.py`, inmediatamente después del método `_parse_decimales` (después de la línea
370, antes de `def _parse_campos_civil_familia`), agregar:

```python
    def _validar_rango(self, valor: Decimal, minimo: Decimal, maximo: Decimal, nombre_campo: str) -> None:
        """Rechaza valores fuera de un rango de sentido comun (Sprint 24) -- no es la
        validacion de usura (esa sigue viviendo en usury_validator.py y corre solo al
        liquidar), es solo para atajar errores de tecleo al guardar (ej. una tasa
        pactada de 99999%)."""
        if valor < minimo or valor > maximo:
            raise ValueError(f"{nombre_campo} debe estar entre {minimo} y {maximo}.")

    def _validar_concepto_no_vacio(self) -> None:
        if not self.campo_concepto.text().strip():
            raise ValueError("El concepto es obligatorio.")

    def _validar_fecha_no_posterior_a_corte(self, fecha: date) -> None:
        """La fecha de origen/inicio de una obligacion no puede quedar despues de la
        fecha de corte del expediente (Sprint 24): de lo contrario la liquidacion no
        tendria ningun dia que acumular intereses, y el dato casi siempre es un error
        de captura (ano equivocado, dia/mes invertido)."""
        session = session_module.get_session()
        try:
            expediente = session.get(Expediente, self._expediente_id)
        finally:
            session.close()
        if fecha > expediente.fecha_corte_default:
            raise ValueError(
                "La fecha de origen/inicio no puede ser posterior a la fecha de corte "
                f"del expediente ({expediente.fecha_corte_default.isoformat()})."
            )

```

- [ ] **Step 5: Cablear los helpers en `guardar()`**

En `app/views/obligaciones.py`, dentro de `guardar()`, después de la línea:

```python
        if not es_sancionatorio and not es_honorarios and valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")
```

agregar:

```python

        self._validar_rango(tasa, Decimal("0"), Decimal("1000"), "La tasa efectiva anual")
        self._validar_concepto_no_vacio()
```

Y después de las líneas que calculan `fecha_origen`/`fecha_inicio`:

```python
        tipo = TipoObligacion(self.combo_tipo.currentData())
        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())
        qdate_inicio = self.campo_fecha_inicio.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())
```

agregar:

```python

        fecha_relevante = fecha_origen if tipo == TipoObligacion.PUNTUAL else fecha_inicio
        self._validar_fecha_no_posterior_a_corte(fecha_relevante)
```

(antes de la línea `session = session_module.get_session()` que sigue).

- [ ] **Step 6: Correr los tests para verificar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: todos PASS (incluidos los 5 nuevos y los ~50 existentes del archivo — nada de lo agregado
cambia el comportamiento de los casos ya cubiertos, ver fechas usadas en `_expediente_de_prueba`, todas
anteriores a `fecha_corte_default`).

- [ ] **Step 7: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint24): validar rango de tasa, concepto no vacio y fecha vs corte en ObligacionFormDialog

EOF
)"
```

---

### Task 2: Rango de cuota litis y costas judiciales en Honorarios

**Files:**
- Modify: `app/views/obligaciones.py:381-397` (`_parse_campos_honorarios`)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_cuota_litis_fuera_de_rango_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Honorarios proceso ejecutivo")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("1000000.00")
    dialog.campo_cuota_litis_pct.setText("150.00")
    dialog.campo_beneficio_obtenido.setText("10000000.00")

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_costas_pct_fuera_de_rango_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Honorarios proceso ejecutivo")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("1000000.00")
    dialog.campo_cuota_litis_pct.setText("20.00")
    dialog.campo_beneficio_obtenido.setText("10000000.00")
    dialog.campo_costas_pct.setText("-5.00")

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `pytest tests/views/test_obligaciones.py -k "cuota_litis_fuera_de_rango or costas_pct_fuera_de_rango" -v`
Expected: 2 tests FAIL.

- [ ] **Step 3: Cablear la validación en `_parse_campos_honorarios`**

En `app/views/obligaciones.py`, el método completo pasa de:

```python
    def _parse_campos_honorarios(self) -> dict:
        honorarios_fijos, cuota_litis_pct, beneficio_obtenido = self._parse_decimales(
            [self.campo_honorarios_fijos, self.campo_cuota_litis_pct, self.campo_beneficio_obtenido],
            "Honorarios fijos, % cuota litis y beneficio obtenido deben ser numeros validos.",
        )
        costas_pct = None
        texto_costas = self.campo_costas_pct.text().strip()
        if texto_costas:
            (costas_pct,) = self._parse_decimales(
                [self.campo_costas_pct], "% Costas judiciales debe ser un numero valido."
            )
        return {
            "honorarios_fijos_pactados": honorarios_fijos,
            "cuota_litis_pactada_pct": cuota_litis_pct,
            "beneficio_obtenido": beneficio_obtenido,
            "costas_pct_manual": costas_pct,
        }
```

a:

```python
    def _parse_campos_honorarios(self) -> dict:
        honorarios_fijos, cuota_litis_pct, beneficio_obtenido = self._parse_decimales(
            [self.campo_honorarios_fijos, self.campo_cuota_litis_pct, self.campo_beneficio_obtenido],
            "Honorarios fijos, % cuota litis y beneficio obtenido deben ser numeros validos.",
        )
        self._validar_rango(cuota_litis_pct, Decimal("0"), Decimal("100"), "El % de cuota litis pactada")
        costas_pct = None
        texto_costas = self.campo_costas_pct.text().strip()
        if texto_costas:
            (costas_pct,) = self._parse_decimales(
                [self.campo_costas_pct], "% Costas judiciales debe ser un numero valido."
            )
            self._validar_rango(costas_pct, Decimal("0"), Decimal("100"), "El % de costas judiciales")
        return {
            "honorarios_fijos_pactados": honorarios_fijos,
            "cuota_litis_pactada_pct": cuota_litis_pct,
            "beneficio_obtenido": beneficio_obtenido,
            "costas_pct_manual": costas_pct,
        }
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint24): validar rango 0-100% de cuota litis y costas en ObligacionFormDialog

EOF
)"
```

---

### Task 3: Positividad de `cantidad_smlmv_uvt` en Sancionatorio

**Files:**
- Modify: `app/views/obligaciones.py:375-379` (`_parse_campos_sancionatorio`)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_cantidad_smlmv_uvt_no_positiva_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Multa SIC")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2019, 6, 1))
    dialog.campo_cantidad_smlmv_uvt.setText("0")

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/views/test_obligaciones.py -k test_cantidad_smlmv_uvt_no_positiva -v`
Expected: FAIL (hoy `cantidad_smlmv_uvt = 0` se guarda sin error).

- [ ] **Step 3: Cablear la validación**

En `app/views/obligaciones.py`, `_parse_campos_sancionatorio` pasa de:

```python
    def _parse_campos_sancionatorio(self) -> dict:
        (cantidad_smlmv_uvt,) = self._parse_decimales(
            [self.campo_cantidad_smlmv_uvt], "Cantidad SMLMV/UVT debe ser un numero valido."
        )
        return {"cantidad_smlmv_uvt": cantidad_smlmv_uvt}
```

a:

```python
    def _parse_campos_sancionatorio(self) -> dict:
        (cantidad_smlmv_uvt,) = self._parse_decimales(
            [self.campo_cantidad_smlmv_uvt], "Cantidad SMLMV/UVT debe ser un numero valido."
        )
        if cantidad_smlmv_uvt <= Decimal("0"):
            raise ValueError("La cantidad de SMLMV/UVT debe ser mayor que cero.")
        return {"cantidad_smlmv_uvt": cantidad_smlmv_uvt}
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint24): exigir cantidad_smlmv_uvt positiva en obligaciones sancionatorias

EOF
)"
```

---

### Task 4: Rango de tasa moratoria e IBC vigente en Comercial

**Files:**
- Modify: `app/views/obligaciones.py:399-436` (`_parse_campos_comercial`)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_tasa_moratoria_comercial_absurdamente_alta_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Capital de pagare")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("99999.00")
    dialog.campo_ibc_vigente.setText("20.00")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_ibc_vigente_negativo_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Capital de pagare")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("24.00")
    dialog.campo_ibc_vigente.setText("-20.00")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `pytest tests/views/test_obligaciones.py -k "tasa_moratoria_comercial_absurdamente_alta or ibc_vigente_negativo" -v`
Expected: 2 tests FAIL.

- [ ] **Step 3: Cablear la validación**

En `app/views/obligaciones.py`, `_parse_campos_comercial` pasa de:

```python
    def _parse_campos_comercial(self) -> dict:
        tasa_moratoria, ibc_vigente = self._parse_decimales(
            [self.campo_tasa_moratoria, self.campo_ibc_vigente],
            "Tasa moratoria e IBC vigente deben ser numeros validos.",
        )
        qdate_vencimiento = self.campo_fecha_vencimiento.date()
```

a:

```python
    def _parse_campos_comercial(self) -> dict:
        tasa_moratoria, ibc_vigente = self._parse_decimales(
            [self.campo_tasa_moratoria, self.campo_ibc_vigente],
            "Tasa moratoria e IBC vigente deben ser numeros validos.",
        )
        self._validar_rango(tasa_moratoria, Decimal("0"), Decimal("1000"), "La tasa moratoria anual")
        self._validar_rango(ibc_vigente, Decimal("0"), Decimal("1000"), "El IBC vigente anual")
        qdate_vencimiento = self.campo_fecha_vencimiento.date()
```

(el resto del método no cambia).

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint24): validar rango 0-1000% de tasa moratoria e IBC vigente en Comercial

EOF
)"
```

---

### Task 5: Concepto no vacío y fecha vs. corte en `_guardar_laboral`

**Files:**
- Modify: `app/views/obligaciones.py:438-481` (`_guardar_laboral`)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_laboral_concepto_vacio_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("  ")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_laboral_fecha_inicio_contrato_posterior_a_fecha_de_corte_lanza_error(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)  # corte = 2026-06-01

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2026, 7, 1))  # posterior al corte
    dialog.campo_fecha_fin.setDate(date(2026, 12, 31))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `pytest tests/views/test_obligaciones.py -k "laboral_concepto_vacio or laboral_fecha_inicio_contrato_posterior" -v`
Expected: 2 tests FAIL.

- [ ] **Step 3: Cablear la validación**

En `app/views/obligaciones.py`, `_guardar_laboral` pasa de:

```python
    def _guardar_laboral(self) -> int:
        try:
            valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("El valor (salario base) debe ser un numero valido.") from error
        if valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")

        qdate_inicio = self.campo_fecha_origen.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())
        qdate_fin = self.campo_fecha_fin.date()
```

a:

```python
    def _guardar_laboral(self) -> int:
        try:
            valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("El valor (salario base) debe ser un numero valido.") from error
        if valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")
        self._validar_concepto_no_vacio()

        qdate_inicio = self.campo_fecha_origen.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())
        self._validar_fecha_no_posterior_a_corte(fecha_inicio)
        qdate_fin = self.campo_fecha_fin.date()
```

(el resto del método no cambia).

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint24): validar concepto no vacio y fecha vs corte en obligaciones laborales

EOF
)"
```

---

### Task 6: Concepto no vacío y fecha vs. corte en `_guardar_tributario`

**Files:**
- Modify: `app/views/obligaciones.py:483-554` (`_guardar_tributario`)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_tributario_concepto_vacio_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    dialog.combo_categoria.setCurrentIndex(0)  # IMPUESTO_A_CARGO
    dialog.campo_concepto.setText("   ")
    dialog.campo_valor.setText("10000000.00")
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_tributario_fecha_origen_posterior_a_fecha_de_corte_lanza_error(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)  # corte = 2026-06-01

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    dialog.combo_categoria.setCurrentIndex(0)  # IMPUESTO_A_CARGO
    dialog.campo_concepto.setText("Impuesto de renta 2026")
    dialog.campo_valor.setText("10000000.00")
    dialog.campo_fecha_origen.setDate(date(2026, 7, 1))  # posterior al corte

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `pytest tests/views/test_obligaciones.py -k "tributario_concepto_vacio or tributario_fecha_origen_posterior" -v`
Expected: 2 tests FAIL.

- [ ] **Step 3: Cablear la validación**

En `app/views/obligaciones.py`, `_guardar_tributario` pasa de:

```python
    def _guardar_tributario(self) -> int:
        categoria = self.combo_categoria.currentData()

        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())

        valor = Decimal("0.00")
```

a:

```python
    def _guardar_tributario(self) -> int:
        categoria = self.combo_categoria.currentData()
        self._validar_concepto_no_vacio()

        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())
        self._validar_fecha_no_posterior_a_corte(fecha_origen)

        valor = Decimal("0.00")
```

(el resto del método no cambia).

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: todos PASS (archivo completo, ~65 tests).

- [ ] **Step 5: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint24): validar concepto no vacio y fecha vs corte en obligaciones tributarias

EOF
)"
```

---

### Task 7: `parametro_service.agregar_valor` — signo, orden de fechas y solapamiento de tramos

**Files:**
- Modify: `app/services/parametro_service.py:260-292` (`agregar_valor`)
- Modify: `app/views/configuracion.py:82-102` (`ParametroFormDialog.guardar`, quitar chequeo duplicado)
- Test: `tests/services/test_parametro_service.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/services/test_parametro_service.py`:

```python
def test_agregar_valor_rechaza_valor_negativo():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor("USURA_MULTIPLICADOR", Decimal("-1.5"), date(2026, 1, 1), "abogado1")


def test_agregar_valor_rechaza_valor_cero():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor("USURA_MULTIPLICADOR", Decimal("0"), date(2026, 1, 1), "abogado1")


def test_agregar_valor_rechaza_vigente_hasta_anterior_a_vigente_desde():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor(
            "IBC_CONSUMO_ORDINARIO", Decimal("16.24"), date(2026, 2, 1), "abogado1",
            vigente_hasta=date(2026, 1, 1),
        )


def test_agregar_valor_rechaza_tramo_cerrado_solapado():
    from app.services.parametro_service import agregar_valor

    agregar_valor(
        "IBC_CONSUMO_ORDINARIO", Decimal("16.24"), date(2026, 1, 1), "abogado1",
        vigente_hasta=date(2026, 1, 31),
    )
    with pytest.raises(ValueError):
        agregar_valor(
            "IBC_CONSUMO_ORDINARIO", Decimal("16.50"), date(2026, 1, 15), "abogado1",
            vigente_hasta=date(2026, 2, 15),
        )


def test_agregar_valor_permite_tramo_cerrado_consecutivo_sin_solape():
    from app.services.parametro_service import agregar_valor

    agregar_valor(
        "IBC_CONSUMO_ORDINARIO", Decimal("16.24"), date(2026, 1, 1), "abogado1",
        vigente_hasta=date(2026, 1, 31),
    )
    fila = agregar_valor(
        "IBC_CONSUMO_ORDINARIO", Decimal("16.82"), date(2026, 2, 1), "abogado1",
        vigente_hasta=date(2026, 2, 28),
    )
    assert fila.valor == Decimal("16.82")
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `pytest tests/services/test_parametro_service.py -k "rechaza_valor_negativo or rechaza_valor_cero or rechaza_vigente_hasta_anterior or rechaza_tramo_cerrado_solapado" -v`
Expected: 4 tests FAIL (`test_agregar_valor_permite_tramo_cerrado_consecutivo_sin_solape` ya pasa hoy, es
solo para fijar el comportamiento correcto de "no solapado" antes de tocar el código).

- [ ] **Step 3: Implementar las 3 validaciones en `agregar_valor`**

En `app/services/parametro_service.py`, la función completa pasa de:

```python
def agregar_valor(
    clave: str,
    valor: Decimal,
    vigente_desde: date,
    usuario: str,
    motivo: str | None = None,
    vigente_hasta: date | None = None,
) -> ParametroLegal:
    """Inserta una fila nueva (append-only: nunca modifica ni borra filas
    existentes). Usada por la GUI (app/views/configuracion.py)."""
    info = _validar_clave(clave)
    if info.modo == ModoResolucion.TRAMO_CERRADO and vigente_hasta is None:
        raise ValueError(f"'{clave}' requiere 'vigente_hasta' (modo TRAMO_CERRADO).")
    if info.modo != ModoResolucion.TRAMO_CERRADO and vigente_hasta is not None:
        raise ValueError(f"'{clave}' no admite 'vigente_hasta' (modo {info.modo.value}).")

    session = session_module.get_session()
    try:
        fila = ParametroLegal(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            usuario=usuario,
            motivo=motivo,
            creado_en=datetime.now(),
        )
        session.add(fila)
        session.commit()
        session.refresh(fila)
        return fila
    finally:
        session.close()
```

a:

```python
def agregar_valor(
    clave: str,
    valor: Decimal,
    vigente_desde: date,
    usuario: str,
    motivo: str | None = None,
    vigente_hasta: date | None = None,
) -> ParametroLegal:
    """Inserta una fila nueva (append-only: nunca modifica ni borra filas
    existentes). Usada por la GUI (app/views/configuracion.py)."""
    info = _validar_clave(clave)
    if info.modo == ModoResolucion.TRAMO_CERRADO and vigente_hasta is None:
        raise ValueError(f"'{clave}' requiere 'vigente_hasta' (modo TRAMO_CERRADO).")
    if info.modo != ModoResolucion.TRAMO_CERRADO and vigente_hasta is not None:
        raise ValueError(f"'{clave}' no admite 'vigente_hasta' (modo {info.modo.value}).")
    if valor <= Decimal("0"):
        raise ValueError("El valor debe ser positivo.")
    if vigente_hasta is not None and vigente_hasta < vigente_desde:
        raise ValueError("'vigente_hasta' no puede ser anterior a 'vigente_desde'.")

    session = session_module.get_session()
    try:
        if info.modo == ModoResolucion.TRAMO_CERRADO:
            tramo_solapado = (
                session.query(ParametroLegal)
                .filter(
                    ParametroLegal.clave == clave,
                    ParametroLegal.vigente_desde <= vigente_hasta,
                    ParametroLegal.vigente_hasta >= vigente_desde,
                )
                .first()
            )
            if tramo_solapado is not None:
                raise ValueError(
                    f"El tramo {vigente_desde} a {vigente_hasta} se solapa con un tramo "
                    f"existente de '{clave}' ({tramo_solapado.vigente_desde} a "
                    f"{tramo_solapado.vigente_hasta})."
                )
        fila = ParametroLegal(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            usuario=usuario,
            motivo=motivo,
            creado_en=datetime.now(),
        )
        session.add(fila)
        session.commit()
        session.refresh(fila)
        return fila
    finally:
        session.close()
```

- [ ] **Step 4: Quitar el chequeo duplicado en `configuracion.py`**

En `app/views/configuracion.py`, dentro de `ParametroFormDialog.guardar()`, cambiar:

```python
        vigente_hasta = None
        if info.modo == ModoResolucion.TRAMO_CERRADO:
            qdate_hasta = self.campo_vigente_hasta.date()
            vigente_hasta = date(qdate_hasta.year(), qdate_hasta.month(), qdate_hasta.day())
            if vigente_hasta < vigente_desde:
                raise ValueError("'Vigente hasta' no puede ser anterior a 'Vigente desde'.")
```

a:

```python
        vigente_hasta = None
        if info.modo == ModoResolucion.TRAMO_CERRADO:
            qdate_hasta = self.campo_vigente_hasta.date()
            vigente_hasta = date(qdate_hasta.year(), qdate_hasta.month(), qdate_hasta.day())
```

(la validación de orden de fechas ahora la hace `agregar_valor()`, llamado más abajo en el mismo método —
el `ValueError` sigue burbujeando igual hacia `_guardar_y_cerrar()`).

- [ ] **Step 5: Correr toda la suite de parámetros y configuración para verificar que pasa**

Run: `pytest tests/services/test_parametro_service.py tests/views/test_configuracion.py -v`
Expected: todos PASS (incluye
`test_parametro_form_dialog_vigente_hasta_anterior_a_desde_lanza_value_error`, que ahora depende de la
validación movida al service).

- [ ] **Step 6: Commit**

```bash
git add app/services/parametro_service.py app/views/configuracion.py tests/services/test_parametro_service.py
git commit -m "$(cat <<'EOF'
feat(sprint24): rechazar valor no positivo y tramos TRAMO_CERRADO solapados en agregar_valor

EOF
)"
```

---

### Task 8: Suite completa y cierre del sprint en `Pendientes.md`

**Files:**
- Modify: `Pendientes.md` (sección "Sprint 24", agregar bloque de cierre)

- [ ] **Step 1: Correr toda la suite del proyecto**

Run: `pytest -v`
Expected: todos los tests en verde (los ~10 nuevos de este plan más los existentes, ningún cambio de
comportamiento en los casos ya cubiertos).

- [ ] **Step 2: Agregar el bloque de cierre en `Pendientes.md`**

En la sección `## Sprint 24 — Validación de datos...`, inmediatamente después de la línea:

```
**Definición de Hecho:**
```

Antes de esa línea, agregar (siguiendo el mismo formato de cierre usado en Sprint 23):

```markdown
**Estado:** Implementado (2026-08-02) — ver
`docs/superpowers/specs/2026-08-01-sprint24-validacion-datos-design.md` y
`docs/superpowers/plans/2026-08-02-sprint24-validacion-datos.md`. Decisiones tomadas con el usuario
durante el brainstorming previo (no asumidas unilateralmente):
- Rango de sentido común para tasas/IBC en `ObligacionFormDialog`: `[0, 1000]` (%), plano y sin relación
  con el cálculo de usura (`usury_validator.py` sigue siendo la única fuente de verdad legal, y sigue
  corriendo solo al liquidar). Se eligió sobre un tope de 100% para no arriesgar falsos rechazos de tasas
  moratorias comerciales legítimas que superen 100% anual.
- La validación cruzada "fecha de origen/inicio no posterior a la fecha de corte del expediente" aplica a
  **las 6 áreas** (incluye Laboral, donde el campo se reutiliza como "fecha de inicio del contrato", y
  Tributario) — no solo a Civil/Familia y Comercial como sugería literalmente el hallazgo original.
- `parametro_service.agregar_valor` rechaza `valor <= 0` para **cualquier clave** del catálogo, sin
  distinción — ninguna clave cargada hoy (tasas, SMLMV, IPC, UVT, plazos en meses, puntos de descuento)
  tiene sentido legal en cero.

`app/views/configuracion.py` perdió su chequeo local de `vigente_hasta < vigente_desde` (ahora vive en el
service, que es donde debía estar desde el principio — cualquier otro caller, no solo la GUI, queda
protegido). No se tocó `README.md`/`docs/GUIA_USUARIO.md`: este sprint corrige validación de datos sobre
módulos ya documentados, no agrega ni cambia funcionalidad visible para el usuario final.
```

- [ ] **Step 3: Commit**

```bash
git add Pendientes.md
git commit -m "$(cat <<'EOF'
docs(sprint24): cerrar sprint de validacion de datos en formularios y parametro_service

EOF
)"
```

---

## Self-review notes

- **Cobertura del spec:** rangos de tasa/IBC (Task 1, 4), rangos de porcentaje honorarios/costas (Task 2),
  positividad `cantidad_smlmv_uvt` (Task 3), concepto no vacío (Task 1, 5, 6), fecha vs. corte (Task 1, 5,
  6), `agregar_valor` signo/orden/solapamiento (Task 7), cierre de sprint (Task 8) — las 8 tareas cubren
  cada bullet de "Código nuevo a crear" del spec.
- **Sin placeholders:** cada paso trae el código completo a pegar, no descripciones genéricas.
- **Consistencia de tipos:** `_validar_rango`, `_validar_concepto_no_vacio` y
  `_validar_fecha_no_posterior_a_corte` se definen una sola vez en Task 1 y se reutilizan verbatim
  (mismos nombres, misma firma) en las Tasks 2-6.
