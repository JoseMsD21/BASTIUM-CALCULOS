# Restablecer datos de fábrica Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar una acción en Configuraciones que borra todos los expedientes y los parámetros legales creados por un usuario (dejando los de sistema intactos), restaura el tema a claro, y crea un backup automático de la base de datos antes de borrar nada.

**Architecture:** Un servicio nuevo (`app/services/restablecer_service.py`) con dos funciones independientes y testeables por separado: `crear_backup_de_base_de_datos()` (copia de archivo, sin tocar el ORM) y `restablecer_datos_fabrica()` (borrado ORM: expedientes en cascada + parámetros de usuario). Una vista nueva (`app/views/restablecer.py`) orquesta ambas funciones en el orden correcto tras una confirmación explícita (escribir "RESTABLECER"), y se cuelga como tercera sección de `ConfiguracionesView` (Sprint 66), junto a Parámetros y Apariencia.

**⚠️ Dependencia real:** `restablecer_datos_fabrica()` filtra `ParametroLegal.creado_por_sistema.is_(False)` — esa columna la agrega el plan **"Parámetros: editar/eliminar de usuario, vigencia clara, unidad y tooltips"** (`docs/superpowers/plans/2026-08-13-parametros-crud-usuario.md`, Task 1: migración `scripts/migrate_creado_por_sistema.py`). **Ese plan debe estar aplicado (al menos su Task 1, idealmente completo y mergeado a main) antes de empezar el Task 2 de este plan** — sin la columna, `ParametroLegal.creado_por_sistema` no existe y el `filter()` lanza `sqlalchemy.exc.OperationalError`. El Task 1 de este plan (backup de archivo) no tiene esa dependencia y puede hacerse en cualquier momento.

**Tech Stack:** SQLAlchemy ORM (`database.session.get_session()`), PySide6 (QDialog/QWidget), pytest + pytest-qt (`qtbot`), `shutil.copy2` para el backup de archivo.

---

### Task 1: `crear_backup_de_base_de_datos` — copia de archivo antes de borrar

**Files:**
- Create: `app/services/restablecer_service.py`
- Test: `tests/services/test_restablecer_service.py`

- [ ] **Step 1: Escribir el test que falla**

```python
from pathlib import Path

from app.services.restablecer_service import crear_backup_de_base_de_datos


def test_crear_backup_de_base_de_datos_copia_el_archivo(tmp_path):
    origen = tmp_path / "bastium.db"
    origen.write_bytes(b"contenido-de-prueba-sqlite")

    destino = crear_backup_de_base_de_datos(db_path=origen)

    assert destino.exists()
    assert destino.parent == tmp_path / "backups"
    assert destino.name.startswith("bastium.db.bak-")
    assert destino.read_bytes() == b"contenido-de-prueba-sqlite"


def test_crear_backup_de_base_de_datos_crea_la_carpeta_backups_si_no_existe(tmp_path):
    origen = tmp_path / "bastium.db"
    origen.write_bytes(b"x")
    assert not (tmp_path / "backups").exists()

    crear_backup_de_base_de_datos(db_path=origen)

    assert (tmp_path / "backups").is_dir()
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/services/test_restablecer_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.restablecer_service'`

- [ ] **Step 3: Implementar `crear_backup_de_base_de_datos`**

