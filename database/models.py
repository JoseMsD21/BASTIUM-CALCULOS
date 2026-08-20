from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class DecimalExacto(TypeDecorator):
    """Columna Numeric que preserva la precision exacta de Decimal
    almacenando como TEXT. SQLite le da afinidad NUMERIC a las columnas
    Numeric/DECIMAL declaradas y termina guardando el valor como REAL
    (float64), lo que pierde precision para Decimals de muchos digitos sin
    redondear (ej. el indice IPC acumulado, encadenado sin redondeo por
    diseno -- ver historical_index.py). Guardar como TEXT evita ese problema
    por completo, en cualquier backend."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # str(value) en vez de Decimal(value) directo: si la fila viene de una
        # tabla que todavia no fue recreada bajo este tipo (afinidad NUMERIC
        # heredada, valor ya almacenado como REAL), sqlite3 entrega un float.
        # Decimal(float) expone el ruido binario del float (ej. Decimal(0.06)
        # -> ...779553950749686919152736663818359375); pasar por str() primero
        # replica el comportamiento del procesador Numeric original de
        # SQLAlchemy, que tambien usa Decimal(str(value)), asi que como minimo
        # no empeora una fila legada respecto al tipo anterior.
        return Decimal(str(value))


class AreaDerecho(enum.Enum):
    CIVIL_FAMILIA = "CIVIL_FAMILIA"
    COMERCIAL = "COMERCIAL"
    LABORAL = "LABORAL"
    SANCIONATORIO = "SANCIONATORIO"
    HONORARIOS = "HONORARIOS"
    TRIBUTARIO = "TRIBUTARIO"


class TipoObligacion(enum.Enum):
    PUNTUAL = "PUNTUAL"
    RECURRENTE = "RECURRENTE"


class TipoReajusteAnual(enum.Enum):
    """Indice de reajuste anual de una cuota alimentaria (obligacion RECURRENTE
    de Civil/Familia, Sprint 41). NINGUNO (default) preserva el comportamiento
    anterior a este sprint: la obligacion recurrente se expande en tiempo real
    con RecurringScheduler dentro de CivilFamiliaStrategy.liquidar(), sin
    persistir cuotas hijas. SMMLV/IPC activan
    app.services.reajuste_anual.generar_cuotas_mensuales -- ver ese modulo y
    CivilFamiliaStrategy._eventos_de_obligacion para el wiring completo."""

    SMMLV = "SMMLV"
    IPC = "IPC"
    NINGUNO = "NINGUNO"


class TipoRecurrencia(enum.Enum):
    """Cadencia de una obligacion RECURRENTE (Sprint 73). MENSUAL (default)
    preserva el comportamiento de siempre: una cuota cada mes (cuota
    alimentaria tipica), generada por app.services.reajuste_anual (Sprint 41)
    o por RecurringScheduler en su forma efimera. FECHAS_ANUALES_FIJAS es un
    patron distinto reportado por el usuario (gastos de vestuario en
    junio/diciembre/cumpleanos del beneficiario, no una cuota mes a mes):
    solo se causan obligaciones en las fechas MM-DD listadas en
    `Obligacion.fechas_anuales_fijas`, cada año, via
    app.services.recurrencia_fechas_fijas.generar_cuotas_fechas_fijas.

    El cumpleanos del beneficiario se ingresa como una entrada MM-DD manual
    mas dentro de esa lista -- NO se deriva automaticamente de
    `Beneficiario.fecha_nacimiento` (esa entidad SI existe desde el Sprint 74,
    ver clase Beneficiario mas abajo); esa derivacion automatica especifica
    (agregar la fecha MM-DD del cumpleanos solo con marcar el beneficiario)
    quedo fuera del alcance de ese sprint y sigue pendiente si el usuario la
    pide."""

    MENSUAL = "MENSUAL"
    FECHAS_ANUALES_FIJAS = "FECHAS_ANUALES_FIJAS"


class TipoEventoLaboral(enum.Enum):
    SUSPENSION = "SUSPENSION"
    INCAPACIDAD_COMUN = "INCAPACIDAD_COMUN"
    INCAPACIDAD_LABORAL = "INCAPACIDAD_LABORAL"


class MotivoSuspension(enum.Enum):
    HUELGA = "HUELGA"
    LICENCIA_NO_REMUNERADA = "LICENCIA_NO_REMUNERADA"
    DISCIPLINARIA = "DISCIPLINARIA"


class TipoContratoLaboral(enum.Enum):
    """Tipo de contrato de trabajo de una obligacion Laboral (Sprint 92) --
    determina que formula de indemnizacion por despido injustificado (Art. 64
    CST) aplica DismissalIndemnityCalculator
    (app/engine/labor/dismissal_indemnity.py): INDEFINIDO usa la tabla de dias
    por año de antiguedad (regimen Ley 50/1990 o Ley 789/2002 segun
    fecha_inicio de la obligacion); FIJO/OBRA_LABOR usan el valor de los
    salarios del tiempo faltante para cumplir el plazo pactado, con piso de
    15 dias -- ambos comparten formula, se distinguen solo para que el reporte
    describa el tipo de contrato real. Default INDEFINIDO preserva el
    comportamiento de toda obligacion Laboral creada antes de este sprint (sin
    indemnizacion por despido, ver migrate_dismissal_indemnity_sprint92.py)."""

    INDEFINIDO = "INDEFINIDO"
    FIJO = "FIJO"
    OBRA_LABOR = "OBRA_LABOR"


class EstadoProcesal(enum.Enum):
    """Estado procesal de un Expediente (Sprint 47) -- no existia ningun campo
    de estado procesal en el modelo antes de este sprint. Se agrega como
    columna aditiva minima con los 3 valores que exige el protocolo de
    recalculo historico del despacho (docs/Preguntas-Para-Abogado-Respondidas.md,
    Sprint 47): EN_TRAMITE dispara recalculo obligatorio + "Memorial de
    Actualizacion/Correccion"; PRESENTADO_JUZGADO_CPACA dispara recalculo +
    memorial de correccion de error aritmetico (Art. 151 CPACA);
    COSA_JUZGADA bloquea el recalculo automatico (se mantiene el valor por
    seguridad juridica). Ver app/services/recalculo_historico.py.

    Default EN_TRAMITE para expedientes existentes/nuevos: es la opcion mas
    conservadora frente a la instruccion "es obligatorio recalcular" del
    despacho (dispara el protocolo de recalculo+memorial en vez de omitirlo
    por silencio) -- PERO debe revisarse manualmente expediente por
    expediente antes de una corrida masiva del script de recalculo
    (scripts/recalcular_historicas_sprint30.py), en particular para marcar
    correctamente los que ya estan en cosa juzgada y no deben tocarse. No hay
    UI de edicion para este campo todavia (fuera de alcance de este sprint,
    que se confino a database/models.py + scripts/ + app/services/ +
    app/engine/reports/ sin tocar app/views/expedientes.py) -- se ajusta
    directo en BD o via un script puntual hasta que un sprint de UI lo
    exponga."""

    EN_TRAMITE = "EN_TRAMITE"
    PRESENTADO_JUZGADO_CPACA = "PRESENTADO_JUZGADO_CPACA"
    COSA_JUZGADA = "COSA_JUZGADA"


class TipoBeneficiario(enum.Enum):
    """Tipo de beneficiario de una obligacion alimentaria de Civil/Familia (Sprint 74)
    -- determina el arbol de decision de vigencia (ver
    app/services/vigencia_alimentos.py::calcular_vigencia_alimentos). Reglas
    confirmadas como hecho conocido segun el reporte del usuario (2026-08-13, ver
    docs/Pendientes.md, Sprint 74) -- NO son la pregunta abierta del sprint:

    - NINO (sin discapacidad): vigente hasta los 18 anos si no estudia, o hasta los
      25 si estudia una carrera profesional/tecnica/tecnologica.
    - NINO_DISCAPACIDAD con `Beneficiario.discapacidad_permanente=True`: obligacion
      vitalicia.

    CONYUGE, PADRES y OTRO **no** tienen ningun criterio operacional/numerico
    confirmado para calcular su vigencia automaticamente -- esa es justamente la
    pregunta abierta sin responder del despacho (ver
    docs/Preguntas-Para-Abogado-Abiertas.md, seccion Sprint 74: como se prueba que
    un conyuge "supero su condicion de vulnerabilidad", que reglas puntuales
    aplican a "otro" beneficiario, etc.). Para estos tipos (y para
    NINO_DISCAPACIDAD sin marcar permanente) el sistema NUNCA aplica el limite de
    edad de NINO ni inventa un plazo/edad -- declara la vigencia como no
    determinable automaticamente, ver `ResultadoVigencia.determinable_automaticamente`
    en vigencia_alimentos.py."""

    NINO = "NINO"
    NINO_DISCAPACIDAD = "NINO_DISCAPACIDAD"
    CONYUGE = "CONYUGE"
    PADRES = "PADRES"
    OTRO = "OTRO"


class Expediente(Base):
    __tablename__ = "expedientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    radicado: Mapped[str] = mapped_column(String(100))
    demandante: Mapped[str] = mapped_column(String(200))
    demandado: Mapped[str] = mapped_column(String(200))
    area_derecho: Mapped[AreaDerecho] = mapped_column(SAEnum(AreaDerecho))
    juzgado: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fecha_corte_default: Mapped[date] = mapped_column(Date)
    # estado_procesal (Sprint 47): ver docstring de EstadoProcesal arriba para
    # el porque del default EN_TRAMITE y la advertencia de revision manual.
    # server_default (ademas de default de Python) porque hay codigo/tests
    # existentes que insertan filas en `expedientes` via SQL crudo, sin pasar
    # por el ORM -- sin un DEFAULT a nivel de DDL, SQLite rechazaria esos
    # INSERT con "NOT NULL constraint failed" en cuanto esta columna existe.
    estado_procesal: Mapped[EstadoProcesal] = mapped_column(
        SAEnum(EstadoProcesal),
        nullable=False,
        default=EstadoProcesal.EN_TRAMITE,
        server_default=EstadoProcesal.EN_TRAMITE.value,
    )

    obligaciones: Mapped[list[Obligacion]] = relationship(
        back_populates="expediente", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="expediente", cascade="all, delete-orphan"
    )


class Obligacion(Base):
    __tablename__ = "obligaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expediente_id: Mapped[int] = mapped_column(ForeignKey("expedientes.id"), index=True)
    tipo: Mapped[TipoObligacion] = mapped_column(SAEnum(TipoObligacion))
    concepto: Mapped[str] = mapped_column(String(200))
    categoria: Mapped[str] = mapped_column(String(50))
    fecha_origen: Mapped[date] = mapped_column(Date)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    tasa_efectiva_anual: Mapped[Decimal] = mapped_column(Numeric(9, 4))
    pagada: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_pago_total: Mapped[date | None] = mapped_column(Date, nullable=True)
    dia_pago: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    tasa_moratoria_anual: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    ibc_vigente_anual: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    cantidad_smlmv_uvt: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    honorarios_fijos_pactados: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    cuota_litis_pactada_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    beneficio_obtenido: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    costas_pct_manual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    costas_tipo_proceso: Mapped[str | None] = mapped_column(String(60), nullable=True)
    costas_instancia: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # Fecha de la providencia judicial que impone las costas (Sprint 18 -- ultraactividad
    # CPC->CGP, Art. 624 CGP) -- distinta de fecha_origen, que representa cuando nacio la
    # obligacion y puede ser muy anterior a cuando un juez impuso costas. Opcional/aditiva:
    # None mantiene el comportamiento actual (tabla granular vigente sin mas validacion),
    # igual que costas_tipo_proceso/costas_instancia arriba -- este sprint no agrega el
    # campo al formulario de UI, solo el motor y la validacion (ver
    # app/engine/costs/agencias_en_derecho.py, validar_ultraactividad_cgp).
    fecha_providencia_costas: Mapped[date | None] = mapped_column(Date, nullable=True)
    aplica_indexacion_ipc: Mapped[bool] = mapped_column(Boolean, default=False)
    interes_sobre_capital_indexado: Mapped[bool] = mapped_column(Boolean, default=False)
    moneda: Mapped[str] = mapped_column(String(3), default="COP")
    trm_aplicable: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    trm_fecha_referencia: Mapped[date | None] = mapped_column(Date, nullable=True)
    anatocismo_demanda_judicial: Mapped[bool] = mapped_column(Boolean, default=False)
    anatocismo_fecha_acuerdo: Mapped[date | None] = mapped_column(Date, nullable=True)
    base_sancion_tributaria: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    meses_extemporaneidad: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sancion_agravada: Mapped[bool] = mapped_column(Boolean, default=False)
    ingresos_brutos: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    devoluciones_rebajas_descuentos: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    costos: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    deducciones: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    rentas_exentas: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    incluir_seguridad_social: Mapped[bool] = mapped_column(Boolean, default=False)
    nivel_riesgo_arl: Mapped[str | None] = mapped_column(String(2), nullable=True)
    # es_smmlv (Sprint 44, punto 1): cuando esta marcado, LaboralStrategy ignora
    # el `valor` capturado a mano y resuelve el salario base desde
    # get_smlmv_for_year(fecha_origen.year) en cada liquidacion -- asi el
    # contrato nunca queda desactualizado si el SMLMV de ese año se corrige
    # despues via la tabla parametros_legales (ver historical_index.py).
    es_smmlv: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_reajuste_anual: Mapped[TipoReajusteAnual] = mapped_column(
        SAEnum(TipoReajusteAnual), default=TipoReajusteAnual.NINGUNO
    )
    # Auto-referencial (Sprint 41): una cuota PUNTUAL generada por
    # generar_cuotas_mensuales() (app/services/reajuste_anual.py) apunta a su
    # obligacion RECURRENTE padre via este campo. Deliberadamente SIN
    # sqlalchemy.ForeignKey(): SQLite rechaza "ALTER TABLE ... DROP COLUMN" sobre
    # una columna que participa en una FOREIGN KEY de tabla (restriccion que no
    # se puede sortear con PRAGMA legacy_alter_table/foreign_keys, verificado
    # empiricamente), lo que habria bloqueado cualquier migracion futura que
    # necesite recrear esta columna. La app tampoco activa
    # `PRAGMA foreign_keys=ON` en ningun punto (ver database/database.py), asi
    # que una FK declarada aqui no aportaria integridad referencial real, solo
    # el riesgo de migracion. La relacion logica (hija -> padre) se resuelve en
    # Python filtrando por este entero, no via relationship() de SQLAlchemy.
    obligacion_padre_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # tipo_recurrencia/fechas_anuales_fijas (Sprint 73): aditivo, solo relevante
    # para una obligacion RECURRENTE. tipo_recurrencia default MENSUAL preserva
    # el comportamiento de todas las obligaciones RECURRENTE creadas antes de
    # este sprint. fechas_anuales_fijas guarda una lista JSON de fechas "MM-DD"
    # (ej. '["06-15", "12-15", "03-22"]') como TEXT en una columna String --
    # mismo patron ya usado por ParametroLegal.areas_derecho (Sprint 57, ver
    # app/services/areas_parametro.py) en vez de inventar un tipo de columna
    # JSON nuevo. Solo se llena cuando tipo_recurrencia ==
    # FECHAS_ANUALES_FIJAS; ver app/services/recurrencia_fechas_fijas.py para
    # la (de)serializacion y el generador de cuotas hijas real.
    # server_default (ademas de default de Python), mismo motivo que
    # EstadoProcesal arriba: hay tests/scripts existentes que insertan filas en
    # `obligaciones` via SQL crudo sin pasar por el ORM -- sin un DEFAULT a
    # nivel de DDL, SQLite rechazaria esos INSERT con "NOT NULL constraint
    # failed" en cuanto esta columna existe.
    tipo_recurrencia: Mapped[TipoRecurrencia] = mapped_column(
        SAEnum(TipoRecurrencia),
        default=TipoRecurrencia.MENSUAL,
        server_default=TipoRecurrencia.MENSUAL.value,
    )
    fechas_anuales_fijas: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # pacto_expreso_indexacion / protegida_inflacion_uvr (Sprint 43, indexacion IPC en
    # Comercial/Laboral/Honorarios/Sancionatorio/Tributario -- ver
    # docs/Preguntas-Para-Abogado-Respondidas.md, seccion Sprint 43):
    #
    # pacto_expreso_indexacion: solo relevante en COMERCIAL. El despacho exige que el
    # modo "(b) capital indexado + interes civil puro 6% anual" (en vez de la tasa
    # comercial, que ya incorpora inflacion) solo sea valido si el titulo trae un
    # pacto expreso que lo autorice -- ver ComercialStrategy._validar_obligacion_comercial,
    # que bloquea con ValueError si aplica_indexacion_ipc esta marcado sin este flag
    # (el XOR "tasa comercial O IPC+civil" del despacho).
    #
    # protegida_inflacion_uvr: solo relevante en TRIBUTARIO. Marca que el
    # titulo/tasa de esta obligacion ya incorpora su propia proteccion inflacionaria
    # (ej. UVR) -- el despacho exige bloquear con error si ademas se intenta aplicar
    # la indexacion IPC del Art. 867-1 E.T. sobre el mismo capital (prohibicion de
    # doble cobro). Ver TributarioStrategy._validar_obligacion_tributaria.
    pacto_expreso_indexacion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    protegida_inflacion_uvr: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    # Sprint 61: tipo de accion (prescripcion, TipoAccion.value en minuscula,
    # ej. "ordinaria") o de proceso (caducidad, clave de
    # PLAZOS_CADUCIDAD_MESES_CONOCIDOS en mayuscula, ej. "CHEQUES") aplicable a
    # esta obligacion -- nulo por defecto, no cambia el comportamiento de
    # ninguna obligacion existente. Ver
    # app.services.areas_parametro.opciones_tipo_accion_proceso_por_area.
    tipo_accion_proceso: Mapped[str | None] = mapped_column(String(60), nullable=True)

    expediente: Mapped[Expediente] = relationship(back_populates="obligaciones")
    abonos: Mapped[list[Abono]] = relationship(
        back_populates="obligacion", cascade="all, delete-orphan"
    )
    eventos_laborales: Mapped[list[EventoLaboral]] = relationship(
        back_populates="obligacion", cascade="all, delete-orphan"
    )
    descuentos_laborales: Mapped[list[DescuentoLaboral]] = relationship(
        back_populates="obligacion", cascade="all, delete-orphan"
    )
    # beneficiario (Sprint 74): relacion 1:1 opcional, solo relevante para una
    # Obligacion RECURRENTE de Civil/Familia (cuota alimentaria) -- ver
    # docstring de Beneficiario abajo para el porque de la entidad propia.
    # uselist=False porque `Beneficiario.obligacion_id` es UNIQUE (a lo sumo un
    # beneficiario por obligacion); cascade delete-orphan porque el
    # beneficiario no tiene sentido sin la obligacion que describe.
    beneficiario: Mapped[Beneficiario | None] = relationship(
        back_populates="obligacion", uselist=False, cascade="all, delete-orphan"
    )


class Beneficiario(Base):
    """Beneficiario real de una obligacion alimentaria RECURRENTE de Civil/Familia
    (Sprint 74) -- entidad propia en vez de campos condicionales sueltos en
    `Obligacion` (decision de diseno de este sprint, el propio backlog dejaba la
    eleccion abierta): un expediente de alimentos puede tener el demandante mismo
    como beneficiario o una persona distinta, y el arbol de decision pedido por el
    usuario (niño / niño con discapacidad / conyuge / padres / otro) necesita
    varios campos propios (nombre, fecha de nacimiento, tipo, si estudia, si la
    discapacidad es permanente, relacion con el demandante) que no aplican a
    ninguna otra area del derecho -- meterlos como columnas nullable sueltas en
    `Obligacion` (que ya tiene mas de 30 columnas condicionales por area) habria
    sido menos legible sin ganar nada. Una entidad propia ademas deja claro en el
    esquema que el beneficiario es un dato de UNA obligacion puntual (relacion 1:1
    via `obligacion_id` UNIQUE), no del expediente completo -- un mismo expediente
    de Familia puede tener varias obligaciones RECURRENTE, cada una con un
    beneficiario distinto (ej. dos hijos con cuotas alimentarias separadas).

    Tabla enteramente nueva -- NO necesita script de migracion ALTER TABLE (mismo
    criterio que `EventoLaboral`/`DescuentoLaboral`, Sprint 16/44: ninguna de esas
    2 tablas nuevas tiene tampoco un scripts/migrate_*.py propio).
    `Base.metadata.create_all()` (`init_db()`, llamada en cada arranque de la app
    ANTES de `aplicar_migraciones_pendientes()`, ver database/database.py) ya crea
    cualquier tabla del modelo actual que todavia no exista en una bastium.db real
    -- un ALTER TABLE en scripts/migrate_*.py solo hace falta para una columna
    nueva en una tabla que YA existia con un esquema mas viejo (ver
    scripts/migrate_fechas_anuales_fijas.py para ese caso, que SI lo necesita)."""

    __tablename__ = "beneficiarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # UNIQUE (no solo index): a lo sumo un Beneficiario por Obligacion (relacion
    # 1:1) -- Obligacion.beneficiario (relationship uselist=False) asume esto.
    obligacion_id: Mapped[int] = mapped_column(
        ForeignKey("obligaciones.id"), unique=True, index=True
    )
    nombre: Mapped[str] = mapped_column(String(200))
    fecha_nacimiento: Mapped[date] = mapped_column(Date)
    tipo: Mapped[TipoBeneficiario] = mapped_column(SAEnum(TipoBeneficiario))
    # es_el_demandante: metadata descriptiva pedida por el reporte del usuario
    # ("preguntar si existe un beneficiario distinto del demandante") -- no
    # participa en ningun calculo de vigencia, solo documenta si el beneficiario
    # capturado es la misma persona que `Expediente.demandante` o alguien
    # distinto.
    es_el_demandante: Mapped[bool] = mapped_column(Boolean, default=False)
    # estudia: solo relevante si tipo == NINO (arbol de decision) -- determina si
    # la vigencia se extiende de 18 a 25 anos. Queda en None para cualquier otro
    # tipo (no se fuerza False, para no insinuar una respuesta que nunca se
    # capturo).
    estudia: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # discapacidad_permanente: solo relevante si tipo == NINO_DISCAPACIDAD -- es
    # el UNICO caso con regla de vigencia automatica confirmada por el usuario
    # (vitalicio). Si queda en False/None para este tipo, vigencia_alimentos.py
    # NO reutiliza la regla de NINO sin discapacidad (18/25) -- esa regla nunca
    # fue confirmada para discapacidad no permanente, se declara no determinable
    # automaticamente en vez de inventarla.
    discapacidad_permanente: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # relacion_demandante: descriptiva/libre (ej. "hijo", "conyuge", "madre") --
    # no participa en el calculo de vigencia (que usa `tipo`, un enum cerrado),
    # solo enriquece el reporte/la lectura humana del expediente.
    relacion_demandante: Mapped[str | None] = mapped_column(String(100), nullable=True)

    obligacion: Mapped[Obligacion] = relationship(back_populates="beneficiario")


class Abono(Base):
    __tablename__ = "abonos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    obligacion_id: Mapped[int] = mapped_column(ForeignKey("obligaciones.id"), index=True)
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    referencia: Mapped[str | None] = mapped_column(String(200), nullable=True)

    obligacion: Mapped[Obligacion] = relationship(back_populates="abonos")


class EventoLaboral(Base):
    """Suspension contractual o incapacidad (comun/laboral) dentro de un
    contrato Laboral -- tabla polimorfica, no dos tablas separadas: un mismo
    contrato puede tener varios eventos de cualquier tipo. `motivo_suspension`
    solo se llena cuando `tipo == SUSPENSION` (validado en
    LaboralStrategy, no aqui)."""

    __tablename__ = "eventos_laborales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    obligacion_id: Mapped[int] = mapped_column(ForeignKey("obligaciones.id"))
    tipo: Mapped[TipoEventoLaboral] = mapped_column(SAEnum(TipoEventoLaboral))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    motivo_suspension: Mapped[MotivoSuspension | None] = mapped_column(
        SAEnum(MotivoSuspension), nullable=True
    )

    obligacion: Mapped[Obligacion] = relationship(back_populates="eventos_laborales")


class DescuentoLaboral(Base):
    """Descuento del empleador sobre la liquidacion laboral (Sprint 44, punto
    3) -- mismo patron que `Abono` (tabla propia, no un campo simple) para
    permitir varios descuentos independientes por obligacion, cada uno con su
    propia fecha y monto. `es_legal` es metadata descriptiva para el reporte
    (permite al abogado distinguir un descuento autorizado de uno que no lo
    fue) -- ambos reducen el neto adeudado de la misma forma, reutilizando el
    mecanismo de pagos/allocation ya existente (ver LaboralStrategy.liquidar,
    que los inyecta como eventos PAYMENT igual que los abonos)."""

    __tablename__ = "descuentos_laborales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    obligacion_id: Mapped[int] = mapped_column(ForeignKey("obligaciones.id"), index=True)
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    es_legal: Mapped[bool] = mapped_column(Boolean, default=True)
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)

    obligacion: Mapped[Obligacion] = relationship(back_populates="descuentos_laborales")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expediente_id: Mapped[int] = mapped_column(ForeignKey("expedientes.id"), index=True)
    usuario: Mapped[str] = mapped_column(String(200))
    fecha_ejecucion: Mapped[datetime] = mapped_column(DateTime)
    fecha_corte: Mapped[date] = mapped_column(Date)
    area_derecho: Mapped[str] = mapped_column(String(50))
    resultado_json: Mapped[str] = mapped_column(Text)
    # Sprint 47 (recalculo historico post-Sprint-30) -- las 3 columnas de abajo
    # son append-only/aditivas, no cambian el significado de ninguna fila
    # existente (todas nacen en False/NULL para filas legadas via el script de
    # migracion, ver scripts/migrate_sprint47_recalculo_historico.py).
    #
    # obsoleto_requiere_recalculo: flag literal "OBSOLETO - REQUIERE RECALCULO"
    # exigido por el despacho -- True cuando esta fila se genero antes del
    # cierre del Sprint 30 (commit 5c4cc9a, 2026-08-04) y por lo tanto pudo
    # calcularse con la logica defectuosa de fecha_interrupcion_efectiva/
    # dias_trabajados. Puesto por
    # app.services.recalculo_historico.marcar_obsoletas -- NUNCA se
    # sobrescribe el resultado_json de la fila marcada (append-only, ver
    # liquidacion_anterior_id).
    obsoleto_requiere_recalculo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    # liquidacion_anterior_id: mecanismo tecnico ya decidido con el usuario
    # (ver docs/Pendientes.md, Sprint 47) -- una liquidacion recalculada NUNCA
    # sobrescribe la fila obsoleta, se guarda como una fila AuditLog nueva que
    # apunta a la anterior via este campo (misma AuditLog, auto-referencial).
    # Deliberadamente SIN sqlalchemy.ForeignKey(): mismo motivo documentado en
    # Obligacion.obligacion_padre_id de arriba -- SQLite no permite
    # "ALTER TABLE ... DROP COLUMN" sobre una columna que participa en una FK
    # de tabla, lo que bloquearia migraciones futuras que necesiten recrear
    # esta columna; la app tampoco activa PRAGMA foreign_keys=ON. La relacion
    # logica se resuelve en Python (session.get(AuditLog, ...)), no via
    # relationship() de SQLAlchemy.
    liquidacion_anterior_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # motivo_recalculo: texto libre -- en la fila VIEJA marcada obsoleta
    # siempre es el flag literal exigido por el despacho
    # ("OBSOLETO - REQUIERE RECALCULO"); en la fila NUEVA que la recalcula
    # describe de que recalculo se trata y cual fila reemplaza (referencia
    # legible, ademas de liquidacion_anterior_id).
    motivo_recalculo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    expediente: Mapped[Expediente] = relationship(back_populates="audit_logs")


class ParametroLegal(Base):
    __tablename__ = "parametros_legales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clave: Mapped[str] = mapped_column(String(100), index=True)
    valor: Mapped[Decimal] = mapped_column(DecimalExacto)
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    usuario: Mapped[str] = mapped_column(String(200))
    motivo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime)
    # areas_derecho/unidad (Sprint 57): lista JSON de codigos AreaDerecho y
    # unidad de medida (ej. "COP"/"%"/"meses"), obligatorias para toda fila
    # nueva creada desde agregar_valor()/la GUI (validado ahi, no aqui) pero
    # nullable a nivel de columna SQLite -- las 683 filas legadas quedan NULL
    # hasta que scripts/migrate_parametros_area_unidad.py las completa (mismo
    # patron que otras columnas agregadas por ALTER TABLE sin DEFAULT viable,
    # ver docstring de ese script), y decenas de tests/scripts no relacionados
    # con este sprint siguen construyendo ParametroLegal directamente sin
    # estos dos campos. Se guardan por FILA (no como metadato fijo de la
    # clave), pero en la practica se asume que no varian entre versiones
    # historicas de una misma clave -- son propiedades de la clave, no del
    # valor puntual -- por eso ni ParametrosView ni HistorialParametroDialog
    # necesitan mostrarlas fila por fila en el historial (Sprint 60): basta
    # con la fila vigente. Si algun dia una clave necesitara area/unidad
    # distinta entre versiones, esta asuncion habria que revisarla.
    areas_derecho: Mapped[str | None] = mapped_column(String(200), nullable=True)
    unidad: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # creado_por_sistema (Sprint "Parametros: editar/eliminar de usuario"):
    # True para las filas sembradas por scripts/migrate_parametros_legales.py
    # y scripts/migrate_ipc_variacion_anual.py, False para cualquier fila
    # creada desde ParametroFormDialog (la UI). Determina si la fila puede
    # editarse/eliminarse (ver editar_valor/eliminar_valor en
    # parametro_service.py) -- a diferencia de `usuario` (texto libre, solo
    # auditoria), este es un flag real que ningun camino de la UI puede
    # poner en True.
    creado_por_sistema: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
