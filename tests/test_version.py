from app._version import __version__


def test_version_sigue_el_formato_semver():
    partes = __version__.split(".")
    assert len(partes) == 3
    assert all(parte.isdigit() for parte in partes)


def test_version_actual_es_0_1_0():
    assert __version__ == "0.1.0"
