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


class TipoEventoLaboral(enum.Enum):
    SUSPENSION = "SUSPENSION"
    INCAPACIDAD_COMUN = "INCAPACIDAD_COMUN"
    INCAPACIDAD_LABORAL = "INCAPACIDAD_LABORAL"


class MotivoSuspension(enum.Enum):
    HUELGA = "HUELGA"
    LICENCIA_NO_REMUNERADA = "LICENCIA_NO_REMUNERADA"
    DISCIPLINARIA = "DISCIPLINARIA"


class Expediente(Base):
    __tablename__ = "expedientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    radicado: Mapped[str] = mapped_column(String(100))
    demandante: Mapped[str] = mapped_column(String(200))
    demandado: Mapped[str] = mapped_column(String(200))
    area_derecho: Mapped[AreaDerecho] = mapped_column(SAEnum(AreaDerecho))
    juzgado: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fecha_corte_default: Mapped[date] = mapped_column(Date)

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
    honorarios_fijos_pactados: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    cuota_litis_pactada_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    beneficio_obtenido: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    costas_pct_manual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    costas_tipo_proceso: Mapped[str | None] = mapped_column(String(60), nullable=True)
    costas_instancia: Mapped[str | None] = mapped_column(String(10), nullable=True)
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
    devoluciones_rebajas_descuentos: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    costos: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    deducciones: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    rentas_exentas: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    incluir_seguridad_social: Mapped[bool] = mapped_column(Boolean, default=False)
    nivel_riesgo_arl: Mapped[str | None] = mapped_column(String(2), nullable=True)

    expediente: Mapped[Expediente] = relationship(back_populates="obligaciones")
    abonos: Mapped[list[Abono]] = relationship(
        back_populates="obligacion", cascade="all, delete-orphan"
    )
    eventos_laborales: Mapped[list[EventoLaboral]] = relationship(
        back_populates="obligacion", cascade="all, delete-orphan"
    )


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


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expediente_id: Mapped[int] = mapped_column(ForeignKey("expedientes.id"), index=True)
    usuario: Mapped[str] = mapped_column(String(200))
    fecha_ejecucion: Mapped[datetime] = mapped_column(DateTime)
    fecha_corte: Mapped[date] = mapped_column(Date)
    area_derecho: Mapped[str] = mapped_column(String(50))
    resultado_json: Mapped[str] = mapped_column(Text)

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
