import importlib.util
from pathlib import Path
import pandas as pd

p=Path(__file__).with_name('anualizar_citra.py')
s=importlib.util.spec_from_file_location('anualizar_citra',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def sample(camp,q):
    return dict(zona_origen=1,zona_destino=2,segmento='VL',campana=camp,control='E0701',
                sentido_control='SN',fechas_representadas='2026-01-01',flujo_corredor_12h=q,
                flujo_A_12h=q,flujo_B_12h=0,advertencia_entre_controles='Sintetico')

def test_anual_12h_con_calendario_y_proxy_explicito(tmp_path):
    d=pd.DataFrame([sample('Verano',10),sample('Otoño',2)])
    r=pd.DataFrame([dict(anio=2024,PC=63,rama=2,segmento='VL',ratio_Invierno_Primavera=.5)])
    a=m.project(d,'zonas',tmp_path,r,2026).set_index('escenario')
    assert a.loc['Central','demanda_anual_ventana12h']==1450
    assert a.loc['Conservador','demanda_anual_ventana12h']==1358
    assert a.loc['Alto','demanda_anual_ventana12h']==1450
    assert a.demanda_anual24h.isna().all()
    assert a.dias_proxy_invierno_primavera.eq(183).all()

def test_campana_unica_no_se_rellena(tmp_path):
    a=m.project(pd.DataFrame([sample('Verano',10)]),'zonas',tmp_path,pd.DataFrame(),2026)
    assert a.demanda_anual_ventana12h.isna().all()
    assert a.dias_con_perfil_o_proxy.eq(90).all()
    assert a.aporte_parcial_meses_con_perfil_12h.eq(900).all()
