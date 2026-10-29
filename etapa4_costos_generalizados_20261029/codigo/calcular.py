"""Etapa 4: solo atributos y costos; no lee EOD ni calcula demanda/rutas.
Ejecutar: python etapa4_costos_generalizados_20261029/codigo/calcular.py
Dependencias existentes: pandas, numpy, openpyxl.
"""
from pathlib import Path
import json, calendar, unicodedata, hashlib, html
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent.parent
ROOT=HERE.parent
REPO=ROOT/'demanda_lago_github'
C=json.loads((HERE/'codigo/config.json').read_text())
OUT=HERE/'resultados'; OUT.mkdir(exist_ok=True)
S2=ROOT/'etapa2_demanda_anual_20261029/resultados/entrega_final/csv'
FILES=[S2/'aristo_anual_detalle.csv',S2/'citra_anual_localidades.csv',REPO/'outputs/atributos_logit_actualizados/atributos_logit_actualizados.csv',REPO/'outputs/etapa12/atributos_bahia_jara_levican.csv',HERE/'recuperacion/longitudes_CAM_agregadas.csv']
def norm(x):
 return ''.join(c for c in unicodedata.normalize('NFD',str(x).upper()) if unicodedata.category(c)!='Mn').strip()
def core(x):
 # Rio Ibanez es comuna: deliberadamente NO se convierte en Puerto Ibanez.
 return {'CHILE CHICO':'Chile Chico','COYHAIQUE':'Coyhaique','PUERTO IBANEZ':'Puerto Ibáñez'}.get(norm(x))
