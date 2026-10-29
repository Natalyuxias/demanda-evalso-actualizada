"""Exploración independiente: usa campos originales conservados en la auditoría264.
python exploracion_tiempos_barcaza_20261029/explorar.py
No ejecuta ni modifica demanda/costos/captación. pandas,numpy.
"""
from pathlib import Path
import hashlib,json
import pandas as pd
import numpy as np
P=Path(__file__).resolve().parent;R=P.parent
source=R/'Cap 6/BBDD EOD/Base de datos agregada.xlsx'
audit=R/'etapa1_lacustre_aristo_20261029/resultados/entrega_final/csv/auditoria_264.csv'
attrs=R/'etapa4_costos_generalizados_20261029/resultados/costos_generalizados_etapa4.xlsx'
paths=[source,audit,attrs];hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
cols=['id_encuesta','origen','destino','segmento','campana','sentido_cruce','b1__Fecha inicio viaje','b1__Hora inicio viaje','b1__Fecha llegada','b1__Hora llegada','b1__Fecha Creación','b1__fila_BBDD1']
d=pd.read_csv(audit,usecols=cols);assert len(d)==264 and d.id_encuesta.is_unique
q=d[((d.origen=='Chile Chico')&(d.destino=='Coyhaique'))|((d.origen=='Coyhaique')&(d.destino=='Chile Chico'))].copy()
q['direccion']=q.origen+' → '+q.destino
for short,col in [('di','b1__Fecha inicio viaje'),('hi','b1__Hora inicio viaje'),('df','b1__Fecha llegada'),('hf','b1__Hora llegada'),('encuesta','b1__Fecha Creación')]:
 q[short]=pd.to_datetime(q[col],format='mixed',errors='coerce')
# EnVerano/Otoño Hora es HH:MM; no usar la fecha automática que asigna un parser.
for short,col in [('hi_reloj','b1__Hora inicio viaje'),('hf_reloj','b1__Hora llegada')]:
 reloj=q[col].astype(str).str.extract(r'(\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)$',expand=False)
 reloj=reloj.where(reloj.str.count(':').ne(1),reloj+':00')
 q[short]=pd.to_timedelta(reloj,errors='coerce')
q['inicio']=q.di.dt.normalize()+q.hi_reloj
q['llegada']=q.df.dt.normalize()+q.hf_reloj
q['total_min']=(q.llegada-q.inicio).dt.total_seconds()/60
q['cambio_fecha']=(q.llegada.dt.normalize()-q.inicio.dt.normalize()).dt.days
q['fechas_horas_completas']=q[['di','hi_reloj','df','hf_reloj']].notna().all(axis=1)
hora_con_fecha_i=q['b1__Hora inicio viaje'].astype(str).str.contains(r'\d{4}-\d{2}-\d{2}',regex=True)
hora_con_fecha_f=q['b1__Hora llegada'].astype(str).str.contains(r'\d{4}-\d{2}-\d{2}',regex=True)
q['fechas_redundantes_contradictorias']=(hora_con_fecha_i&(q.di.dt.normalize()!=q.hi.dt.normalize()))|(hora_con_fecha_f&(q.df.dt.normalize()!=q.hf.dt.normalize()))
# Solo tiempos terrestres ya existentes, sin rutas nuevas ni parámetros nuevos.
a=pd.read_excel(attrs,'Costos desagregados OD')
a=a[(a.alternativa=='barcaza_actual')&a.origen.isin(['Chile Chico','Coyhaique'])&a.destino.isin(['Chile Chico','Coyhaique'])]
road=a[a.segmento.isin(['VL','CAM','PEATON'])].groupby('segmento').tiempo_vial_h.first().to_dict()
# VP conserva clasificación propia; el perfilVL es la aproximación ya usadaEtapa5, no una recodificación.
road['VP']=road.get('VL',np.nan)
q['vial_min']=q.segmento.map(road)*60
q['residual_barcaza_min']=q.total_min-q.vial_min
q['adicional_120_min']=q.residual_barcaza_min-120
q['adicional_160_min']=q.residual_barcaza_min-160
q['primario']=q.fechas_horas_completas&q.total_min.gt(0)&q.cambio_fecha.eq(0)&~q.fechas_redundantes_contradictorias&q.vial_min.notna()
q['llegada_posterior_registro']=q.llegada.gt(q.encuesta)&q.encuesta.notna()
# Atípicos descriptivos: se marcan, pero no se eliminan por la reglaTukey.
s=q.loc[q.primario,'total_min'];lo=s.quantile(.25)-1.5*(s.quantile(.75)-s.quantile(.25));hi=s.quantile(.75)+1.5*(s.quantile(.75)-s.quantile(.25))
q['atipico_Tukey_total']=q.total_min.lt(lo)|q.total_min.gt(hi)
valid=q[q.primario]
rows=[]
groups=[('Total exploratorio','Todos',valid)]
for dr,g in valid.groupby('direccion'):
 if len(g)>=10:groups.append(('Sentido',dr,g))