```python
"""Servicio de "Restablecer datos de fábrica" (Configuraciones › Restablecer):
borra expedientes y parametros legales de usuario, dejando la app como recien
instalada. Ver docs/superpowers/specs/2026-08-13-restablecer-datos-fabrica-design.md.

Dos funciones deliberadamente separadas (en vez de una sola que haga todo):
`crear_backup_de_base_de_datos` es I/O de archivo puro, sin sesion SQLAlchemy
-- se puede testear con cualquier archivo temporal, sin la fixture de base en
memoria. `restablecer_datos_fabrica` es ORM puro, sin tocar el sistema de
archivos -- se testea con la misma fixture en memoria que el resto de
tests/services/. El llamador (RestablecerView) orquesta ambas en el orden
correcto: primero el backup, y solo si tuvo exito, el borrado."""

import shutil
from datetime import datetime
from pathlib import Path

import database.session as session_module
from database.database import DB_PATH
from database.models import Expediente, ParametroLegal


def crear_backup_de_base_de_datos(db_path: Path | None = None) -> Path:
    """Copia el archivo de base de datos a `<carpeta-del-archivo>/backups/`,
    con el mismo patron de nombre (`<nombre>.bak-<timestamp>`) que ya usan los
    backups manuales existentes en esa carpeta (Sprint 64). `db_path` es
    opcional (default: `database.database.DB_PATH`, la base activa real) --
    los tests lo pasan explicito para nunca tocar el archivo real.

    Puede lanzar OSError (permiso denegado, disco lleno, etc.) -- el llamador
    debe abortar el resto del restablecimiento si esto falla, para nunca
    borrar datos sin backup exitoso."""
    origen = db_path if db_path is not None else DB_PATH
    carpeta_backups = origen.parent / "backups"
    carpeta_backups.mkdir(parents=True, exist_ok=True)
    marca_de_tiempo = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = carpeta_backups / f"{origen.name}.bak-{marca_de_tiempo}"
    shutil.copy2(origen, destino)
    return destino


def restablecer_datos_fabrica() -> None:
    """Borra TODOS los expedientes (obligaciones/abonos/eventos_laborales/
    descuentos_laborales/audit_logs se van en cascada, cascade="all,
    delete-orphan" en Expediente -- ver database/models.py) y todos los
    parametros_legales creados por un usuario (creado_por_sistema=False); los
    de sistema quedan intactos. No crea backup ni toca el tema -- eso es
    responsabilidad del llamador (RestablecerView), que orquesta backup +
    este borrado + reset de tema en el orden correcto."""
    session = session_module.get_session()
    try:
        for expediente in session.query(Expediente).all():
            session.delete(expediente)
        session.query(ParametroLegal).filter(
            ParametroLegal.creado_por_sistema.is_(False)
        ).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/services/test_restablecer_service.py -v`
Expected: PASS (2 tests) — nota: `restablecer_datos_fabrica` no tiene test todavía (Task 2), así que este archivo por ahora solo importa `crear_backup_de_base_de_datos` en los tests, pero define ambas funciones (la segunda se prueba en el próximo task).

- [ ] **Step 5: Commit**

```bash
git add app/services/restablecer_service.py tests/services/test_restablecer_service.py
git commit -m "feat: agregar crear_backup_de_base_de_datos y restablecer_datos_fabrica"
```

---

### Task 2: `restablecer_datos_fabrica` — borrado ORM (requiere `creado_por_sistema`)

**Precondición:** la columna `ParametroLegal.creado_por_sistema` debe existir (ver advertencia de dependencia arriba). Verificar antes de empezar: `grep -n "creado_por_sistema" database/models.py` debe encontrar la columna.

