"""Costos hipotéticos de buses coordinados: sólo Chile Chico <-> Coyhaique.
No ejecuta rutas/modelos ni modifica fuentes. Integra bus+barcaza una sola vez.
"""
from pathlib import Path
import unicodedata
import numpy as np
import pandas as pd


def _norm(value):
    return ''.join(c for c in unicodedata.normalize('NFD', str(value).upper())
                   if unicodedata.category(c) != 'Mn').strip()


def build_bus_costs(root: Path, cfg: dict, *, flows=None, attributes=None) -> pd.DataFrame:
    """Retorna todos los peatones; sin conexión respaldada => CG nuevo NaN.

    flows/attributes opcionales evitan releer libros que ya cargó el integrador.
    cfg['buses']: tarifa_referencia, km_referencia, factor_tarifa_integrada,
    tarifa_lacustre, factor_tiempo_bus_sobre_VL (default1). No opera descuentos
    diferentes por escenario: los escenarios de captación deben aislar elección.
    """
    root = Path(root)
    b = cfg.get('buses', {})
    vst = float(cfg.get('vst', cfg.get('vst_persona_h', 10047)))
    if flows is None:
        flows = pd.read_excel(root/'etapa5_logit_preliminar_20261029/resultados/captacion_logit_preliminar.xlsx',
                              sheet_name='Flujos armonizados')
    else:
        flows = flows.copy()
    if 'escenario' in flows:
        flows = flows[flows.escenario.eq('central')]
    flows = flows[flows.segmento.eq('PEATON')].drop_duplicates('id_flujo')
    if attributes is None:
        attributes = pd.read_excel(root/'etapa4_costos_generalizados_20261029/resultados/costos_generalizados_etapa4.xlsx',
                                   sheet_name='Costos desagregados OD')
    routes = pd.read_csv(root/'demanda_lago_github/outputs/etapa12/tramos_proyecto.csv')
    routes = routes[(routes.segmento=='VL') & (routes.destino_norte=='Coyhaique')]
    # Orden0..2 =6,7kmR265+10kmX763; orden4.. =31,14X735+121,546troncal.
    south = routes[routes.orden_sur_norte.lt(3)]
    north = routes[routes.orden_sur_norte.gt(3)]
    km_sur, km_norte = south.km.sum(), north.km.sum()
    h_sur = south.h.sum()
    north_h = north.h.sum()
    factor_h = float(b.get('factor_tiempo_bus_sobre_VL', 1.0))
    factor_integrated = float(b.get('factor_tarifa_integrada', 1.0))
    if not 0 <= factor_integrated <= 1:
        raise ValueError('factor_tarifa_integrada debe estar entre0y1; sólo afecta a los dos buses, no ferry.')
    if factor_h <= 0:
        raise ValueError('factor_tiempo_bus_sobre_VL debe ser positivo')
    rate = float(b.get('tarifa_referencia', 10000)) / float(b.get('km_referencia', 121.956))
    ferry = float(b.get('tarifa_lacustre', 2550))
    names = list(cfg.get('escenarios', {'conservador': {}, 'central': {}, 'alto': {}}))
    if not names:
        names = ['conservador', 'central', 'alto']
    out = []
    for r in flows.to_dict('records'):
        o, d = _norm(r['origen']), _norm(r['destino'])
        old = r.get('CG_actual_modelo', r.get('CG_actual', np.nan))
        compatible = {o, d} == {'CHILE CHICO', 'COYHAIQUE'} and pd.notna(old)
        for scenario in names:
            row = {k: r.get(k, np.nan) for k in ['id_flujo','version','origen','destino','temporada','segmento','unidad']}
            row.update(escenario=scenario, CG_origen_actual=old, CG_nuevo_bus=np.nan,
                       modelable_bus=False, costo_imputado=True, tarifa_km_CLP=rate,
                       tarifa_bus_referencia_CLP=b.get('tarifa_referencia',10000),
                       km_bus_referencia=b.get('km_referencia',121.956),
                       tarifa_Cerro_Castillo_referencia_CLP=b.get('tarifa_Cerro',8000),
                       uso_tarifa_Cerro='Contraste documental: distancia inequívoca no usada; no se promedian referencias sin denominador.',
                       factor_tarifa_integrada=factor_integrated,
                       fuente='Etapa4 Costos desagregados OD, VL nuevo cruce; outputs/etapa12/tramos_proyecto.csv; tarifas bus10000/8000 proporcionadas por usuario.',
                       limite='Servicio bus hipotético no comprometido. Sólo OD Chile Chico–Coyhaique y sentido contrario; otros peatones quedan residuales. VelocidadesVL son proxy bus, no velocidades de servicio observadas.',
                       base_precios='CLP enero2026 convencional de Etapa4; tarifas bus de referencia con fecha no certificada')
            if compatible:
                subset = attributes[(attributes.segmento=='VL') &
                                    (attributes.alternativa=='bahia_jara_levican') &
                                    (attributes.temporada==r['temporada']) &
                                    (attributes.origen.map(_norm)==o) &
                                    (attributes.destino.map(_norm)==d)]
                if not subset.empty:
                    at = subset.iloc[0]
                    if not np.isclose(km_sur+km_norte, at.distancia_vial_km):
                        raise AssertionError('No duplicar accesos: tramos no coinciden con distancia Etapa4')
                    # Mantener tiempo exactoEtapa4 por sentido y ajustar residual norte sólo por precisión.
                    h_total = float(at.tiempo_vial_h)*factor_h
                    hs = h_sur*factor_h
                    hn = h_total-hs
                    fare_sur, fare_norte = km_sur*rate, km_norte*rate
                    fare_bus_list = fare_sur+fare_norte
                    fare_bus_paid = fare_bus_list*factor_integrated
                    fare_total = fare_bus_paid+ferry
                    nav = float(at.tiempo_navegacion_h)
                    emb, des = float(at.tiempo_embarque_h), float(at.tiempo_desembarque_h)
                    schedule = float(at.tiempo_horario_h)
                    total_h = h_total+nav+emb+des+schedule
                    row.update(modelable_bus=True, km_bus_sur=km_sur, km_bus_norte=km_norte,
                               km_bus_total=km_sur+km_norte, tiempo_bus_sur_h=hs,
                               tiempo_bus_norte_h=hn, tiempo_bus_total_h=h_total,
                               velocidad_sur_efectiva_kmh=km_sur/hs,
                               velocidad_norte_efectiva_kmh=km_norte/hn,
                               tiempo_navegacion_h=nav, tiempo_embarque_h=emb,
                               tiempo_desembarque_h=des, tiempo_horario_barcaza_h=schedule,
                               espera_adicional_bus_h=0.0, tiempo_total_h=total_h,
                               tarifa_bus_sur_sin_descuento_CLP=fare_sur,
                               tarifa_bus_norte_sin_descuento_CLP=fare_norte,
                               tarifa_buses_lista_CLP=fare_bus_list,
                               descuento_integracion_CLP=fare_bus_list-fare_bus_paid,
                               tarifa_buses_integrada_CLP=fare_bus_paid,
                               tarifa_lacustre_CLP=ferry, costo_monetario_CLP=fare_total,
                               costo_temporal_CLP=vst*total_h, personas_por_unidad=1.0,
                               VST_CLP_persona_h=vst, CG_nuevo_bus=fare_total+vst*total_h,
                               supuesto='Operación hipotética de dos buses coordinados; velocidades por tramos reutilizadas de VL Etapa4 como proxy. Un solo desfase barcaza, cero espera bus adicional. Tarifa integrada sólo afecta buses una vez. No COV de automóvil a peatones.')
            out.append(row)
    result = pd.DataFrame(out)
    valid = result[result.modelable_bus]
    assert not result.duplicated(['id_flujo','escenario']).any()
    assert valid.espera_adicional_bus_h.eq(0).all()
    assert np.allclose(valid.CG_nuevo_bus, valid.costo_monetario_CLP+valid.costo_temporal_CLP)
    return result
