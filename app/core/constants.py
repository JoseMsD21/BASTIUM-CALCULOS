"""Listas y etiquetas usadas por los formularios de la GUI."""

CATEGORIAS_CIVIL_FAMILIA = [
    ("CHILD_SUPPORT", "Cuota alimentaria"),
    ("DANO_EMERGENTE", "Dano emergente"),
    ("LUCRO_CESANTE_CONSOLIDADO", "Lucro cesante consolidado"),
    ("DANOS_MORALES", "Danos morales"),
    ("CAPITAL_PAGARE", "Capital de pagare"),
    ("CLOTHING", "Gastos de vestuario"),
    ("MULTA", "Multa"),
]
# Nota: esta lista debe reflejar un subconjunto de
# app.engine.liquidation.engine.LiquidationCore._capital_concepts pertinente
# al area Civil/Familia. Si se agrega un concepto nuevo alla, agregarlo aqui tambien.

CATEGORIAS_COMERCIAL = [
    ("CAPITAL_PAGARE", "Capital de pagare"),
    ("CAPITAL_LETRA_CAMBIO", "Capital de letra de cambio"),
    ("CAPITAL_CHEQUE", "Capital de cheque"),
    ("CAPITAL_FACTURA", "Capital de factura"),
]
# Nota: igual que CATEGORIAS_CIVIL_FAMILIA, cada codigo debe existir en
# app.engine.liquidation.engine.LiquidationCore._capital_concepts.

CATEGORIAS_LABORAL = [
    ("LIQUIDACION_CONTRATO_LABORAL", "Liquidacion de contrato laboral"),
]
# Nota: a diferencia de CATEGORIAS_CIVIL_FAMILIA/CATEGORIAS_COMERCIAL, esta
# categoria es solo una etiqueta de UI -- el event_type real de cada linea de
# la liquidacion (CESANTIAS, INTERESES_CESANTIAS, PRIMA_JUNIO, PRIMA_DICIEMBRE,
# VACACIONES, SANCION_MORATORIA) lo define LaborScheduler/
# MoratoryIndemnityCalculator internamente en app/services/area_strategy.py,
# no este codigo.

CATEGORIAS_SANCIONATORIO = [
    ("MULTA_SANCIONATORIA", "Multa sancionatoria (SMLMV/UVT)"),
]
# Solo una categoria: una obligacion Sancionatorio siempre genera un unico evento de
# capital ("MULTA_SANCIONATORIA"), convertido desde cantidad_smlmv_uvt.

CATEGORIAS_HONORARIOS = [
    ("HONORARIOS_PROFESIONALES", "Honorarios profesionales (fijo + cuota litis)"),
]
# "COSTAS_PROCESALES" no aparece aqui: no es una categoria que el usuario elija, se
# genera automaticamente como un segundo evento si costas_pct_manual esta seteado
# (ver HonorariosStrategy._eventos_de_obligacion).

AREAS_DERECHO = [
    ("CIVIL_FAMILIA", "Civil / Familia", True),
    ("COMERCIAL", "Comercial", True),
    ("LABORAL", "Laboral", True),
    ("SANCIONATORIO", "Sancionatorio", True),
    ("HONORARIOS", "Honorarios / Litigio", True),
]
# El tercer valor de cada tupla indica si el area esta habilitada para calcular
# en este sprint. Ver Pendientes.md para el orden de habilitacion de las demas.
