"""Actualizaciónoficial parametrizada; fórmulas deEtapas5–6 sin reconstruir entradas.
python actualizacion_oficial_alternativas_20261029/codigo/calcular.py
Requiere pandas,numpy,openpyxl. --config archivo.json --salida (opcional; entrega oficial se actualiza enresultados).
"""
from pathlib import Path
import argparse,json,hashlib,calendar,unicodedata
import pandas as pd
import numpy as np
from tablas_equipo import construir_tablas_equipo, informe_equipo
P=Path(__file__).resolve().parent.parent;R=P.parent
ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=P/'codigo/configuracion.json');ap.add_argument('--salida',type=Path,default=P/'resultados');args=ap.parse_args();C=json.loads(args.config.read_text());O=args.salida;O.mkdir(parents=True,exist_ok=True)
paths={'cierre6':R/'etapa6_cierre_incremental_20261029/resultados/demanda_inducida_incremental_final.xlsx','cfg_captacion':R/'etapa5_transferencia_principal_20261029/codigo/configuracion.json','cfg_elasticidades':R/'etapa6_demanda_inducida_20261029/codigo/configuracion.json','atributos4':R/'etapa4_costos_generalizados_20261029/resultados/costos_generalizados_etapa4.xlsx','componentes5':R/'etapa5_logit_preliminar_20261029/resultados/captacion_logit_preliminar.xlsx','buses5':R/'etapa5_ampliacion_peatones_20261029/resultados/ampliacion_peatones_sensibilidad.xlsx','tramos':R/'demanda_lago_github/outputs/etapa12/tramos_proyecto.csv'}
hashes={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
cc=json.loads(paths['cfg_captacion'].read_text());ec=json.loads(paths['cfg_elasticidades'].read_text());assert C['VST']==10047
with pd.ExcelFile(paths['cierre6']) as w:
 b=pd.read_excel(w,'Distribucion por conexion');foreign=pd.read_excel(w,'Indicadores extranjeros')
b=b[b.escenario_elasticidad.eq('central')&b.anio.isin(C['anios'])].copy().reset_index(drop=True)
keep=['version_referencia','version','fuente','id_flujo','id_base','origen','destino','zona_origen','zona_destino','sentido_cruce','temporada','segmento','unidad','componente','subtipo','anio','Q_referencia','factor_crecimiento_existente','Q_heredada_expandida','Q_imputacion_temporal_adicional','Q_OD_imputado_ARISTO','peso_conexion','conexion','CG_SBO','CG_tierra','CG_actual','CG_nuevo','en_mercado_modelado','costo_solo_nucleo','costos_imputados','estado_conexion','supuesto','nacionalidad_declarada_OD','patente_extranjera_OD','OD_internacional']
b=b[[c for c in keep if c in b]].copy();assert b.id_base.is_unique
attrs=pd.read_excel(paths['atributos4'],'Costos desagregados OD')
oldcomp=pd.read_excel(paths['componentes5'],'Costos utilizados e imputados')
bus=pd.read_excel(paths['buses5'],'Costos y conexiones buses');bus=bus[bus.caso_operacional.eq('base_con_buses')&bus.escenario_transferencia.eq('central')]
tr=pd.read_csv(paths['tramos']);access=tr[tr.id.astype(str).str.startswith('X735')].groupby('segmento').first();covrate=(access['cov']/access.km/C['ipc_enero2026_a_dic2025']).to_dict();covrate['VP']=covrate['VL'];covrate['PEATON']=0.
# Tiempos terrestresya calculados; añadir únicamente la diferencia de acceso autorizada.
def norm(v):return ''.join(c for c in unicodedata.normalize('NFD',str(v).upper()) if unicodedata.category(c)!='Mn').strip()
for df in [attrs,oldcomp]:df['o']=df.origen.map(norm);df['d']=df.destino.map(norm)
aidx={(r.fuente_demanda,r.o,r.d,r.segmento,r.temporada,r.alternativa):r._asdict() for r in attrs.itertuples(index=False)}
cidx={(r.fuente,r.o,r.d,r.segmento,r.temporada,r.alternativa):r._asdict() for r in oldcomp.itertuples(index=False)}
cache={}
def components(source,o,d,seg,t,alt):
 key=(source,o,d,seg,t,alt)
 if key in cache:return cache[key]
 if seg=='VP':
  out=components(source,o,d,'VL',t,alt);cache[key]=out;return out
 a=aidx.get(key);cp=cidx.get(key);out={'km':np.nan,'h':np.nan,'cov':np.nan,'fare':np.nan,'tipo':'Sin componentes completos; conservar CG previo documentado'}
 if a is not None:
  out.update(km=a['distancia_vial_km'],h=a['tiempo_vial_h'],cov=a['COV_privado_CLP'],fare=a['tarifa_lacustre_CLP'],tipo=a['fuente_fisica'])
 if cp is not None and pd.notna(cp.get('componentes_imputados')):
  try:
   js=json.loads(cp['componentes_imputados'])
   for dst,src in [('km','distancia_vial_km'),('h','tiempo_vial_h'),('cov','COV_CLP'),('fare','tarifa_CLP')]:
    if src in js:out[dst]=js[src]
   out['tipo']='Componentes imputados ya existentesEtapa5, sin nuevos recorridos'
  except (ValueError,TypeError):pass
 if cp is not None and cp.get('tipo_costo')=='nucleo_diferencial_cola_comun':
  x,y=('CHILE CHICO','COYHAIQUE') if o=='CHILE CHICO' else ('COYHAIQUE','CHILE CHICO');out=components('ARISTO',x,y,seg,t,alt).copy();out['tipo']='Solo núcleo referencial, cola externa no valorada; no distancia total del OD'
 cache[key]=out;return out
# Exposiciónequivalente y horario: mismaSBO para las3alternativas.
season={}
for t,months in C['meses_temporada'].items():
 ds=np.array([calendar.monthrange(2026,m)[1] for m in months]);oldfs=np.array([14 if m in C['SBO']['meses_alta'] else 12 for m in months]);newfs=np.array([C['SBO']['frecuencia_alta'] if m in C['SBO']['meses_alta'] else C['SBO']['frecuencia_baja'] for m in months]);proyfs=np.array([C['frecuencia_nuevo']['alta'] if m in C['frecuencia_nuevo_meses_alta'] else C['frecuencia_nuevo']['baja'] for m in months])
 season[t]={'days':int(ds.sum()),'oldhor':float(np.average(42/oldfs,weights=ds)),'hor':float(np.average(C['w_horario']*168/newfs,weights=ds)),'zactual':float(np.sum(ds*newfs/7)),'hor_nuevo':float(np.average(C['w_horario']*168/proyfs,weights=ds)),'znuevo':float(np.sum(ds*proyfs/7))}
b['ocupacion']=b.segmento.map({'VL':1.98,'VP':1.98,'CAM':1.,'PEATON':1.})
b['anticipacion_nueva_h']=b.segmento.map(C['anticipacion_h'])
b['T_horario_actual']=b.temporada.map({t:v['hor'] for t,v in season.items()})
b['T_horario_actual_anterior']=b.temporada.map({t:v['oldhor'] for t,v in season.items()})
b['dias_equivalentes']=b.temporada.map({t:v['days'] for t,v in season.items()})
b['zarpes_actual_sentido_temporada']=b.temporada.map({t:v['zactual'] for t,v in season.items()})
b['zarpes_nuevo_sentido_temporada']=b.temporada.map({t:v['znuevo'] for t,v in season.items()})
b['CG_actual_SBO']=b.CG_actual+C['VST']*b.ocupacion*((C['SBO']['navegacion_min']-120)/60+(b.anticipacion_nueva_h-.25)+(C['desembarque_h']-.25)+(b.T_horario_actual-b.T_horario_actual_anterior))
b['CG_tierra_SBO']=b.CG_tierra
b['CG_origen_SBO']=b.CG_actual_SBO.where(b.fuente.eq('ARISTO'),b.CG_tierra_SBO)
# Componentes de entrada porcohorte; se mantienen faltantes cuando nunca fueron completos.
metricrows=[]
for r in b.itertuples(index=False):
 row={'id_base':r.id_base}
 for name,alt in [('tierra','terrestre_chile'),('actual','barcaza_actual'),('nuevo','bahia_jara_levican')]:
  a=components(r.fuente,norm(r.origen),norm(r.destino),r.segmento,r.temporada,alt)
  for col in ['km','h','cov','fare']:row[name+'_'+col+'_base']=a[col]
  row[name+'_fuente_componentes']=a['tipo']
 if r.segmento=='PEATON':
  q=bus[(bus.id_flujo==r.id_flujo)&(bus.conexion==r.conexion)]
  if len(q):
   q=q.iloc[0];row['nuevo_km_base']=q.km_vial_nuevo;row['nuevo_h_base']=q.h_vial_nuevo;row['nuevo_cov_base']=0.;row['nuevo_fare_base']=q.tarifa_lacustre_nueva;row['nuevo_tarifa_bus_base']=q.tarifa_buses_nueva
   row['nuevo_transbordo_adicional_h']=q.h_transbordo_adicional
   row['nuevo_fuente_componentes']='Busescoordinados/conexiones previas; no servicioscomprometidos'
 metricrows.append(row)
b=b.merge(pd.DataFrame(metricrows),on='id_base',validate='one_to_one')
# MantenerdirecciónobservadaARISTO; CITRA dirección geográfica porOD ya homologado.
b['direccion_cruce']=np.where(b.fuente.eq('ARISTO'),np.where(b.sentido_cruce.eq('Chile Chico → Puerto Ibáñez'),'Sur → Norte',np.where(b.sentido_cruce.eq('Puerto Ibáñez → Chile Chico'),'Norte → Sur','Sin dirección determinable')),np.where(b.zona_origen.eq(39),'Sur → Norte',np.where(b.zona_destino.eq(39),'Norte → Sur','Sin dirección determinable')))
b['direccion_servicio_actual']=b.direccion_cruce.map({'Sur → Norte':'Chile Chico → Puerto Ibáñez','Norte → Sur':'Puerto Ibáñez → Chile Chico'})
b['direccion_servicio_nuevo']=b.direccion_cruce.map({'Sur → Norte':'Bahía Jara → Levicán','Norte → Sur':'Levicán → Bahía Jara'})
costs=[];result=[]
knots=np.asarray(cc['nudos_ahorro_relativo'])
for project in C['alternativas']:
 q=b.copy();q['alternativa_proyecto']=project['id'];q['nombre_proyecto']=project['nombre'];q['acceso']=project['acceso'];q['km_acceso_norte']=project['km_acceso'];q['nave']=project['nave'];q['infraestructura']=project['puerto']
 dk=project['km_acceso']-C['km_acceso_referencia'];q['delta_km_acceso']=dk;q['delta_tiempo_vial_h']=dk/q.segmento.map(C['velocidad_acceso_kmh']);q['delta_COV_acceso']=dk*q.segmento.map(covrate)
 q['delta_tarifa_buses']=np.where(q.segmento.eq('PEATON'),dk*C['tarifa_bus_km'],0.)
 q['tiempo_navegacion_nuevo_h']=project['navegacion_min']/60;q['tiempo_presentacion_h']=q.anticipacion_nueva_h;q['tiempo_desembarque_h']=C['desembarque_h'];q['tiempo_horario_nuevo_h']=q.temporada.map({t:v['hor_nuevo'] for t,v in season.items()});q['distancia_lacustre_km']=C['distancia_navegacion_millas']*1.852
 q['nuevo_km_actualizado']=q.nuevo_km_base+dk;q['nuevo_h_vial_actualizado']=q.nuevo_h_base+q.delta_tiempo_vial_h;q['nuevo_COV_actualizado']=q.nuevo_cov_base+q.delta_COV_acceso;q['nuevo_tarifa_buses_actualizada']=q.get('nuevo_tarifa_bus_base',np.nan)+q.delta_tarifa_buses
 q['CG_nuevo_CP']=q.CG_nuevo+q.delta_COV_acceso+q.delta_tarifa_buses+C['VST']*q.ocupacion*(q.delta_tiempo_vial_h+(project['navegacion_min']-80)/60+(q.anticipacion_nueva_h-.25)+(C['desembarque_h']-.25)+(q.tiempo_horario_nuevo_h-3))
 q['nuevo_tiempo_total_h']=q.nuevo_h_vial_actualizado+q.tiempo_navegacion_nuevo_h+q.tiempo_presentacion_h+q.tiempo_desembarque_h+q.tiempo_horario_nuevo_h+q.nuevo_transbordo_adicional_h.fillna(0)
 q['nuevo_costo_monetario']=q.nuevo_COV_actualizado+q.nuevo_fare_base+q.nuevo_tarifa_buses_actualizada.where(q.segmento.eq('PEATON'),0.)
 q['nuevo_costo_temporal']=C['VST']*q.ocupacion*q.nuevo_tiempo_total_h
 q['CG_actual_CP']=q.CG_actual_SBO;q['CG_tierra_CP']=q.CG_tierra_SBO
 q['delta_CG_captacion']=q.CG_origen_SBO-q.CG_nuevo_CP;q['A']=q.delta_CG_captacion/q.CG_origen_SBO
 q['CG_min_SBO']=q[['CG_tierra_SBO','CG_actual_SBO']].min(axis=1,skipna=True);q['CG_min_CP']=q[['CG_tierra_CP','CG_actual_CP','CG_nuevo_CP']].min(axis=1,skipna=True)
 q['modelable_captacion']=q.en_mercado_modelado.fillna(False)&q.CG_origen_SBO.gt(0)&q.CG_nuevo_CP.gt(0)&q.segmento.isin(cc['familia'])
 q['modelable_induccion']=q.modelable_captacion&~q.costo_solo_nucleo.fillna(False)&q.CG_min_SBO.gt(0)&q.CG_min_CP.gt(0)
 costs.append(q.copy())
 for case in C['casos']:
  z=q.copy();sc=case['captacion'];ep=case['elasticidad'];z['escenario_captacion']=sc;z['escenario_elasticidad']=ep;z['p_nuevo']=np.nan
  for seg,fam in cc['familia'].items():
   m=z.segmento.eq(seg)&z.modelable_captacion;abs_m=m&~z.costo_solo_nucleo.fillna(False);tail_m=m&z.costo_solo_nucleo.fillna(False)
   z.loc[abs_m,'p_nuevo']=np.interp(z.loc[abs_m,'A'],knots,cc['curvas'][fam][sc])*cc['factibilidad'][fam]
   lam=cc['peso_cota_superior_cola_comun'][sc];lo=np.minimum(z.loc[tail_m,'A'],0);hi=np.maximum(z.loc[tail_m,'A'],0)
   z.loc[tail_m,'p_nuevo']=((1-lam)*np.interp(lo,knots,cc['curvas'][fam][sc])+lam*np.interp(hi,knots,cc['curvas'][fam][sc]))*cc['factibilidad'][fam]
  z['D_existente_nuevo']=z.Q_referencia*z.p_nuevo
  z['D_tierra_SBO']=z.Q_referencia.where(z.fuente.eq('CITRA'),0.);z['D_actual_SBO']=z.Q_referencia.where(z.fuente.eq('ARISTO'),0.)
  z['D_desviada_tierra']=z.D_existente_nuevo.where(z.fuente.eq('CITRA'),0.).where(z.p_nuevo.notna());z['D_desviada_actual']=z.D_existente_nuevo.where(z.fuente.eq('ARISTO'),0.).where(z.p_nuevo.notna())
  stay=z.Q_referencia-z.D_existente_nuevo
  z['D_tierra_CP_existente']=stay.where(z.fuente.eq('CITRA'),0.).where(z.p_nuevo.notna());z['D_actual_CP_existente']=stay.where(z.fuente.eq('ARISTO'),0.).where(z.p_nuevo.notna())
  z['D_residual_existente']=z.Q_referencia.where(z.p_nuevo.isna(),0.)
  z['epsilon_CG']=z.segmento.map({s:d[ep] for s,d in ec['elasticidades'].items()})
  z['D_inducida_incremental']=np.nan;valid=z.modelable_induccion&z.Q_referencia.notna();improve=valid&z.CG_min_CP.lt(z.CG_min_SBO-1e-9)
  z.loc[valid,'D_inducida_incremental']=0.
  # Misma descomposiciónincremental finalEtapa6: brutoCPmenos potencial yaSBO.
  z.loc[improve,'D_inducida_incremental']=(z.loc[improve,'Q_referencia']*((z.loc[improve,'CG_min_CP']/z.loc[improve,'CG_origen_SBO'])**z.loc[improve,'epsilon_CG']-(z.loc[improve,'CG_min_SBO']/z.loc[improve,'CG_origen_SBO'])**z.loc[improve,'epsilon_CG'])).clip(lower=0)
  z['D_inducida_nuevo']=z.D_inducida_incremental*z.p_nuevo
  z['D_inducida_tierra']=(z.D_inducida_incremental*(1-z.p_nuevo)).where(z.fuente.eq('CITRA'),0.).where(z.D_inducida_incremental.notna());z['D_inducida_actual']=(z.D_inducida_incremental*(1-z.p_nuevo)).where(z.fuente.eq('ARISTO'),0.).where(z.D_inducida_incremental.notna())
  for route,existing in [('nuevo','D_existente_nuevo'),('tierra','D_tierra_CP_existente'),('actual','D_actual_CP_existente')]:
   z['D_'+route+'_CP_total']=z[existing].fillna(0)+z['D_inducida_'+route].fillna(0);z.loc[z[existing].isna()&z['D_inducida_'+route].isna(),'D_'+route+'_CP_total']=np.nan
  z['D_base_fuera_soporte_induccion']=z.Q_referencia.where(~z.modelable_induccion,0.)
  z['nuevo_diario_equiv']=z.D_nuevo_CP_total/z.dias_equivalentes;z['nuevo_por_zarpe_equiv']=z.D_nuevo_CP_total/z.zarpes_nuevo_sentido_temporada
  z['actual_SBO_por_zarpe_equiv']=z.D_actual_SBO/z.zarpes_actual_sentido_temporada;z['actual_CP_por_zarpe_equiv']=z.D_actual_CP_total/z.zarpes_actual_sentido_temporada
  result.append(z)
costs=pd.concat(costs,ignore_index=True);d=pd.concat(result,ignore_index=True)
# Unidades y versionesseparadas; alternativasycasos nunca se suman entre sí.
keys=['alternativa_proyecto','version_referencia','escenario_captacion','escenario_elasticidad','anio','segmento','unidad']
metrics=['Q_referencia','D_tierra_SBO','D_actual_SBO','D_existente_nuevo','D_desviada_tierra','D_desviada_actual','D_tierra_CP_existente','D_actual_CP_existente','D_inducida_incremental','D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_tierra_CP_total','D_actual_CP_total','D_nuevo_CP_total','D_residual_existente','D_base_fuera_soporte_induccion']
summary=d.groupby(keys,dropna=False)[metrics].sum(min_count=1).reset_index()
summary['alcance']='Aportesestimados yescenarios demercado cubierto; CITRAno totalterrestre, A/Bindependientes; no sumartiposincompatibles'
byperiod=d.groupby(keys+['temporada','direccion_cruce'],dropna=False)[metrics].sum(min_count=1).reset_index();byperiod['dias_equivalentes']=byperiod.temporada.map({t:v['days'] for t,v in season.items()});byperiod['zarpes_nuevo_equiv']=byperiod.temporada.map({t:v['znuevo'] for t,v in season.items()})
byperiod['nuevo_diario_equiv']=byperiod.D_nuevo_CP_total/byperiod.dias_equivalentes;byperiod['nuevo_por_zarpe_equiv']=byperiod.D_nuevo_CP_total/byperiod.zarpes_nuevo_equiv
# Modelo oficialdetallado deja disponibles los componentes sin repetir metadatos largos en todaslasfilas.
cov=d[(d.anio==2026)&d.escenario_captacion.eq('central')&d.escenario_elasticidad.eq('central')].copy()
cov['Q_modelada_captacion']=cov.Q_referencia.where(cov.p_nuevo.notna(),0.)
cov['Q_modelada_induccion']=cov.Q_referencia.where(cov.modelable_induccion,0.)
cov['Q_costos_imputados']=cov.Q_modelada_captacion.where(cov.costos_imputados,0.)
coverage=cov.groupby(['alternativa_proyecto','version_referencia','fuente','segmento','unidad'],dropna=False)[['Q_referencia','Q_modelada_captacion','Q_modelada_induccion','Q_costos_imputados','Q_imputacion_temporal_adicional','D_residual_existente']].sum(min_count=1).reset_index()
cols=['alternativa_proyecto','nombre_proyecto','acceso','version_referencia','fuente','id_flujo','id_base','conexion','peso_conexion','origen','destino','zona_origen','zona_destino','segmento','unidad','temporada','direccion_cruce','anio','escenario_captacion','escenario_elasticidad']+metrics+['p_nuevo','epsilon_CG','CG_origen_SBO','CG_min_SBO','CG_min_CP','CG_nuevo_CP','modelable_captacion','modelable_induccion','nuevo_diario_equiv','nuevo_por_zarpe_equiv','actual_SBO_por_zarpe_equiv','actual_CP_por_zarpe_equiv']
# Validaciones enfocadas en diferencias oficiales yconservación.
checks=[]
def check(name,test):checks.append({'validacion':name,'cumple':bool(test)});assert test,name
check('MismaSBO costos entre3proyectos',costs.groupby('id_base')[['CG_actual_SBO','CG_tierra_SBO']].nunique(dropna=False).eq(1).all().all())
check('Misma demanda baseenproyectosycasos',d.groupby('id_base').Q_referencia.nunique(dropna=False).eq(1).all())
check('Atributosterrestres no cambian',np.allclose(costs.CG_tierra_CP,costs.CG_tierra,equal_nan=True))
check('Servicioactual idénticoSBO/CP',np.allclose(costs.CG_actual_SBO,costs.CG_actual_CP,equal_nan=True))
check('COVHDM4sin actualizaciónmetodológica',abs(covrate['VL']-216/C['ipc_enero2026_a_dic2025'])<1e-8 and abs(covrate['CAM']-1103/C['ipc_enero2026_a_dic2025'])<1e-8)
check('Desembarque30min igualtodos',costs.tiempo_desembarque_h.eq(.5).all())
check('Presentaciónsin doble15min',costs.tiempo_presentacion_h.eq(costs.segmento.map(C['anticipacion_h'])).where(costs.segmento.isin(C['anticipacion_h']),True).all())
check('Ambos cruces mismo horario11/8',np.allclose(costs.tiempo_horario_nuevo_h,costs.T_horario_actual))
check('Ambos cruces misma exposición11/8',np.allclose(costs.zarpes_nuevo_sentido_temporada,costs.zarpes_actual_sentido_temporada))
check('Frecuencia oficial nuevo11/8',C['frecuencia_nuevo']=={'alta':11,'baja':8})
check('Probabilidades0a1',d.p_nuevo.dropna().between(0,1).all())
m=d[d.p_nuevo.notna()&d.Q_referencia.notna()]
check('Conservación existenteCP',np.allclose(m.D_tierra_CP_existente+m.D_actual_CP_existente+m.D_existente_nuevo,m.Q_referencia))
known=d.Q_referencia.notna()
check('Conservación global existente incluye residual',np.allclose(d.loc[known,['D_tierra_CP_existente','D_actual_CP_existente','D_existente_nuevo']].fillna(0).sum(axis=1)+d.loc[known,'D_residual_existente'],d.loc[known,'Q_referencia']))
check('Desviadaigualsuma deprocedencias',np.allclose(m.D_existente_nuevo,m.D_desviada_tierra+m.D_desviada_actual))
mm=d[d.D_inducida_incremental.notna()]
check('Conservaciónrepartoinducida',np.allclose(mm.D_inducida_incremental,mm.D_inducida_nuevo+mm.D_inducida_tierra+mm.D_inducida_actual))
check('Sinmejora mínimoSBOnoinducida',d.loc[d.modelable_induccion&d.CG_min_CP.ge(d.CG_min_SBO-1e-9)&d.Q_referencia.notna(),'D_inducida_incremental'].eq(0).all())
check('Sin sumarA/Bo vistaprivados',not d.segmento.eq('PRIVADOS_COMPATIBLES').any() and not d.duplicated(['alternativa_proyecto','id_base','escenario_captacion','escenario_elasticidad']).any())
knownkm=costs.nuevo_km_base.notna()
check('Accesonuevoreemplazadounavez',np.allclose(costs.loc[knownkm,'nuevo_km_actualizado']-costs.loc[knownkm,'nuevo_km_base'],costs.loc[knownkm,'delta_km_acceso']))
check('Tiempoaccesovaría conlongitud',np.allclose(costs.delta_tiempo_vial_h,costs.delta_km_acceso/costs.segmento.map(C['velocidad_acceso_kmh']),equal_nan=True))
check('Menortiempoylongitud noempeoraCGnuevo',costs.pivot(index='id_base',columns='alternativa_proyecto',values='CG_nuevo_CP').apply(lambda x:True if x.isna().any() else x.A3<=x.A2+1e-8 and x.A2<=x.A1+1e-8,axis=1).all())
complete=costs[['nuevo_costo_monetario','nuevo_costo_temporal','CG_nuevo_CP']].notna().all(axis=1)
check('CGnuevo reproduce componentes disponibles',np.allclose(costs.loc[complete,'CG_nuevo_CP'],costs.loc[complete,'nuevo_costo_monetario']+costs.loc[complete,'nuevo_costo_temporal'],rtol=1e-8,atol=.02))
check('FuenteSBO11y8sinotrosaumentos',set([C['SBO']['frecuencia_alta'],C['SBO']['frecuencia_baja']])=={11,8})
check('Fuentesprevias intactas',all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[k] for k,p in paths.items()))
checks=pd.DataFrame(checks)
params=pd.DataFrame([{'parametro':k,'valor':json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v} for k,v in C.items()])
notes=pd.DataFrame([
 ['Fuenteanticipación','NavieraAustralFAQ recuperada previamente enconfig_atributos.json:2hvehículos/1hpeatón. Referencia histórica no reconsultada; transferencia alnuevo como supuesto. Incluye embarque; no añadir15min.'],
 ['ActualizaciónSBO','107min,11/8sem/sentido yreemplazo denave según instrucciónoficial. Se dejaatrás14/12/120min deentregas anteriores. Es idéntica enlostresproyectos. No beneficio atribuido aoptimización porproyecto.'],
 ['Accesos','P20a/d/b31,14/24,62/22,60km sustituyen soloX735. I1RBM1ripio50km/h equivalenteenlostres, salvo actualizaciónjustificada posterior. SurR2656,7+X76310km ytroncalnorte permanecen; no sumardenuevo16,7km. EmpalmePI1021 esproxyheredada: no se recertificó topología deproyectonuevo.'],
 ['Tarifas/COV','Estructuratarifaria previa sin cambio. COVprivadosARISTO/HDM4dic2025 convertidos convencionalmente aene2026, sin nuevoCOPER. DatosimputadosCITRA yperfilesVP/CAM mantienenlimitaciones. Bususa tarifa/km, no COVautomóvil.'],
 ['Captación','Mismasnudos ycurvas porsegmentoEtapa5. Se evalúa origenrealdecohorte versusnuevo yse conserva restoenorigen. Costosdecolaexternano sonabsolutos: se mantienencotas captación yse excluyen deinducción.'],
 ['Inducción','Misma Etapa6finalincremental: Db*((minCP/CGusadoSBO)^eps-(minSBO/CGusadoSBO)^eps), solo disminuye mínimoSBO. Distribución p nuevo y1-p origen. No logsum nirecalibración.'],
 ['Escenarios','Trescaptaciones conelasticidadcentral y doselasticidades±0,1concaptacióncentral. Cinco casosporproyecto, sincartesianototal innecesario; crecimiento siemprecentral.'],
 ['Peatones','Busescoordinadoshipotéticos y3proxiesRíoIbáñez conservados. Accesocambia kilómetros,tiempoytarifa. No nuevosservicios externos. No sonpasajerostotales. Operaciónbus requiere costosposteriores.'],
 ['Exposición','Promedios diarios/porzarpe equivalentes del soporte y temporada, no mediciones ni horaspunta. Año2026normalizado365días; frecuencia porunsentido. CITRA factor1,20no completa demanda geográficafaltante.'],
 ['Totalyriesgo','Los totales sonaportes estimados. Residuales ycostos no comparables permanecen identificados. No sumarA/B, alternativas excluyentes ounidades distintas. Desagregacionescomunales sonproxies, no localidadesobservadas.'],
 ['Siguienteetapa','Capacidad,flotayprogramación, inversiones ycostosdeoperación/mantenimiento,evaluaciónsocial. No se calculan enestaentrega.'],
 ['Reproducir','python actualizacion_oficial_alternativas_20261029/codigo/calcular.py; --config archivo.json --salida (opcional; entrega oficial se actualiza enresultados). No ejecutaetapasprevias ni EOD/red.']
],columns=['tema','detalle'])
trace=pd.DataFrame([{'fuente':k,'archivo':str(p),'sha256':hashes[k]} for k,p in paths.items()])
central=summary[(summary.version_referencia==C['version_informe'])&summary.escenario_captacion.eq('central')&summary.escenario_elasticidad.eq('central')&summary.segmento.isin(['VL','CAM','VP','PEATON'])]
costs_export=costs.rename(columns={'CG_SBO':'CG_fuente_historica_SBO','CG_actual':'CG_fuente_historica_actual','CG_nuevo':'CG_fuente_historica_nuevo','CG_tierra':'CG_terrestre_base_invariable','T_horario_actual_anterior':'horario_fuente_historica_actual'})
sheets={'Resumen oficial':summary,'Temporadas y equivalentes':byperiod,'Demanda detallada':d[cols],'Costos por alternativa':costs_export,'Alternativas y parametros':params,'Cobertura y residuales':coverage,'Supuestos y limites':notes,'Curvas heredadas':pd.DataFrame([{'familia':f,'escenario':sc,'ahorros':str(cc['nudos_ahorro_relativo']),'probabilidades':str(pp)} for f,dd in cc['curvas'].items() for sc,pp in dd.items()]),'Elasticidades heredadas':pd.DataFrame(ec['elasticidades']).T.reset_index(names='segmento'),'Extranjeros heredados':foreign,'Validaciones':checks,'Trazabilidad':trace}
extra,metadata=construir_tablas_equipo(R,C,b,d,costs,summary,byperiod,coverage)
sheets={**extra,**sheets}
with pd.ExcelWriter(O/'demanda_oficial_tres_alternativas.xlsx',engine='openpyxl') as w:
 for name,df in sheets.items():
  df.to_excel(w,sheet_name=name,index=False);ws=w.book[name];ws.freeze_panes='D2';ws.auto_filter.ref=ws.dimensions
  for col in ws.columns:
   ws.column_dimensions[col[0].column_letter].width=min(45,max(14,len(str(col[0].value or ''))+2))
   for cell in col[1:]:
    if isinstance(cell.value,float):cell.number_format='0.0%' if any(t in str(df.columns[cell.column-1]).lower() for t in ['participacion','porcentaje','fraccion']) else '#,##0.0000'
