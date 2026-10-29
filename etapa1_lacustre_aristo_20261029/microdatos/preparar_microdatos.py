"""Lee originales ARISTO, enlaza BBDD1/BBDD2 por ID2, nunca suma encuestas."""
from pathlib import Path
import unicodedata, hashlib, json, argparse, datetime, math
import pandas as pd
import openpyxl

def norm(x):
 if x is None or pd.isna(x):return ''
 return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',str(x)) if not unicodedata.combining(c)).lower().split())

def ferry(x):return 'ibanez' in norm(x) and 'chile chico' in norm(x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
 if isinstance(v,list):return [clean(x) for x in v]
 if isinstance(v,float) and not math.isfinite(v):return None
 return v
def sheet(w,name):
 it=w[name].values;headers=next(it);counts={};unique=[]
 for h in headers:
  h=str(h);counts[h]=counts.get(h,0)+1;unique.append(h if counts[h]==1 else h+'__'+str(counts[h]))
 return pd.DataFrame(it,columns=unique)
def main(root,out):
 root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if (out/'microdatos_ferry_264.csv').exists():raise FileExistsError('Carpeta de salida ya generada')
 e=root/'Cap 6/BBDD EOD/Base de datos agregada.xlsx';z=root/'Cap 8/BBDD_para_Pijas_actualizada_EOD_Final.xlsx';dic=root/'Cap 6/BBDD EOD/DiccionarioAPP.xlsx'
 before={str(p):sha(p) for p in [e,z,dic]}
 w=openpyxl.load_workbook(e,read_only=True,data_only=True,keep_links=False)
 a=sheet(w,'BBDD-1');b=sheet(w,'BBDD-2 (solo válidas)');semi=sheet(w,'Semi-diccionario');w.close()
 a['fila_BBDD1']=range(2,len(a)+2);b['fila_BBDD2']=range(2,len(b)+2)
 assert a['ID 2'].notna().all() and b['ID 2'].notna().all()
 assert a['ID 2'].is_unique and b['ID 2'].is_unique
 aa=a[a['Lugar encuestado'].map(ferry)].copy();bb=b[b['Lugar encuestado'].map(ferry)].copy()
 d=bb.add_prefix('b2__').merge(aa.add_prefix('b1__'),left_on='b2__ID 2',right_on='b1__ID 2',validate='one_to_one')
 assert len(aa)==290 and len(bb)==264 and len(d)==264
 wz=openpyxl.load_workbook(z,read_only=True,data_only=True,keep_links=False);zz=sheet(wz,'Zonas');wz.close();assert set(zz.ID_Nodo)==set(range(1,56))
 zmap={norm(r['Zona']):int(r['ID_Nodo']) for r in zz.to_dict('records')}
 def homologar(row,side):
  name=row['b2__Nombre '+side];country=row['b2__País'+('' if side=='origen' else '__2')];level=row['b2__Nivel administrativo'+('' if side=='origen' else '__2')]
  if norm(name) in zmap:return zmap[norm(name)],'Nombre exacto normalizado en catálogo original Zonas; no es ID BBDD2'
  if norm(country)=='argentina' and norm(level)=='provincia':
   candidates=[(n,k) for n,k in zmap.items() if n in ['provincia de '+norm(name),'provincia del '+norm(name),'provincia '+norm(name)]]
   if len(candidates)==1:return candidates[0][1],'Provincia argentina declarada BBDD2 coincide con catálogo Zonas omitiendo prefijo Provincia de/del'
  if norm(country)=='chile' and norm(level)=='region' and norm(name) in ['metropolitana','biobio']:
   return 55,'Región chilena declarada fuera de regiones de cobertura 10/11/12; catálogo original Resto de Chile (macrozona, no localidad)'
  return None,'Pendiente: nombre BBDD2 sin equivalencia unívoca documentada'
 geo=[]
 for side in ['origen','destino']:
  names=d['b2__Nombre '+side]
  d[side+'_nombre_BBDD2']=names;d[side+'_codigo_geografico_BBDD2']=d['b2__ID '+side]
  mapped=d.apply(lambda row:homologar(row,side),axis=1)
  d[side+'_zona_modelacion_ARISTO']=mapped.map(lambda x:x[0])
  d[side+'_metodo_homologacion']=mapped.map(lambda x:x[1])
  d[side+'_localidad_no_inferida']='No se asigna localidad a partir de comuna; conservar direcciones y búsquedas originales'
  for row in d.to_dict('records'):
   geo.append({'extremo':side,'codigo_BBDD2':row['b2__ID '+side],'nombre_BBDD2':row['b2__Nombre '+side],'pais_BBDD2':row['b2__País'+('' if side=='origen' else '__2')],'nivel_BBDD2':row['b2__Nivel administrativo'+('' if side=='origen' else '__2')],'zona_modelacion_ARISTO':row[side+'_zona_modelacion_ARISTO'],'metodo':row[side+'_metodo_homologacion']})
 d['id_encuesta']=d['b1__ID 2'].astype(int).astype(str)
 d['campana_BBDD1_original']=d['b1__Versión'];d['campana_BBDD2_original']=d['b2__Versión'];d['campana']=d['b2__Versión'];d['sentido_cruce']=d['b1__Sentido Viaje'];d['tipo_usuario_BBDD1']=d['b1__Tipo de usuario encuestado'];d['tipo_usuario_BBDD2']=d['b2__Tipo usuario']
 d['nacionalidad_declarada']=d['b1__Nacionalidad'];d['patente_categoria_declarada']=d['b1__Patente'];d['ocupantes_vehiculo']=d['b1__Ocupantes del vehículo'];d['tamano_grupo']=d['b1__Tamaño del Grupo']
 d['fuente_excel']=str(e);d['fuente_hoja_original']='BBDD-1';d['fuente_hoja_valida']='BBDD-2 (solo válidas)';d['unidad_registro']='Una entrevista válida; no sumar hojas originales y válidas'
 d.to_csv(out/'microdatos_ferry_264.csv',index=False,encoding='utf-8-sig')
 d.groupby(['campana','sentido_cruce','tipo_usuario_BBDD2'],dropna=False).size().rename('entrevistas').reset_index().to_csv(out/'denominadores_por_tipo_usuario.csv',index=False,encoding='utf-8-sig')
 aa[~aa['ID 2'].isin(bb['ID 2'])].to_csv(out/'26_originales_no_en_BBDD2.csv',index=False,encoding='utf-8-sig')
 aa.to_csv(out/'290_originales_ferry.csv',index=False,encoding='utf-8-sig')
 zz.to_csv(out/'catalogo_original_zonas_55.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame(geo).drop_duplicates().to_csv(out/'correspondencias_BBDD2_zonas.csv',index=False,encoding='utf-8-sig')
 checks={'290_originales':len(aa)==290,'264_validas':len(d)==264,'ID2_unico':d.id_encuesta.is_unique,'enlace_uno_a_uno':len(d)==len(bb),'no_sumar_hojas':len(d)!=len(aa)+len(bb),'campana_consistente_normalizando_alias_Normal_Otono':d['b1__Versión'].replace({'Normal':'Otoño'}).eq(d['b2__Versión']).all(),'sentido_consistente':d['b1__Sentido Viaje'].eq(d['b2__Sentido Viaje']).all(),'55_zonas':len(zz)==55,'originales_intactos':before=={str(p):sha(p) for p in [e,z,dic]}}
 result={'verificaciones':{k:bool(v) for k,v in checks.items()},'sha256_fuentes':before,'alias_campana_Normal_Otono':int((d['b1__Versión']!=d['b2__Versión']).sum()),'originales':len(aa),'validas':len(d),'no_validas_en_BBDD2':len(aa)-len(d),'campana_sentido_usuario':d.groupby(['campana','sentido_cruce','tipo_usuario_BBDD2'],dropna=False).size().rename('entrevistas').reset_index().to_dict('records'),'extremos_sin_zona':{s:int(d[s+'_zona_modelacion_ARISTO'].isna().sum()) for s in ['origen','destino']},'nombre_ID_BBDD2':pd.DataFrame(geo).drop_duplicates(['codigo_BBDD2','nombre_BBDD2']).to_dict('records')}
 result=clean(result)
 (out/'validacion_microdatos.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n')
 assert all(checks.values()), checks
 print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--anexos',default='.');p.add_argument('--salida',required=True);x=p.parse_args();main(x.anexos,x.salida)