a=pd.read_csv(FILES[0]); b=pd.read_csv(FILES[1])
keys=['origen','destino','zona_origen','zona_destino','segmento']
a=a[keys].drop_duplicates().assign(fuente_demanda='ARISTO',detalle_geografico='Detalle original administrativo; anclaje piloto solo como aproximación explícita')
b=b[keys].drop_duplicates().assign(fuente_demanda='CITRA',detalle_geografico='Localidad homologada conservada; no sustituida por cabecera comunal')
od=pd.concat([a,b],ignore_index=True); od.insert(0,'id_od',range(1,len(od)+1))
# Leer únicamente atributos físicos previamente auditados: no importar betas, perfiles imputados o CG previos.
oldcols=['origen','destino','segmento','estacion','alternativa','distancia_terrestre_km','tiempo_conduccion_h','COV_privado_CLP_dic2025','tiempo_navegacion_h','ruta_id']
old=pd.read_csv(FILES[2],usecols=oldcols)
new=pd.read_csv(FILES[3],usecols=['origen','destino','segmento','estacion','distancia_terrestre_km','tiempo_conduccion_h','COV','secuencia_arcos'])
lengths=pd.read_csv(FILES[4])
# Caché geográfico ajeno al modelo de elección: medias de distancias referenciales, no kilómetros medidos.
geo_path=Path('/home/nataly/Escritorio/demanda_evalso/eod_filtrada/tablas/distancias_individuales.csv')
geocol=['origen','destino','km_tierra_referencia','km_accesos_barcaza_actual','km_accesos_nuevo_cruce','km_lacustres_nuevo_recta','separacion_origen_red_m','separacion_destino_red_m']
geo=pd.read_csv(geo_path,usecols=geocol) if geo_path.exists() else pd.DataFrame(columns=geocol)
geo['o']=geo.origen.map(norm);geo['d']=geo.destino.map(norm)
group=geo.groupby(['o','d'])[geocol[2:]].agg(['mean','min','max'])
rows=[]
for r in od.to_dict('records'):
 o,d=core(r['origen']),core(r['destino']); seg=r['segmento']
 for season,months in C['meses_temporada'].items():
  for alt in ['terrestre_chile','barcaza_actual','bahia_jara_levican']:
   z={**r,'temporada':season,'alternativa':alt,'unidad_costo':'CLP/persona-viaje' if seg=='PEATON' else 'CLP/'+('vehículo-viaje' if seg in ['VL','CAM','VP','PRIVADOS_COMPATIBLES','MOTO'] else 'unidad original-viaje'),
      'distancia_vial_km':np.nan,'tiempo_vial_h':np.nan,'distancia_navegacion_km':0 if alt=='terrestre_chile' else (37.277 if alt=='barcaza_actual' else np.nan),
      'distancia_recta_nueva_referencial_km':np.nan,'tiempo_navegacion_h':0 if alt=='terrestre_chile' else C['nav_actual_h'] if alt=='barcaza_actual' else C['nav_nueva_h'],
      'tiempo_embarque_h':0 if alt=='terrestre_chile' else C['embarque_h'],'tiempo_desembarque_h':0 if alt=='terrestre_chile' else C['desembarque_h'],
      'COV_privado_CLP':np.nan,'tarifa_lacustre_CLP':0 if alt=='terrestre_chile' else np.nan,'tarifa_bus_CLP':0 if seg!='PEATON' else np.nan,
      'fuente_fisica':'Sin recorrido completo respaldado','estado_localizacion':'Sin acceso asignable','advertencias':'','longitud_CAM_m':np.nan,
      'personas_por_unidad':C['ocupacion_vl'] if seg=='VL' else 1 if seg in ['CAM','PEATON','MOTO','BICI'] else np.nan,
      'base_precios':C['base_precios'],'fuente_tarifa':'ARISTO Tabla 52 p.121; nominal recuperada en configuración anterior; actualización no certificada',
      'supuesto_ocupacion':'Referencia 1,98 sin perfil OD compatible' if seg=='VL' else 'Un conductor provisional' if seg=='CAM' else 'Una persona; sin multiplicar grupos no identificados' if seg in ['PEATON','MOTO','BICI'] else 'Clase agregada: ocupación no asignada'}
   weights=np.array([calendar.monthrange(2026,m)[1] for m in months])
   fs=np.array([C['frecuencia_nueva'] if alt=='bahia_jara_levican' else C['frecuencia_actual_alta'] if m in C['meses_alta'] else C['frecuencia_actual_baja'] for m in months])
   z['frecuencia_semanal_min']=0 if alt=='terrestre_chile' else fs.min()
   z['frecuencia_semanal_max']=0 if alt=='terrestre_chile' else fs.max()
   z['H_indice_teorico_h']=0 if alt=='terrestre_chile' else np.average(168/fs,weights=weights)
   z['tiempo_horario_h']=C['w_horario']*z['H_indice_teorico_h']
   z['definicion_horario']='No aplica' if alt=='terrestre_chile' else 'Índice heredado 168/f; NO intervalo programado ni espera física; no presume operación uniforme 24h'
   # Tarifas por unidad; conductor liberado y acompañantes adultos son supuestos explícitos.
   if alt!='terrestre_chile':
    if seg=='VL': z['tarifa_lacustre_CLP']=C['tarifa_vl']+max(C['ocupacion_vl']-1,0)*C['tarifa_adulto'];z['advertencias']+='Conductor liberado y 0,98 acompañantes adultos de referencia; '
    elif seg=='PEATON':z['tarifa_lacustre_CLP']=C['tarifa_adulto']
    elif seg=='MOTO':z['tarifa_lacustre_CLP']=C['tarifa_moto'];z['advertencias']+='Inclusión de conductor en tarifa moto pendiente; '
    elif seg=='BICI':z['tarifa_lacustre_CLP']=C['tarifa_bici'];z['advertencias']+='Inclusión de ciclista en tarifa bici pendiente; '
    elif seg=='CAM':
     direction='Chile Chico a Ibanez' if norm(r['origen'])=='CHILE CHICO' else 'Ibanez a Chile Chico' if norm(r['destino'])=='CHILE CHICO' else None
     l=lengths[(lengths.nivel=='estacion_sentido_cruce')&(lengths.estacion==season)&(lengths.sentido_cruce==direction)]
     if r['fuente_demanda']=='ARISTO' and len(l)==1 and l.iloc[0].n_longitud_hasta5_5m==0 and l.iloc[0].n_longitud_numerica_positiva>=2:
      z['longitud_CAM_m']=l.iloc[0].longitud_media_m
      z['tarifa_lacustre_CLP']=C['tarifa_cam_m']*z['longitud_CAM_m']
      z['advertencias']+='Tarifa lineal provisional por longitud media de campaña/sentido, no OD; mismo vehículo de referencia en ambos cruces; facturación no verificada; '
     else:z['advertencias']+='Falta longitud/categoría tarifaria compatible; sin imponer 16m ni transferir flota ARISTO a CITRA; '
   # Misma localización en todas las alternativas: anclajes del piloto, nunca cabeceras de otras localidades.
   physseg=seg if seg in ['VL','CAM'] else None
   if o and d and physseg:
    tab=new if alt=='bahia_jara_levican' else old
    q=tab[(tab.origen==o)&(tab.destino==d)&(tab.segmento==physseg)&(tab.estacion==season)]
    if alt!='bahia_jara_levican':q=q[q.alternativa==alt]
    if len(q):
     v=q.iloc[0];z['distancia_vial_km']=v.distancia_terrestre_km;z['tiempo_vial_h']=v.tiempo_conduccion_h
     z['COV_privado_CLP']=(v.COV if alt=='bahia_jara_levican' else v.COV_privado_CLP_dic2025)/C['ipc_enero2026_a_dic2025']
     z['fuente_fisica']='Etapa12 tramos_proyecto/atributos físicos' if alt=='bahia_jara_levican' else 'atributos_logit_actualizados: SOLO distancia, conducción y COV; red ARISTO'
     z['estado_localizacion']='Anclaje vial de localidad' if r['fuente_demanda']=='CITRA' else 'Aproximación por anclajes del piloto; dato comunal no equivale a punto exacto'
     if seg=='CAM':z['advertencias']+='COV categoría pesada VP (mezcla CA/CS) como proxy CAM; '
   # Distancias referenciales adicionales sin inventar velocidades ni COV uniformes.
   k=(norm(r['origen']),norm(r['destino']))
   if r['fuente_demanda']=='CITRA' and k in group.index:
    g=group.loc[k];field={'terrestre_chile':'km_tierra_referencia','barcaza_actual':'km_accesos_barcaza_actual','bahia_jara_levican':'km_accesos_nuevo_cruce'}[alt]
    if pd.isna(z['distancia_vial_km']):
     z['distancia_vial_km']=g[(field,'mean')];z['fuente_fisica']='distancias_individuales.csv: media de referencias de red preexistentes para esta localidad OD'
     z['estado_localizacion']='Localidades del caché; extremos aproximados, no localización exacta individual'
     z['advertencias']+='Distancia referencial; faltan velocidades/COV del itinerario; no se estima desde tasa promedio por km del piloto; '
    z['distancia_recta_nueva_referencial_km']=g[('km_lacustres_nuevo_recta','mean')]
   # Bus: no asignar COV de automóvil. Solo piloto documentado con supuestos monetarios sin confirmar.
   if seg=='PEATON' and {o,d}=={'Chile Chico','Coyhaique'}:
    z['COV_privado_CLP']=0
    if alt=='terrestre_chile':
     z['tiempo_vial_h']=C['bus_terrestre_core_h'];z['tarifa_bus_CLP']=C['bus_terrestre_core_tarifa'];z['distancia_vial_km']=382.515
    elif alt=='barcaza_actual':
     z['tiempo_vial_h']=C['bus_acceso_actual_core_h'];z['tarifa_bus_CLP']=C['bus_acceso_actual_core_tarifa'];z['distancia_vial_km']=121.956
    z['estado_localizacion']='Anclajes piloto; servicio bus aproximado, sin contrato completo verificado'
    z['fuente_fisica']='ARISTO Tabla61: terrestre bus8h; acceso bus2,5h residual del servicio6h anterior, supuesto revisado'
    z['advertencias']+='Bus9000/10000 nominales son supuestos previos sin tarifa vigente confirmada; acceso2,5h aproximado por diferencia, NO medido; '
   if alt=='bahia_jara_levican':z['advertencias']+='Tarifas iguales al actual como supuesto; nave adicional independiente; distancia navegación real faltante (0 caché descartado); X73531,14+X76310+R2656,7, sin sumar nuevamente16,7; empalme norte PI aproximado; '
   z['tiempo_total_h']=sum(z[k] for k in ['tiempo_vial_h','tiempo_navegacion_h','tiempo_embarque_h','tiempo_desembarque_h','tiempo_horario_h'])
   z['costo_monetario_CLP']=z['COV_privado_CLP']+z['tarifa_lacustre_CLP']+z['tarifa_bus_CLP']
   z['costo_temporal_CLP']=C['vst_clp_persona_h']*z['personas_por_unidad']*z['tiempo_total_h']
   z['CG_CLP']=z['costo_monetario_CLP']+z['costo_temporal_CLP']
   z['estado']='Calculable con supuestos explícitos' if pd.notna(z['CG_CLP']) else 'Parcial: costo total faltante'
   z['nivel_confianza']='Media-baja: anclaje y parámetros de trabajo; no costo observado' if pd.notna(z['CG_CLP']) and seg=='VL' else 'Baja: supuestos de clase/servicio' if pd.notna(z['CG_CLP']) else 'Insuficiente para CG total'
   z['faltantes']='; '.join(k for k in ['distancia_vial_km','tiempo_vial_h','distancia_navegacion_km','COV_privado_CLP','tarifa_lacustre_CLP','tarifa_bus_CLP','personas_por_unidad'] if pd.isna(z[k]))
   z['costo_recursos_sociales_CLP']=np.nan
   rows.append(z)
