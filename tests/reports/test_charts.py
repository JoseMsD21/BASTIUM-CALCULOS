from pathlib import Path

from app.reports.charts import BastiumChartGenerator


def test_generar_grafica_distribucion_devuelve_path_en_directorio_actual(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    datos_rubros = [
        {"concepto": "Capital", "capital": "1000000"},
        {"concepto": "Intereses", "capital": "250000"},
    ]
    generador = BastiumChartGenerator()

    ruta = generador.generar_grafica_distribucion(datos_rubros, output_filename="prueba.png")

    assert isinstance(ruta, Path)
    assert ruta == tmp_path / "prueba.png"
    assert ruta.exists()