**Files:**
- Modify: `tests/services/test_restablecer_service.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
from datetime import date, datetime
from decimal import Decimal

from app.services.parametro_service import agregar_valor
from app.services.restablecer_service import restablecer_datos_fabrica
from database.models import AreaDerecho, Expediente, Obligacion, ParametroLegal, TipoObligacion
from database.session import get_session


def _crear_expediente_con_obligacion() -> int:
    session = get_session()
    expediente = Expediente(radicado="2026-99999", area_derecho=AreaDerecho.CIVIL_FAMILIA)
    session.add(expediente)
    session.commit()
    session.refresh(expediente)
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Capital de prueba",
            valor=Decimal("1000000"),
            fecha_origen=date(2026, 1, 1),
            tasa_efectiva_anual=Decimal("6"),
            tasa_moratoria_anual=Decimal("24"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_restablecer_datos_fabrica_borra_expedientes_y_obligaciones_en_cascada():
    expediente_id = _crear_expediente_con_obligacion()

    restablecer_datos_fabrica()

    session = get_session()
    assert session.get(Expediente, expediente_id) is None
    assert session.query(Obligacion).count() == 0
    session.close()


def test_restablecer_datos_fabrica_borra_solo_parametros_de_usuario():
    session = get_session()
    session.add(
        ParametroLegal(
            clave="USURA_MULTIPLICADOR",
            valor=Decimal("1.5"),
            vigente_desde=date(1900, 1, 1),
            usuario="sistema",
            creado_en=datetime.now(),
            creado_por_sistema=True,
        )
    )
    session.commit()
    session.close()
    agregar_valor(
        "HONORARIOS_TOTAL_PCT",
        Decimal("50"),
        date(2026, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.HONORARIOS],
        unidad="%",
    )

    restablecer_datos_fabrica()

    session = get_session()
    claves_restantes = [fila.clave for fila in session.query(ParametroLegal).all()]
    assert claves_restantes == ["USURA_MULTIPLICADOR"]
    session.close()
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/services/test_restablecer_service.py -v`
Expected: FAIL si la columna `creado_por_sistema` todavía no existe (`OperationalError`), o FAIL por lógica si `restablecer_datos_fabrica` todavía no filtra correctamente (no debería pasar, ya se implementó en el Task 1 — este paso es la confirmación de que el Task 1 ya cubre el comportamiento correcto).

- [ ] **Step 3: Si falla por lógica (no por columna faltante), ajustar `restablecer_datos_fabrica`**

El código del Task 1 ya implementa el filtro correcto (`creado_por_sistema.is_(False)`) — este paso solo aplica si la revisión encuentra una discrepancia real entre el código y estos tests.

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/services/test_restablecer_service.py -v`
Expected: PASS (4 tests en total, contando el Task 1)

- [ ] **Step 5: Commit**

```bash
git add tests/services/test_restablecer_service.py
git commit -m "test: cubrir restablecer_datos_fabrica con expedientes en cascada y parametros de usuario"
```

---

### Task 3: `ConfirmarRestablecerDialog` — confirmación escrita

**Files:**
- Create: `app/views/restablecer.py`
- Test: `tests/views/test_restablecer.py`

- [ ] **Step 1: Escribir el test que falla**

```python
from app.views.restablecer import ConfirmarRestablecerDialog


def test_confirmar_restablecer_dialog_boton_deshabilitado_por_defecto(qtbot):
    dialogo = ConfirmarRestablecerDialog()
    qtbot.addWidget(dialogo)
    assert dialogo.boton_confirmar.isEnabled() is False


def test_confirmar_restablecer_dialog_boton_se_habilita_con_el_texto_exacto(qtbot):
    dialogo = ConfirmarRestablecerDialog()
    qtbot.addWidget(dialogo)

    dialogo.campo_confirmacion.setText("restablecer")
    assert dialogo.boton_confirmar.isEnabled() is False

    dialogo.campo_confirmacion.setText("RESTABLECER")
    assert dialogo.boton_confirmar.isEnabled() is True


def test_confirmar_restablecer_dialog_confirmar_acepta_el_dialogo(qtbot):
    from PySide6.QtWidgets import QDialog

    dialogo = ConfirmarRestablecerDialog()
    qtbot.addWidget(dialogo)
    dialogo.campo_confirmacion.setText("RESTABLECER")
    dialogo.boton_confirmar.click()
    assert dialogo.result() == QDialog.DialogCode.Accepted
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/views/test_restablecer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.views.restablecer'`

- [ ] **Step 3: Implementar `ConfirmarRestablecerDialog`**