for (dr,seg),g in valid.groupby(['direccion','segmento']):
 if len(g)>=10:groups.append(('Sentido/segmento',dr+' / '+seg,g))
for (dr,seg,camp),g in valid.groupby(['direccion','segmento','campana']):
 if seg=='VL' and len(g)>=10:groups.append(('VL por campaña',dr+' / '+camp,g))
for seg,g in valid.groupby('segmento'):
 if len(g)>=10:groups.append(('Segmento ambos sentidos',seg,g))
for scope,label,g in groups:
 row={'nivel':scope,'grupo':label,'n':len(g),'total_p50_min':g.total_min.median(),'vial_p50_min':g.vial_min.median(),'residual_p25_min':g.residual_barcaza_min.quantile(.25),'residual_p50_min':g.residual_barcaza_min.median(),'residual_p75_min':g.residual_barcaza_min.quantile(.75),'extra120_p25_min':g.adicional_120_min.quantile(.25),'extra120_p50_min':g.adicional_120_min.median(),'extra120_p75_min':g.adicional_120_min.quantile(.75),'extra160_p25_min':g.adicional_160_min.quantile(.25),'extra160_p50_min':g.adicional_160_min.median(),'extra160_p75_min':g.adicional_160_min.quantile(.75),'n_extra120_negativo':int(g.adicional_120_min.lt(0).sum()),'n_extra160_negativo':int(g.adicional_160_min.lt(0).sum())}
 rows.append(row)
stats=pd.DataFrame(rows)
quality=pd.DataFrame([
 ['Universo ferry válido (BBDD-2 enlazada porID2)',len(d)],['OD nominal ChileChico↔Coyhaique',len(q)],['Cuatro campos temporales completos',int(q.fechas_horas_completas.sum())],['Duraciónnegativa',int(q.total_min.lt(0).sum())],['Duración0',int(q.total_min.eq(0).sum())],['Fechas redundantes contradictorias',int(q.fechas_redundantes_contradictorias.sum())],['Cambio de día (no prueba por sí solo pernocta)',int(q.cambio_fecha.gt(0).sum())],['Duración>24horas',int(q.total_min.gt(1440).sum())],['Sin tiempo vial compatible disponible',int(q.vial_min.isna().sum())],['Muestra primaria mismo día/duraciónpositiva/tiempovial',len(valid)],['AtípicosTukey dentro de primaria (retenidos)',int(valid.atipico_Tukey_total.sum())],['Llegada posterior a registro entre primarios',int(valid.llegada_posterior_registro.sum())],['Relojllegada00:00 entre ODseleccionados',int(q.hf_reloj.eq(pd.Timedelta(0)).sum())]
],columns=['criterio','n'])
flags=q[~q.primario|q.atipico_Tukey_total][['direccion','segmento','campana','total_min','cambio_fecha','primario','atipico_Tukey_total']].copy()
# Informeagregado, sin identificadores, domicilios ni coordenadas. Casos se agrupan por criterio.
flags=flags.groupby(['direccion','campana','primario','atipico_Tukey_total'],dropna=False).agg(n=('total_min','size'),duracion_minima_min=('total_min','min'),duracion_maxima_min=('total_min','max'),cambio_fecha_max_dias=('cambio_fecha','max')).reset_index()
robust=[]
for label,g in [('Todos primarios',valid),('SoloVL',valid[valid.segmento=='VL']),('Primarios sin atípicosTukey (solo contraste)',valid[~valid.atipico_Tukey_total])]:
 if len(g):robust.append({'muestra':label,'n':len(g),'extra120_mediana_min':g.adicional_120_min.median(),'extra160_mediana_min':g.adicional_160_min.median()})
