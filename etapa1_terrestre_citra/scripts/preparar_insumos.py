"""Congela las decisiones ya existentes y las29 homologaciones autorizadas. Sin estimar."""
from pathlib import Path
import csv,json,hashlib
B=Path(__file__).resolve().parents[2];O=B/'etapa1_terrestre_citra/insumos_decisiones';S=Path('/home/nataly/Escritorio/demanda_evalso')
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def save(name,rows):
 p=O/name
 if p.exists():raise RuntimeError('Insumo congelado existente; no se sobrescribe: '+str(p))
 cols=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
d=read(S/'eod_filtrada/tablas/base_completa_filtrada.csv')
cols=['id_encuesta','campana_archivo','fila_excel','id_par','id_caso','estado_filtro','motivo_filtro','decision_usuario','comentarios_usuario','decision_previa','comentario_previo','decision_lista_corta','ambiguo_relevante','ruta_utilizada','ruta_probable','regla_ruta','estado_validacion_ruta','seleccionada_nueva','pantalla_nueva']
save('alcance_y_clasificacion_anteriores.csv',[{k:r.get(k,'') for k in cols} for r in d])
p=read(B/'homologacion_geografica_etapa1/segunda_revision/propuestas_por_extremo.csv');approved=[r for r in p if r['resuelto_propuesto']=='True'];pending=[r for r in p if r['requiere_manual']=='True'];assert len(approved)==29 and len(pending)==8
save('homologaciones_aprobadas_29.csv',approved);save('pendientes_no_imputar_8.csv',pending)
(B/'etapa1_terrestre_citra/insumos_decisiones/autorizacion.json').write_text(json.dumps({'instruccion_usuario':'Aplicar29 propuestas (11 con coordenada,18 nominales);8 extremos pendientes sin imputar; auditar112 entrevistas Tierra confirmada del filtro previo; matriz Chile estricta sin logit ni imputaciones.','alcance_geografico':'Decisiones previas de área conservadas; no inclusión automática de viajes externos ni Ruta7 local.','sha256_fuente_alcance':hashlib.sha256((S/'eod_filtrada/tablas/base_completa_filtrada.csv').read_bytes()).hexdigest(),'sha256_fuente_propuestas':hashlib.sha256((B/'homologacion_geografica_etapa1/segunda_revision/propuestas_por_extremo.csv').read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
print('Insumos de decisiones congelados;29 aprobadas y8 pendientes.')
