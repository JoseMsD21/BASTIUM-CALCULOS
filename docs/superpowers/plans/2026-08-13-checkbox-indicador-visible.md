# Checkbox con indicador invisible (claro y oscuro) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hacer visible el recuadro (indicador) de cualquier `QCheckBox` de la app, marcado o sin marcar, en modo claro y en modo oscuro.

**Architecture:** Agregar un bloque `QCheckBox::indicator` (con estados `:hover`, `:checked`, `:checked:hover`, `:disabled`, `:checked:disabled`) a `resources/theme.qss` y su equivalente a `resources/theme_dark.qss`, usando exclusivamente los colores de marca ya documentados en el encabezado de cada archivo. El estado "marcado" se representa con relleno de color solido (sin glifo de tilde dibujado encima) — no se crea ningun asset SVG nuevo, evitando el riesgo de un `image:` de QSS mal referenciado.

**Tech Stack:** Qt Style Sheets (QSS), pytest para verificar el contenido de los archivos `.qss`.

---

### Task 1: Test que falla — modo claro define el indicador del checkbox

**Files:**
- Create: `tests/core/test_theme_qss.py`

- [ ] **Step 1: Escribir el test que falla**

```python
from pathlib import Path

_RESOURCES_DIR = Path(__file__).resolve().parents[2] / "resources"
THEME_QSS = _RESOURCES_DIR / "theme.qss"
THEME_DARK_QSS = _RESOURCES_DIR / "theme_dark.qss"


def test_theme_claro_define_indicador_de_checkbox():
    contenido = THEME_QSS.read_text(encoding="utf-8")
    assert "QCheckBox::indicator {" in contenido
    assert "QCheckBox::indicator:checked {" in contenido
    assert "QCheckBox::indicator:hover {" in contenido
    assert "QCheckBox::indicator:disabled {" in contenido


def test_theme_claro_indicador_checkbox_usa_colores_de_marca():
    contenido = THEME_QSS.read_text(encoding="utf-8")
    bloque_normal = contenido.split("QCheckBox::indicator {", 1)[1].split("}", 1)[0]
    assert "#D8CDBB" in bloque_normal  # borde estandar sin marcar
    bloque_checked = contenido.split("QCheckBox::indicator:checked {", 1)[1].split("}", 1)[0]
    assert "#AE1C21" in bloque_checked  # primario burdeos al marcar
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/core/test_theme_qss.py -v`
Expected: FAIL — `resources/theme.qss` no existe o no tiene `QCheckBox::indicator`, ambos asserts de la primera funcion fallan con `AssertionError`.

- [ ] **Step 3: Commit**

```bash
git add tests/core/test_theme_qss.py
git commit -m "test: agregar test que falla para el indicador de QCheckBox en theme.qss"
```

---

### Task 2: Implementar el indicador en `resources/theme.qss` (modo claro)

**Files:**
- Modify: `resources/theme.qss:182-202` (bloque "Campos de entrada", justo antes de "Tablas")

- [ ] **Step 1: Insertar el bloque `QCheckBox` entre el fin de "Campos de entrada" (línea 201, `QLineEdit:disabled, ...`) y el comentario `/* --- Tablas ... --- */` (línea 203)**

Texto exacto a insertar (nueva sección, con su propio comentario de cabecera):

```css
/* --- Checkbox (indicador visible en ambos temas: ver comentario de la
 * paleta arriba). El estado "marcado" se muestra con relleno de color solido
 * (sin glifo de tilde dibujado encima) -- una vez que QSS define
 * background-color/border en QCheckBox::indicator, Qt deja de dibujar el
 * check nativo del estilo Fusion, asi que el relleno solido es la señal
 * visual de "marcado" en vez de un tilde. --- */

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid #D8CDBB;
    border-radius: 3px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:hover {
    border: 1.5px solid #AE1C21;
}

QCheckBox::indicator:checked {
    border: 1.5px solid #AE1C21;
    background-color: #AE1C21;
}

QCheckBox::indicator:checked:hover {
    border: 1.5px solid #931116;
    background-color: #931116;
}

QCheckBox::indicator:disabled {
    border: 1.5px solid #D8CDBB;
    background-color: #F5F1E9;
}

QCheckBox::indicator:checked:disabled {
    border: 1.5px solid #D8CDBB;
    background-color: #A69C92;
}
```

- [ ] **Step 2: Correr el test del Task 1 para confirmar que ahora pasa**

Run: `pytest tests/core/test_theme_qss.py -v`
Expected: PASS (2 tests)

- [ ] **Step 3: Commit**

```bash
git add resources/theme.qss
git commit -m "fix: agregar indicador visible de QCheckBox al tema claro"
```

