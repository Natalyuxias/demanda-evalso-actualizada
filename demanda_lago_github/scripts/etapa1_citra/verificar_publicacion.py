"""Valida la selección pública de Etapa1 sin leer microdatos ni resultados privados."""
from pathlib import Path
import json,hashlib,ast

def main():
 root=Path(__file__).resolve().parents[2];folder=root/'results/etapa1_citra';manifest=json.loads((folder/'manifest_publicacion.json').read_text())
 expected={'results/etapa1_citra/resumen_publico.json','results/etapa1_citra/resumen_publico.html'}
 assert {r['archivo'] for r in manifest['archivos']}==expected
 for row in manifest['archivos']:
  p=root/row['archivo'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];assert p.stat().st_size<20000
 d=json.loads((folder/'resumen_publico.json').read_text());banned={'id_encuesta','lat','lon','latitud','longitud','origen','destino','direccion','patente','flujo','factor_expansion'}
 assert not set(d)&banned and d['matriz_principal_contiene_flujo_estimado'] is False
 assert {p.name for p in folder.iterdir()}=={'manifest_publicacion.json','resumen_publico.json','resumen_publico.html'}
 final=root/'results/citra_cierre';fm=json.loads((final/'manifest_publicacion.json').read_text())
 assert {p.name for p in final.iterdir()}=={'manifest_publicacion.json','resumen_publico.json','resumen_publico.html'}
 assert {r['archivo'] for r in fm['archivos']}=={'results/citra_cierre/resumen_publico.json','results/citra_cierre/resumen_publico.html'}
 for row in fm['archivos']:
  p=root/row['archivo'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];assert p.stat().st_size<20000
 fd=json.loads((final/'resumen_publico.json').read_text());assert not set(fd)&banned and fd['viabilidad'].startswith('B')
 for p in Path(__file__).parent.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
 print(json.dumps({'estado':'correcto','manifiesto':True,'sin_microdatos_ni_flujos':True,'sintaxis_scripts':True},ensure_ascii=False))
if __name__=='__main__':main()
