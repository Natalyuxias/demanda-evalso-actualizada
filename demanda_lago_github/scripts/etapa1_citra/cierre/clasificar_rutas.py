"""Clasificación final de corredor; reutiliza trayectorias cacheadas, sin buscar rutas."""
from pathlib import Path
import argparse, hashlib, json
import pandas as pd

def classify(r):
    """Alta confianza es inferencia multicriterio, no observación del itinerario."""
    reasons=[]
    if not r['OD_homologado']:
        return 'C', 'Geografía insuficiente: OD no determinado; no imputar.'
    for col,label in [('control_en_camino_Chile','control fuera de la trayectoria chilena de referencia'),('sentido_compatible','sentido incompatible con trayectoria de referencia'),('corredor_R7_y_R265','no acredita corredor pertinente R7–R265')]:
        if not r[col]: reasons.append(label)
    if reasons: return 'C', '; '.join(reasons)+'.'
    if r['referencia_internacional'] or r['Argentina_observada']:
        return 'B', 'Referencia internacional o evidencia argentina: no atribuir automáticamente a Chile.'
    if r['alternativa_barcaza_compatible']:
        return 'B', 'Alternativa lacustre compatible con interceptación; itinerario chileno terrestre no suficientemente distinguido.'
    if not pd.notna(r['km_referencia_Chile']):
        return 'B', 'Sin longitud de referencia chilena verificable.'
    if r['alternativa_Argentina_compatible']:
        if not pd.notna(r['km_alternativa_argentina_referencia']):
            return 'B', 'Alternativa argentina existente sin comparación verificable.'
        if r['km_alternativa_argentina_referencia'] <= r['km_referencia_Chile']:
            return 'B', 'Alternativa argentina no dominada en longitud; tiempos desconocidos.'
        if pd.isna(r['entrada_argentina']) or pd.isna(r['salida_argentina']) or r['entrada_argentina']==r['salida_argentina']:
            return 'B', 'No acredita comparación consistente de dos pasos distintos.'
    return 'A', ('OD pertinente, control y sentido compatibles con corredor terrestre chileno; sin alternativa lacustre compatible ni evidencia internacional contradictoria. '
                 'Testigo mixto argentino más largo y con dos cruces fronterizos; inferencia de alta confianza del corredor, no declaración de itinerario completo.')

def run(source,out):
    source=Path(source);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    target=out/'clasificacion_112.csv'
    if target.exists(): raise FileExistsError('No sobrescribir clasificación previa')
    d=pd.read_csv(source)
    assert len(d)==112 and d.id_encuesta.nunique()==112
    results=d.apply(classify,axis=1)
    d['categoria_final']=[r[0] for r in results]
    d['categoria']=d['categoria_final']
    d['motivo_clasificacion_final']=[r[1] for r in results]
    d['motivo']=d['motivo_clasificacion_final']
    d['evidencia_ruta']='Inferencia topológica y comparación de atributos; no ruta declarada'
    d['itinerario_integro_por_Chile_observado']=False
    d['tiempo_Chile_h']=None;d['tiempo_Argentina_h']=None
    d['estado_operativo_pasos_en_fecha']='No verificado; no se supone cierre ni habilitación'
    d['incertidumbre_residual']='Ruta individual no declarada; velocidades, esperas y habilitación fronteriza por fecha no observadas; coordenadas pueden ser geocodificadas'
    d['diferencia_km_Argentina_menos_Chile']=d.km_alternativa_argentina_referencia-d.km_referencia_Chile
    d['razon_km_Argentina_Chile']=d.km_alternativa_argentina_referencia/d.km_referencia_Chile
    d.to_csv(target,index=False,encoding='utf-8-sig')
    a=d[d.categoria_final=='A']
    meta={'fuente':str(source),'sha256_fuente':hashlib.sha256(source.read_bytes()).hexdigest(),'metodo':'Inferencia multicriterio de corredor: topología, sentido, pertinencia, sin contradicción y comparación distancia/cruces. No umbral de desvío ni tiempo supuesto.','categorias':{k:int((d.categoria_final==k).sum()) for k in ['A','B','C']},'por_control_categoria':d.groupby(['control','categoria_final']).size().rename('entrevistas').reset_index().to_dict('records'),'A_km_adicionales_argentina_min':float(a.diferencia_km_Argentina_menos_Chile.min()),'A_km_adicionales_argentina_max':float(a.diferencia_km_Argentina_menos_Chile.max()),'A_razon_distancia_min':float(a.razon_km_Argentina_Chile.min()),'A_razon_distancia_max':float(a.razon_km_Argentina_Chile.max()),'A_con_factor':int(a.factor_expansion.notna().sum()),'rutas_recalculadas':0,'alcance':'Cohorte de 112; no estima automáticamente todo CITRA ni todo mercado terrestre. La categoría A no certifica país del recorrido completo.','no_verificado':['tiempos de viaje comparables por itinerario','esperas y trámites fronterizos','habilitación efectiva de pasos por fecha y clase','itinerario individual elegido','recorridos con paradas intermedias no declaradas']}
    (out/'resumen_rutas.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    return meta

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--auditoria',required=True);parser.add_argument('--salida',required=True);args=parser.parse_args()
    print(json.dumps(run(args.auditoria,args.salida),ensure_ascii=False,indent=2))
