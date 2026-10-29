"""Pruebas geométricas de compatibilidad; no predicción de elección de rutas."""
import math,collections,itertools,json
import geopandas as gp,networkx as nx,numpy as np
from shapely.geometry import Point,LineString
from shapely.ops import linemerge
from shapely.strtree import STRtree
from pyproj import Transformer
from fuentes import num,canon

class Red:
 def __init__(self,base,interviews,geos,points,scope):
  self.proj=Transformer.from_crs(4326,32718,always_xy=True);self.geos=geos;self.points=points
  roads=gp.read_file(base/'Cap 7/SIG Red_Vial_Final/Red_Vial_Final.shp');nodes=gp.read_file(base/'Cap 7/SIG Red_Vial_Final/Nodos_RedVial.shp');passes=gp.read_file(base/'Cap 7/SIG Red_Vial_Final/Nodos_Puntos_Pasada.shp')
  self.passes={int(r.ID_Nodo):r.Pto_Pasada for _,r in passes.iterrows()};nodepoints={int(r.ID_Nodo):self.xy(r.geometry.y,r.geometry.x) for _,r in nodes.iterrows()}
  self.es=[]
  for _,r in roads[(roads.TIPO_PAVIM!='A')&~roads.RUTA.str.startswith('Conect')].to_crs(32718).iterrows():
   geom=linemerge(r.geometry) if r.geometry.geom_type=='MultiLineString' else r.geometry
   if geom.geom_type!='LineString':continue
   u,v=int(r.Nodo_A),int(r.Nodo_B)
   if Point(geom.coords[0]).distance(nodepoints[u])>Point(geom.coords[-1]).distance(nodepoints[u]):geom=LineString(list(geom.coords)[::-1])
   self.es.append(dict(u=u,v=v,geom=geom,km=float(r.LONGITUD),arco=int(r.ID_Arco),pais='Argentina' if r.REGI_N=='Argentina' else 'Chile',ruta=str(r.RUTA)))
  self.ces=[e for e in self.es if e['pais']=='Chile'];self.tree=STRtree([e['geom'] for e in self.ces]);self.splits=collections.defaultdict(list);self.snaps={};self.refs={}
  names={'01 Pto. Cisnes':'PUERTO CISNES','02 Pto. Chacabuco':'PUERTO CHACABUCO','03 Raul Marin Balmaceda':'RAUL MARIN BALMACEDA','04 Balmaceda':'BALMACEDA','05 Coyhaique':'COYHAIQUE','06 Pto Bertrand':'PUERTO BERTRAND','07 Pto Tranquilo':'PUERTO RIO TRANQUILO','08 Chile Chico':'CHILE CHICO','09 Bahia Jara':'BAHIA JARA','09 Levican':'LEVICAN','10 Mallin Grande':'MALLIN GRANDE','10 Puerto Guadal':'PUERTO GUADAL','11 Villa Cerro Castillo':'VILLA CERRO CASTILLO','Murta':'PUERTO MURTA','Puerto Ibañez':'PUERTO IBANEZ'}
  for key,name in names.items():
   r=points[key];self.refs[name]=dict(lat=r['lat'],lon=r['lon'],fuente='KMZ original; '+key)
  # Reproducir referencias nominales adicionales desde coordenadas originales CITRA.
  additional={'COCHRANE',"VILLA O'HIGGINS",'CALETA TORTEL','PUYUHUAPI','LA JUNTA','MANIHUALES','EL BLANCO','VALLE SIMPSON','PUERTO AYSEN','VILLA ORTEGA','COYHAIQUE ALTO'}
  vals=collections.defaultdict(list)
  for row in interviews:
   for side in ['origen','destino']:
    raw=row[side+'_original']
    if not raw.lstrip().startswith('{'):continue
    try:j=json.loads(raw);name=canon(j.get('search','').split(',')[0]);lat,lon=num(j.get('coords',{}).get('lat')),num(j.get('coords',{}).get('lon'))
    except (ValueError,TypeError,AttributeError):continue
    if name in additional and lat is not None and lon is not None and -56<lat<-35 and -76<lon<-66:vals[name].append((lat,lon))
  for name,vv in vals.items():
   if len(vv)<5:continue
   cell=collections.Counter((round(a,2),round(b,2)) for a,b in vv).most_common(1)[0][0];p=self.xy(*cell);cluster=[v for v in vv if self.xy(*v).distance(p)<5000]
   if len(cluster)<max(5,.6*len(vv)):continue
   self.refs[name]=dict(lat=float(np.median([v[0] for v in cluster])),lon=float(np.median([v[1] for v in cluster])),fuente=f'Referencia calculada desde originales CITRA;{len(cluster)}/{len(vv)} extremos; no coordenada individual')
  for key,r in points.items():
   if key.startswith('E'):self.request(key,r['lat'],r['lon'])
  self.endpoint={}
  for rid in scope:
   for side in ['origen','destino']:
    geo=geos[rid,side];raw=geo['literal_original'];lat,lon=num(geo['lat_original']),num(geo['lon_original']);primary=canon(geo['localidad_original'].split(',')[0]);loc=geo.get('localidad_homologada','') or (primary if primary in self.refs else '')
    info=dict(localidad=loc,localidad_literal=geo['localidad_original'],CUT=geo['cut_comuna'],zona=geo['zona_modelacion_aristo'],tipo_punto='',lat_modelo=None,lon_modelo=None,fuente='',motivo='')
    if geo['estado']!='Homologado comuna y zona':info['motivo']='OD sin homologación comunal y zonal aprobada'
    elif lat is not None and lon is not None and -90<lat<90 and -180<lon<180 and lat!=0 and lon!=0:
     info.update(lat_modelo=lat,lon_modelo=lon,tipo_punto='Coordenada geocodificada original; precisión individual no certificada',fuente='EOD original JSON; no desplazada')
    elif loc in self.refs:
     rr=self.refs[loc];info.update(lat_modelo=rr['lat'],lon_modelo=rr['lon'],tipo_punto='Referencia del topónimo explícito; no coordenada original',fuente=rr['fuente'])
    else:info['motivo']='No hay localidad explícita o punto validable; no se usa cabecera/centroide de comuna'
    if info['lat_modelo'] is not None:
     self.request(rid+'_'+side,info['lat_modelo'],info['lon_modelo']);info.update(self.snaps[rid+'_'+side])
    self.endpoint[rid,side]=info
  self.G=nx.Graph();self.C=nx.Graph();self.A=nx.Graph();self.keynodes={}
  for e in self.es:
   seq=sorted([(0,('NODE',e['u'])),(e['geom'].length,('NODE',e['v']))]+self.splits[e['arco']],key=lambda x:x[0]);clean=[]
   for pos,key in seq:
    if clean and abs(pos-clean[-1][0])<.01:self.keynodes[key]=clean[-1][1];continue
    node=e['u'] if abs(pos)<.01 else e['v'] if abs(pos-e['geom'].length)<.01 else f"s{e['arco']}_{len(clean)}"
    self.keynodes[key]=node;clean.append((pos,node));p=e['geom'].interpolate(pos)
    for graph in [self.G,self.C if e['pais']=='Chile' else self.A]:graph.add_node(node,x=p.x,y=p.y)
   for (pa,u),(pb,v) in zip(clean,clean[1:]):
    attr=dict(weight=e['km']*(pb-pa)/e['geom'].length,arco=e['arco'],pais=e['pais'],ruta=e['ruta'])
    for graph in [self.G,self.C if e['pais']=='Chile' else self.A]:
     if not graph.has_edge(u,v) or attr['weight']<graph[u][v]['weight']:graph.add_edge(u,v,**attr)
  self.cache={};self.borders=sorted(set(self.C)&set(self.A));self.landpaths={};self.argument_paths=[]
 def xy(self,lat,lon):return Point(*self.proj.transform(float(lon),float(lat)))
 def request(self,key,lat,lon):
  p=self.xy(lat,lon);e=self.ces[int(self.tree.nearest(p))];pos=e['geom'].project(p);self.splits[e['arco']].append((pos,key));self.snaps[key]=dict(arco_red=e['arco'],posicion_en_arco_m=pos,separacion_red_m=e['geom'].distance(p))
 def path(self,g,u,v):
  if u not in g or v not in g:return None
  key=(id(g),u)
  if key not in self.cache:self.cache[key]=nx.single_source_dijkstra_path(g,u,weight='weight')
  return self.cache[key].get(v)
 @staticmethod
 def stitch(paths):
  if any(p is None for p in paths):return None
  out=paths[0].copy()
  for p in paths[1:]:out+=p[1:]
  return out if len(out)==len(set(out)) else None
 def direction(self,p,ctrl):
  cn=self.keynodes[ctrl]
  if not p or cn not in p or len(p)<2:return None
  k=p.index(cn);u=p[k-1] if k>0 else cn;v=p[k+1] if k<len(p)-1 else cn
  dx=self.G.nodes[v]['x']-self.G.nodes[u]['x'];dy=self.G.nodes[v]['y']-self.G.nodes[u]['y'];return dx,dy
 def matches(self,p,ctrl,sense):
  d=self.direction(p,ctrl)
  if d is None or sense not in ['NS','SN','PO','OP']:return False
  comp=d[1] if sense in ['NS','SN'] else d[0]
  return (comp>0)==(sense in ['SN','PO']) and abs(comp)>1
 def expected(self,p,ctrl,sense):
  d=self.direction(p,ctrl)
  if d is None:return ''
  return ('SN' if d[1]>0 else 'NS') if sense in ['NS','SN'] else ('PO' if d[0]>0 else 'OP')
 def arcs(self,p):return [self.G[u][v]['arco'] for u,v in zip(p,p[1:])] if p else []
 def km(self,p):return sum(self.G[u][v]['weight'] for u,v in zip(p,p[1:])) if p else None
 def pair_route(self,rid):
  o=self.keynodes.get(rid+'_origen');d=self.keynodes.get(rid+'_destino');return self.path(self.C,o,d)
 def audit(self,row):
  rid,ctrl,sense=row['id_encuesta'],row['control'],row['sentido'];a,b=self.endpoint[rid,'origen'],self.endpoint[rid,'destino'];p=self.pair_route(rid);self.landpaths[rid]=p
  controlsense=self.expected(p,ctrl,sense) if ctrl in self.keynodes else ''
  out=dict(id_encuesta=rid,control=ctrl,sentido_observado=sense,sentido_compatible_modelo=controlsense,control_en_camino_Chile=bool(p and self.keynodes[ctrl] in p),sentido_compatible=self.matches(p,ctrl,sense),separacion_control_red_m=self.snaps[ctrl]['separacion_red_m'],separacion_origen_red_m=a.get('separacion_red_m'),separacion_destino_red_m=b.get('separacion_red_m'),arcos_camino_Chile='|'.join(map(str,self.arcs(p))),nodos_camino_Chile='|'.join(map(str,p)) if p else '',km_referencia_Chile=self.km(p),alternativa_barcaza_compatible=False,alternativa_Argentina_compatible=False,alternativas_argentina_sin_repetir_nodos=0,alternativas_argentina_compatibles_control=0,entrada_argentina='',salida_argentina='',km_alternativa_argentina_referencia=None,arcos_alternativa_argentina='',inferencia='Se observa interceptación en un punto; el itinerario completo solo se infiere. La distancia selecciona un testigo reproducible, no demuestra elección.')
  if not p:return out
  roadnames={self.G[u][v]['ruta'] for u,v in zip(p,p[1:])}
  out['corredor_R7_y_R265']=('R7' in roadnames and 'R265-CH' in roadnames)
  o,d=p[0],p[-1];ferries=[];lacustre_posible=0
  for left,right in [(1026,1117),(1117,1026)]:
   pa,pb=self.path(self.C,o,left),self.path(self.C,right,d)
   # Cruce explícito entre terminales; los dos accesos no pueden repetir nodos.
   fp=pa+pb if pa is not None and pb is not None and not(set(pa)&set(pb)) else None
   if fp:lacustre_posible+=1
   if self.matches(fp,ctrl,sense):ferries.append((left,right))
  out['alternativa_barcaza_compatible']=bool(ferries)
  out['alternativas_lacustres_sin_retorno']=lacustre_posible
  candidates=[]
  for left in self.borders:
   pa=self.path(self.C,o,left)
   if pa is None:continue
   for right in self.borders:
    if right==left:continue
    ap=self.stitch([pa,self.path(self.A,left,right),self.path(self.C,right,d)])
    if ap:
     out['alternativas_argentina_sin_repetir_nodos']+=1
     if self.matches(ap,ctrl,sense):candidates.append((self.km(ap),left,right,ap))
  out['alternativas_argentina_compatibles_control']=len(candidates)
  if candidates:
   km,left,right,ap=min(candidates,key=lambda v:v[:3]);out.update(alternativa_Argentina_compatible=True,entrada_argentina=self.passes.get(left,'Nodo frontera '+str(left)),salida_argentina=self.passes.get(right,'Nodo frontera '+str(right)),km_alternativa_argentina_referencia=km,arcos_alternativa_argentina='|'.join(map(str,self.arcs(ap))))
   self.argument_paths.append(dict(id_encuesta=rid,entrada_nodo=left,salida_nodo=right,nodos_testigo='|'.join(map(str,ap)),arcos_testigo=out['arcos_alternativa_argentina'],km_referencia=km,prueba_no_repeticion=len(ap)==len(set(ap)),sentido_control_compatible=True,alcance='Contraejemplo de unicidad en red; NO viaje observado por Argentina; habilitación y fechas de paso no certificadas'))
  return out
 def screen_geometry(self,rids,ctrl,sense):
  result=[];mandatory=[]
  for rid in rids:
   p=self.landpaths.get(rid) or self.pair_route(rid);ok=self.matches(p,ctrl,sense);result.append(ok)
   if not p or self.keynodes[ctrl] not in p:mandatory.append(False);continue
   cn=self.keynodes[ctrl];o,d=p[0],p[-1]
   if cn in [o,d]:mandatory.append(False);continue
   # Si eliminar el nodo rompe el camino, es una pantalla obligatoria en la red chilena modelada.
   view=nx.subgraph_view(self.C,filter_node=lambda n:n!=cn)
   mandatory.append(not nx.has_path(view,o,d))
  return result,mandatory