x=pd.DataFrame(rows)
# Integrar nuevos atributos SOLO si un caché de tramos preexistentes se pudo enlazar directamente.
# El script no depende de resultados de tareas simultáneas: todas las entradas están enumeradas arriba.
attrs=x[['id_od','fuente_demanda','origen','destino','zona_origen','zona_destino','segmento','temporada','alternativa','distancia_vial_km','tiempo_vial_h','distancia_navegacion_km','distancia_recta_nueva_referencial_km','tiempo_navegacion_h','tiempo_embarque_h','tiempo_desembarque_h','H_indice_teorico_h','tiempo_horario_h','tiempo_total_h','frecuencia_semanal_min','frecuencia_semanal_max','fuente_fisica','estado_localizacion']]
comp=x[['id_od','fuente_demanda','origen','destino','segmento','temporada','alternativa','CG_CLP']].copy()
piv=comp.pivot(index=['id_od','temporada'],columns='alternativa',values='CG_CLP')
for left,right in [('barcaza_actual','terrestre_chile'),('bahia_jara_levican','terrestre_chile'),('bahia_jara_levican','barcaza_actual')]:
 piv['delta_'+left+'_menos_'+right]=piv[left]-piv[right]
comp=comp.merge(piv.filter(like='delta_').reset_index(),on=['id_od','temporada'],how='left')
situations=pd.concat([comp.assign(situacion='SBO',disponible=comp.alternativa!='bahia_jara_levican'),comp.assign(situacion='Con proyecto',disponible=True)],ignore_index=True)
situations.loc[~situations.disponible,'CG_CLP']=np.nan
new_deltas=[c for c in situations.columns if c.startswith('delta_') and 'bahia_jara' in c]
situations.loc[situations.situacion=='SBO',new_deltas]=np.nan
situations.loc[~situations.disponible,[c for c in situations.columns if c.startswith('delta_')]]=np.nan
example=x[(x.origen.map(norm)=='CHILE CHICO')&(x.destino.map(norm)=='COYHAIQUE')&(x.temporada.isin(['Verano','Invierno']))]
checks=[]
def check(name,result):
 checks.append({'validacion':name,'cumple':bool(result)});assert result,name
