"""Metodología principal: transferencia por tramos y buses coordinados hipotéticos.
Reutiliza entregas finales y factores existentes; no ejecuta modelos anteriores.
DesdeAnexos: python etapa5_transferencia_principal_20261029/codigo/calcular.py
Dependencias: pandas,numpy,openpyxl. Parámetros: configuracion.json.
"""
from pathlib import Path
import json,hashlib,argparse
import numpy as np
import pandas as pd
from buses import build_bus_costs
P=Path(__file__).resolve().parent.parent;R=P.parent
ap=argparse.ArgumentParser();ap.add_argument('--costos-actualizados',type=Path,help='CSV/XLSX con id_flujo,CG_origen_usado,CG_nuevo_usado: costos absolutos documentados de una ejecución posterior');ap.add_argument('--config',type=Path,default=P/'codigo/configuracion.json');ap.add_argument('--salida',type=Path,default=P/'resultados');args=ap.parse_args();cfg=json.loads(args.config.read_text());O=args.salida;O.mkdir(parents=True,exist_ok=True)
paths={'logit':R/'etapa5_logit_preliminar_20261029/resultados/captacion_logit_preliminar.xlsx','costos4':R/'etapa4_costos_generalizados_20261029/resultados/costos_generalizados_etapa4.xlsx','regla_anterior':R/'etapa5_captacion_20261029/resultados/captacion_etapa5.xlsx','logit_codigo':R/'etapa5_logit_preliminar_20261029/codigo/calcular.py','logit_config':R/'etapa5_logit_preliminar_20261029/codigo/configuracion.json','tramos':R/'demanda_lago_github/outputs/etapa12/tramos_proyecto.csv'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if args.costos_actualizados:paths['costos_actualizados']=args.costos_actualizados
hashes={k:sha(p) for k,p in paths.items()}
def sumq(s):return s.sum(min_count=1)
with pd.ExcelFile(paths['logit']) as w:
 f=pd.read_excel(w,'Flujos armonizados');cs=pd.read_excel(w,'Costos utilizados e imputados');oldprob=pd.read_excel(w,'Probabilidades');oldsum=pd.read_excel(w,'Resumen mercado modelado')
 g=pd.read_excel(w,'Demanda SBO y proyecto',usecols=['id_flujo','version_referencia','escenario','anio','factor_crecimiento_existente','crecimiento'])
f=f[f.escenario.eq('central')].copy().reset_index(drop=True)
assert not f.id_flujo.duplicated().any()
assert f.loc[f.fuente.eq('CITRA'),'factor_horario'].eq(cfg['factor_CITRA_12_24']).all(),'Factor fijo1,20; no reconstruir ni variar cobertura en estaejecución'
assert cfg['vst']==10047
assert cfg['crecimiento']=='central'
g=g[g.escenario.eq('central')&g.anio.isin(cfg['anios'])];assert g.crecimiento.eq('central').all()
assert g.groupby(['id_flujo','anio']).factor_crecimiento_existente.nunique().eq(1).all()
g=g[['id_flujo','anio','factor_crecimiento_existente']].drop_duplicates()
# No se recalculan PIB, elasticidades, rutas o los costos completos previos.
attributes=pd.read_excel(paths['costos4'],'Costos desagregados OD')
bus=build_bus_costs(R,cfg,flows=f,attributes=attributes)
ledger=cs.pivot(index='id_flujo',columns='alternativa',values='tipo_costo')
f=f.merge(ledger.add_prefix('tipo_'),on='id_flujo',validate='one_to_one')
f['CG_origen_usado']=f.CG_actual_modelo.where(f.fuente.eq('ARISTO'),f.CG_tierra_modelo)
f['CG_nuevo_usado']=f.CG_nuevo_modelo
f['tipo_origen']=f['tipo_barcaza_actual'].where(f.fuente.eq('ARISTO'),f['tipo_terrestre_chile'])
f['tipo_nuevo']=f['tipo_bahia_jara_levican']
f['familia_transferencia']=f.segmento.map(cfg['familia'])
f['factor_factibilidad']=f.familia_transferencia.map(cfg['factibilidad'])
f['costos_dep_imputacion']=f.tipo_origen.ne('calculado_etapa4')|f.tipo_nuevo.ne('calculado_etapa4')
f['es_cola_comun']=f.tipo_origen.eq('nucleo_diferencial_cola_comun')|f.tipo_nuevo.eq('nucleo_diferencial_cola_comun')
# VP puede envolver una cola común: reconocer procedencia mediante la descripción, no solo etiqueta exterior.
meta=cs.assign(cola=cs.supuesto.fillna('').str.contains('cola común|cola comun|tramo norte común',case=False,regex=True)).groupby('id_flujo').cola.any()
f['es_cola_comun']=f.es_cola_comun|f.id_flujo.map(meta).fillna(False)
knots=np.asarray(cfg['nudos_ahorro_relativo'],float)
def capture(a,fam,scenario):return np.interp(a,knots,np.asarray(cfg['curvas'][fam][scenario],float))
curve=[]
for fam,dd in cfg['curvas'].items():
 for scen,pp in dd.items():
  for a,p in zip(knots,pp):curve.append({'familia':fam,'escenario':scen,'ahorro_relativo':a,'p_captacion':p,'naturaleza':'Supuesto propio editable, no elasticidad/calibración empírica'})
curve=pd.DataFrame(curve)
updates=None
if args.costos_actualizados:
 updates=pd.read_excel(args.costos_actualizados) if args.costos_actualizados.suffix.lower()=='.xlsx' else pd.read_csv(args.costos_actualizados)
 required=['id_flujo','CG_origen_usado','CG_nuevo_usado']
 if not set(required)<=set(updates):raise ValueError('Faltan columnas de costos actualizados: '+str(required))
 updates=updates[required]
 if updates.id_flujo.duplicated().any() or not set(updates.id_flujo)<=set(f.id_flujo):raise ValueError('id_flujo duplicado o ajeno a la entrega')
 if not (updates.CG_origen_usado.gt(0).all() and updates.CG_nuevo_usado.ge(0).all()):raise ValueError('Actualizar ambos costos absolutos, sinNaN ni negativos')
 updates=updates.rename(columns={'CG_origen_usado':'override_origen','CG_nuevo_usado':'override_nuevo'})
scenarios=[]
for scenario in cfg['escenarios']:
 q=f.copy();q['escenario_transferencia']=scenario
 b=bus[bus.escenario.eq(scenario)][['id_flujo','CG_nuevo_bus','modelable_bus']]
 q=q.merge(b,on='id_flujo',how='left',validate='one_to_one')
 foot=q.segmento.eq('PEATON');q.loc[foot,'CG_nuevo_usado']=q.loc[foot,'CG_nuevo_bus'];q.loc[foot,'tipo_nuevo']='bus_coordinado_hipotetico';q.loc[foot,'costos_dep_imputacion']=True
 if updates is not None:
  q=q.merge(updates,on='id_flujo',how='left',validate='one_to_one');changed=q.override_origen.notna()
  q.loc[changed,'CG_origen_usado']=q.loc[changed,'override_origen'];q.loc[changed,'CG_nuevo_usado']=q.loc[changed,'override_nuevo']
  q.loc[changed,'es_cola_comun']=False;q.loc[changed,'costos_dep_imputacion']=True
  q.loc[changed,['tipo_origen','tipo_nuevo']]='entrada_costos_absolutos_actualizada'
 q['delta_CG']=q.CG_origen_usado-q.CG_nuevo_usado
 q['ahorro_relativo']=(q.delta_CG/q.CG_origen_usado).where(q.CG_origen_usado.gt(0)&~q.es_cola_comun)
 q['A_cota_inferior_cola']=np.where(q.es_cola_comun,np.minimum(q.delta_CG/q.CG_origen_usado,0),np.nan)
 q['A_cota_superior_cola']=np.where(q.es_cola_comun,np.maximum(q.delta_CG/q.CG_origen_usado,0),np.nan)
 q['p_captacion']=np.nan;q['regla_aplicada']='Sin soporte de costos/factibilidad'
 q['modelable']=q.CG_origen_usado.gt(0)&q.CG_nuevo_usado.notna()&q.familia_transferencia.notna()&q.factor_factibilidad.gt(0)
 q.loc[foot,'modelable']=q.loc[foot,'modelable']&q.loc[foot,'modelable_bus'].eq(True)
 # Sin costo absoluto de cola común se trabaja con cotas, sin inventar A puntual.
 for fam in cfg['curvas']:
  mask=q.modelable&q.familia_transferencia.eq(fam)&~q.es_cola_comun
  q.loc[mask,'p_captacion']=capture(q.loc[mask,'ahorro_relativo'].to_numpy(),fam,scenario)*cfg['factibilidad'][fam]
  q.loc[mask,'regla_aplicada']='Interpolación lineal entre nudos; ahorro de la propia alternativa de procedencia'
  tail=q.modelable&q.familia_transferencia.eq(fam)&q.es_cola_comun
  lam=cfg['peso_cota_superior_cola_comun'][scenario]
  pl=capture(q.loc[tail,'A_cota_inferior_cola'].to_numpy(),fam,scenario);pu=capture(q.loc[tail,'A_cota_superior_cola'].to_numpy(),fam,scenario)
  q.loc[tail,'p_captacion']=((1-lam)*pl+lam*pu)*cfg['factibilidad'][fam]
  q.loc[tail,'regla_aplicada']='Cola común no valorada: cotas deA, conservador/central/alto ponderan0/0,5/1 deprobabilidad superior. Con delta<=0 central/conservadorp0 y altof(0) por atractivo no observado'
 q['captacion_por_atributos_no_observados']=q.p_captacion.gt(0)&q.delta_CG.le(0)
 q['estado_costos']='Completo previo o aproximación sin cola común';q.loc[q.es_cola_comun,'estado_costos']='Solo diferencial del núcleo; A absoluto no identificable; usar regla acotada explícita'
 scenarios.append(q)
base=pd.concat(scenarios,ignore_index=True)
z=base.merge(g,on='id_flujo',how='left',validate='many_to_many')
assert z.anio.notna().all()
z['Q_referencia']=z.Q_armonizada_2026*z.factor_crecimiento_existente
z['Q_heredada_expandida']=z.Q_heredada_armonizada*z.factor_crecimiento_existente
z['Q_imputacion_temporal_adicional']=z.Q_imputada_armonizada*z.factor_crecimiento_existente
z['Q_OD_imputado_ARISTO']=z.Q_heredada_expandida.where(z.fuente.eq('ARISTO')&z.componente.eq('imputado'),0.)
z['D_nuevo']=z.Q_referencia*z.p_captacion
z['D_permanece_origen']=z.Q_referencia-z.D_nuevo
z['D_tierra_SBO']=z.Q_referencia.where(z.fuente.eq('CITRA'),0.)
z['D_actual_SBO']=z.Q_referencia.where(z.fuente.eq('ARISTO'),0.)
z['D_nuevo_SBO']=0.
z['D_tierra_CP']=z.D_permanece_origen.where(z.fuente.eq('CITRA'),0.).where(z.modelable)
z['D_actual_CP']=z.D_permanece_origen.where(z.fuente.eq('ARISTO'),0.).where(z.modelable)
z['D_desviado_tierra']=z.D_nuevo.where(z.fuente.eq('CITRA'),0.).where(z.modelable)
z['D_desviado_actual']=z.D_nuevo.where(z.fuente.eq('ARISTO'),0.).where(z.modelable)
z['Q_residual_CP']=z.Q_referencia.where(~z.modelable,0.)
z['D_nuevo_costos_imputados']=z.D_nuevo.where(z.costos_dep_imputacion,0.).where(z.modelable)
z['Q_modelada']=z.Q_referencia.where(z.modelable,0.)
z['Q_modelada_costos_imputados']=z.Q_modelada.where(z.costos_dep_imputacion,0.)
z['sin_magnitud']=z.Q_referencia.isna()
z['estado_demanda']=np.select([z.sin_magnitud,~z.modelable,z.captacion_por_atributos_no_observados],['Sin magnitud estimable: no se crea demanda','Demanda conocida fuera soporte; conservar residual','Modelada: parte captación depende de atractivo no observado'],default='Modelada: transferencia por ahorro relativo')
# Duplicar cohortesCITRA SOLO como vistas alternativasA/B, nunca sumarlas.
res=pd.concat([z[z.version.eq(v)|z.fuente.eq('CITRA')].assign(version_referencia=v) for v in cfg['versiones_ARISTO']],ignore_index=True)
keys=['version_referencia','escenario_transferencia','anio','segmento','unidad']
cols=['Q_referencia','Q_heredada_expandida','Q_imputacion_temporal_adicional','Q_OD_imputado_ARISTO','Q_modelada','Q_modelada_costos_imputados','D_tierra_SBO','D_actual_SBO','D_tierra_CP','D_actual_CP','D_nuevo','D_desviado_tierra','D_desviado_actual','Q_residual_CP','D_nuevo_costos_imputados']
summary=res.groupby(keys,dropna=False)[cols].agg(sumq).reset_index()
summary['fraccion_fuera_soporte']=summary.Q_residual_CP/summary.Q_referencia.replace(0,np.nan)
summary['fraccion_modelada_costos_imputados']=summary.Q_modelada_costos_imputados/summary.Q_modelada.replace(0,np.nan)
summary['fraccion_captacion_costos_imputados']=summary.D_nuevo_costos_imputados/summary.D_nuevo.replace(0,np.nan)
# Repartosmodelados: mismo soporte enSBO/CP. Elresumen completo incluye residuales en columna separada.
model=res[res.modelable&res.Q_referencia.notna()].copy()
ms=model.groupby(keys,dropna=False)[cols].agg(sumq).reset_index()
for a in ['tierra','actual']:ms['P_'+a+'_CP']=ms['D_'+a+'_CP']/ms.Q_referencia.replace(0,np.nan)
ms['P_nuevo_CP']=ms.D_nuevo/ms.Q_referencia.replace(0,np.nan)
cover=res[res.anio.eq(2026)].groupby(['version_referencia','escenario_transferencia','fuente','segmento','unidad'],dropna=False).agg(Q_referencia=('Q_referencia',sumq),Q_modelada=('Q_modelada',sumq),Q_fuera_soporte=('Q_residual_CP',sumq),Q_costos_imputados=('Q_modelada_costos_imputados',sumq),Q_temporal_imputada=('Q_imputacion_temporal_adicional',sumq),celdas_sin_magnitud=('sin_magnitud','sum')).reset_index()
cover['fraccion_fuera_soporte']=cover.Q_fuera_soporte/cover.Q_referencia.replace(0,np.nan)
# Contraste publicado y contraste a igual base/soporte: no reejecutar logit ni sus parámetros.
oldprob=oldprob.rename(columns={'escenario':'escenario_transferencia','P_nuevo_CP':'P_nuevo_logit'})
qq=res.merge(oldprob[['version_referencia','escenario_transferencia','id_flujo','P_nuevo_logit']],on=['version_referencia','escenario_transferencia','id_flujo'],how='left',validate='many_to_one')
qq['en_soporte_comun']=qq.modelable&qq.P_nuevo_logit.notna()&qq.Q_referencia.notna()
qq['logit_reescalado_misma_base']=qq.Q_referencia*qq.P_nuevo_logit
common=qq[qq.en_soporte_comun].groupby(keys,dropna=False).agg(Q_soporte_comun=('Q_referencia',sumq),captacion_transferencia=('D_nuevo',sumq),captacion_logit_misma_base=('logit_reescalado_misma_base',sumq)).reset_index()
common['diferencia_metodos_misma_base']=common.captacion_transferencia-common.captacion_logit_misma_base
common['interpretacion']='Mismo soporte y flujos conCITRA1,20fijo; se reutilizan probabilidades guardadas, NO nueva calibración ni ejecuciónlogit'
published=oldsum.rename(columns={'escenario':'escenario_transferencia','D_nuevo_CP':'logit_publicado'})[['version_referencia','escenario_transferencia','anio','segmento','unidad','logit_publicado','Q_referencia']].rename(columns={'Q_referencia':'Q_modelada_logit_publicado'})
comp=summary.merge(published,on=keys,how='outer').merge(common,on=keys,how='left')
comp['nota']='Logit publicado usa factores1,10/1,20/1,40 segúnescenario y no buspeatonal; diferencia bruta mezcla método/base/cobertura. Comparaciónmismabase usa intersección y factor1,20.'
byorigin=qq[qq.en_soporte_comun].groupby(keys+['fuente'],dropna=False).agg(nuevo_transferencia=('D_nuevo',sumq),nuevo_logit_misma_base=('logit_reescalado_misma_base',sumq)).reset_index()
# Pruebas focalizadas deaplicación y conservación, no nuevaauditoría.
checks=[]
def check(name,ok):checks.append({'validacion':name,'cumple':bool(ok)});assert ok,name
check('Nudos estrictamente crecientes',np.all(np.diff(knots)>0))
for fam, dd in cfg['curvas'].items():
 for scen, yy in dd.items():check('Curva monótona y acotada '+fam+' '+scen,np.all(np.diff(yy)>=0)&np.all((np.array(yy)>=0)&(np.array(yy)<=1)))
 check('Escenarios ordenados '+fam,np.all(np.array(dd['conservador'])<=dd['central']) and np.all(np.array(dd['central'])<=dd['alto']))
check('Probabilidades válidas',res.p_captacion.dropna().between(0,1).all())
check('ConservaciónSBO toda magnitud conocida',np.allclose((res.D_tierra_SBO+res.D_actual_SBO).to_numpy(),res.Q_referencia.to_numpy(),equal_nan=True))
check('ConservaciónCP sobre soporte',np.allclose(model.D_tierra_CP+model.D_actual_CP+model.D_nuevo,model.Q_referencia))
check('Captación igual a desvíos por procedencia',np.allclose(model.D_desviado_tierra+model.D_desviado_actual,model.D_nuevo))
known=res.Q_referencia.notna()
check('BalanceglobalCPincluye residual sin perder magnitud',np.allclose(res.loc[known,['D_tierra_CP','D_actual_CP','D_nuevo']].fillna(0).sum(axis=1)+res.loc[known,'Q_residual_CP'],res.loc[known,'Q_referencia']))
check('Sin redistribuir alternativas existentes enSBO',res.loc[res.fuente.eq('ARISTO'),'D_tierra_SBO'].eq(0).all() and res.loc[res.fuente.eq('CITRA'),'D_actual_SBO'].eq(0).all())
check('Residual preserva magnitud fuera soporte',np.allclose(res.loc[~res.modelable,'Q_residual_CP'],res.loc[~res.modelable,'Q_referencia'],equal_nan=True))
check('Sin captación0 por ausencia de soporte',res.loc[~res.modelable,'D_nuevo'].isna().all())
check('Sin duplicar cohortes dentro de vista',not res.duplicated(['version_referencia','escenario_transferencia','anio','id_flujo']).any())
check('Sin vista privada agregada sumada a componentes',not res.segmento.eq('PRIVADOS_COMPATIBLES').any())
check('Nuevo indisponible enSBO',res.D_nuevo_SBO.eq(0).all())
check('Sin factorhorario sobreARISTO',f.loc[f.fuente.eq('ARISTO'),'factor_horario'].eq(1).all())
check('CITRA1,20igualtresescenarios',base.loc[base.fuente.eq('CITRA'),'factor_horario'].eq(1.2).all())
check('Sin doblecrecimiento2026',g[g.anio.eq(2026)].factor_crecimiento_existente.eq(1).all())
# Bajar elCGnuevo mejoraA; comprobarcurvas sin modificar la ejecución de costos.
mono=[]
for r in base[base.modelable].itertuples(index=False):
 aa=(r.CG_origen_usado-(r.CG_nuevo_usado-1000))/r.CG_origen_usado
 if r.es_cola_comun:
  lam=cfg['peso_cota_superior_cola_comun'][r.escenario_transferencia]
  pp=(1-lam)*capture(min(aa,0),r.familia_transferencia,r.escenario_transferencia)+lam*capture(max(aa,0),r.familia_transferencia,r.escenario_transferencia)
 else:pp=capture(aa,r.familia_transferencia,r.escenario_transferencia)
 mono.append(pp*r.factor_factibilidad>=r.p_captacion-1e-12)
check('ReducirCGnuevo mantiene/aumenta captación',all(mono))
validbus=bus[bus.modelable_bus]
check('Bus un solo horario y sin doble espera',validbus.espera_adicional_bus_h.eq(0).all() and validbus.tiempo_horario_barcaza_h.eq(3).all())
check('Bus tarifas una sola vez',np.allclose(validbus.costo_monetario_CLP,validbus.tarifa_buses_integrada_CLP+validbus.tarifa_lacustre_CLP))
check('Bus mismo costo tres escenarios',validbus.groupby('id_flujo').CG_nuevo_bus.nunique().eq(1).all())
check('Curvas no fuerzan captación sin ahorro central/conservador',base.loc[base.escenario_transferencia.isin(['central','conservador'])&base.modelable&base.delta_CG.le(0),'p_captacion'].eq(0).all())
order=res.pivot(index=['version_referencia','anio','id_flujo'],columns='escenario_transferencia',values='D_nuevo')
check('Captaciónconservadora<=central<=alta misma base',((order.conservador<=order.central)&(order.central<=order.alto)).where(order.notna().all(axis=1),True).all())
check('Fuentes y ambas metodologías previas intactas',all(sha(paths[k])==v for k,v in hashes.items()))
checks=pd.DataFrame(checks)
refs=pd.DataFrame([
 {'fuente':'ATAP Step4 §4.5/4.6','ubicacion':'https://www.atap.gov.au/tools-techniques/cost-benefit-analysis/5-step-4-make-demand-forecasts','uso':'Tráfico desviado por segmento; juicio explícito, elasticidad cruzada/costo generalizado; separar viajesnuevos. Respaldo general, NO nudosnuméricos de esta curva.'},
 {'fuente':'TII PAG Unit5.1 §2.7 y6.2, pp6 y21–23; diciembre2023','ubicacion':'https://www.tiipublications.ie/library/PE-PAG-02015-02.pdf','uso':'Distingue plausibilidad de validación, elasticidades directas/cruzadas y cambiosdecosto. No se toma elasticidad ni porcentajecaptación deTII.'},
 {'fuente':'SNI Transporte: vialidadinterurbana/marítimo-lacustre','ubicacion':'https://sni.gob.cl/formulacion-de-iniciativas/transporte/','uso':'Catálogo consultado: identifica metodología vialidad y Módulo beneficios mejora trasbordo. Documento individual no recuperado portimeout; NO atribuirle fórmulas/porcentajes ni calcularbeneficios enestaetapa.'},
 {'fuente':'Mejoramiento ConectividadLacustre LGC, tablas53–54 p58','ubicacion':'/home/nataly/Descargas/Mejorameinto de la Conectividad Lacustre en el Lago General Carrera.pdf; contraste recuperadoEtapa3','uso':'Escenarioshistóricos de crecimiento pasajeros sin auto; no sonobservaciones actuales ni parámetros decaptación. Referenciaestructuralescenarios, sin transferirtasas a nudos.'},
 {'fuente':'Compra de unaEmbarcación ServiciosZonasAisladas, §2.2/2.2.1 p7','ubicacion':'/home/nataly/Descargas/Compra de una Embarcación para Servicios de Transporte Marítimo en Zonas Aisladas.pdf','uso':'Consultaacotada índicep2 y p7escaneada: separa pasajeros,autos,buses/camiones,carga,maquinaria; modeloPIB/población propiootraregión. No se reproduce regresión ni se transfieren coeficientes deelección.'},
 {'fuente':'InformeFinalARISTO Cap6–8','ubicacion':'Informe ARISTO.pdf; entregasEtapas1–4; Tabla38p112/Tabla52p121/Tabla61','uso':'Fuentes deencuestas,flujos,red,costos yproyecciones ya procesadas; solo se reutilizan entregasvalidadas.'},
 {'fuente':'CITRA Informes2/3 y EOD','ubicacion':'Estudios de consultoras/Informe 2c - MOP aysen vf.pdf pp406,417; Informe3p78; resultadosEtapas1–4','uso':'Accesos, velocidades y navegación80min ya recuperados; cobertura terrestre parcial y franjas12h. No se transfiere porcentaje de otro mercado.'},
 {'fuente':'Informe2EVALSO caps4–6/cuadro6.1','ubicacion':'INFORME_2_EVALSO-1.pdf; evidencia_documental_acotada.json enEtapa4/recuperacion','uso':'HipótesisSBO,accesos ycostos ya resumidos. Distinguir costosprivados+VSTsocial de evaluaciónsocialpura.'}])
notes=pd.DataFrame([{'parametro':k,'valor':json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v} for k,v in cfg.items()])
extras=[
 ('Naturaleza de curva','Interpolación lineal entre nudos configurables; fuera delrango se mantiene valor extremo. Son probabilidades/fracciones deescenario, NOelasticidades calibradas, ajuste aencuestas ni porcentajesextraídos debibliografía.'),
 ('SBO yprocedencia','SBO conservaexactamente cada cohorte enalternativaoriginal. CPsolo desvía alnuevo y mantiene elresto enorigen. No se introduce elrepartoSBOdelMNL en elmodelo principal.'),
 ('Demanda','FactorCITRAcentral1,20 y temporadascompletadas deúltimaEtapa5, idénticos en3escenarios. No se reconstruye cobertura ni se añade ningúnOD. ARISTOA/Bindependientes;Bprincipal. Anualizados/imputados no se etiquetan como conteosobservados.'),
 ('Costos','Se importan sin cambiar costoscompletosEtapa4 yaproximacionesúltimaEtapa5. Se usa CGpropio deprocedencia, no siempre elmenor CG. Peatones reciben costo nuevo delescenariobus; costoactual sin cambio.'),
 ('Cola común','Un costo diferencial delnúcleo no permite calcular ahorrorelativo completo delODexterno. Se conservanCGcomparativos ydelta. Con ahorro no positivo, p0central/conservador es robusto a cualquier costo exterior común no negativo; enalto f(0) es cota optimista explícita, no Aestimado.'),
 ('Factibilidad','Factor1supone que están disponibles ambos cruces yaccesos del escenario, NO capacidad verificada. Para peatones soloChCh↔Coyhaique dispone del circuito hipotético completo; otros siguen residuales sininventar servicio directo.'),
 ('Tarifa integrada','Unbillete bus+barcaza=dos tarifasbus por km ×factorintegración +tarifalacustre una vez. Factor1default, sin descuento adicional. Tarifa8000deCruceCerroCastillo se conserva comocontraste, sininferirkmnoverificados.'),
 ('Peatones','Modelo depeatonesencuestados/aforados; no pasajeros totales. No todoslos51542anualesARISTO se modelan y solo una fracción deconectados se desvía. Buseshipotéticos no contratados, velocidadesVLproxybus.'),
 ('Residuales','Sinmagnitud y fuerasoporteno son ceros. ConservaciónCPdentro soporte; para total físico conservar residualCPaparte. VPmantieneunidadheterogénea, no convertir aVLni sumar convistaagregada.'),
 ('Precios','Se mantiene CLPenero2026convencional deEtapa4; referenciasbuses10000/8000sinfecha certificada no se presentan como actualizaciónoficial.'),
 ('Comparación MNL','Logitpublicado intacto: cambios deoperación/base frente3escenarios distintos. Comparación a igualbase usaPguardadas aplicadas a flujoscomunesCITRA1,20; no se recalibra ni ejecutaMNL. Para procedencia se comparan cohorteshistóricas, no sus redistribucionesSBO.'),
 ('Sensibilidadesfuturas','--costos-actualizados archivo.csv|xlsx permite importarid_flujo,CG_origen_usado,CG_nuevo_usado de una evaluaciónoperacional posterior: ambos costosabsolutos documentados, sin editarfuentes. Curvasconfig aíslan elección. Buscompuesto seactualiza medianteconfig y atributosEtapa4deentrada; si hayoverride depeatón, Costosutilizados eslaentradaautoritaria y Costosbusessigue mostrandoelescenario hipotéticobase.'),
 ('Reproducir','DesdeAnexos:python etapa5_transferencia_principal_20261029/codigo/calcular.py. Configalternativa:--config archivo.json --salida carpeta_nueva; costosabsolutosposteriores:--costos-actualizados archivo.csv --salida carpeta_nueva. No se publica aGitHub.')]
notes=pd.concat([notes,pd.DataFrame(extras,columns=['parametro','valor'])],ignore_index=True)
trace=pd.DataFrame([{'fuente':k,'archivo':str(paths[k]),'sha256':v} for k,v in hashes.items()])
costused=base[['id_flujo','version','fuente','origen','destino','zona_origen','zona_destino','segmento','temporada','escenario_transferencia','CG_origen_usado','CG_nuevo_usado','delta_CG','ahorro_relativo','A_cota_inferior_cola','A_cota_superior_cola','tipo_origen','tipo_nuevo','estado_costos','costos_dep_imputacion','factor_factibilidad','modelable','p_captacion','captacion_por_atributos_no_observados','regla_aplicada']]
sheets={'Parametros captacion':curve,'Supuestos y decisiones':notes,'Fuentes bibliograficas':refs,'Costos utilizados':costused,'Costos buses coordinados':bus,'Flujos de referencia':f,'Demanda por alternativa':res.drop(columns=[c for c in ['o','d'] if c in res]),'Resumen soporte modelado':ms,'Resumen general y residual':summary,'Peatones':res[res.segmento.eq('PEATON')].drop(columns=[c for c in ['o','d'] if c in res]),'Comparacion logit':comp,'Comparacion por procedencia':byorigin,'Cobertura':cover,'Validaciones':checks,'Trazabilidad':trace}
with pd.ExcelWriter(O/'captacion_transferencia_principal.xlsx',engine='openpyxl') as w:
 for name,df in sheets.items():
  df.to_excel(w,sheet_name=name,index=False);ws=w.book[name];ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions
  for col in ws.columns:
   ws.column_dimensions[col[0].column_letter].width=min(46,max(14,len(str(col[0].value or ''))+2))
   for c in col[1:]:
    if isinstance(c.value,float):c.number_format='#,##0.0000'
fmt=lambda d:d.to_html(index=False,border=0,na_rep='Sin estimación',float_format=lambda v:f'{v:,.3f}')
central=summary[summary.version_referencia.eq(cfg['version_informe'])&summary.escenario_transferencia.eq('central')&summary.segmento.isin(['VL','VP','CAM','PEATON'])]
sc=summary[(summary.version_referencia==cfg['version_informe'])&(summary.anio==2026)&summary.segmento.isin(['VL','VP','CAM','PEATON'])]
cb=comp[(comp.version_referencia=='B')&(comp.escenario_transferencia=='central')&(comp.anio==2026)&comp.segmento.isin(['VL','VP','CAM','PEATON'])]
bus_example=bus[bus.modelable_bus&bus.version.eq('B')&bus.escenario.eq('central')][['origen','destino','temporada','km_bus_sur','km_bus_norte','tiempo_bus_total_h','tarifa_buses_integrada_CLP','tarifa_lacustre_CLP','CG_origen_actual','CG_nuevo_bus']].drop_duplicates()
curvetable=curve.pivot(index=['familia','ahorro_relativo'],columns='escenario',values='p_captacion').reset_index()
page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Captación por escenarios</title><style>body{{font:16px system-ui;max-width:1300px;margin:32px auto;padding:0 20px;color:#19364a}}p{{line-height:1.5}}table{{border-collapse:collapse;display:block;overflow:auto;font-size:12px;margin:16px 0}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#eaf1f7}}</style><h1>Captación principal por escenarios</h1>
<p>La demanda existente se conserva. Se utiliza el crecimiento central heredado y la versión ARISTO {cfg['version_informe']} como referencia; A queda como contraste independiente. El factor CITRA es 1,20 en los tres escenarios. No se calcula demanda inducida, capacidad ni beneficios sociales.</p>
<h2>Resultados centrales</h2>{fmt(central[['anio','segmento','unidad','Q_referencia','Q_modelada','D_nuevo','D_desviado_tierra','D_desviado_actual','Q_residual_CP','fraccion_captacion_costos_imputados']])}
<p>Las cifras corresponden al mercado cubierto y a los supuestos temporales heredados. No representan toda la demanda terrestre. VP conserva su unidad heterogénea; no debe interpretarse como VL estricto. Las fracciones se expresan entre 0 y 1.</p>
<h2>Comparación de escenarios en 2026</h2>{fmt(sc[['escenario_transferencia','segmento','D_nuevo','D_desviado_tierra','D_desviado_actual']])}
<h2>Función de transferencia</h2><p>Para cada cohorte se calcula ΔCG = CG de procedencia − CG nuevo y A = ΔCG / CG de procedencia. La probabilidad se obtiene interpolando entre los nudos siguientes. Son supuestos propios editables, no elasticidades calibradas ni porcentajes publicados por las referencias.</p>{fmt(curvetable)}
<p>Las curvas de carga representan una respuesta menor por fricciones operacionales supuestas. La curva peatonal más favorable exige que exista el circuito completo de buses hipotéticos. Los escenarios conservador y central dan captación nula cuando el nuevo cruce es más caro. El alto permite una captación limitada por atributos no observados, expresamente supuesta. Los costos y la demanda son idénticos entre escenarios: solo cambia la función de transferencia.</p>
<h2>Buses coordinados hipotéticos</h2><p>El circuito Chile Chico–Coyhaique y su inverso incluyen un bus sur de 16,7 km, navegación de 80 minutos y un bus norte de 152,686 km. Se reutilizan los tiempos viales de VL de la Etapa 4 como aproximación del bus. Se añaden 15 minutos de embarque y 15 de desembarque, más una sola penalización horaria de 3 horas; la coordinación evita otra espera completa del bus.</p>
<p>La tarifa de referencia es 10.000 / 121,956 = 81,997 CLP/km. Los dos buses cuestan $13.889,11 y la tarifa lacustre $2.550: $16.439,11 por persona. Con VST de $10.047/persona-hora, el CG nuevo es $88.364,28. La tarifa integrada cobra esos componentes una sola vez; su factor editable es actualmente 1, sin descuento. Los $8.000 de Coyhaique–Cruce Cerro Castillo se conservan como contraste documental, sin inventar una distancia para calcular otra tasa.</p>{fmt(bus_example)}
<p>Estos buses no son servicios existentes ni comprometidos. Solo se modela el par Chile Chico–Coyhaique y el sentido contrario; no se supone un bus directo para todas las zonas externas. Los demás peatones mantienen su demanda residual. No se convierten todos los peatones anuales de ARISTO en pasajeros del nuevo servicio.</p>
<h2>Comparación con el logit anterior</h2>{fmt(cb[['segmento','D_nuevo','logit_publicado','Q_soporte_comun','captacion_transferencia','captacion_logit_misma_base','diferencia_metodos_misma_base']])}
<p>La comparación a igual base utiliza únicamente el soporte coincidente, los mismos flujos con CITRA 1,20 y las probabilidades del logit ya guardadas. No se ejecuta ni recalibra ese modelo. El logit publicado utilizaba factores horarios distintos según escenario y no incluía buses para peatones; su diferencia bruta también refleja cambios de cobertura. Ninguna metodología se presenta como estadísticamente validada.</p>
<p>El método principal conserva la procedencia: la SBO mantiene cada cohorte en su ruta de origen y el proyecto solo desvía una fracción al nuevo cruce. El resto permanece en la ruta original. No se incorpora la redistribución hipotética de la SBO del logit como si fuera un desvío provocado por el proyecto.</p>
<h2>Cobertura y dependencia de supuestos</h2>{fmt(cover[(cover.version_referencia=='B')&(cover.escenario_transferencia=='central')])}
<p>Los costos completos de la Etapa 4 permanecen intactos. Se reutilizan las aproximaciones de la última Etapa 5 y se cuantifica la demanda que depende de ellas. Toda la captación peatonal depende del servicio hipotético; la de camiones depende también de costos o tarifas aproximados. Las temporadas CITRA completadas anteriormente siguen identificadas como imputaciones.</p>
<p>En los OD largos con solo un costo del núcleo y una cola exterior común, ese costo no permite calcular un ahorro relativo absoluto. Se mantienen las cotas compatibles con cualquier costo exterior común no negativo: conservador usa la probabilidad inferior, central el punto medio y alto la superior. Cuando el ahorro es no positivo, central y conservador dan cero y el alto admite atractivo no observado. No se inventa la ubicación de una zona externa ni su costo absoluto.</p>
<p>Los OD sin soporte y los flujos sin OD se conservan como residuales, no como demanda cero. La magnitud de los corredores terrestres nunca observados continúa desconocida. No se suman las versiones A/B ni la vista agregada de privados con sus componentes.</p>
<h2>Fundamento y referencias</h2><p><a href="https://www.atap.gov.au/tools-techniques/cost-benefit-analysis/5-step-4-make-demand-forecasts">ATAP, §4.5–4.6</a>, distingue tráfico desviado y generado, y admite juicio explícito por segmento y métodos basados en costo generalizado. <a href="https://www.tiipublications.ie/library/PE-PAG-02015-02.pdf">TII, Unit 5.1, §2.7 y 6.2</a>, explica elasticidades directas/cruzadas y diferencia plausibilidad de validación. Respaldan el enfoque general, no los valores de estas curvas.</p>
<p>El <a href="https://sni.gob.cl/formulacion-de-iniciativas/transporte/">catálogo SNI de Transporte</a> identifica la metodología de vialidad interurbana y el módulo de beneficios de mejora de trasbordo. No se recuperó el documento individual, por lo que no se le atribuyen fórmulas ni coeficientes.</p>
<p>Las tablas 53–54, p.58, del estudio histórico del Lago General Carrera aportan escenarios de crecimiento, no de captación. <em>Compra de una Embarcación para Servicios de Transporte Marítimo en Zonas Aisladas</em>, §2.2, p.7, separa usuarios y desarrolla modelos propios de otra región; no se trasladan sus regresiones. ARISTO, CITRA y el Informe 2 EVALSO aportan los atributos y operaciones previamente procesados. Las referencias locales precisas están en el Excel.</p>
<h2>Validaciones y reproducción</h2>{fmt(checks)}<p><a href="captacion_transferencia_principal.xlsx">Descargar Excel</a>. Desde Anexos: <code>python etapa5_transferencia_principal_20261029/codigo/calcular.py</code>. Las curvas y la tarifa integrada se editan en <code>configuracion.json</code>. Para costos absolutos de una evaluación operacional posterior: <code>--costos-actualizados archivo.csv --salida carpeta_nueva</code>; columnas: <code>id_flujo, CG_origen_usado, CG_nuevo_usado</code>. Esto permite actualizar la captación sin reconstruir encuestas o redes. Las dos implementaciones anteriores permanecen intactas.</p></html>'''
(O/'informe_transferencia_principal.html').write_text(page,encoding='utf-8')
print(json.dumps({'validaciones':len(checks),'central2026':central[central.anio.eq(2026)][['segmento','D_nuevo','D_desviado_tierra','D_desviado_actual','Q_residual_CP']].to_dict('records'),'salida':str(O)},ensure_ascii=False))
