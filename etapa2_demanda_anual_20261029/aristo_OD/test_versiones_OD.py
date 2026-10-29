import pandas as pd
from construir_versiones_OD import alloc_profile,build,balances

def interview(**kw):
 r=dict(campana='Verano',fecha='2026-01-27',sentido_cruce='PI→CC',segmento='CAM',origen='A',destino='B',zona_origen=55.,zona_destino=39.,aporte_flujo_medido=2.)
 r.update(kw);return r

def stratum(**kw):
 r=dict(campana='Verano',fecha='2026-02-01',sentido_cruce='PI→CC',segmento='CAM',unidad='vehículos',F_total_filas_fecha=5.,N_entrevistas_fecha=0,filas_fuente='7')
 r.update(kw);return r

def test_transferencia_conserva_solo_embarque_medido():
 a=pd.DataFrame([interview(),interview()]);b=pd.DataFrame([stratum()]);d=build(a,b,'B')
 assert d.flujo.sum()==5 and d.componente.tolist()==['imputado'] and d.N_perfil.tolist()==[2]
 assert balances(d,b).balance_exacto.all()

def test_A_no_transfiere_entre_dias():
 d=build(pd.DataFrame([interview()]),pd.DataFrame([stratum()]),'A')
 assert d.subtipo.tolist()==['residual_sinperfil'] and d.flujo.sum()==5

def test_no_transfiere_otra_temporada():
 d=build(pd.DataFrame([interview(campana='Primavera')]),pd.DataFrame([stratum()]),'B')
 assert d.componente.tolist()==['residual']

def test_no_transfiere_sentido_opuesto():
 d=build(pd.DataFrame([interview(sentido_cruce='CC→PI')]),pd.DataFrame([stratum()]),'B')
 assert d.componente.tolist()==['residual']

def test_no_transfiere_clase_distinta():
 d=build(pd.DataFrame([interview(segmento='VL')]),pd.DataFrame([stratum()]),'B')
 assert d.componente.tolist()==['residual']

def test_externo_no_inventa_zona_ni_denominador_filtrado():
 p=pd.DataFrame([interview(),interview(origen='Internacional',zona_origen=None)])
 d=pd.DataFrame(alloc_profile(p,10.,{},False));ext=d[d.subtipo=='residual_externo']
 assert d.flujo.sum()==10 and ext.flujo.iloc[0]==5 and ext.zona_origen.isna().all()
 assert ext.origen.iloc[0]=='EXTERNO_NO_ESPECIFICADO' and set(d.N_perfil)=={2}

def test_falta_aforo_no_es_cero():
 a=pd.DataFrame([interview(segmento='OTRO_PASAJERO',fecha='2026-02-01')]);b=pd.DataFrame([stratum(segmento='OTRO_PASAJERO',F_total_filas_fecha=None,N_entrevistas_fecha=1)])
 d=build(a,b,'B');assert d.flujo.isna().all() and balances(d,b).balance_exacto.all()

def test_aforo_cero_no_produce_OD_cero_inventado():
 d=build(pd.DataFrame([interview()]),pd.DataFrame([stratum(F_total_filas_fecha=0.)]),'B')
 assert d.origen.tolist()==['SIN_OD_NO_PERFIL'] and d.subtipo.tolist()==['aforo_cero_sin_perfil'] and d.flujo.sum()==0