check('Un registro único por OD fuente, segmento, temporada y alternativa',not x.duplicated(['id_od','temporada','alternativa']).any())
check('Todos los OD preservados',x.id_od.nunique()==len(od))
check('Todos los OD tienen tres alternativas y cuatro temporadas',x.groupby('id_od').size().eq(12).all())
nums=['distancia_vial_km','tiempo_vial_h','tiempo_navegacion_h','tiempo_embarque_h','tiempo_desembarque_h','tiempo_horario_h','COV_privado_CLP','tarifa_lacustre_CLP','tarifa_bus_CLP']
check('Atributos no negativos',x[nums].ge(0).where(x[nums].notna(),True).all().all())
t=x[x.alternativa=='terrestre_chile'];check('Terrestre sin navegación, tarifa ni penalización lacustre',t[['tiempo_navegacion_h','tiempo_embarque_h','tiempo_desembarque_h','tiempo_horario_h','tarifa_lacustre_CLP']].eq(0).all().all())
check('VST único y fórmula temporal exacta',np.allclose(x.costo_temporal_CLP,C['vst_clp_persona_h']*x.personas_por_unidad*x.tiempo_total_h,equal_nan=True))
check('SBO solo 14/12; nuevo14',x[x.alternativa!='terrestre_chile'].frecuencia_semanal_min.isin([12,14]).all())
check('Nuevo no disponible en SBO',not situations[(situations.situacion=='SBO')&(situations.alternativa=='bahia_jara_levican')].disponible.any())
for alt in ['terrestre_chile','barcaza_actual']:
 ss=situations[situations.alternativa==alt].pivot(index=['id_od','temporada'],columns='situacion',values='CG_CLP');check('CG idéntico entre situaciones: '+alt,np.allclose(ss.SBO,ss['Con proyecto'],equal_nan=True))
