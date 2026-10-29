"""Pruebas sintéticas: no leen encuestas, coordenadas personales ni modelos."""
import collections,copy,datetime
import pytest
import networkx as nx
from fuentes import expansion,minutes,payload
from red import Red
from pantallas import build
from correr_etapa1 import route_decision,apply_geography

def fixture_stratum(n=4):
 obs=[dict(id_encuesta=f'SYN_{i}',campana='Verano',fecha='2026-01-15',control='CONTROL_SINTETICO',sentido='SN',segmento='VL',minuto=500+i,archivo='sintetico',fila_excel=i+2,hash_registro=f'distinto{i}') for i in range(n)]
 flows=[dict(campana='Verano',fecha='2026-01-15',control='CONTROL_SINTETICO',sentido='SN',minuto=minute,VL=10,CAM=2,incidencias='',archivo='sintetico',fila_excel=i+2) for i,minute in enumerate(range(480,1200,15))]
 return obs,flows

def test_denominador_completo_antes_del_filtro():
 obs,flows=fixture_stratum();ss,ww,_=expansion(obs,flows);s=next(s for s in ss if s['segmento']=='VL')
 assert s['N_entrevistas_originales_ventana']==4 and s['factor_expansion']==120
 assert ww['SYN_0']['factor']==120  # seleccionar solo1 no convierte w en480

def test_intervalo_duplicado_no_se_suma_como_jornada():
 obs,ff=fixture_stratum();ff.append(dict(ff[0]));_,w,_=expansion(obs,ff)
 assert w['SYN_0']['factor'] is None and 'duplicados' in w['SYN_0']['motivo']

def test_grilla_incompleta_no_se_rellena():
 obs,ff=fixture_stratum();_,w,_=expansion(obs,ff[:-1]);assert w['SYN_0']['factor'] is None

def test_hora_desconocida_bloquea_denominador_del_estrato():
 obs,ff=fixture_stratum();obs[-1]['minuto']=None;_,w,_=expansion(obs,ff);assert w['SYN_0']['factor'] is None

def test_fuera_de_ventana_no_recibe_factor():
 obs,ff=fixture_stratum();obs[-1]['minuto']=1200;ss,w,_=expansion(obs,ff);assert w['SYN_3']['factor'] is None and w['SYN_0']['factor']==160

def test_filas_identicas_se_preservan_sin_expansion_incierta():
 obs,ff=fixture_stratum();obs[-1]['hash_registro']=obs[0]['hash_registro'];_,w,_=expansion(obs,ff);assert len(obs)==4 and w['SYN_0']['factor'] is None

def test_muestra_superior_al_aforo_no_pesa():
 obs,ff=fixture_stratum();
 for r in ff:r['VL']=0
 _,w,_=expansion(obs,ff);assert w['SYN_0']['factor'] is None

def test_sin_aforo_misma_fecha_no_toma_otro_dia():
 obs,ff=fixture_stratum();
 for r in ff:r['fecha']='2026-01-16'
 _,w,_=expansion(obs,ff);assert all(v['factor'] is None for v in w.values())

def test_reloj_no_inventa_medianoche_y_blanco_no_nulo():
 assert minutes('24:00') is None and minutes('12:75') is None and minutes(datetime.time(8,0))==480
 assert payload([None])!=payload([''])

def base_decision():return dict(OD_homologado=True,separacion_control_red_m=0,separacion_origen_red_m=0,separacion_destino_red_m=0,control_en_camino_Chile=True,sentido_compatible=True,corredor_R7_y_R265=True,alternativa_barcaza_compatible=False,referencia_internacional=False,alternativa_Argentina_compatible=False)

def small_network(arg=True):
 n=Red.__new__(Red);n.C=nx.Graph();n.A=nx.Graph()
 pos={'o':(0,0),'c':(10,0),'d':(20,0),'g1':(10,10),'g2':(20,10)}
 for v,(x,y) in pos.items():n.C.add_node(v,x=x,y=y)
 for u,v,i,route in [('o','c',1,'R7'),('c','d',2,'R265-CH'),('c','g1',3,'LOCAL'),('g2','d',4,'LOCAL')]:n.C.add_edge(u,v,weight=1,arco=i,pais='Chile',ruta=route)
 n.G=n.C.copy()
 if arg:
  for v in ['g1','g2']:n.A.add_node(v,**n.C.nodes[v])
  n.A.add_edge('g1','g2',weight=1,arco=5,pais='Argentina',ruta='RN');n.G.add_edge('g1','g2',**n.A['g1']['g2'])
 n.keynodes={'SYN_origen':'o','SYN_destino':'d','CTRL':'c'};n.endpoint={('SYN','origen'):{},('SYN','destino'):{}};n.snaps={'CTRL':{'separacion_red_m':0}};n.passes={};n.cache={};n.borders=sorted(set(n.A)&set(n.C));n.landpaths={};n.argument_paths=[]
 return n

