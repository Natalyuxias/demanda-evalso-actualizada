import pytest
import pandas as pd
from preparar_compatibilidad import validar_reglas


def test_rechaza_ARISTO_como_donante_terrestre():
    with pytest.raises(ValueError, match='CITRA'):
        validar_reglas([dict(fuente='CITRA', flujo_imputado_OD=4., fuente_imputacion_OD='ARISTO')])


def test_permite_imputacion_ferry_diferenciada():
    assert validar_reglas([dict(fuente='ARISTO', flujo_imputado_OD=4., fuente_imputacion_OD='ARISTO')])


def test_no_convierteVP_enVL():
    with pytest.raises(ValueError, match='VP'):
        validar_reglas([dict(segmento='VP', unidad='vehiculos_livianos_4_ruedas')])


def test_24h_sin_factor_es_invalido():
    with pytest.raises(ValueError, match='24h'):
        validar_reglas([dict(fuente='CITRA', demanda_anual_24h=100., factor_12_24=None)])


def test_24h_faltante_permanece_valido():
    assert validar_reglas([dict(fuente='CITRA', demanda_anual_24h=None, demanda_anual_12h=50.)])


def test_residual_nullable_conserva_zonas_faltantes():
    assert validar_reglas([dict(subtipo_residual='externo_no_especificado', zona_origen=pd.NA, zona_destino=pd.NA)])


def test_externo_generico_no_recibeOD_inventado():
    with pytest.raises(ValueError, match='Residual'):
        validar_reglas([dict(subtipo_residual='externo_no_especificado', zona_origen=39, zona_destino=55)])
