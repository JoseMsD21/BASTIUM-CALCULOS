class AreaRegistry:
    """
    Despacho central de areas juridicas.
    Registra que estrategia de calculo corresponde a cada area del derecho.
    """

    _areas = {}

    @classmethod
    def register(cls, area_name: str, description: str, strategy_class):
        cls._areas[area_name] = {
            "description": description,
            "strategy": strategy_class,
        }

    @classmethod
    def get_available_areas(cls) -> dict:
        return cls._areas

    @classmethod
    def get_strategy(cls, area_name: str):
        if area_name not in cls._areas:
            raise ValueError(f"El area juridica '{area_name}' no esta registrada.")
        return cls._areas[area_name]["strategy"]()


def _register_default_areas():
    from app.services.area_strategy import (
        CivilFamiliaStrategy,
        ComercialStrategy,
        HonorariosStrategy,
        LaboralStrategy,
        SancionatorioStrategy,
    )

    AreaRegistry.register(
        "CIVIL_FAMILIA", "Obligaciones Civiles y de Familia (Art. 1617 C.C.)", CivilFamiliaStrategy
    )
    AreaRegistry.register("COMERCIAL", "Obligaciones Comerciales (Art. 884 C.Co.)", ComercialStrategy)
    AreaRegistry.register("LABORAL", "Obligaciones Laborales (Cesantias, Art. 65 CST)", LaboralStrategy)
    AreaRegistry.register("SANCIONATORIO", "Sanciones administrativas (SMLMV / UVT)", SancionatorioStrategy)
    AreaRegistry.register("HONORARIOS", "Cobro de honorarios y cuota litis", HonorariosStrategy)


_register_default_areas()
