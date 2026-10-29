"""Auditoria de codigo/salidas historicas; no ejecuta el estimador 07."""
from pathlib import Path
import argparse, hashlib, json
import pandas as pd

def run(repo, out):
    repo,out=Path(repo),Path(out);out.mkdir(parents=True,exist_ok=True)
    codepath=repo/'scripts/07_matrices_od_referencia.py'
    code=codepath.read_text()
    old=repo/'outputs/matrices_od_referencia'
    bar=pd.read_csv(old/'matriz_od_barcaza.csv')
    bal=pd.read_csv(old/'conservacion_flujos_barcaza.csv')
    config=json.loads((repo/'data/templates/config_matrices_od.json').read_text())
    issues=[
      dict(tema='Universo lacustre',decision='Reutilizar',evidencia='lake=d.loc[d.ruta.eq(barcaza_actual)]',
           razon='Interceptacion del cruce actual conserva OD largos; no limita barcaza al nucleo comunal.',
           control_recomendado='264 ID2 validos unicos, enlace uno a uno BBDD1/BBDD2 y sentidos originales.'),
      dict(tema='Unidad temporal',decision='Reemplazar en esta etapa',evidencia='per_sailing*frequency/7',
           razon='El resultado historico es promedio diario semanal condicionado a frecuencia; no es flujo observado de la jornada.',
           control_recomendado='Mantener fecha y zarpe/conjunto de operaciones realmente cubierto; no usar 11/8frecuencias ni /7.'),
      dict(tema='Fila igual zarpe',decision='Revalidar',evidencia='media_por_fila_zarpe; filas_contadas_asimiladas_a_zarpes',
           razon='La propia salida historica reconoce un supuesto de exposicion; una fila no certifica una unica operacion.',
           control_recomendado='Identificar que embarques agrupa cada fila desde fuente/documentacion; medias no equivalentes si exposiciones difieren.'),
      dict(tema='Perfiles estacionales',decision='Reemplazar en esta etapa',evidencia='mes_representativo_barcaza y periodo_barcaza config',
           razon='Transferir campanas a septiembre/enero/mayo y a estaciones completas excede la estimacion observada.',
           control_recomendado='Presentar solo periodos medidos; no extrapolar invierno ni anualizar.'),
      dict(tema='Asignacion OD',decision='Reutilizar condicionada',evidencia='q=rr.flujo_dia*r.n/n',
           razon='La proporcion OD es transparente y conserva flujo cuando F y N son compatibles; el factor no certifica muestreo ni no respuesta.',
           control_recomendado='Usar F*n_OD/N en la misma campana, direccion, clase y exposicion conciliada; sin muestra conservar flujo sin OD.'),
      dict(tema='PEATON persona/grupo',decision='Revalidar antes de estimar',evidencia='PEATON se agrupa por size; no se lee tamano de grupo',
           razon='Contar entrevistas como personas supone mecanismo individual; si se selecciona un representante por grupo puede requerirse ponderacion por tamano.',
           control_recomendado='Distinguir estimador por respuestas individuales de sensibilidad por grupos; no multiplicar F ya contado en personas por ocupacion.'),
      dict(tema='Pasajeros totales',decision='No reutilizar como total',evidencia='OTRO_PASAJERO sin conteo compatible; campos ocupacion no leidos',
           razon='La matriz no calcula ocupantes de autos/camiones/motos ni pasajeros de buses/VAN/transfer; peatones no son todos los pasajeros.',
           control_recomendado='Mantener vehiculos, peatones y ocupantes separados; total de personas solo si dominios son excluyentes y completos.'),
      dict(tema='VL y privados ARISTO',decision='Revalidar componentes',evidencia='VL suma vehiculos livianos+Camioneta+Minivan+Van+Casa Rodante; privados=VL+MOTO+BICI',
           razon='Privados original incorpora motos/bicis; no equivale a VL. sum(min_count=1) puede ocultar componentes ausentes.',
           control_recomendado='No tratar blancos como cero sin regla documentada; separar motos/bicis y reconciliar privados originales por formula.'),
      dict(tema='Nacionalidad/patente/OD extranjero',decision='Agregar capa nueva',evidencia='07 no selecciona ni calcula estos campos',
           razon='No existe separacion de usuarios extranjeros en las matrices historicas; conservar demanda fisica completa.',
           control_recomendado='Tres indicadores distintos con intersecciones y desconocidos; no sumar como personas extranjeras.'),
      dict(tema='Geografia',decision='Reutilizar con limite',evidencia='resolver_lugar Rio Ibanez por texto; Nombre origen/destino BBDD2',
           razon='No asimila Rio Ibanez a Puerto Ibanez, pero BBDD2 no es zonificacion de55zonas.',
           control_recomendado='Mantener campos originales BBDD1/BBDD2 y capa comuna/ARISTO independiente; no autocompletar localidades.'),
    ]
    pd.DataFrame(issues).to_csv(out/'comparacion_metodologica_07.csv',index=False)
    observed=bar.groupby('segmento',dropna=False).agg(filas=('segmento','size'),entrevistas=('encuestas_validas','sum'),celdas_con_flujo=('demanda_expandida_viajes_diarios_promedio','count')).reset_index()
    observed.to_csv(out/'inventario_matriz_07_historica.csv',index=False)
    columns=['estacion','sentido_control','segmento','referencia_dia','asignado_OD','sin_asignar_dia','n_estrato']
    bal[columns].to_csv(out/'balance_07_historico_NO_actual.csv',index=False)
    summary=dict(no_ejecutado_07=True,filas_matriz_historica=len(bar),
                 entrevistas_matriz_historica=int(bar.encuestas_validas.sum()),
                 unidad_historica='Viajes diarios promedio por perfil de campana y frecuencia semanal asumida',
                 unidad_requerida_actual='Flujo observado en exposicion conciliada, sin frecuencia ni anualizacion',
                 frecuencias_historicas=config['frecuencia_ordinaria_zarpes_semanales_por_mes'],
                 diferencias_metodologicas=issues,
                 fuentes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [codepath,old/'matriz_od_barcaza.csv',old/'conservacion_flujos_barcaza.csv',repo/'data/templates/config_matrices_od.json']})
    (out/'comparacion_07.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--salida',required=True);a=p.parse_args()
    print(json.dumps(run(a.repo,a.salida),ensure_ascii=False,indent=2))