```python
"""Sección "Restablecer" de Configuraciones: ConfirmarRestablecerDialog (esta
clase) exige escribir "RESTABLECER" para habilitar el botón de confirmar --
misma filosofía de "sin papelera, definitivo tras confirmar" que ya usan
Eliminar en Obligaciones/Abonos (Sprint 60), reforzada porque el radio de
acción de esta acción es TODA la base, no una fila."""

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.apariencia import MODO_CLARO, aplicar_tema, guardar_modo_tema
from app.services.restablecer_service import (
    crear_backup_de_base_de_datos,
    restablecer_datos_fabrica,
)
from app.views.form_utils import hacer_redimensionable


class ConfirmarRestablecerDialog(QDialog):
    TEXTO_CONFIRMACION = "RESTABLECER"

    def __init__(self, parent=None):
        super().__init__(parent)
        hacer_redimensionable(self)
        self.setWindowTitle("Confirmar restablecimiento")

        advertencia = QLabel(
            "Esta acción borra TODOS los expedientes, obligaciones, abonos, eventos, "
            "descuentos y los parámetros legales que hayas cargado tú mismo (los del "
            "sistema no se tocan). El tema visual vuelve a claro. No se puede deshacer, "
            "salvo restaurando el backup automático que se crea antes de borrar.\n\n"
            f"Escribe {self.TEXTO_CONFIRMACION} para habilitar el botón de confirmar."
        )
        advertencia.setWordWrap(True)

        self.campo_confirmacion = QLineEdit()
        self.campo_confirmacion.textChanged.connect(self._actualizar_estado_boton)

        self.boton_confirmar = QPushButton("Restablecer datos de fábrica")
        self.boton_confirmar.setProperty("class", "destructive")
        self.boton_confirmar.setEnabled(False)
        self.boton_confirmar.clicked.connect(self.accept)

        boton_cancelar = QPushButton("Cancelar")
        boton_cancelar.setProperty("class", "secondary")
        boton_cancelar.clicked.connect(self.reject)

        botones = QHBoxLayout()
        botones.addWidget(boton_cancelar)
        botones.addWidget(self.boton_confirmar)

        layout = QVBoxLayout()
        layout.addWidget(advertencia)
        layout.addWidget(self.campo_confirmacion)
        layout.addLayout(botones)
        self.setLayout(layout)

    def _actualizar_estado_boton(self, texto: str) -> None:
        self.boton_confirmar.setEnabled(texto == self.TEXTO_CONFIRMACION)
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/views/test_restablecer.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/views/restablecer.py tests/views/test_restablecer.py
git commit -m "feat: agregar ConfirmarRestablecerDialog con confirmacion escrita"
```

---

### Task 4: `RestablecerView` — orquesta backup + borrado + reset de tema

**Files:**
- Modify: `app/views/restablecer.py`
- Modify: `tests/views/test_restablecer.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
from unittest.mock import patch

from PySide6.QtWidgets import QDialog

from app.views.restablecer import RestablecerView


def test_restablecer_view_tiene_boton_destructivo(qtbot):
    vista = RestablecerView()
    qtbot.addWidget(vista)
    assert vista.boton_restablecer.property("class") == "destructive"


def test_restablecer_view_no_hace_nada_si_se_cancela_la_confirmacion(qtbot, tmp_path):
    vista = RestablecerView()
    qtbot.addWidget(vista)

    with (
        patch("app.views.restablecer.ConfirmarRestablecerDialog.exec", return_value=0),
        patch("app.views.restablecer.crear_backup_de_base_de_datos") as mock_backup,
        patch("app.views.restablecer.restablecer_datos_fabrica") as mock_restablecer,
    ):
        vista._restablecer()

    mock_backup.assert_not_called()
    mock_restablecer.assert_not_called()


def test_restablecer_view_confirmado_llama_backup_y_restablecer_en_orden(qtbot, tmp_path):
    vista = RestablecerView()
    qtbot.addWidget(vista)
    orden_llamadas = []

    with (
        patch(
            "app.views.restablecer.ConfirmarRestablecerDialog.exec",
            return_value=QDialog.DialogCode.Accepted,
        ),
        patch(
            "app.views.restablecer.crear_backup_de_base_de_datos",
            side_effect=lambda: orden_llamadas.append("backup") or (tmp_path / "x.bak"),
        ) as mock_backup,
        patch(
            "app.views.restablecer.restablecer_datos_fabrica",
            side_effect=lambda: orden_llamadas.append("restablecer"),
        ) as mock_restablecer,
        patch("app.views.restablecer.QMessageBox.information"),
    ):
        vista._restablecer()

    mock_backup.assert_called_once()
    mock_restablecer.assert_called_once()
    assert orden_llamadas == ["backup", "restablecer"]


def test_restablecer_view_no_borra_si_el_backup_falla(qtbot):
    vista = RestablecerView()
    qtbot.addWidget(vista)

    with (
        patch(
            "app.views.restablecer.ConfirmarRestablecerDialog.exec",
            return_value=QDialog.DialogCode.Accepted,
        ),
        patch(
            "app.views.restablecer.crear_backup_de_base_de_datos",
            side_effect=OSError("disco lleno"),
        ),
        patch("app.views.restablecer.restablecer_datos_fabrica") as mock_restablecer,
        patch("app.views.restablecer.QMessageBox.critical") as mock_critical,
    ):
        vista._restablecer()

    mock_restablecer.assert_not_called()
    mock_critical.assert_called_once()
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_restablecer.py -v`
Expected: FAIL — `AttributeError: module 'app.views.restablecer' has no attribute 'RestablecerView'`

