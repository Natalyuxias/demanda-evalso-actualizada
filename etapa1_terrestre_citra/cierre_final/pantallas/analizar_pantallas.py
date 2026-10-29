"""Contrasta pantallas del cache aprobado, sin reconstruir rutas ni sumar controles."""
from pathlib import Path
import argparse, hashlib, itertools, json
import pandas as pd

def ejecutar(cache, salida):
    cache, salida = Path(cache), Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    validacion = json.loads((cache / 'validacion.json').read_text())
    assert all(validacion['verificaciones'].values())
    files = ['seleccion_pantallas', 'relaciones_entre_controles',
             'estimaciones_por_dia_y_pantalla', 'auditoria_112']
    tables = {f: pd.read_csv(cache / 'csv' / (f + '.csv')) for f in files}
    sel, rel, dia, aud = [tables[f] for f in files]
    assert sel.groupby('id_OD_zonal')['seleccionada'].sum().eq(1).all()
    assert not rel['se_suman'].any()
    comparisons, details = [], []
    for gid, group in sel.groupby('id_OD_zonal', sort=True):
        for (_, x), (_, y) in itertools.combinations(group.iterrows(), 2):
            dx = dia[(dia.id_OD_zonal == gid) & (dia.control == x.control) &
                     (dia.sentido_control == x.sentido_control)]
            dy = dia[(dia.id_OD_zonal == gid) & (dia.control == y.control) &
                     (dia.sentido_control == y.sentido_control)]
            paired = dx.merge(dy, on=['id_OD_zonal', 'fecha'], suffixes=('_1', '_2'))
            full = bool(x.cubre_trayectorias_todos_OD_detallados and
                        y.cubre_trayectorias_todos_OD_detallados)
            item = dict(id_OD_zonal=gid, control_1=x.control,
                        sentido_1=x.sentido_control, control_2=y.control,
                        sentido_2=y.sentido_control,
                        cobertura_completa_ambas=full,
                        fechas_validas_1=x.fechas_validas,
                        fechas_validas_2=y.fechas_validas,
                        fechas_coincidentes='|'.join(sorted(paired.fecha)),
                        jornadas_comparables=len(paired) if full else 0,
                        comparabilidad=('Fecha y cobertura geometrica compatibles; muestras independientes no enlazadas'
                                       if full and len(paired) else
                                       'No valida equivalencia de poblacion: cobertura parcial' if not full else
                                       'Sin fecha coincidente; contraste descriptivo de jornadas distintas'),
                        se_suman=False)
            if len(paired):
                for _, p in paired.iterrows():
                    rec = dict(item, fecha=p.fecha,
                               entrevistas_1=int(p.n_entrevistas_corredor_aceptadas_1),
                               entrevistas_2=int(p.n_entrevistas_corredor_aceptadas_2),
                               N_1=int(p.N_estrato_original_1), N_2=int(p.N_estrato_original_2),
                               F_1=p.aforo_clase_12h_1, F_2=p.aforo_clase_12h_2,
                               Q_1=p.flujo_corredor_12h_1, Q_2=p.flujo_corredor_12h_2,
                               diferencia_Q_2_menos_1=p.flujo_corredor_12h_2-p.flujo_corredor_12h_1,
                               razon_Q_2_Q_1=(p.flujo_corredor_12h_2/p.flujo_corredor_12h_1
                                              if p.flujo_corredor_12h_1 else None))
                    comparisons.append(rec)
                    # Descomposicion en la misma fecha y mismos extremos nominales.
                    # Se retienen los ceros muestrales; no indican ausencia de demanda.
                    if full:
                        zo, zd, camp, seg = gid.split('|')
                        aa = aud[(aud.zona_origen == float(zo)) &
                                 (aud.zona_destino == float(zd)) &
                                 (aud.campana == camp) & (aud.segmento == seg) &
                                 aud.aceptada_corredor_auxiliar & (aud.fecha == p.fecha)]
                        for (o, d), _ in aa.groupby(['origen_detallado', 'destino_detallado']):
                            row = dict(id_OD_zonal=gid, fecha=p.fecha, origen=o, destino=d,
                                       control_1=x.control, control_2=y.control,
                                       interpretacion='Contraste descriptivo de muestras; cero muestral no es ausencia poblacional')
                            for i, c, sense, fac in [(1,x.control,x.sentido_control,p.factor_1),
                                                     (2,y.control,y.sentido_control,p.factor_2)]:
                                n = len(aa[(aa.origen_detallado == o) & (aa.destino_detallado == d) &
                                           (aa.control == c) & (aa.sentido_observado == sense) &
                                           aa.factor_expansion.notna()])
                                row[f'n_{i}'] = n
                                row[f'Q_{i}'] = n*fac
                            details.append(row)
            else:
                comparisons.append(item)
    comp = pd.DataFrame(comparisons)
    comp.to_csv(salida / 'comparaciones_pantallas.csv', index=False)
    pd.DataFrame(details).to_csv(salida / 'comparaciones_detalladas_compatibles.csv', index=False)
    sel.to_csv(salida / 'seleccion_reutilizada.csv', index=False)
    rel.to_csv(salida / 'relaciones_reutilizadas.csv', index=False)
    summary = dict(candidatos=len(sel), pantallas_elegidas=int(sel.seleccionada.sum()),
                   pares_solapados=len(rel), pares_en_serie=int(rel.relacion.str.startswith('En serie').sum()),
                   independencia_ramas_paralelas_demostrada=0,
                   contrastes_misma_fecha=int(comp.fecha.notna().sum()),
                   contrastes_misma_fecha_y_cobertura=int(((comp.jornadas_comparables>0) & comp.fecha.notna()).sum()),
                   seleccion_cubre_trayectorias_modeladas=bool(sel[sel.seleccionada].cubre_trayectorias_todos_OD_detallados.all()),
                   seleccion_usa_flujo_mayor_como_criterio=False,
                   recomendacion='Reutilizar una pantalla por OD ordenado, campana y clase; preservar contrastes. '
                   'No declarar consistencia general entre controles: solo dos pares comparten fecha y cobertura, '
                   'y uno presenta Q=3.73 frente a25.07 vehiculos/12h. Sin aforos repetidos/muestreo certificado '
                   'no se determina cual estima mejor la poblacion; no promediar ni sumar para resolver diferencia.',
                   incertidumbre='La geometria procede de rutas de referencia ya auditadas; no es observacion de itinerarios. '
                   'La correspondencia de sentidos se respeta por campana; E1003 usa distinta codificacion verano/otono.',
                   sin_nuevas_rutas=True,
                   fuentes={str(cache / 'csv' / (f+'.csv')): hashlib.sha256((cache/'csv'/(f+'.csv')).read_bytes()).hexdigest() for f in files})
    (salida / 'resumen_pantallas.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    return summary

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cache', required=True)
    p.add_argument('--salida', required=True)
    args=p.parse_args()
    print(json.dumps(ejecutar(args.cache,args.salida),ensure_ascii=False,indent=2))