check('Suma monetaria consistente',np.allclose(x.costo_monetario_CLP,x.COV_privado_CLP+x.tarifa_lacustre_CLP+x.tarifa_bus_CLP,equal_nan=True))
check('Suma CG consistente',np.allclose(x.CG_CLP,x.costo_monetario_CLP+x.costo_temporal_CLP,equal_nan=True))
check('Peatones sin COV de automóvil',x[x.segmento=='PEATON'].COV_privado_CLP.fillna(0).eq(0).all())
check('Zonas externas y residuales permanecen',set(od.id_od)==set(x.id_od))
params=pd.DataFrame([{'parametro':k,'valor':json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v,'fuente':'Decisión usuario Etapa4 / configuración previa documentada'} for k,v in C.items()])
notes=[
 ('Naturaleza CG','Costo monetario privado + VST social común como aproximación conductual. No costo social puro ni beneficio social.'),
 ('Precios','COV diciembre2025 convertido a enero2026 dividiendo por109,26/109,71. Se mantienen tarifas nominales previas y VST10047. Mes real tarifario/VST no certificado: homogeneización convencional explícita, no actualización oficial.'),
 ('Navegación actual','Central anterior120min: ARISTO Tabla38p112. Contraste160min: CITRA Informe2p417; usuario150–160min. Diferencia40min añade 6698 CLP/persona-viaje (13262,04 VL1,98), sin ejecutar sensibilidad.'),
 ('Presentación','Se sustituye antiguo previo2h vehículo/1h peatón y desembarque0,5h por0,25h embarque+0,25h desembarque por instrucción. No es tiempo de presentación operacional verificado.'),
 ('Horario','w168/f es índice de desfase horario heredado, NO espera ni headway programado; incorpora noches. Falta calendario real para validar penalización; ningún factor adicional al VST. Otoño pondera meses marzo/abril14,mayo12 por días2026.'),
 ('Accesos proyecto','X73531,14km ripio50km/h; R2656,7+X76310=16,7km sur. X763pavimentada cacheVL60/CAM50, CITRA2p406; no aplicar50 de ripio a pavimento. Distancia lacustre real desconocida; recta11,34km es referencia distinta, no navegación.'),
 ('CAM','COV pesado es proxy VP CA/CS, no costo individual. Tarifa lineal solo en estratos ARISTO con >=2 longitudes válidas y ninguna<=5,5m; supuesto por temporada/sentido. No transferir media flota a CITRA.'),
 ('VP','VP y PRIVADOS_COMPATIBLES no se convierten en VL. Costo total permanece faltante sin composición compatible.'),
 ('Peatones','Bus8hTabla61; tarifas9000/10000 son supuestos heredados, no tarifas confirmadas. Acceso2,5h inferido del servicio previo6h: aproximación explícita. Bus nuevo sin operación/tarifa suficiente: CG faltante.'),
 ('Localización','ARISTO conserva escala administrativa. Costos piloto son referencia por anclajes de cabeceras SOLO donde origen nominal coincide, no ubicación exacta de viajes comunales. Río Ibáñez no se transforma en Puerto Ibáñez.'),
 ('SBO y proyecto','Segunda nave actual permanece SBO14/12; nueva nave adicional independiente supuesto. Servicio actual y terrestre idénticos entre situaciones. Histórica11/8 y opción3diarios solo antecedentes no ejecutados.'),
 ('Limitación de cachés CITRA','Rutas almacenadas contienen IDs repetidos por subdivisión y nodos fraccionados, sin longitudes por subarco. Sumar arcos completos duplicaría recorridos; no se reconstruye la red. Se conservan distancias y faltantes de tiempo/COV. Evidencia: recuperacion/enlace_rutas_CITRA_no_directo.json.'),
 ('Alcance','No demanda, probabilidades, logit, captación, crecimiento, capacidad ni beneficios. Sin sumar fuentes ni unidades. Faltantes no son ceros; extranjeros y OD residuales permanecen.'),
 ('Referencias OD','94 referencias fuente–OD–segmento incluyen vistas físicas y PRIVADOS_COMPATIBLES; no son94pares únicos ni se suman como demanda. Costos repetidos entre ARISTO/CITRA se conservan para trazabilidad.'),
 ('Reproducción','python etapa4_costos_generalizados_20261029/codigo/calcular.py; pandas,numpy,openpyxl. Recuperación opcional en recuperacion/recuperar_atributos.py si existe. No se leen EOD.'),
 ('Fuentes','demanda_lago_github/docs/04_atributos_alternativas.md; outputs/atributos_alternativas; outputs/atributos_logit_actualizados; outputs/etapa12/tramos_proyecto.csv; config_etapa12.json; resumen_etapa12.md; ARISTO tablas38,52,61; CITRA2pp406,417 y CITRA3p78. Informe2 EVALSO caps4–6 y cuadro6.1 según parámetros proporcionados por usuario.')]