def test_control_chileno_no_excluye_itinerario_mixto_simple():
 n=small_network();a=n.audit(dict(id_encuesta='SYN',control='CTRL',sentido='PO'))
 assert a['sentido_compatible'] and a['alternativa_Argentina_compatible']
 assert n.argument_paths and n.argument_paths[0]['prueba_no_repeticion']
 d=base_decision();d.update(alternativa_Argentina_compatible=True);primary,aux,_,_=route_decision(d);assert not primary and aux

def test_no_se_impone_aceptacion_cero_si_fuente_suficiente():
 assert not small_network(False).audit(dict(id_encuesta='SYN',control='CTRL',sentido='PO'))['alternativa_Argentina_compatible']
 assert route_decision(base_decision())[0]

def test_sentido_contrario_y_acceso_ferry_no_entran():
 n=small_network();assert not n.matches(['o','c','d'],'CTRL','OP')
 d=base_decision();d['alternativa_barcaza_compatible']=True;assert route_decision(d)[:2]==(False,False)

def test_itinerarios_que_repiten_nodos_no_son_prueba_simple():
 assert Red.stitch([['o','c','g1'],['g1','c','g2'],['g2','d']]) is None

def test_pantallas_seriales_no_se_suman_y_no_maximiza_flujo():
 audits=[];obs=[];weights={};strata=[]
 for ctrl,factor in [('E0701',10),('E1003',100)]:
  for local in ['A','B']:
   rid=ctrl+local;audits.append(dict(id_encuesta=rid,aceptada_corredor_auxiliar=True,zona_origen='39',zona_destino='31',campana='Verano',segmento='VL',origen_detallado=local,destino_detallado='D',control=ctrl,sentido_observado='SN',comuna_origen='X',comuna_destino='Y',CUT_origen='X',CUT_destino='Y'))
   obs.append(dict(id_encuesta=rid,fecha='2026-01-15'));weights[rid]=dict(factor=factor)
  strata.append(dict(campana='Verano',fecha='2026-01-15',control=ctrl,sentido='SN',segmento='VL',factor_expansion=factor,filas_aforo=48,entrevistas_estrato=10,N_entrevistas_originales_ventana=10,aforo_vehiculos_12h=factor*10,id_estrato=ctrl))
 class N:
  landpaths={a['id_encuesta']:['O','C1','C2','D'] for a in audits};keynodes={'E0701':'C1','E1003':'C2'}
  def screen_geometry(self,rids,ctrl,sense):return [True]*len(rids),[True]*len(rids)
 dd,zz,ss,pp,days,selected=build(audits,obs,strata,weights,N())
 assert len([s for s in ss if s['seleccionada']])==1
 assert zz[0]['control']=='E0701' and zz[0]['flujo_corredor_auxiliar_12h']==20
 assert sum(d['flujo_corredor_auxiliar_12h'] for d in dd)==20 and sum(selected.values())==2
 assert all(not p['se_suman'] for p in pp)

def test_homologacion_aprobada_no_mueve_coordenadas_ni_otros_extremos():
 old=[]
 for side in ['origen','destino']:old.append(dict(id_encuesta='SYN',extremo=side,literal_original='LUGAR',lat_original='',lon_original='',estado='Pendiente',cut_comuna='',zona_modelacion_aristo=''))
 raw=[dict(id_encuesta='SYN',origen_original='LUGAR',destino_original='LUGAR',hash_registro='hash')]
 approved=[dict(id_encuesta='SYN',extremo='origen',literal_original='LUGAR',lat_original='',lon_original='',hash_registro_original='hash',CUT_propuesto='C1',zona_propuesta='1',coordenada_individual_disponible='False',nivel_evidencia='B nominal',justificacion='Evidencia',fuentes_evidencia='fuente')]
 geo,changes=apply_geography(old,approved,[],raw,{'C1':dict(zona=1,comuna='COMUNA',nombre_zona='ZONA')},None)
 assert len(changes)==1 and geo['SYN','destino']==old[1] and geo['SYN','origen']['lat_original']==''

def test_matriz_principal_no_hereda_muestra_ni_flujo_del_auxiliar():
 from correr_etapa1 import principal_sin_identificacion
 row={'origen':'A','destino':'B','zona_origen':'39','zona_destino':'31','campana':'Verano','segmento':'VL','flujo_corredor_auxiliar_12h':99,'entrevistas_con_factor':8,'control':'OTRO'}
 out=principal_sin_identificacion([row])[0]
 assert out['flujo_terrestre_Chile_confirmado_12h'] is None and out['factor_expansion_principal'] is None
 assert out['entrevistas_aceptadas_recorrido_Chile_completo']==0
 assert 'entrevistas_con_factor' not in out and 'flujo_corredor_auxiliar_12h' not in out
