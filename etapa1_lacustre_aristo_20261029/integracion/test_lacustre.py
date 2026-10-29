import pandas as pd
import math
from consolidar_aristo import assign, aggregate, balances


def fixture():
    a = pd.DataFrame([
        dict(id_encuesta='s1', campana='Ejemplo', fecha='2026-01-01', sentido_cruce='A→B', segmento='VL', OD_zonal_completo=True, origen='A', destino='B'),
        dict(id_encuesta='s2', campana='Ejemplo', fecha='2026-01-01', sentido_cruce='A→B', segmento='VL', OD_zonal_completo=False, origen='A', destino='Ambiguo'),
        dict(id_encuesta='s3', campana='Ejemplo', fecha='2026-01-02', sentido_cruce='A→B', segmento='VL', OD_zonal_completo=True, origen='A', destino='B'),
    ])
    st = pd.DataFrame([
        dict(campana='Ejemplo', fecha='2026-01-01', sentido_cruce='A→B', segmento='VL', N_entrevistas_fecha=2, F_total_filas_fecha=10.),
        dict(campana='Ejemplo', fecha='2026-01-02', sentido_cruce='A→B', segmento='VL', N_entrevistas_fecha=1, F_total_filas_fecha=8.),
        dict(campana='Ejemplo', fecha='2026-01-03', sentido_cruce='A→B', segmento='VL', N_entrevistas_fecha=0, F_total_filas_fecha=6.),
    ])
    return a, st


def test_N_incluye_respuestas_OD_ambiguas():
    a, st = assign(*fixture())
    assert a.iloc[0].coef_asignacion_fecha == 5.
    assert a.iloc[1].coef_asignacion_fecha == 5.


def test_no_transfiere_a_fecha_sin_muestra():
    a, st = assign(*fixture()); b = balances(st, a)
    d = b[b.fecha.eq('2026-01-03')].iloc[0]
    assert d.flujo_asignado_zonas == 0.
    assert d.flujo_sin_OD_zonal == 6.


def test_residual_incluye_OD_generico_y_N_no_se_reduce():
    a, st = assign(*fixture()); b = balances(st, a)
    assert b.iloc[0].flujo_asignado_zonas == 5.
    assert b.iloc[0].flujo_sin_OD_zonal == 5.
    assert b.N_recalculado.tolist() == [2, 1, 0]


def test_asigna_por_fecha_y_no_por_campana_agrupada():
    a, st = assign(*fixture())
    assert a.aporte_flujo_medido.tolist() == [5., 5., 8.]
    d = aggregate(a[a.OD_zonal_completo], ['campana', 'segmento', 'origen', 'destino'])
    assert d.iloc[0].flujo_asignado_exposicion_medida == 13.


def test_coef_menor_uno_conserva_N_sin_fingir_expansion_individual():
    a, st = fixture(); st.loc[0, 'F_total_filas_fecha'] = 1.
    assigned, result = assign(a, st)
    assert assigned.iloc[0].coef_asignacion_fecha == .5
    assert result.iloc[0].N_recalculado == 2


def test_conteo_faltante_no_se_convierte_en_cero():
    a, st = fixture(); st.loc[0, 'F_total_filas_fecha'] = None
    a, st = assign(a, st); b = balances(st, a)
    assert pd.isna(a.iloc[0].aporte_flujo_medido)
    assert pd.isna(b.iloc[0].flujo_sin_OD_zonal)


def test_balance_estrato_sin_suma_personas_vehiculos():
    a, st = assign(*fixture()); b = balances(st, a)
    assert all(math.isclose(r.F_total_filas_fecha, r.flujo_asignado_zonas+r.flujo_sin_OD_zonal) for r in b.itertuples())
