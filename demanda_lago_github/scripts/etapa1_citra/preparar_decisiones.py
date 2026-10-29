"""Congelar insumos de decisiones existentes; no estimar ni modificar formularios.
Los CSV de salida contienen claves privadas y deben permanecer fuera de Git.
"""
import argparse,csv,json,hashlib
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--base-anterior',type=Path,required=True);p.add_argument('--propuestas-geograficas',type=Path,required=True);p.add_argument('--salida',type=Path,required=True);a=p.parse_args();a.salida.mkdir(parents=True,exist_ok=True)
 def read(path):return list(csv.DictReader(path.open(encoding='utf-8-sig')))
 def write(name,rows):
  target=a.salida/name
  if target.exists():raise RuntimeError('Decisión congelada existente; no se sobrescribe: '+str(target))
  cols=list(dict.fromkeys(k for r in rows for k in r))
  with target.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
 d=read(a.base_anterior);cols=['id_encuesta','campana_archivo','fila_excel','id_par','id_caso','estado_filtro','motivo_filtro','decision_usuario','comentarios_usuario','decision_previa','comentario_previo','decision_lista_corta','ambiguo_relevante','ruta_utilizada','ruta_probable','regla_ruta','estado_validacion_ruta','seleccionada_nueva','pantalla_nueva']
 proposals=read(a.propuestas_geograficas);approved=[r for r in proposals if r['resuelto_propuesto']=='True'];pending=[r for r in proposals if r['requiere_manual']=='True'];assert len(approved)==29 and len(pending)==8
 write('alcance_y_clasificacion_anteriores.csv',[{k:r.get(k,'') for k in cols} for r in d]);write('homologaciones_aprobadas_29.csv',approved);write('pendientes_no_imputar_8.csv',pending)
 (a.salida/'autorizacion.json').write_text(json.dumps({'autorizacion':'29 propuestas aprobadas expresamente por usuario;8 pendientes sin imputación; conservar alcance previo','sha256_fuente_alcance':hashlib.sha256(a.base_anterior.read_bytes()).hexdigest(),'sha256_fuente_propuestas':hashlib.sha256(a.propuestas_geograficas.read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
