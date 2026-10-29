"""Ampliación peatonal y sensibilidad un atributo por vez. No ejecuta etapasprevias.
python etapa5_ampliacion_peatones_20261029/codigo/calcular.py
Requiere pandas,numpy,openpyxl. Editar configuracion.json; --salida para otrodestino.
"""
from pathlib import Path
import json,hashlib,argparse,unicodedata
import pandas as pd
import numpy as np
P=Path(__file__).resolve().parent.parent;R=P.parent
ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=P/'codigo/configuracion.json');ap.add_argument('--salida',type=Path,default=P/'resultados');args=ap.parse_args();cfg=json.loads(args.config.read_text());O=args.salida;O.mkdir(parents=True,exist_ok=True)
paths={'principal':R/'etapa5_transferencia_principal_20261029/resultados/captacion_transferencia_principal.xlsx','cfg_principal':R/'etapa5_transferencia_principal_20261029/codigo/configuracion.json','atributos4':R/'etapa4_costos_generalizados_20261029/resultados/costos_generalizados_etapa4.xlsx','tabla61':R/'etapa1_lacustre_aristo_20261029/fuentes/informe_aristo.txt','tramos':R/'demanda_lago_github/outputs/etapa12/tramos_proyecto.csv','logit':R/'etapa5_logit_preliminar_20261029/resultados/captacion_logit_preliminar.xlsx'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
hashes={k:sha(p) for k,p in paths.items()};pcfg=json.loads(paths['cfg_principal'].read_text())
def total(x):return x.sum(min_count=1)
def norm(x):return ''.join(c for c in unicodedata.normalize('NFD',str(x).upper()) if unicodedata.category(c)!='Mn').strip()
with pd.ExcelFile(paths['principal']) as w:
 f=pd.read_excel(w,'Flujos de referencia');old=pd.read_excel(w,'Demanda por alternativa');cost=pd.read_excel(w,'Costos utilizados');busold=pd.read_excel(w,'Costos buses coordinados');prior=pd.read_excel(w,'Resumen general y residual')
attrs=pd.read_excel(paths['atributos4'],'Costos desagregados OD')
assert cfg['VST']==10047
assert f.loc[f.fuente.eq('CITRA'),'factor_horario'].eq(1.2).all()
rate=cfg['referencia_bus_CLP']/cfg['referencia_bus_km'];vst=cfg['VST'];knots=np.array(pcfg['nudos_ahorro_relativo'])
def capt(a,fam,s):return np.interp(a,knots,pcfg['curvas'][fam][s])
# Factores/años y cantidades ya proyectados se reutilizan directamente.
ref=old[old.escenario_transferencia.eq('central')].copy();peat=ref[ref.segmento.eq('PEATON')].copy();veh=ref[~ref.segmento.eq('PEATON')].copy()
assert not ref.duplicated(['version_referencia','id_flujo','anio']).any()
corebus=busold[busold.escenario.eq('central')&busold.modelable_bus].set_index('id_flujo')
# Distanciasproxy existentes: no confundir cruce con Villa; se conservan como aproximación de localidad.
routes=[]
for r in f[f.segmento.eq('PEATON')].to_dict('records'):
 o,d=norm(r['origen']),norm(r['destino']);iscore={o,d}=={'CHILE CHICO','COYHAIQUE'};isrio={o,d}=={'CHILE CHICO','RIO IBANEZ'}
 common={'id_flujo':r['id_flujo'],'version':r['version'],'origen':r['origen'],'destino':r['destino'],'temporada':r['temporada']}
 if iscore and r['id_flujo'] in corebus.index:
  b=corebus.loc[r['id_flujo']];routes.append({**common,'conexion':'circuito_Coyhaique','peso':1.,'estado':'completa_hipotetica','localidad_proxy':'No: ODoriginal','CG_actual_base':b.CG_origen_actual,'CG_nuevo_base':b.CG_nuevo_bus,'km_vial_nuevo':b.km_bus_total,'h_vial_nuevo':b.tiempo_bus_total_h,'tarifa_buses_nueva':b.tarifa_buses_integrada_CLP,'tarifa_lacustre_nueva':b.tarifa_lacustre_CLP,'h_transbordo_adicional':0.,'h_horario_actual':(b.CG_origen_actual-12550)/vst-5.,'h_horario_nuevo':3.,'fuente':'Carolina Tabla61p127; circuito coordinado y componentes Etapa5principal','supuesto':'Conserva exactamente el circuito/CG ya implementado; bus hipotético.'})
 elif isrio and cfg['proxy_Rio_Ibanez']:
  # No desagregar microdatos: subcohortes de escenario, con distribución espacial no observada.
  direct=attrs[(attrs.segmento=='VL')&(attrs.alternativa=='bahia_jara_levican')&(attrs.temporada==r['temporada'])&attrs.origen.map(norm).eq('CHILE CHICO')&attrs.destino.map(norm).eq('PUERTO IBANEZ')]
  if direct.empty:direct=attrs[(attrs.segmento=='VL')&(attrs.alternativa=='bahia_jara_levican')&(attrs.temporada==r['temporada'])&attrs.origen.map(norm).eq('PUERTO IBANEZ')&attrs.destino.map(norm).eq('CHILE CHICO')]
  b=direct.iloc[0];schedule=b.tiempo_horario_h
  # HorarioSBOoriginal por temporada, mismos criteriosEtapa4.
  ab=attrs[(attrs.segmento=='VL')&(attrs.alternativa=='barcaza_actual')&(attrs.temporada==r['temporada'])].iloc[0];schold=ab.tiempo_horario_h
  for loc,w in cfg['pesos_localidades_Rio_Ibanez'].items():
   km_extra={'PUERTO IBANEZ':0.,'VILLA CERRO CASTILLO':cfg['km_PI_Cerro_proxy'],'PUERTO RIO TRANQUILO':cfg['km_PI_Tranquilo_proxy']}[loc]
   transfers=1 if loc=='PUERTO RIO TRANQUILO' else 0
   conn_h=transfers*cfg['transferencia_adicional_h']
   # Servicioactual: tramoPI–localidad prorateado desde antecedenteCarolina, explícitaaproximación.
   tvold=km_extra*cfg['tiempo_bus_actual_PI_Coy_h']/cfg['referencia_bus_km']
   tvnew=b.tiempo_vial_h+km_extra/cfg['velocidad_conexion_bus_kmh']
   kmnew=b.distancia_vial_km+km_extra
   moneyold=cfg['tarifa_adulta_lacustre']+km_extra*rate
   moneynew=cfg['tarifa_adulta_lacustre']+kmnew*rate
   oldcg=moneyold+vst*(tvold+2.+.5+schold+conn_h)
   newcg=moneynew+vst*(tvnew+80/60+.5+schedule+conn_h)
   routes.append({**common,'conexion':'Rio_Ibanez_proxy_'+loc,'peso':w,'estado':'completa_bajo_imputacion_geografica','localidad_proxy':loc,'CG_actual_base':oldcg,'CG_nuevo_base':newcg,'km_vial_nuevo':kmnew,'h_vial_nuevo':tvnew,'tarifa_buses_nueva':kmnew*rate,'tarifa_lacustre_nueva':2550.,'h_transbordo_adicional':conn_h,'h_horario_actual':schold,'h_horario_nuevo':schedule,'fuente':'Carolina/CCTravel/Interlagos Tabla61p127; distanciasproxy de cacheEtapa4','supuesto':'ODoriginalesRíoIbáñezcomuna intactos. Mezcla virtual de tres localidades, no ubicación observada; conexión aTranquilo víaVillaCerroCastillo coordinada15min. PI–Villa39,8km yPI–Tranquilo158,4km son aproximaciones, no CruceCerroCastillo exacto. Sin descontar tiempo histórico como si fuera navegación.'})
 else:
  state='parcial' if (o=='CHILE CHICO' or d=='CHILE CHICO' or 'COCHRANE' in [o,d]) and 'SIN_OD' not in o and 'SIN_OD' not in d else 'sin_soporte'
  tail=17. if {o,d}=={'CHILE CHICO','PUERTO MONTT'} else np.nan
  routes.append({**common,'conexion':'parcial_o_sin_conexion','peso':1.,'estado':state,'localidad_proxy':'No asignada','CG_actual_base':np.nan,'CG_nuevo_base':np.nan,'km_vial_nuevo':np.nan,'h_vial_nuevo':np.nan,'tarifa_buses_nueva':np.nan,'tarifa_lacustre_nueva':2550.,'h_transbordo_adicional':np.nan,'h_horario_actual':np.nan,'h_horario_nuevo':3.,'h_tramos_historicos_parciales':tail,'km_nucleo_circuito_propuesto':169.386 if state=='parcial' else np.nan,'h_nucleo_circuito_propuesto':7.158870346008373 if state=='parcial' else np.nan,'CG_nucleo_circuito_propuesto':88364.27879297613 if state=='parcial' else np.nan,'fuente':'Tabla61pp127–128 y ODoriginal; no se inventa cabecera o servicio externo','supuesto':'PuertoMontt–Chaitén9h yChaitén–Coyhaique8h conectan nodos históricos, pero faltan acceso aterminal, tarifas ycoordinaciónentre servicios. Aysén–Coyhaique no está acreditado por esta tabla; Cochrane–ChCh4,5h no resuelve extremoAysén. Biobío/SantaCruz/sinOD conservan residual.'})
routes=pd.DataFrame(routes)
partial=routes.estado.eq('parcial')
if partial.any():
 b=corebus.iloc[0]
 routes.loc[partial,'km_nucleo_circuito_propuesto']=b.km_bus_total
 routes.loc[partial,'h_nucleo_circuito_propuesto']=b.tiempo_total_h
 routes.loc[partial,'CG_nucleo_circuito_propuesto']=b.CG_nuevo_bus
 routes['CG_componentes_identificados_sin_tarifa_externa']=routes.CG_nucleo_circuito_propuesto+vst*routes.h_tramos_historicos_parciales.fillna(0)
assert np.allclose(routes.groupby('id_flujo').peso.sum(),1)
# Registrooperacional: únicos servicios posibles, NO multiplicar porOD ni sumar ramas superpuestas.
ops=[]
for freq in [14,21]:
 for name,km,status in [('Chile Chico–Bahía Jara',16.7,'necesario circuito principal'),('Levicán–Coyhaique',152.686,'necesario circuito principal; paradas/intercambios requieren programación'),('Villa Cerro Castillo–Puerto Río Tranquilo',cfg['km_PI_Tranquilo_proxy']-cfg['km_PI_Cerro_proxy'],'refuerzo condicional de escenario comunal; verificar trazado/operación, no sumar con otro servicio duplicado')]:
  ops.append({'servicio':name,'km_por_servicio':km,'zarpes_semana_sentido_coordinados':freq,'salidas_bus_semana_ambos_sentidos':2*freq,'km_bus_semanales_si_se_opera':km*freq*2,'estado':status,'naturaleza':'Hipótesis, no compromiso ni cálculo de flota/costo. Frecuencia histórica de alimentadores no se afirma equivalente a14/21.'})
ops=pd.DataFrame(ops)
# Evaluaciónsincruces: dosoperacionesbase con 3curvas, y sensibilidadesde1atributo solo curvacentral.
allcases=[];costcases=[]
for case in cfg['sensibilidades']:
 choices=cfg['escenarios_eleccion'] if case['id'].startswith('base_') else ['central']
 for choice in choices:
  rr=routes.copy();rr['caso_operacional']=case['id'];rr['con_buses']=case['buses'];rr['escenario_transferencia']=choice
  rr['CG_actual']=rr.CG_actual_base+vst*(case['nav_actual_min']-120)/60
  rr['CG_nuevo']=rr.CG_nuevo_base+vst*((case['nav_nueva_min']-80)/60+.25*168/case['frecuencia_nueva']-3)+(case['factor_tarifa_nueva']-1)*rr.tarifa_lacustre_nueva
  rr['A']=(rr.CG_actual-rr.CG_nuevo)/rr.CG_actual
  rr['conexion_modelable']=rr.CG_actual.gt(0)&rr.CG_nuevo.notna()
  rr['p']=np.where(rr.conexion_modelable,capt(rr.A.to_numpy(),'peatones',choice),np.nan)
  # Ausencia de buses hipotéticos: nueva alternativa no disponible, p0 en soporte identificado.
  if not case['buses']:rr.loc[rr.conexion_modelable,'p']=0.
  rr['h_horario_nuevo_aplicado']=.25*168/case['frecuencia_nueva']
  rr['h_navegacion_nueva_aplicada']=case['nav_nueva_min']/60
  rr['h_navegacion_actual_aplicada']=case['nav_actual_min']/60
  rr['tarifa_lacustre_nueva_aplicada']=rr.tarifa_lacustre_nueva*case['factor_tarifa_nueva']
  rr['p_ponderada']=rr.p*rr.peso;rr['nueva_frecuencia']=case['frecuencia_nueva'];rr['nueva_navegacion_min']=case['nav_nueva_min'];rr['actual_navegacion_min']=case['nav_actual_min'];rr['factor_tarifa_nueva']=case['factor_tarifa_nueva']
  costcases.append(rr)
  group=rr.groupby('id_flujo').agg(p=('p_ponderada',total),cobertura_peso=('peso','sum'),todas_conexiones=('conexion_modelable','all')).reset_index()
  group.loc[~group.todas_conexiones,'p']=np.nan
  out=peat.merge(group,on='id_flujo',how='left',validate='many_to_one')
  out['caso_operacional']=case['id'];out['escenario_transferencia']=choice;out['con_buses']=case['buses']
  out['captacion_peatonal']=out.Q_referencia*out.p
  out['permanece_actual_en_soporte']=out.Q_referencia-out.captacion_peatonal
  out['residual_sin_conexion']=out.Q_referencia.where(out.p.isna(),0.)
  out['referencia_modelada']=out.Q_referencia.where(out.p.notna(),0.)
  previous=old[old.segmento.eq('PEATON')][['version_referencia','id_flujo','anio','escenario_transferencia','D_nuevo']].rename(columns={'D_nuevo':'captacion_anterior_mismo_OD'})
  out=out.merge(previous,on=['version_referencia','id_flujo','anio','escenario_transferencia'],how='left',validate='many_to_one')
  out['diferencia_vs_anterior_mismo_OD']=out.captacion_peatonal-out.captacion_anterior_mismo_OD
  out['naturaleza']='Reemplazo de estimación porOD, no suma con8460,53 previos. Demanda anualizada heredada, geografía proxy marcada.'
  allcases.append(out)
pe=pd.concat(allcases,ignore_index=True);costcases=pd.concat(costcases,ignore_index=True)
# Vehículosprincipales intactos: copiar filas previas para ambasbases de buses. Sensibilidad: solo ajustesaditivos.
vcases=[]
# Ocupacionesy tarifas se leen de componentes/cfg existente; no cambiaVST ni flujos.
csbase=cost[cost.escenario_transferencia.eq('central')].set_index('id_flujo')
for case in cfg['sensibilidades']:
 choices=cfg['escenarios_eleccion'] if case['id'].startswith('base_') else ['central']
 for choice in choices:
  vv=old[~old.segmento.eq('PEATON')&old.escenario_transferencia.eq(choice)].copy()
  vv['caso_operacional']=case['id'];vv['con_buses']=case['buses']
  if not case['id'].startswith('base_'):
   occ=np.where(vv.segmento.isin(['VL','VP']),1.98,1.)
   fare=np.where(vv.segmento.isin(['VL','VP']),21270+.98*2550,np.where(vv.segmento.eq('CAM'),7310*8.657894736842104,np.nan))
   # ParaCAMcon tarifa compatible original,recuperarimporte exacto deEtapa4 porOD ytemporada.
   for idx,r in vv[vv.segmento.eq('CAM')].iterrows():
    ar=attrs[(attrs.fuente_demanda==r.fuente)&(attrs.origen.map(norm)==norm(r.origen))&(attrs.destino.map(norm)==norm(r.destino))&(attrs.segmento=='CAM')&(attrs.temporada==r.temporada)&(attrs.alternativa=='bahia_jara_levican')]
    if len(ar) and pd.notna(ar.iloc[0].tarifa_lacustre_CLP):fare[vv.index.get_loc(idx)]=ar.iloc[0].tarifa_lacustre_CLP
   vv['CG_origen_usado']=vv.CG_origen_usado+np.where(vv.fuente.eq('ARISTO'),vst*occ*(case['nav_actual_min']-120)/60,0)
   vv['CG_nuevo_usado']=vv.CG_nuevo_usado+vst*occ*((case['nav_nueva_min']-80)/60+.25*168/case['frecuencia_nueva']-3)+(case['factor_tarifa_nueva']-1)*fare
   aa=(vv.CG_origen_usado-vv.CG_nuevo_usado)/vv.CG_origen_usado
   ps=[]
   for r,A in zip(vv.itertuples(index=False),aa):
    fam=pcfg['familia'].get(r.segmento)
    if not r.modelable or fam is None:ps.append(np.nan);continue
    if r.es_cola_comun:
     lam=pcfg['peso_cota_superior_cola_comun'][choice];pp=(1-lam)*capt(min(A,0),fam,choice)+lam*capt(max(A,0),fam,choice)
    else:pp=capt(A,fam,choice)
    ps.append(pp)
   vv['p_captacion']=ps;vv['D_nuevo']=vv.Q_referencia*vv.p_captacion
  vv['D_permanece_origen']=vv.Q_referencia-vv.D_nuevo
  vv['D_tierra_CP']=vv.D_permanece_origen.where(vv.fuente.eq('CITRA'),0.).where(vv.modelable)
  vv['D_actual_CP']=vv.D_permanece_origen.where(vv.fuente.eq('ARISTO'),0.).where(vv.modelable)
  vv['D_desviado_tierra']=vv.D_nuevo.where(vv.fuente.eq('CITRA'),0.).where(vv.modelable)
  vv['D_desviado_actual']=vv.D_nuevo.where(vv.fuente.eq('ARISTO'),0.).where(vv.modelable)
  vv['delta_CG']=vv.CG_origen_usado-vv.CG_nuevo_usado
  vv['ahorro_relativo']=(vv.delta_CG/vv.CG_origen_usado).where(~vv.es_cola_comun)
  vv['captacion_total']=vv.D_nuevo;vv['demanda_permanece_origen']=vv.Q_referencia-vv.D_nuevo;vv['residual']=vv.Q_referencia.where(vv.p_captacion.isna(),0.)
  vcases.append(vv)
ve=pd.concat(vcases,ignore_index=True)
# Resultadosdesagregados porunidades: peatón jamás se suma con vehículo.
k=['version_referencia','caso_operacional','escenario_transferencia','anio']
ps=pe.groupby(k,dropna=False).agg(demanda_peatonal_referencia=('Q_referencia',total),demanda_modelada=('referencia_modelada',total),captacion=('captacion_peatonal',total),permanece_actual_modelada=('permanece_actual_en_soporte',total),residual=('residual_sin_conexion',total)).reset_index();ps['segmento']='PEATON';ps['unidad']='personas_peatones'
vs=ve.groupby(k+['segmento','unidad'],dropna=False).agg(demanda_referencia=('Q_referencia',total),captacion=('captacion_total',total),residual=('residual',total)).reset_index()
sensitivity=pd.concat([ps.rename(columns={'demanda_peatonal_referencia':'demanda_referencia'}),vs],ignore_index=True)
base= sensitivity[sensitivity.caso_operacional.eq('base_con_buses')&sensitivity.escenario_transferencia.eq('central')][['version_referencia','anio','segmento','unidad','captacion']].rename(columns={'captacion':'captacion_central_base'})
sensitivity=sensitivity.merge(base,on=['version_referencia','anio','segmento','unidad'],how='left');sensitivity['cambio_vs_base']=sensitivity.captacion-sensitivity.captacion_central_base
before=prior[prior.segmento.eq('PEATON')][['version_referencia','escenario_transferencia','anio','D_nuevo','Q_residual_CP']].rename(columns={'D_nuevo':'captacion_anterior','Q_residual_CP':'residual_anterior'})
comparison=ps.merge(before,on=['version_referencia','escenario_transferencia','anio'],how='left');comparison['diferencia_captacion']=comparison.captacion-comparison.captacion_anterior;comparison['diferencia_residual']=comparison.residual-comparison.residual_anterior
# Cobertura antes/después porOD; se conservan nombres y zonasoriginales enpe.
coverage=pe[(pe.anio==2026)&(pe.caso_operacional=='base_con_buses')&(pe.escenario_transferencia=='central')].groupby(['version_referencia','origen','destino','zona_origen','zona_destino'],dropna=False).agg(referencia=('Q_referencia',total),referencia_modelada=('referencia_modelada',total),captacion=('captacion_peatonal',total),residual=('residual_sin_conexion',total)).reset_index()
services=pd.DataFrame([
 ['Carolina','Coyhaique–Puerto Ibáñez–Chile Chico',6.,'Tabla61p127; incluye cruceactual, no usar6h como tramo vial'],
 ['Freddy','Aeropuerto Balmaceda–Puerto Ibáñez–Chile Chico',5.,'Tabla61p127; no hay ODpeatonalAeropuertoBalmaceda enbase utilizada'],
 ['CCTravel','Puerto Río Tranquilo–Coyhaique',4.5,'Tabla61p127; respalda enlace histórico, no horarios coordinados actuales'],
 ['Eca','Puerto Guadal–Coyhaique',5.75,'Tabla61p127; no hay ODpeatonalPuertoGuadal enbase utilizada'],
 ['Interlagos','Coyhaique–Villa Cerro Castillo–Puerto Río Tranquilo–Puerto Guadal–Chile Chico',8.,'Tabla61p127; rutaexclusivamenteterrestre histórica'],
 ['Kemel/Becker','Puerto Montt–Chaitén–Coyhaique',17.,'Tabla61p127; 9h+8h serviciosdistintos, tarifa/conexiónfinal/accesolocal no completos'],
 ['PauloLanderos','Cochrane–Chile Chico',4.5,'Tabla61p127; no resuelve extremoAysén delODencuestado']
],columns=['empresa','ruta_historica','tiempo_historico_h','uso_y_limite'])
checks=[]
def check(name,ok):checks.append({'validacion':name,'cumple':bool(ok)});assert ok,name
check('Misma demanda porcaso ycurva',ps.groupby(['version_referencia','anio']).demanda_peatonal_referencia.nunique().eq(1).all())
check('Conservación peatonal conresidual',np.allclose(ps.permanece_actual_modelada+ps.captacion+ps.residual,ps.demanda_peatonal_referencia))
check('Sin buses no captaciónpeatonal',ps.loc[ps.caso_operacional.eq('base_sin_buses'),'captacion'].eq(0).all())
check('Probabilidadesválidas',costcases.p.dropna().between(0,1).all())
# Elcircuito previamente calculado se reemplazaexactamente, no se sumaotra vez.
coreids=set(corebus.index)
core=pe[pe.id_flujo.isin(coreids)&pe.caso_operacional.eq('base_con_buses')]
check('Circuitocentral anterior intacto mismoOD',np.allclose(core.captacion_peatonal,core.captacion_anterior_mismo_OD))
original_vehicle=old[~old.segmento.eq('PEATON')].set_index(['version_referencia','escenario_transferencia','anio','id_flujo']).D_nuevo
for casebase in ['base_con_buses','base_sin_buses']:
 actual=ve[ve.caso_operacional.eq(casebase)].set_index(['version_referencia','escenario_transferencia','anio','id_flujo']).captacion_total
 check('Captaciónvehicular principal intacta '+casebase,np.allclose(actual,original_vehicle.reindex(actual.index),equal_nan=True))
check('A/Bnunca duplicadas dentrocaso',not pe.duplicated(['version_referencia','id_flujo','anio','caso_operacional','escenario_transferencia']).any())
check('PesosproxyconservanOD',np.allclose(routes.groupby('id_flujo').peso.sum(),1))
check('No nuevosODni magnitudes',set(pe.id_flujo)==set(peat.id_flujo))
vg=ve[ve.Q_referencia.notna()&ve.p_captacion.notna()]
check('Conservaciónvehicularsensibilidades',np.allclose(vg.demanda_permanece_origen+vg.captacion_total,vg.Q_referencia))
check('Busesun solo desfasehorario',costcases.loc[costcases.conexion_modelable,'h_horario_nuevo'].eq(3).all())
check('Sin nuevosviajesenvehículos',ve.groupby(['version_referencia','escenario_transferencia','anio','id_flujo']).Q_referencia.nunique(dropna=False).eq(1).all())
check('Fuentesanteriores intactas',all(sha(paths[k])==v for k,v in hashes.items()))
check('Todas sensibilidades unatributo',all(sum(c[x]!=cfg['sensibilidades'][0][x] for x in ['buses','nav_actual_min','nav_nueva_min','frecuencia_nueva','factor_tarifa_nueva'])==1 for c in cfg['sensibilidades'][1:]))
checks=pd.DataFrame(checks)
notes=pd.DataFrame([{'parametro':k,'valor':json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v} for k,v in cfg.items()])
extras=[('Principio','No se suman8460,53peatones anteriores con nuevasestimaciones. Se reemplaza cadacelda enestaentrega y se conserva antes/después.'),('RíoIbáñez','Escomuna sin localidadobservada. Pesos1/3porPI,VillaCerroCastillo,Tranquilo son hipótesis explícita, NOreclasificación geográfica. La captación se calcula porrepresentante y luego pondera probabilidades, no CGmedios.'),('Servicios','ARISTOTabla61pp127–128 contiene antecedenteshistóricos, no vigenciaactual. La frecuencia hipotética14/21 por sentido requiere coordinar/alimentar servicios; no se heredan esas frecuencias de operadoreshistóricos.'),('ActualPI','Para el circuitooriginal se conserva CGactual sin modificar. Para nuevosproxies se usa navegación120,emb/des0,5h yhorarioSBO14/12; vialactual proratea2,5hCarolinaPI-Coyhaique sobre121,956km. Esunaimputación, no tramo6hcomovial.'),('Nuevobus','Coremantiene2,325537hVLproxybus. Extensionesnorte desconocidas usan50km/hdeacceso; tarifa10000/121,956km; nueva tarifaadulta2550. Cambioextracoordinado15min una vez. Sin otraesperacompleta delbus. Sin descuentoedad/estudio.'),('Sin buses','Se supone nuevo cruce no disponible alpeatónsin alimentaciónhipotética. P0solo ensoportegeográfico identificado; otrosflujos siguenresiduales. Losservicioshistóricosactuales sonreferencia, no desvío aterminalesnuevos.'),('Sensibilidad','Se usa solo curva central para variantesoperacionales. Navegaciónactual160 afecta solo procedenciaARISTO; nueva40 afecta todousuario nuevo. Frecuencia21 cambiaúnicamente w168/f. Tarifa75%reduce solo tarifalacustrenueva, sin tocarbusni tarifaactual.'),('Peatonesparciales','PuertoMontt tiene cadena histórica de17h, pero no tarifa/accesoalterminalcompletos. Aysén–Coyhaique no está identificado enTabla61; sinOD/internacionales no se localizanprecisamente. Se conservan componentesparciales y residual.'),('Costosopbuses','Serviciosnecesarios y km/frecuencia quedanregistrados; no se calculacostooperacional ni tamañodeflota. No sumar kilómetros porOD ni ramas que duplican recorridos. Alimentadores adicionales sonrefuerzos condicionales, no oferta actual.'),('Unidades','VL,VP,CAMypeatones por separado. No son todoslospasajeros. DemandaCITRA conserva1,20 y coberturaanterior. Crecimientocentral yfactoresanuales ya existentes, sin nuevos cálculosPIB.'),('Reproducir','DesdeAnexos:python etapa5_ampliacion_peatones_20261029/codigo/calcular.py. Configuracióneditable y--salida nueva_carpeta. Solo resultados previos yTabla61yaextraída; sin EOD/geocodificación/red/logit.')]
notes=pd.concat([notes,pd.DataFrame(extras,columns=['parametro','valor'])],ignore_index=True)
trace=pd.DataFrame([{'fuente':k,'archivo':str(paths[k]),'sha256':v} for k,v in hashes.items()])
sheets={'Parametros y supuestos':notes,'Servicios historicos':services,'Costos y conexiones buses':costcases,'Cobertura peatonal OD':coverage,'Demanda peatonal OD':pe,'Resultados peatones':ps,'Comparacion anterior':comparison,'Sensibilidad operacional':sensitivity,'Detalle vehicular':ve,'Oferta buses para evaluar':ops,'Validaciones':checks,'Trazabilidad':trace}
with pd.ExcelWriter(O/'ampliacion_peatones_sensibilidad.xlsx',engine='openpyxl') as w:
 for name,df in sheets.items():
  df.to_excel(w,sheet_name=name,index=False);ws=w.book[name];ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions
  for col in ws.columns:
   ws.column_dimensions[col[0].column_letter].width=min(48,max(14,len(str(col[0].value or ''))+2))
   for c in col[1:]:
    if isinstance(c.value,float):c.number_format='#,##0.0000'
fmt=lambda d:d.to_html(index=False,border=0,na_rep='No estimable',float_format=lambda v:f'{v:,.3f}')
main=ps[(ps.version_referencia=='B')&(ps.escenario_transferencia=='central')];sens=sensitivity[(sensitivity.version_referencia=='B')&(sensitivity.anio==2026)&(sensitivity.escenario_transferencia=='central')&sensitivity.segmento.isin(['VL','VP','CAM','PEATON'])]
page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Peatones y sensibilidad operacional</title><style>body{{font:16px system-ui;max-width:1300px;margin:32px auto;padding:0 20px;color:#18374a}}p{{line-height:1.5}}table{{border-collapse:collapse;display:block;overflow:auto;font-size:12px}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#eaf2f7}}</style><h1>Ampliación peatonal y sensibilidad operacional</h1>
<p>Se conserva la demanda anualizada, el crecimiento central y la función principal por tramos. Cada OD se estima de nuevo en esta carpeta; no se suma su captación a los 8.460,53 peatones anteriores. El escenario vehicular de referencia permanece intacto.</p><h2>Resultados peatonales centrales — ARISTO B</h2>{fmt(main[['caso_operacional','anio','demanda_peatonal_referencia','demanda_modelada','captacion','permanece_actual_modelada','residual']])}
<h2>Cobertura y nuevas conexiones</h2>{fmt(coverage[coverage.version_referencia=='B'])}<p>El circuito Chile Chico–Coyhaique y su inverso conservan exactamente sus costos y captación anteriores. Río Ibáñez se mantiene como comuna: se evalúa una mezcla explícita de tres localidades representativas, no ubicaciones observadas. Para cada representante se calcula su captación y luego se pondera; no se asigna toda la comuna a Puerto Ibáñez. Este supuesto puede desactivarse en la configuración.</p>
<p>Las extensiones tienen tarifas por distancia a81,997CLP/km y velocidad de referencia50km/h cuando no existe tiempo completo de bus. Para el servicio actual se usa una aproximación desde el accesoCarolinaPI–Coyhaique de2,5h, conservando el cruce por separado. Los nuevos accesos más largos pueden eliminar el ahorro; ampliar la cobertura no obliga a obtener captación positiva.</p>
<p>Puerto Montt tiene una cadena histórica víaChaitén/Coyhaique, pero faltan tarifas, acceso local y coordinación suficientes para un CG completo. Aysén no debe convertirse automáticamente en una cabecera con bus disponible. Los OD internacionales, genéricos y sin OD conservan su balance residual.</p>
<h2>Servicios históricos consultados</h2>{fmt(services)}<p>Fuente: Informe FinalARISTO, tabla61,páginas127–128; tarifa adulta tabla52,p121. Los servicios y tiempos son históricos, no una confirmación de operación vigente. Los tiempos6h/5h que incluyen el ferry no se usan como si fueran solo conducción terrestre.</p>
<h2>Sin buses frente a buses coordinados</h2><p>Sin nuevos buses, se supone que el nuevo cruce no ofrece acceso peatonal completo; la captación en el soporte identificado es cero y los otros viajes siguen residuales. Con buses se supone una operación nueva coordinada con14zarpes semanales/sentido, navegación80min y15min por terminal. Se aplica una sola penalizaciónhoraria; un cambio adicional coordinado agrega15min, no otra espera de barcaza. No hay descuentos automáticos por edad o condición estudiantil.</p>
<h2>Sensibilidades de un atributo — 2026</h2>{fmt(sens[['caso_operacional','segmento','unidad','captacion','cambio_vs_base']])}<p>Las variantes usan la curva central y modifican un atributo respecto de la base: navegación actual160min, nueva40min, frecuencia nueva21/sentido/semana o tarifa lacustre nueva75%de referencia. No se combinan. Los restantes años están en el Excel. Se conservan unidades distintas y no se suman VP con VL.</p>
<h2>Servicios y kilómetros para evaluación posterior</h2>{fmt(ops)}<p>Estos kilómetros y frecuencias son hipótesis operacionales, no costos ya evaluados ni tamaño de flota. Los refuerzos y ramas no se suman indiscriminadamente; su trazado y coordinación requieren definir el plan de operación. No se estima todavía demanda inducida, capacidad ni beneficios sociales.</p>
<h2>Validaciones y reproducción</h2>{fmt(checks)}<p><a href="ampliacion_peatones_sensibilidad.xlsx">Descargar Excel</a>. Desde Anexos:<code>python etapa5_ampliacion_peatones_20261029/codigo/calcular.py</code>. Parámetros editables en<code>codigo/configuracion.json</code>. Todas las entregas anteriores permanecen intactas.</p></html>'''
(O/'informe_peatones_sensibilidad.html').write_text(page,encoding='utf-8')
print(json.dumps({'controles':len(checks),'peatones2026':main[main.anio.eq(2026)][['caso_operacional','captacion','demanda_modelada','residual']].to_dict('records')},ensure_ascii=False))
