from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/etapa1_citra/cierre'))
from clasificar_rutas import classify

def row(**changes):
    r=dict(OD_homologado=True, control_en_camino_Chile=True, sentido_compatible=True, corredor_R7_y_R265=True, referencia_internacional=False,Argentina_observada=False,alternativa_barcaza_compatible=False,km_referencia_Chile=300.,alternativa_Argentina_compatible=True,km_alternativa_argentina_referencia=600.,entrada_argentina='Paso 1',salida_argentina='Paso 2')
    r.update(changes);return r

def test_argentina_posible_no_excluye_por_si_sola():
    assert classify(row())[0]=='A'

def test_argentina_no_dominada_retiene_incertidumbre():
    assert classify(row(km_alternativa_argentina_referencia=200.))[0]=='B'

def test_ferry_compatible_retiene_incertidumbre():
    assert classify(row(alternativa_barcaza_compatible=True))[0]=='B'

def test_evidencia_internacional_no_se_convierte_en_chile():
    assert classify(row(referencia_internacional=True))[0]=='B'

def test_geografia_insuficiente_excluye():
    assert classify(row(OD_homologado=False))[0]=='C'

def test_sentido_incompatible_excluye():
    assert classify(row(sentido_compatible=False))[0]=='C'
