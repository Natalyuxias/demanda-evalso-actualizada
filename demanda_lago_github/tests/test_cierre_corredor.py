from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/etapa1_citra/cierre'))
import math
import pandas as pd
from estimar_corredor import estimate_cell, build_matrices


def strata():
    return pd.DataFrame([
        dict(id_estrato='dia1', fecha='2026-02-01', factor_expansion=2., aforo_vehiculos_12h=20., N_entrevistas_originales_ventana=10, campana='Verano', control='E1', sentido='SN', segmento='VL'),
        dict(id_estrato='dia2', fecha='2026-02-02', factor_expansion=5., aforo_vehiculos_12h=50., N_entrevistas_originales_ventana=10, campana='Verano', control='E1', sentido='SN', segmento='VL'),
    ])


def rows():
    return pd.DataFrame([
        dict(id_encuesta='s1', id_estrato='dia1', categoria='A', factor_expansion=2.),
        dict(id_encuesta='s2', id_estrato='dia1', categoria='B', factor_expansion=2.),
    ])


def test_media_incluye_jornada_valida_sin_entrevista_positiva():
    x = estimate_cell(rows(), strata())
    assert x['flujo_corredor_12h'] == 2.
    assert x['flujo_A_12h'] == x['flujo_B_12h'] == 1.


def test_sin_entrevista_expandible_es_faltante_no_cero():
    r = rows(); r['factor_expansion'] = None
    assert estimate_cell(r, strata())['flujo_corredor_12h'] is None


def test_no_expande_factor_ajeno_a_las_fechas_seleccionadas():
    r = rows(); r['id_estrato'] = 'otro_dia'
    assert estimate_cell(r, strata())['entrevistas_con_factor'] == 0
    assert estimate_cell(r, strata())['flujo_A_12h'] is None


def test_categoria_sin_muestra_es_cero_muestral_solo_si_celda_expandible():
    r = rows(); r['categoria'] = 'A'
    x = estimate_cell(r, strata())
    assert x['flujo_B_12h'] == 0.
    assert x['flujo_corredor_12h'] == x['flujo_A_12h']


def test_una_pantalla_conserva_N_original_y_excluye_otro_control_y_C():
    rr = rows()
    for col, value in dict(id_OD_zonal='1|2|Verano|VL', zona_origen=1, zona_destino=2, campana='Verano', segmento='VL', control='E1', sentido_observado='SN', origen_detallado='Localidad A', destino_detallado='Localidad B', comuna_origen='Comuna A', comuna_destino='Comuna B', CUT_origen='001', CUT_destino='002').items():
        rr[col] = value
    other = rr.iloc[0].copy(); other['id_encuesta'] = 's3'; other['control'] = 'E2'; other['factor_expansion'] = 900.
    excluded = rr.iloc[0].copy(); excluded['id_encuesta'] = 's4'; excluded['categoria'] = 'C'; excluded['factor_expansion'] = 1000.
    audit = pd.concat([rr, pd.DataFrame([other, excluded])], ignore_index=True)
    screen = pd.DataFrame([dict(id_OD_zonal='1|2|Verano|VL', zona_origen=1, zona_destino=2, campana='Verano', segmento='VL', control='E1', sentido_control='SN', seleccionada=True)])
    detailed, zonal, daily = build_matrices(audit, screen, strata())
    assert zonal.iloc[0].flujo_corredor_12h == 2.
    assert detailed.iloc[0].flujo_corredor_12h == 2.
    assert daily.N_original.eq(10).all()
    assert daily.n_corredor.tolist() == [2, 0]
    assert daily.Q_corredor_12h.tolist() == [4., 0.]
    assert math.isclose(daily.Q_A_12h.sum() + daily.Q_B_12h.sum(), daily.Q_corredor_12h.sum())
