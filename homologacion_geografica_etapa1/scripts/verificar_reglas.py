"""Casos adversos de geografía: solo lectura de polígonos, sin modelos ni expansión."""
import json
from homologar_geografia import Homologador,OUT
h=Homologador();checks={}
a=h.endpoint('Mallín Grande','Chile Chico');checks['Mallin_Grande_11401_zona39']=a['cut_comuna']=='11401' and a['zona_modelacion_aristo']==39 and a['lat_original']==''
a=h.endpoint('Río Ibáñez');checks['comuna_no_localidad_Puerto_Ibanez']=a['cut_comuna']=='11402' and a['zona_modelacion_aristo']==40 and a['localidad_homologada']==''
a=h.endpoint('Puerto Ibáñez');checks['Puerto_Ibanez_zona40_no_ID42']=a['cut_comuna']=='11402' and a['zona_modelacion_aristo']==40
checks['texto_y_comuna_contradictorios_sin_asignar']=h.endpoint('CHILE CHICO','COYHAIQUE')['estado']=='Pendiente'
c=h.refs['COYHAIQUE'];literal=json.dumps({'search':'Chile Chico','address':'Chile Chico, Aysén, Chile','coords':{'lat':c['lat'],'lon':c['lon']}})
a=h.endpoint(literal);checks['coordenada_no_prevalece_sobre_conflicto']=a['estado']=='Pendiente' and a['cut_comuna']=='' and a['zona_modelacion_aristo']==''
literal=json.dumps({'search':'COYHAIQUE','address':'Coyhaique, Aysén, Chile','coords':{'lat':c['lat'],'lon':c['lon']}})
a=h.endpoint(literal);checks['Aysen_regional_no_conflicto_comunal']=a['cut_comuna']=='11101' and a['zona_modelacion_aristo']==31
checks['coordenadas_y_JSON_originales_intactos']=a['literal_original']==literal and a['lat_original']==c['lat'] and a['lon_original']==c['lon']
a=h.endpoint(json.dumps({'search':'ALEMANIA','address':'Coyhaique, Aysén, Chile','coords':{'lat':c['lat'],'lon':c['lon']}}));checks['nombre_internacional_y_punto_Chile_pendiente']=a['estado']=='Pendiente'
a=h.endpoint(json.dumps({'search':'Coyhaique','coords':{'lat':0,'lon':0}}));checks['cero_coordenadas_no_asignado']=a['estado']=='Pendiente' and a['lat_original']==0
q=h.comunas[h.comunas.CUT_COM.eq('11402')].iloc[0];p=q.geometry.boundary.interpolate(.3,normalized=True)
a=h.endpoint(json.dumps({'search':'Río Ibáñez','coords':{'lat':p.y,'lon':p.x}}));checks['limite_poligono_no_asignado']=a['estado']=='Pendiente'
a=h.endpoint(json.dumps({'coords':{'lat':c['lat'],'lon':c['lon']}}));checks['punto_sin_contraste_textual_no_asignado']=a['estado']=='Pendiente' and a['cut_candidato']=='11101'
a=h.endpoint('SANTIAGO');checks['macrozona55_sin_CUT_inventado']=a['zona_modelacion_aristo']==55 and a['cut_comuna']=='' and a['comuna_homologada']==''
a=h.endpoint('CALLE CHILE CHICO 12, COYHAIQUE, AYSEN, CHILE');checks['nombre_calle_no_se_convierte_en_comuna']=a['zona_modelacion_aristo']==31
checks['etiqueta_ambigua_IBANEZ_sin_asignar']=h.endpoint('IBANEZ')['estado']=='Pendiente'
q=h.refs['PUERTO GUADAL']
a=h.endpoint(json.dumps({'search':'Puerto Guadal, Chile Chico, Chile','address':'Puerto Guadal, Chile Chico, Aysén, Chile','coords':{'lat':q['lat'],'lon':q['lon']}}))
checks['cola_comunal_no_es_segunda_localidad']=a['cut_comuna']=='11401' and a['zona_modelacion_aristo']==39 and a['localidad_homologada']=='PUERTO GUADAL'
(OUT/'verificacion_reglas.json').write_text(json.dumps({'estado':'correcto' if all(checks.values()) else 'ERROR','pruebas':checks},ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2));assert all(checks.values())
