class AreaRegistry:
    """
    Despacho central de áreas jurídicas.
    Registra dinámicamente qué calculadoras están disponibles.
    """
    _areas = {}

    @classmethod
    def register(cls, area_name: str, description: str, strategy_class):
        cls._areas[area_name] = {
            "description": description,
            "strategy": strategy_class
        }

    @classmethod
    def get_available_areas(cls) -> dict:
        return cls._areas

    @classmethod
    def get_strategy(cls, area_name: str):
        if area_name not in cls._areas:
            raise ValueError(f"El área jurídica '{area_name}' no está registrada.")
        return cls._areas[area_name]["strategy"]()

# --- Simulación de registro de estrategias ---
class LaboralStrategy: pass
class FamiliaStrategy: pass

AreaRegistry.register("LABORAL", "Obligaciones Laborales (Cesantías, Art 65 CST)", LaboralStrategy)
AreaRegistry.register("FAMILIA", "Obligaciones Alimentarias (Art 1617 CC)", FamiliaStrategy)
AreaRegistry.register("CIVIL", "Obligaciones Civiles / Pagarés", None) # Añadir estrategia real