- [ ] **Step 3: Implementar `RestablecerView`, agregado al final de `app/views/restablecer.py`**

```python
class RestablecerView(QWidget):
    """Sección "Restablecer" de Configuraciones (ver design spec
    2026-08-13-restablecer-datos-fabrica-design.md): borra todos los
    expedientes y los parámetros legales de usuario, restaura el tema claro,
    con backup automático previo y confirmación escrita."""

    def __init__(self):
        super().__init__()

        descripcion = QLabel(
            "Borra todos los expedientes, obligaciones, abonos, eventos, descuentos y "
            "los parámetros legales que hayas cargado tú mismo, dejando la app como "
            "recién instalada (los parámetros de sistema y el tema claro por defecto "
            "quedan intactos/restaurados). Antes de borrar se crea automáticamente una "
            "copia de seguridad en la carpeta backups/."
        )
        descripcion.setWordWrap(True)

        self.boton_restablecer = QPushButton("Restablecer datos de fábrica")
        self.boton_restablecer.setProperty("class", "destructive")
        self.boton_restablecer.clicked.connect(self._restablecer)

        layout = QVBoxLayout()
        layout.addWidget(descripcion)
        layout.addWidget(self.boton_restablecer)
        layout.addStretch()
        self.setLayout(layout)

    def _restablecer(self) -> None:
        dialogo = ConfirmarRestablecerDialog(self)
        if not dialogo.exec():
            return
        try:
            ruta_backup = crear_backup_de_base_de_datos()
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error al crear el backup",
                f"No se pudo crear la copia de seguridad, no se borró nada:\n{error}",
            )
            return
        restablecer_datos_fabrica()
        guardar_modo_tema(MODO_CLARO)
        aplicar_tema(QApplication.instance(), MODO_CLARO)
        QMessageBox.information(
            self,
            "Restablecimiento completo",
            f"Se restablecieron los datos de fábrica.\nCopia de seguridad guardada en:\n{ruta_backup}",
        )
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_restablecer.py -v`
Expected: PASS (7 tests en total)

- [ ] **Step 5: Commit**

```bash
git add app/views/restablecer.py tests/views/test_restablecer.py
git commit -m "feat: agregar RestablecerView, orquesta backup + borrado + reset de tema"
```

---

### Task 5: Colgar "Restablecer" del submenú de `ConfiguracionesView`

**Files:**
- Modify: `app/views/configuraciones.py`
- Test: `tests/views/test_configuraciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_configuraciones.py` (revisar primero el archivo existente para seguir el mismo estilo de fixture/imports que ya usa para `mostrar_parametros`/`mostrar_apariencia`):