robust=pd.DataFrame(robust)
comparison=a.groupby(['segmento','temporada']).agg(vial_h=('tiempo_vial_h','first'),horario_h=('tiempo_horario_h','first'),embarque_h=('tiempo_embarque_h','first'),desembarque_h=('tiempo_desembarque_h','first')).reset_index()
comparison=comparison[comparison.segmento.isin(['VL','CAM','PEATON'])]
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p0,h in hashes.items() for p in [Path(p0)])
textfmt=lambda x:x.to_html(index=False,border=0,na_rep='No disponible',float_format=lambda v:f'{v:.1f}')
page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Exploración independiente de tiempos del ferry</title><style>body{{font:16px system-ui;max-width:1400px;margin:32px auto;padding:0 20px;color:#18384b}}p{{line-height:1.5}}table{{border-collapse:collapse;display:block;overflow:auto;font-size:12px}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#e9f2f7}}</style><h1>Tiempo residual del cruce Puerto Ibáñez–Chile Chico</h1>
<p>Exploración independiente, sin modificar demanda, costos o captación. Universo:264 entrevistas válidas del cruce, ya enlazadas BBDD-1/BBDD-2 porID2. Se utilizan las cuatro columnas originales de BBDD-1 conservadas enla auditoría264, con la cabecera comprobada en el Excel original. No se relee ni reconstruye el procesamiento de encuestas.</p>
<h2>Control breve de duraciones</h2>{textfmt(quality)}
<p>Los conteos de incidencias pueden superponerse. Se combina la fecha de cada campoFecha con el reloj del correspondiente campoHora. En Primavera los camposHora contienen un timestamp completo; en Verano/Otoño contienen solo HH:MM. Se extrae únicamente el reloj, sin interpretar la fecha automática del parser. No se corrigen negativos sumando24h ni se imputan horas. La muestra principal exige datos completos, duraciónpositiva, mismo día, fechas redundantes consistentes y tiempo vial disponible. Cambiar de día se separa por prudencia; no significa necesariamente una pernoctación. Duraciones largas y atípicos se muestran abajo, sin borrarlos de las fuentes. Las horas de llegada pueden ser previstas; estar después del registro refuerza esa cautela, sin demostrar cómo se formularon.</p>
<h2>Resultados en minutos</h2>{textfmt(stats)}
<p>Residualbarcaza=duracióntotaldeclarada−tiempovialrepresentativo; adicional120/160=residual−navegaciónsupuestade120/160min. Los percentiles se calculan directamente sobre entrevistas, sin expansión ni ponderar por ocupantes. Se desagrega solo con almenos10observaciones, umbral práctico descriptivo; n no equivale a zarpes independientes. La muestra total mezcla segmentos y no debe sustituir los resultados específicos.</p>
<h2>Contraste de atípicos</h2>{textfmt(robust)}<p>Tukey marca valores fuera de[Q1−1,5IQR,Q3+1,5IQR]deltiempototal entre primarios: límites{lo:.1f}y{hi:.1f}min. Se mantienen en la tabla principal. La tabla siguiente conserva sus magnitudes y los grupos excluidos por duración/fecha/tiempo vial; no identifica personas.</p>{textfmt(flags)}
<h2>Comparación con supuestos actuales</h2>{textfmt(comparison)}
<p>La conducciónVL corresponde a121,956km y aproximadamente87,5min en el acceso PuertoIbáñez–Coyhaique del piloto; el acceso del ladoChileChico es el del anclaje existente. CAM utiliza el perfilpesado de119,1min, ya aproximado. VP usa el perfilVL solo como contraste, sin convertir sus viajes enVLestricto. Peatones utilizan150min de acceso bus deEtapa4: ese valor fue inferido del servicio previo de6h, no medido independientemente; por ello su residual no valida de forma independiente la espera. Los OD nominales son administrativos y sus extremos pueden no coincidir exactamente con los anclajes viales.</p>
<p>Los15min de embarque más15min de desembarque representan30min físicos supuestos. La penalización0,25×168/f es un índice de inconveniencia por horario, no espera observada: para laSBO14/12equivale a180–210min (otoño ponderado entre ambos). Las encuestas no acreditan que se operara bajo laSBO14/12 que hoy usamos como supuesto; esa diferencia operacional también limita la comparación. No debe sumarse o equipararse directamente al residual. Este puede incorporar presentación, detenciones, errores de fecha/hora, accesos distintos y previsiones de llegada.</p>
<h2>Alcance y conclusión</h2><p>En {len(valid)} casos utilizables, la mediana adicional es {valid.adicional_120_min.median():.1f}min bajo navegación120 y {valid.adicional_160_min.median():.1f}min bajo navegación160; sus rangos intercuartiles son {valid.adicional_120_min.quantile(.25):.1f}–{valid.adicional_120_min.quantile(.75):.1f} y {valid.adicional_160_min.quantile(.25):.1f}–{valid.adicional_160_min.quantile(.75):.1f}min. En {int(valid.llegada_posterior_registro.sum())} casos la llegada es posterior al registro. Por tanto, sirve como contraste aproximado de tiempos declarados/previstos, pero no como medición confiable de espera efectiva. No permite identificar separadamente espera, embarque o desembarque, ni calibrar la penalización por frecuencia. El resultado sirve como contraste exploratorio de magnitudes; no justifica por sí solo reemplazar parámetros del modelo. Los percentiles y la proporción de inconsistencias deben acompañar cualquier interpretación.</p>
<p>Fuentes:Cap6/BBDDEOD/Base de datos agregada.xlsx, BBDD-1:ID2,Fecha/Horainicioviaje,Fecha/Horallegada yFechaCreación; selecciónválida deBBDD-2 reproducida en etapa1_lacustre_aristo_20261029/resultados/entrega_final/csv/auditoria_264.csv. Tiempos:Etapa4/costos_generalizados_etapa4.xlsx, hojaCostosdesagregadosOD, alternativaactual, columnas tiempo_vial_h/embarque/desembarque/horario. Reproducción:<code>python exploracion_tiempos_barcaza_20261029/explorar.py</code>. Fuentes verificadas sin cambios porSHA256.</p></html>'''
(P/'informe_tiempos.html').write_text(page,encoding='utf-8')
print('CALIDAD');print(quality.to_string(index=False));print('ESTADISTICAS');print(stats.to_string(index=False));print('ROBUSTEZ');print(robust.to_string(index=False));print('CASOS resumidos');print(flags.to_string(index=False));print('ROAD',road)