notes=pd.DataFrame(notes,columns=['tema','detalle'])
checks=pd.DataFrame(checks)
coverage=x.groupby(['fuente_demanda','segmento','alternativa']).agg(celdas=('id_od','size'),OD=('id_od','nunique'),con_distancia=('distancia_vial_km','count'),con_tiempo=('tiempo_vial_h','count'),con_CG=('CG_CLP','count')).reset_index()
hashes=pd.DataFrame([{'archivo':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in FILES+[geo_path] if p.exists()])
with pd.ExcelWriter(OUT/'costos_generalizados_etapa4.xlsx',engine='openpyxl') as writer:
 params.to_excel(writer,sheet_name='Parametros y fuentes',index=False)
 notes.to_excel(writer,sheet_name='Parametros y fuentes',startrow=len(params)+3,index=False)
 hashes.to_excel(writer,sheet_name='Parametros y fuentes',startrow=len(params)+len(notes)+6,index=False)
 attrs.to_excel(writer,sheet_name='Atributos alternativas',index=False)
 x.to_excel(writer,sheet_name='Costos desagregados OD',index=False)
 situations.to_excel(writer,sheet_name='SBO vs proyecto',index=False)
 x[x.faltantes.ne('')].to_excel(writer,sheet_name='Faltantes y advertencias',index=False)
 example.to_excel(writer,sheet_name='Chile Chico Coyhaique',index=False)
 coverage.to_excel(writer,sheet_name='Cobertura y validaciones',index=False)
 checks.to_excel(writer,sheet_name='Cobertura y validaciones',startrow=len(coverage)+3,index=False)
 for ws in writer.book:
  ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions
  for col in ws.columns:
   letter=col[0].column_letter;ws.column_dimensions[letter].width=min(55,max(14,len(str(col[0].value or ''))+2))
   for cell in col[1:]:
    if isinstance(cell.value,float):cell.number_format='#,##0.00'
fmt=lambda d:d.to_html(index=False,border=0,na_rep='Faltante',float_format=lambda v:f'{v:,.2f}')
ex=example[example.fuente_demanda=='CITRA'][['segmento','temporada','alternativa','distancia_vial_km','tiempo_vial_h','tiempo_navegacion_h','tiempo_horario_h','costo_monetario_CLP','costo_temporal_CLP','CG_CLP']]
if len(ex)==0:ex=example[['segmento','temporada','alternativa','distancia_vial_km','tiempo_vial_h','tiempo_navegacion_h','tiempo_horario_h','CG_CLP']]
page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Etapa4 Costos generalizados</title><style>body{{font:16px system-ui;max-width:1250px;margin:35px auto;padding:0 20px;color:#172c3b}}table{{border-collapse:collapse;font-size:12px;display:block;overflow:auto;margin:15px 0}}th,td{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#e8f0f5}}p{{line-height:1.5}}code{{background:#eef;padding:3px}}</style><h1>Etapa 4 · Costos generalizados</h1>
<p>Se conservan {len(od)} referencias OD–segmento–fuente, incluidas zonas externas y residuales; {x.id_od.nunique()} permanecen en las tres alternativas. De {len(x)} celdas OD–temporada–alternativa, {x.CG_CLP.notna().sum()} tienen costo total calculable con supuestos explícitos. Los demás conservan atributos parciales y costos faltantes. Esta cobertura no representa una proporción de la demanda.</p>
<p><b>CG = COV privado + tarifas + 10.047 × personas por unidad × (tiempo vial + navegación + embarque + desembarque + desfase horario).</b> Un mismo VST individual para todos. VL1,98; CAM1conductor provisional; peatón1. No se modifica ninguna cantidad de la demanda ni se estima elección.</p>
<h2>Comparación Chile Chico–Coyhaique</h2><p>Referencia vial382,52km y6,05h VL frente a379km y5–6h de antecedentes. El proyecto conserva16,7km sur y31,14km norte, más el troncal hastaCoyhaique; no suma nuevamente los accesos. Es una comparación de anclajes de referencia, no una localización individual de cada viaje comunal.</p>{fmt(ex)}
<h2>Cobertura</h2>{fmt(coverage)}
<h2>Decisiones y limitaciones</h2>{fmt(notes[notes.tema!='Reproducción'])}
<h2>Validaciones y reproducción</h2><p>Todos los controles focalizados aprobaron. Las alternativas existentes tienen exactamente el mismo costo SBO/con proyecto. El nuevo cruce figura no disponible en SBO. No se usan probabilidades ni atributos monetarios imputados del logit.</p>{fmt(checks)}
<p>Ejecutar desde Anexos: <code>python etapa4_costos_generalizados_20261029/codigo/calcular.py</code>. Configuración única editable: <code>codigo/config.json</code>. Libro: <a href="costos_generalizados_etapa4.xlsx">costos_generalizados_etapa4.xlsx</a>. Las huellas de fuentes reutilizadas quedan en el libro. Ningún original ni entrega histórica se modifica.</p></html>'''
(OUT/'informe_etapa4.html').write_text(page,encoding='utf-8')
print(json.dumps({'OD_segmento_fuente':len(od),'celdas':len(x),'CG_calculados':int(x.CG_CLP.notna().sum()),'distancias':int(x.distancia_vial_km.notna().sum()),'validaciones':len(checks),'salida':str(OUT)},ensure_ascii=False))
