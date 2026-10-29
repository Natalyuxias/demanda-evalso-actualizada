"""Etapa6 directa, sin ejecutar Etapas1–5 ni proyecciones/rutas.
DesdeAnexos: python etapa6_demanda_inducida_20261029/codigo/calcular.py
Dependencias: pandas,numpy,openpyxl. Configuración editable; --salida carpeta_nueva.
"""
from pathlib import Path
import argparse,json,hashlib
import pandas as pd
import numpy as np
P=Path(__file__).resolve().parent.parent;R=P.parent
ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=P/'codigo/configuracion.json');ap.add_argument('--salida',type=Path,default=P/'resultados');args=ap.parse_args();cfg=json.loads(args.config.read_text());O=args.salida;O.mkdir(parents=True,exist_ok=True)
paths={'etapa5':R/'etapa5_ampliacion_peatones_20261029/resultados/ampliacion_peatones_sensibilidad.xlsx','etapa5_principal':R/'etapa5_transferencia_principal_20261029/resultados/captacion_transferencia_principal.xlsx','extranjeros':R/'etapa2_demanda_anual_20261029/resultados/entrega_final/csv/extranjeros_aportes_anuales.csv'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def total(s):return s.sum(min_count=1)
hashes={k:sha(p) for k,p in paths.items()}
with pd.ExcelFile(paths['etapa5']) as w:
 v=pd.read_excel(w,'Detalle vehicular');p=pd.read_excel(w,'Demanda peatonal OD');c=pd.read_excel(w,'Costos y conexiones buses')
select=lambda d:d[d.caso_operacional.eq(cfg['operacion'])&d.escenario_transferencia.eq('central')&d.anio.isin(cfg['anios'])].copy()
v=select(v);p=select(p);c=c[c.caso_operacional.eq(cfg['operacion'])&c.escenario_transferencia.eq('central')].copy()
# Conservar exactamente demanda y captación anteriores, sin recalcular factores de crecimiento.
basecols=['version_referencia','version','id_flujo','fuente','origen','destino','zona_origen','zona_destino','sentido_cruce','temporada','segmento','unidad','componente','subtipo','anio','Q_referencia','factor_crecimiento_existente','Q_heredada_expandida','Q_imputacion_temporal_adicional','Q_OD_imputado_ARISTO']
vv=v[basecols].copy();vv['D_desviada_nuevo_existente']=v.captacion_total.to_numpy();vv['p_nuevo_guardada']=v.p_captacion.to_numpy();vv['CG_SBO']=v.CG_origen_usado.to_numpy();vv['CG_tierra']=v.CG_tierra_modelo.to_numpy();vv['CG_actual']=v.CG_actual_modelo.to_numpy();vv['CG_nuevo']=v.CG_nuevo_usado.to_numpy();vv['en_mercado_modelado']=v.modelable.to_numpy();vv['costo_solo_nucleo']=v.es_cola_comun.fillna(False).to_numpy();vv['peso_conexion']=1.;vv['conexion']='OD_original';vv['costos_imputados']=v.costos_dep_imputacion.to_numpy()
pp=p[basecols].copy();pp['D_desviada_nuevo_existente']=p.captacion_peatonal.to_numpy();pp['p_nuevo_OD_guardada']=p.p.to_numpy()
# No asignar a un OD comunal un único CG promedio: preservar subcohortes virtuales previas.
ck=['id_flujo','conexion','peso','CG_actual','CG_nuevo','p','conexion_modelable','estado','supuesto']
pp=pp.merge(c[ck],on='id_flujo',how='left',validate='many_to_many').rename(columns={'peso':'peso_conexion','p':'p_nuevo_guardada','conexion_modelable':'en_mercado_modelado','estado':'estado_conexion'})
pp['D_desviada_nuevo_existente']=pp.D_desviada_nuevo_existente*pp.peso_conexion
for col in ['Q_referencia','Q_heredada_expandida','Q_imputacion_temporal_adicional','Q_OD_imputado_ARISTO']:pp[col]=pp[col]*pp.peso_conexion
# Preferir participación porconexión guardada; no reejecutar la curva de captación.
pp['CG_SBO']=pp.CG_actual;pp['CG_tierra']=np.nan
# Solo circuitooriginal tiene costoterrestre bus completo reutilizable.
land=p[['id_flujo','CG_tierra_modelo']].drop_duplicates()
assert not land.id_flujo.duplicated().any()
pp=pp.merge(land,on='id_flujo',how='left',validate='many_to_one');pp['CG_tierra']=pp.CG_tierra_modelo
pp['costo_solo_nucleo']=False;pp['costos_imputados']=True
base=pd.concat([vv,pp],ignore_index=True)
base['id_base']=range(len(base))
base['CG_CP']=base[['CG_tierra','CG_actual','CG_nuevo']].min(axis=1,skipna=True)
base['CG_min_SBO']=base[['CG_tierra','CG_actual']].min(axis=1,skipna=True)
base['alternativa_menor_CG_CP']=base[['CG_tierra','CG_actual','CG_nuevo']].rename(columns={'CG_tierra':'tierra','CG_actual':'actual','CG_nuevo':'nuevo'}).apply(lambda x:x.idxmin() if x.notna().any() else 'Sin costos',axis=1)
base['alternativas_con_costo']=base[['CG_tierra','CG_actual','CG_nuevo']].notna().sum(axis=1)
base['costos_comparables']=base.en_mercado_modelado.fillna(False)&~base.costo_solo_nucleo&base.CG_SBO.gt(0)&base.CG_CP.gt(0)&base.segmento.isin(cfg['elasticidades'])
base['ahorro_ya_disponible_SBO_CLP']=(base.CG_SBO-base.CG_min_SBO).clip(lower=0)
base['ahorro_adicional_minimo_por_proyecto_CLP']=(base.CG_min_SBO-base.CG_CP).clip(lower=0)
base['reduccion_CG']=base.CG_CP.lt(base.CG_SBO-1e-9)
base['mejora_minimo_SBO_por_proyecto']=base.CG_CP.lt(base.CG_min_SBO-1e-9)
base['reduccion_ya_disponible_en_SBO']=base.reduccion_CG&~base.mejora_minimo_SBO_por_proyecto
base['participaciones_validas']=base.p_nuevo_guardada.between(0,1)
base['P_nuevo']=base.p_nuevo_guardada
base['P_tierra']=np.where(base.fuente.eq('CITRA'),1-base.P_nuevo,0.)
base['P_actual']=np.where(base.fuente.eq('ARISTO'),1-base.P_nuevo,0.)
base.loc[~base.participaciones_validas,['P_nuevo','P_tierra','P_actual']]=np.nan
base['D_desviada_tierra_existente']=base.D_desviada_nuevo_existente.where(base.fuente.eq('CITRA'),0.)
base['D_desviada_actual_existente']=base.D_desviada_nuevo_existente.where(base.fuente.eq('ARISTO'),0.)
base['D_tierra_CP_existente']=(base.Q_referencia-base.D_desviada_nuevo_existente).where(base.fuente.eq('CITRA'),0.).where(base.D_desviada_nuevo_existente.notna())
base['D_actual_CP_existente']=(base.Q_referencia-base.D_desviada_nuevo_existente).where(base.fuente.eq('ARISTO'),0.).where(base.D_desviada_nuevo_existente.notna())
base['D_existente_residual']=base.Q_referencia.where(base.D_desviada_nuevo_existente.isna(),0.)
base['D_base_sin_soporte_induccion']=base.Q_referencia.where(~base.costos_comparables,0.)
base['indicador_OD_externo_generico']=base.subtipo.eq('residual_externo')
base['nacionalidad_declarada_OD']='No disponible a este nivel; ver indicadores agregados heredados'
base['patente_extranjera_OD']='No disponible a este nivel; no inferir desde OD'
base['OD_internacional']='No se recodifica; se conservan OD y zonas originales, indicador agregado aparte'
# Tres sensibilidades sobre un mismo vector de demanda ya proyectada y los mismos costos.
outputs=[]
for scenario in ['menor_induccion','central','mayor_induccion']:
 z=base.copy();z['escenario_elasticidad']=scenario
 z['epsilon_CG']=z.segmento.map({s:d[scenario] for s,d in cfg['elasticidades'].items()})
 supported=z.costos_comparables&z.Q_referencia.notna();gain=supported&z.reduccion_CG
 z['D_inducida']=np.nan;z.loc[supported,'D_inducida']=0.
 z.loc[gain,'D_inducida']=z.loc[gain,'Q_referencia']*((z.loc[gain,'CG_CP']/z.loc[gain,'CG_SBO'])**z.loc[gain,'epsilon_CG']-1)
 # Descomposición diagnóstica exacta con la mismaepsilon/base, no otro escenario.
 z['D_inducida_potencial_ya_SBO']=np.nan
 z.loc[supported,'D_inducida_potencial_ya_SBO']=(z.loc[supported,'Q_referencia']*((z.loc[supported,'CG_min_SBO']/z.loc[supported,'CG_SBO'])**z.loc[supported,'epsilon_CG']-1)).clip(lower=0)
 z['D_inducida_incremento_minimo_proyecto']=(z.D_inducida-z.D_inducida_potencial_ya_SBO).clip(lower=0)
 z['D_inducida_incremental_nuevo']=z.D_inducida_incremento_minimo_proyecto*z.P_nuevo
 z['D_inducida_nuevo']=z.D_inducida*z.P_nuevo
 z['D_inducida_tierra']=z.D_inducida*z.P_tierra
 z['D_inducida_actual']=z.D_inducida*z.P_actual
 z['D_inducida_sin_asignar']=z.D_inducida.where(~z.participaciones_validas,0.).where(z.D_inducida.notna())
 # Si inducción0, asignación0 no requiere cuotas: no hay viajes adicionales que repartir.
 zero=z.D_inducida.eq(0);z.loc[zero,['D_inducida_nuevo','D_inducida_tierra','D_inducida_actual','D_inducida_sin_asignar']]=0.
 for alt,existing in [('nuevo','D_desviada_nuevo_existente'),('tierra','D_tierra_CP_existente'),('actual','D_actual_CP_existente')]:
  z['D_'+alt+'_total_aporte_estimado']=z[existing].fillna(0)+z['D_inducida_'+alt].fillna(0)
  z.loc[z[existing].isna()&z['D_inducida_'+alt].isna(),'D_'+alt+'_total_aporte_estimado']=np.nan
 z['D_inducida_con_mejora_min_SBO']=z.D_inducida.where(z.mejora_minimo_SBO_por_proyecto,0.).where(z.D_inducida.notna())
 z['D_inducida_sin_mejora_min_SBO']=z.D_inducida.where(~z.mejora_minimo_SBO_por_proyecto,0.).where(z.D_inducida.notna())
 z['D_nuevo_inducido_con_mejora_min_SBO']=z.D_inducida_nuevo.where(z.mejora_minimo_SBO_por_proyecto,0.).where(z.D_inducida_nuevo.notna())
 z['estado_induccion']=np.select([z.Q_referencia.isna(),~z.costos_comparables,~z.reduccion_CG,z.reduccion_ya_disponible_en_SBO],['Sin magnitud de demanda','Fuera soporte: costos absolutos/mercado insuficientes','Sin reducción: inducción0','Fórmula da inducción pero mínimoCP ya estaba disponible enSBO'],default='Inducción bajo aproximación solicitada; mejora mínimoSBO')
 z['alcance_total']='Aporte estimado dentro soporte; no total del mercado desconocido ni cuantificación completa de residuales'
 outputs.append(z)
d=pd.concat(outputs,ignore_index=True)
# TablaOD: agregar solo subcohortesvirtuales de la misma unidad/fuente/version, no A/B ni segmentos.
keys=['version_referencia','version','fuente','id_flujo','origen','destino','zona_origen','zona_destino','temporada','segmento','unidad','componente','subtipo','anio','escenario_elasticidad']
metrics=['D_inducida_potencial_ya_SBO','D_inducida_incremento_minimo_proyecto','D_inducida_incremental_nuevo','Q_referencia','D_desviada_nuevo_existente','D_desviada_tierra_existente','D_desviada_actual_existente','D_tierra_CP_existente','D_actual_CP_existente','D_existente_residual','D_base_sin_soporte_induccion','D_inducida','D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_inducida_sin_asignar','D_nuevo_total_aporte_estimado','D_tierra_total_aporte_estimado','D_actual_total_aporte_estimado','D_inducida_con_mejora_min_SBO','D_inducida_sin_mejora_min_SBO','D_nuevo_inducido_con_mejora_min_SBO']
od=d.groupby(keys,dropna=False)[metrics].agg(total).reset_index()
summary=od.groupby(['version_referencia','escenario_elasticidad','anio','segmento','unidad'],dropna=False)[metrics].agg(total).reset_index()
summary['proporcion_base_sin_soporte_induccion']=summary.D_base_sin_soporte_induccion/summary.Q_referencia.replace(0,np.nan)
summary['nota_total']='Totalnuevo=desviadaexistente+inducidaasignadaalnuevo, solo aportes estimables. No confundir con demanda física total desconocida.'
foreign=pd.read_csv(paths['extranjeros']);foreign=foreign[foreign.escenario.str.lower().eq('central')].copy();foreign['uso_en_Etapa6']='Indicadores2026 heredados, NO se asignan porOD ni a viajeros inducidos, no residencia'
notes=pd.DataFrame([{'parametro':k,'valor':json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v} for k,v in cfg.items()])
extras=[
 ('Descomposición diagnóstica','La fórmula principal se mantiene. Potencial yaSBO=Db*((CGminSBO/CGusado)^epsilon-1); incremento delmínimo porproyecto=inducidaformula-potencialyaSBO. Mismaepsilon y base, sin nuevoescenario. Es diagnóstico deaccesibilidad, no validacióncausal; evitaatribuir mejoras yaexistentes alproyecto.'),
 ('Interpretación causal','La fórmula usa CG de ruta utilizada y mínimoCP. Si el mínimoCP era ya posible enSBO, el resultado no identifica causalmente demanda creada por el nuevo proyecto. Se conserva la fórmula solicitada y se separa explícitamente esa parte para no usarla automáticamente como beneficio social.'),
 ('Demanda fija','Se toman cantidades ya proyectadas2026/2030/2040/2050 de últimaEtapa5, baseconbuses/curvacentral. Ningún crecimientoPIBni expansión adicional, ningún cambio de captación ni sensibilidadoperacional nueva.'),
 ('Participaciones','Las cuotasguardadas de transferencia asignan p alnuevo y1-p al modo deprocedencia. No se reasignan todos los inducidos alnuevo ni se modela una nueva elección. Los usuarios de lacustre no se convierten automáticamente en demanda terrestre.'),
 ('Costos disponibles','Vehículos: mínimo de los costosconocidosEtapa4–5 para las3alternativas; fuentes/limitaciones se conservan. Peatones: costo terrestre solo cuandoestaba completo; restantes conexiones comparan actual/nuevo, no se inventa un bus terrestre completo.'),
 ('Proxy comunal','RíoIbáñez mantiene los3representantes conpesosanteriores; cada Qse divide porpeso y se agregan resultados de inducción, no se usa f delCGmedio. No se crean3veces los viajeros.'),
 ('Residuos','Costos solo delnúcleo con colaexterna no valorada no admiten ratioCG: inducciónfaltante. También quedan fueraODsin conexión o sin magnitud. Un total que suma aportes conocidos no implica cero enlos faltantes.'),
 ('Extranjeros','No hay nacionalidad/patente porOD disponible en estasentregas. Se conservan indicadoresagregados porcampaña/sentido/segmento, con nacionalidad,patente yODinternacional separados. No se les atribuye residencia ni nacionalidad a viajes adicionales.'),
 ('Sensibilidades','ElasticidadesCG -0,254/-0,354/-0,454paraVL/VP/peatones; -0,006/-0,106/-0,206CAM. Son supuestos transferidos del proyecto. No elasticidadesPIB ni estimaciones estadísticas nuevas.'),
 ('Reproducir','DesdeAnexos:python etapa6_demanda_inducida_20261029/codigo/calcular.py. --config archivo.json --salida carpeta_nueva. No se leen EOD,PDF,redni se ejecutan scriptsanteriores.'),
 ('Alcance','No se calculan capacidad, flota, costosoperacionales ni beneficios sociales. Datos locales detallados no publicados aGitHub.')]
notes=pd.concat([notes,pd.DataFrame(extras,columns=['parametro','valor'])],ignore_index=True)
elastic=pd.DataFrame([{'segmento':s,**dd,'naturaleza':'ElasticidaddemandarespectoCG, supuestotransferido; distinta aelasticidadPIB'} for s,dd in cfg['elasticidades'].items()])
checks=[]
def check(name,ok):checks.append({'validacion':name,'cumple':bool(ok)});assert ok,name
check('Sin reducción implica inducción0',d.loc[d.costos_comparables&~d.reduccion_CG&d.Q_referencia.notna(),'D_inducida'].eq(0).all())
wide=d.pivot(index='id_base',columns='escenario_elasticidad',values='D_inducida')
check('Magnitudelasticidad ordena inducción',((wide.menor_induccion<=wide.central+1e-10)&(wide.central<=wide.mayor_induccion+1e-10)).where(wide.notna().all(axis=1),True).all())
check('Misma base ycostos en3elasticidades',d.groupby('id_base')[['Q_referencia','CG_SBO','CG_CP']].nunique(dropna=False).eq(1).all().all())
check('Demanda existente no recalculada',d.groupby('id_base').D_desviada_nuevo_existente.nunique(dropna=False).eq(1).all())
valid=d.D_desviada_nuevo_existente.notna()&d.Q_referencia.notna()
check('Conservación de existente',np.allclose(d.loc[valid,'D_tierra_CP_existente']+d.loc[valid,'D_actual_CP_existente']+d.loc[valid,'D_desviada_nuevo_existente'],d.loc[valid,'Q_referencia']))
assigned=d.D_inducida.notna()
check('Conservaciónasignacióndeinducida',np.allclose(d.loc[assigned,['D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_inducida_sin_asignar']].fillna(0).sum(axis=1),d.loc[assigned,'D_inducida']))
check('Descomposición con la mismaepsilon conserva fórmula principal',np.allclose(d.loc[assigned,'D_inducida'],d.loc[assigned,'D_inducida_potencial_ya_SBO']+d.loc[assigned,'D_inducida_incremento_minimo_proyecto']))
check('No todo inducido se asigna automáticamente alnuevo',np.allclose(d.loc[assigned&d.participaciones_validas,'D_inducida_nuevo'],d.loc[assigned&d.participaciones_validas,'D_inducida']*d.loc[assigned&d.participaciones_validas,'P_nuevo']))
check('Fuera soporte mantiene inducciónfaltante',d.loc[~d.costos_comparables,'D_inducida'].isna().all())
check('Solo4años ycaptacióncentral',set(d.anio)==set(cfg['anios']) and cfg['captacion']=='central_heredada')
# Verificar físicamente que dividir peatones porrepresentantes no pierde ni duplica la base.
for version in ['A','B']:
 a=base[base.version_referencia.eq(version)].groupby(['anio','segmento','unidad'],dropna=False).Q_referencia.sum(min_count=1)
 original=pd.concat([v,p]);b=original[original.version_referencia.eq(version)].groupby(['anio','segmento','unidad'],dropna=False).Q_referencia.sum(min_count=1)
 check('Mismos flujos existentes heredados '+version,np.allclose(a,b,equal_nan=True))
check('No se sumanvistasprivadasagregadas',not d.segmento.eq('PRIVADOS_COMPATIBLES').any())
check('Desviada e inducida distintas en totalnuevo',np.allclose(d.loc[assigned&valid,'D_nuevo_total_aporte_estimado'],d.loc[assigned&valid,'D_desviada_nuevo_existente']+d.loc[assigned&valid,'D_inducida_nuevo']))
check('Fuentesprevias intactas',all(sha(paths[k])==v for k,v in hashes.items()))
checks=pd.DataFrame(checks)
trace=pd.DataFrame([{'fuente':k,'archivo':str(paths[k]),'sha256':v} for k,v in hashes.items()])
sheets={'Elasticidades':elastic,'Supuestos y limites':notes,'Demanda por OD':od,'Calculo por conexion':d,'Comparacion elasticidades':summary,'Indicadores extranjeros':foreign,'Validaciones':checks,'Trazabilidad':trace}
with pd.ExcelWriter(O/'demanda_inducida_etapa6.xlsx',engine='openpyxl') as w:
 for name,df in sheets.items():
  df.to_excel(w,sheet_name=name,index=False);ws=w.book[name];ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions
  for col in ws.columns:
   ws.column_dimensions[col[0].column_letter].width=min(48,max(14,len(str(col[0].value or ''))+2))
   for cell in col[1:]:
    if isinstance(cell.value,float):cell.number_format='#,##0.0000'
fmt=lambda x:x.to_html(index=False,border=0,na_rep='Sin estimación',float_format=lambda v:f'{v:,.3f}')
main=summary[(summary.version_referencia==cfg['version_informe'])&(summary.escenario_elasticidad=='central')&summary.segmento.isin(cfg['elasticidades'])]
comparison=summary[(summary.version_referencia==cfg['version_informe'])&(summary.anio==2026)&summary.segmento.isin(cfg['elasticidades'])]
page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Etapa6 · Demanda inducida</title><style>body{{font:16px system-ui;max-width:1300px;margin:32px auto;padding:0 20px;color:#183449}}p{{line-height:1.5}}table{{border-collapse:collapse;display:block;overflow:auto;font-size:12px;margin:16px 0}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#e9f1f6}}</style><h1>Etapa 6 · Demanda inducida</h1>
<p>Se reutilizan los flujos ya proyectados y la captación central con buses de la última Etapa5. La demanda existente y desviada permanece intacta. No se ejecutan nuevamente proyecciones, encuestas, rutas, logit o sensibilidades operacionales. Referencia ARISTO{cfg['version_informe']}; A permanece como contraste independiente.</p>
<h2>Resultados centrales</h2>{fmt(main[['anio','segmento','unidad','D_desviada_nuevo_existente','D_inducida','D_inducida_nuevo','D_nuevo_total_aporte_estimado','D_inducida_con_mejora_min_SBO','D_inducida_sin_mejora_min_SBO']])}
<p><b>Importante para la atribución al proyecto:</b> la aproximación solicitada compara la alternativa utilizada enSBO con la más barata enCP. Una alternativa que ya existía puede ser más barata que la ruta utilizada. La fórmula entonces produce inducción aunque el nuevo cruce no haya reducido el mínimo de costo disponible. Esa parte se identifica y no debe transformarse automáticamente en un beneficio causal del proyecto. Además, incluso cuando el mínimo mejora, una parte del ahorro total puede estar ya disponible antes. La siguiente descomposición usa exactamente la misma base y elasticidad, sin agregar otro escenario.</p><h2>Diagnóstico de atribución — escenario central</h2>{fmt(main[['anio','segmento','D_inducida_potencial_ya_SBO','D_inducida_incremento_minimo_proyecto','D_inducida_incremental_nuevo']])}<p>Estas cantidades son diagnósticos del supuesto de accesibilidad, no estimaciones causales validadas. La fórmula principal y la captación existente se mantienen íntegramente.</p>
<h2>Elasticidades y fórmula</h2>{fmt(elastic)}<p>D_inducida = D_base × [(CG_CP/CG_SBO)^ε − 1], únicamente cuando0&lt;CG_CP&lt;CG_SBO. Sin reducción, el resultado es0; sin soporte suficiente, es faltante. Las elasticidades son supuestos de demanda respecto deCG, no elasticidadesPIB ni parámetros calibrados.</p>
<h2>Comparación de las tres elasticidades en2026</h2>{fmt(comparison[['escenario_elasticidad','segmento','D_inducida','D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_nuevo_total_aporte_estimado']])}
<h2>Asignación y conservación</h2><p>Se aplican las participaciones centrales guardadas: p al nuevo cruce y1−p a la alternativa de procedencia de cada bloque. No se supone que todos los viajes inducidos utilizan BahíaJara–Levicán. Sin participaciones válidas, los adicionales quedan sin asignar. La demanda desviada es una transferencia de viajes existentes; la inducida se calcula y registra por separado.</p>
<p>RíoIbáñez conserva las conexiones virtuales y pesos de la etapa anterior: se calcula por representante y se agrega, sin multiplicar personas. Peatones y vehículos mantienen unidades distintas. VP no se convierte en VL. Los costos comparativos del núcleo con cola externa no valorada quedan fuera de inducción, porque no respaldan un cociente de costos absolutos.</p>
<h2>Cobertura y usuarios extranjeros</h2>{fmt(main[['anio','segmento','Q_referencia','D_base_sin_soporte_induccion','proporcion_base_sin_soporte_induccion']])}
<p>Los totales son aportes estimados del mercado cubierto, no una cuantificación del mercado terrestre desconocido. Los OD residuales y externos permanecen identificados. Nacionalidad declarada, patente y OD internacional se conservan en la tabla agregada heredada; no hay correspondencia porOD suficiente para atribuir nacionalidad a viajes inducidos. No se confunde residencia con esos indicadores.</p>
<h2>Validaciones y reproducción</h2>{fmt(checks)}<p><a href="demanda_inducida_etapa6.xlsx">Descargar Excel</a>. DesdeAnexos:<code>python etapa6_demanda_inducida_20261029/codigo/calcular.py</code>. Parámetros en<code>configuracion.json</code>. Todas las etapas anteriores permanecen intactas. No se calculan todavía capacidad ni beneficios sociales.</p></html>'''
(O/'informe_demanda_inducida.html').write_text(page,encoding='utf-8')
print(json.dumps({'validaciones':len(checks),'central2026':main[main.anio.eq(2026)][['segmento','D_desviada_nuevo_existente','D_inducida','D_inducida_nuevo','D_nuevo_total_aporte_estimado','D_inducida_con_mejora_min_SBO','D_inducida_sin_mejora_min_SBO']].to_dict('records')},ensure_ascii=False))
