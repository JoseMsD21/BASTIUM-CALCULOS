from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AreaDerecho(enum.Enum):
    CIVIL_FAMILIA = "CIVIL_FAMILIA"
    COMERCIAL = "COMERCIAL"
    LABORAL = "LABORAL"
    SANCIONATORIO = "SANCIONATORIO"
    HONORARIOS = "HONORARIOS"


class TipoObligacion(enum.Enum):
    PUNTUAL = "PUNTUAL"
    RECURRENTE = "RECURRENTE"


class Expediente(Base):
    __tablename__ = "expedientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    radicado: Mapped[str] = mapped_column(String(100))
    demandante: Mapped[str] = mapped_column(String(200))
    demandado: Mapped[str] = mapped_column(String(200))
    area_derecho: Mapped[AreaDerecho] = mapped_column(SAEnum(AreaDerecho))
    juzgado: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fecha_corte_default: Mapped[date] = mapped_column(Date)

    obligaciones: Mapped[list["Obligacion"]] = relationship(
        back_populates="expediente", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="expediente", cascade="all, delete-orphan"
    )


class Obligacion(Base):
    __tablename__ = "obligaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expediente_id: Mapped[int] = mapped_column(ForeignKey("expedientes.id"))
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

    expediente: Mapped["Expediente"] = relationship(back_populates="obligaciones")
    abonos: Mapped[list["Abono"]] = relationship(
        back_populates="obligacion", cascade="all, delete-orphan"
    )


class Abono(Base):
    __tablename__ = "abonos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    obligacion_id: Mapped[int] = mapped_column(ForeignKey("obligaciones.id"))
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    referencia: Mapped[str | None] = mapped_column(String(200), nullable=True)

    obligacion: Mapped["Obligacion"] = relationship(back_populates="abonos")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expediente_id: Mapped[int] = mapped_column(ForeignKey("expedientes.id"))
    usuario: Mapped[str] = mapped_column(String(200))
    fecha_ejecucion: Mapped[datetime] = mapped_column(DateTime)
    fecha_corte: Mapped[date] = mapped_column(Date)
    area_derecho: Mapped[str] = mapped_column(String(50))
    resultado_json: Mapped[str] = mapped_column(Text)

    expediente: Mapped["Expediente"] = relationship(back_populates="audit_logs")