```python
def test_configuraciones_view_tiene_seccion_restablecer(qtbot):
    from app.views.configuraciones import ConfiguracionesView
    from app.views.restablecer import RestablecerView

    vista = ConfiguracionesView()
    qtbot.addWidget(vista)
    assert isinstance(vista.restablecer_view, RestablecerView)


def test_configuraciones_view_mostrar_restablecer_cambia_seccion_y_stack(qtbot):
    from app.views.configuraciones import ConfiguracionesView, SECCION_RESTABLECER

    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    vista.mostrar_restablecer()

    assert vista.seccion_actual == SECCION_RESTABLECER
    assert vista.etiqueta_seccion_actual() == "Restablecer"
    assert vista._stack_secciones.currentWidget() is vista.restablecer_view


def test_configuraciones_view_mostrar_restablecer_emite_seccion_cambiada(qtbot):
    from app.views.configuraciones import ConfiguracionesView, SECCION_RESTABLECER

    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    with qtbot.waitSignal(vista.seccion_cambiada, timeout=1000) as blocker:
        vista.mostrar_restablecer()
    assert blocker.args == [SECCION_RESTABLECER]
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_configuraciones.py -v`
Expected: FAIL — `AttributeError: 'ConfiguracionesView' object has no attribute 'restablecer_view'`

- [ ] **Step 3: Modificar `app/views/configuraciones.py`**

```python
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.views.apariencia import AparienciaView
from app.views.configuracion import ParametrosView
from app.views.restablecer import RestablecerView

SECCION_PARAMETROS = "parametros"
SECCION_APARIENCIA = "apariencia"
SECCION_RESTABLECER = "restablecer"

_ETIQUETA_POR_SECCION = {
    SECCION_PARAMETROS: "Parámetros",
    SECCION_APARIENCIA: "Apariencia",
    SECCION_RESTABLECER: "Restablecer",
}
```

Dentro de `ConfiguracionesView.__init__`, después de `self.apariencia_view = AparienciaView()`:

```python
        self.restablecer_view = RestablecerView()
```

Después de `self.boton_seccion_apariencia = QPushButton(" Apariencia")` / su `.clicked.connect(...)`:

```python
        self.boton_seccion_restablecer = QPushButton(" Restablecer")
        self.boton_seccion_restablecer.clicked.connect(self.mostrar_restablecer)
```

En el bloque del `submenu` (`layout_submenu.addWidget(self.boton_seccion_apariencia)`), agregar justo después:

```python
        layout_submenu.addWidget(self.boton_seccion_restablecer)
```

En el bloque de `self._stack_secciones` (después de `self._stack_secciones.addWidget(self.apariencia_view)`):

```python
        self._stack_secciones.addWidget(self.restablecer_view)
```

Nuevo método, junto a `mostrar_apariencia`:

```python
    def mostrar_restablecer(self) -> None:
        self._seccion_actual = SECCION_RESTABLECER
        self._stack_secciones.setCurrentWidget(self.restablecer_view)
        self._actualizar_estado_activo_submenu()
        self.seccion_cambiada.emit(self._seccion_actual)
```

En `_actualizar_estado_activo_submenu`, agregar el tercer botón siguiendo el mismo patrón `unpolish()/polish()` que ya usan los otros dos:

```python
        self.boton_seccion_restablecer.setProperty(
            "class", "primary" if self._seccion_actual == SECCION_RESTABLECER else "secondary"
        )
        self.boton_seccion_restablecer.style().unpolish(self.boton_seccion_restablecer)
        self.boton_seccion_restablecer.style().polish(self.boton_seccion_restablecer)
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_configuraciones.py -v`
Expected: PASS (todos, incluidos los 3 nuevos)

- [ ] **Step 5: Commit**

```bash
git add app/views/configuraciones.py tests/views/test_configuraciones.py
git commit -m "feat: agregar seccion Restablecer al submenu de Configuraciones"
```

---

### Task 6: Documentación (README, GUIA_USUARIO, CHANGELOG)