---

### Task 3: Test que falla — modo oscuro define el indicador del checkbox

**Files:**
- Modify: `tests/core/test_theme_qss.py`

- [ ] **Step 1: Agregar el test que falla, al final del archivo**

```python
def test_theme_oscuro_define_indicador_de_checkbox():
    contenido = THEME_DARK_QSS.read_text(encoding="utf-8")
    assert "QCheckBox::indicator {" in contenido
    assert "QCheckBox::indicator:checked {" in contenido
    assert "QCheckBox::indicator:hover {" in contenido
    assert "QCheckBox::indicator:disabled {" in contenido


def test_theme_oscuro_indicador_checkbox_usa_colores_de_marca():
    contenido = THEME_DARK_QSS.read_text(encoding="utf-8")
    bloque_normal = contenido.split("QCheckBox::indicator {", 1)[1].split("}", 1)[0]
    assert "#4A4039" in bloque_normal  # borde estandar sin marcar (modo oscuro)
    bloque_checked = contenido.split("QCheckBox::indicator:checked {", 1)[1].split("}", 1)[0]
    assert "#D9484D" in bloque_checked  # primario burdeos claro al marcar
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/core/test_theme_qss.py -v`
Expected: FAIL — los 2 tests nuevos fallan, los 2 del Task 1/2 siguen en PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/core/test_theme_qss.py
git commit -m "test: agregar test que falla para el indicador de QCheckBox en theme_dark.qss"
```

---

### Task 4: Implementar el indicador en `resources/theme_dark.qss` (modo oscuro)

**Files:**
- Modify: `resources/theme_dark.qss:159-179` (bloque "Campos de entrada", justo antes de "Tablas")

- [ ] **Step 1: Insertar el bloque `QCheckBox` entre el fin de "Campos de entrada" (línea 178, `QLineEdit:disabled, ...`) y el comentario `/* --- Tablas ... --- */` (línea 180)**

```css
/* --- Checkbox (ver resources/theme.qss para el detalle completo del
 * criterio de diseño -- mismo esquema, colores del modo oscuro). --- */

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid #4A4039;
    border-radius: 3px;
    background-color: #2A2422;
}

QCheckBox::indicator:hover {
    border: 1.5px solid #D9484D;
}

QCheckBox::indicator:checked {
    border: 1.5px solid #D9484D;
    background-color: #D9484D;
}

QCheckBox::indicator:checked:hover {
    border: 1.5px solid #C93338;
    background-color: #C93338;
}

QCheckBox::indicator:disabled {
    border: 1.5px solid #4A4039;
    background-color: #332C29;
}

QCheckBox::indicator:checked:disabled {
    border: 1.5px solid #4A4039;
    background-color: #6B5F57;
}
```

- [ ] **Step 2: Correr toda la suite del archivo de test para confirmar que los 4 pasan**

Run: `pytest tests/core/test_theme_qss.py -v`
Expected: PASS (4 tests)

- [ ] **Step 3: Commit**

```bash
git add resources/theme_dark.qss
git commit -m "fix: agregar indicador visible de QCheckBox al tema oscuro"
```

---

### Task 5: Verificación visual manual + suite completa

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Correr la suite completa del proyecto**

Run: `pytest -q`
Expected: todos los tests existentes siguen en verde (este cambio no toca ningún `.py`, así que no debería romper nada; confirma que no hay una dependencia oculta con el contenido exacto de los `.qss`).

- [ ] **Step 2: Arrancar la app y verificar visualmente en modo claro**

Run: `python main.py` (o `Iniciar BASTIUM.bat`)

Navegar a un expediente existente (o crear uno de prueba) → "Agregar obligación" → confirmar que las casillas "Demanda judicial (habilita anatocismo, Art. 886 C.Co.)" y "¿Hay acuerdo posterior de capitalización?" muestran un recuadro con borde visible sin marcar, y un recuadro relleno de color burdeos al marcar.

- [ ] **Step 3: Activar modo oscuro y repetir la verificación**

En Configuraciones › Apariencia, activar "Modo oscuro". Repetir el mismo flujo de "Agregar obligación" y confirmar que el recuadro es visible (borde `#4A4039` sin marcar, relleno `#D9484D` marcado) contra el fondo oscuro. Verificar también las casillas de área del derecho en Configuraciones › Parámetros › "+ Agregar valor nuevo".

- [ ] **Step 4: Commit final (si hubo algún ajuste de la verificación manual)**

Si el Step 2/3 no encontró ningún problema, no hay nada que commitear en este task — los commits de los Tasks 1-4 ya cubren el cambio completo.
