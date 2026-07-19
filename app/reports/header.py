def build_encabezado(radicado: str, demandante: str, demandado: str, juzgado: str | None) -> dict:
    """Arma el bloque de encabezado (radicado/partes/juzgado) para PDF y Word."""
    return {
        "radicado": radicado,
        "partes": f"{demandante} vs. {demandado}",
        "juzgado": juzgado,
    }