**Files:**
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: `docs/GUIA_USUARIO.md`** — buscar el párrafo (línea ~213-216 al momento de escribir este plan, puede haber corrido si otros sprints ya editaron el archivo) que dice:

```
5. **⚙ Configuraciones** — pantalla con dos secciones, elegibles desde un submenú lateral propio:
   **Parámetros** (tasas, topes, plazos e indicadores históricos legales) y **Apariencia** (el interruptor
   de modo oscuro/claro). Se abre desde el botón **"⚙ Configuraciones"** del panel lateral de navegación,
```

Reemplazar por:

```
5. **⚙ Configuraciones** — pantalla con tres secciones, elegibles desde un submenú lateral propio:
   **Parámetros** (tasas, topes, plazos e indicadores históricos legales), **Apariencia** (el interruptor
   de modo oscuro/claro) y **Restablecer** (borra todos los expedientes y los parámetros legales que hayas
   cargado tú mismo, con backup automático previo). Se abre desde el botón **"⚙ Configuraciones"** del
   panel lateral de navegación,
```

- [ ] **Step 2: Agregar una subsección nueva en `docs/GUIA_USUARIO.md`**, después de la sección "Modo oscuro / claro" (buscar el texto `**"Apariencia"** en el submenú de la izquierda. Márcalo para cambiar toda la aplicación a un tema oscuro` y ubicar el final de ese párrafo), agregar:

```markdown

**Restablecer datos de fábrica (Configuraciones → Restablecer):** borra TODOS los expedientes,
obligaciones, abonos, eventos, descuentos y los parámetros legales que hayas cargado tú mismo — los
parámetros de sistema no se tocan y el tema vuelve a claro. Antes de borrar se crea automáticamente una
copia de seguridad en la carpeta `backups/`. Pide escribir "RESTABLECER" para confirmar; no hay papelera
ni deshacer, solo restaurar el backup manualmente si te equivocas.
```

- [ ] **Step 3: `README.md`** — buscar la descripción de la pantalla de Configuraciones (mismo texto que en GUIA_USUARIO, buscar "Parámetros" y "Apariencia" juntos) y aplicar el mismo tipo de actualización: mencionar la tercera sección "Restablecer".

- [ ] **Step 4: `CHANGELOG.md`** — agregar una entrada nueva en la sección `[Unreleased]` (o crear una si no existe, siguiendo el formato Keep a Changelog que ya usa el archivo):

```markdown
### Added
- Sección "Restablecer" en Configuraciones: borra todos los expedientes y los parámetros legales
  creados por el usuario (deja los de sistema intactos), con backup automático previo y confirmación
  escrita.
```

- [ ] **Step 5: Commit**

```bash
git add docs/GUIA_USUARIO.md README.md CHANGELOG.md
git commit -m "docs: documentar la seccion Restablecer de Configuraciones"
```

---

### Task 7: Suite completa + verificación manual

- [ ] **Step 1: Correr la suite completa**

Run: `pytest -q`
Expected: todos los tests pasan, incluidos los nuevos de este plan.

- [ ] **Step 2: Correr `ruff check .`**

Run: `ruff check .`
Expected: "All checks passed!"

- [ ] **Step 3: Verificación manual**

Run: `python main.py`. Ir a Configuraciones › Restablecer. Confirmar: texto de advertencia visible, botón "Restablecer datos de fábrica" en rojo destructivo. Pulsar → confirmar que el botón de confirmar del diálogo empieza deshabilitado, se habilita solo al escribir exactamente "RESTABLECER", y que "Cancelar" no hace nada. Con datos de prueba cargados (un expediente + un parámetro agregado manualmente), confirmar el restablecimiento y verificar: el expediente desaparece de la lista, el parámetro de prueba desaparece de la tabla de Parámetros, se creó un archivo nuevo en `backups/`, y el tema quedó en claro.

- [ ] **Step 4: Commit final (si la verificación manual encontró algo que corregir)**

Si el Step 3 no encontró ningún problema, no hay nada que commitear en este task.
