from datetime import date, datetime
from decimal import Decimal

from app.services.parametro_service import agregar_valor
from app.services.restablecer_service import (
    crear_backup_de_base_de_datos,
    restablecer_datos_fabrica,
)
from database.models import AreaDerecho, Expediente, Obligacion, ParametroLegal, TipoObligacion
from database.session import get_session


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


def _crear_expediente_con_obligacion() -> int:
    session = get_session()
    expediente = Expediente(
        radicado="2026-99999",
        demandante="Demandante de prueba",
        demandado="Demandado de prueba",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    session.refresh(expediente)
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Capital de prueba",
            categoria="CAPITAL_PAGARE",
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