fmt=lambda df:df.to_html(index=False,border=0,na_rep='Sin estimación',float_format=lambda v:f'{v:,.3f}')
show=central[['alternativa_proyecto','anio','segmento','unidad','D_tierra_SBO','D_actual_SBO','D_tierra_CP_total','D_actual_CP_total','D_existente_nuevo','D_inducida_nuevo','D_nuevo_CP_total','D_residual_existente']]
page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Demanda oficial de alternativas</title><style>body{{font:16px system-ui;max-width:1400px;margin:32px auto;padding:0 20px;color:#17374a}}p{{line-height:1.5}}table{{border-collapse:collapse;display:block;overflow:auto;font-size:12px}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#eaf2f7}}</style><h1>Demanda oficial de las tres alternativas</h1>
<p>Actualización de parámetros sobre las mismas matrices y proyecciones centrales, curvas de transferencia e inducción incremental de las Etapas1–6. Las alternativas se evalúan por separado; no compiten entre sí ni se suman. Referencia ARISTO{C['version_informe']}; A queda como contraste independiente.</p>
<h2>Configuraciones oficiales (frecuencia común11/8)</h2>{fmt(pd.DataFrame(C['alternativas']))}<p>Distancia lacustre7,3millas náuticas=13,5196km. Nuevo servicio11zarpes semanales por sentido enalta y8enbaja en las tres alternativas. Rampa/linkspan no alteran por sí mismos ningún tiempo. El acceso de ripio se representa con el tipoHDM4I1RBM1 y50km/h; solo cambia la longitud de cada trazado.</p>
<h2>SBO común</h2><p>PuertoIbáñez–ChileChico utiliza CapitánWellmann en reemplazo deLaTehuelche,107min y11salidas semanales por sentido en diciembre–abril,8en mayo–noviembre. La sustitución pertenece aSBO; se conservan exactamente sus atributos conproyecto. La terrestre tampoco cambia. Presentación documentada anteriormente:2hvehículos y1hpeatones, incluida operación previa alzarpe, sin añadir otros15min. Desembarque30min para todos por decisión basada en el antecedente verbal entregado. Estas referencias no son mediciones individuales.</p>
<h2>Demanda central2026–2050</h2>{fmt(show)}<p>Las cantidades son aportes del mercado cubierto e imputaciones identificadas. VP mantiene unidad heterogénea; no se suma comoVLestricto. Peatones no representan todos los pasajeros transportados. Los residuales de cada fuente permanecen separados; las cifras no completan el mercado terrestre desconocido.</p>
<h2>Costos y metodología</h2><p>Se conserva cada CG terrestre y el COV/fare previo. La actualización del ferryactual cambia navegación, presentación, desembarque y0,25×168/f. En el nuevo cruce se reemplaza una sola vez X73531,14km por31,14/24,62/22,60km, sumando la diferencia de tiempo a50km/h y COV por km del mismo tipoHDM4. El troncal y los16,7km del acceso sur permanecen, sin duplicación. En buses, esa diferencia modifica tarifa por kilómetro, no COVdeautomóvil.</p>
<p>La captación utiliza las mismas curvas por ahorro relativo respecto de cada procedencia. La inducción es solo el incremento adicional del mínimo de costo frenteSBO, con las mismas elasticidades. Se distribuye usando las nuevas participaciones de transferencia del mismo caso. Las tres curvas se ejecutan con elasticidadcentral; la sensibilidad±0,1se ejecuta sobre captacióncentral, sin mezclar todas las combinaciones.</p>
<h2>Cobertura y residuales</h2>{fmt(coverage[coverage.version_referencia.eq('B')])}<h2>Limitaciones y equivalentes</h2><p>El empalme norte enPuertoIbáñez1021es la referencia heredada: las longitudes oficiales se sustituyen bajo esa continuidad topológica. No se reconstruyó la red para certificar empalmes nuevos. Los costos imputados y núcleos deODexternos mantienen sus restricciones. La inducción excluye los costos de núcleo sin costo exterior absoluto. Buses nuevos son hipótesis operacionales aún no costeadas.</p>
<p>El Excel incluye equivalentes diarios y por zarpe por temporada/sentido. Son promedios normalizados, no demanda punta ni operación efectiva, y no determinan todavía la capacidad necesaria. CITRA mantiene sus OD parciales, factor1,20 y cobertura temporal ya acordada. La penalización por frecuencia no es espera física medida. Los precios siguen siendo CLPenero2026convencionales de las etapas previas, no costos sociales puros.</p>
<h2>Validaciones y reproducción</h2>{fmt(checks)}<p><a href="demanda_oficial_tres_alternativas.xlsx">Descargar Excel</a>. DesdeAnexos:<code>python actualizacion_oficial_alternativas_20261029/codigo/calcular.py</code>. Parámetros editables en<code>codigo/configuracion.json</code>. READMEprincipal documenta el flujo y resultados. Entregas anteriores verificadas intactas por huellas. Siguiente etapa:capacidad operacional, inversión,O&amp;Myevaluaciónsocial.</p></html>'''
page=informe_equipo(C,extra,summary,coverage,checks,metadata)
(O/'informe_alternativas_oficiales.html').write_text(page,encoding='utf-8')
print(json.dumps({'validaciones':len(checks),'filas':len(d),'central2026':central[central.anio.eq(2026)][['alternativa_proyecto','segmento','D_existente_nuevo','D_inducida_nuevo','D_nuevo_CP_total']].to_dict('records')},ensure_ascii=False))
