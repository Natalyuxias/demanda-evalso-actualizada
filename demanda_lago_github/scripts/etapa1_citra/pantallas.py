"""Pantallas alternativas sin suma de cordones; matrices de corredor auxiliares."""
import collections,itertools,math,hashlib

def build(audit,obs,strata,weights,net):
 valid=[a for a in audit if a['aceptada_corredor_auxiliar']];byid={r['id_encuesta']:r for r in obs};index={tuple(r[k] for k in ['campana','fecha','control','sentido','segmento']):r for r in strata}
 groups=collections.defaultdict(list)
 for a in valid:groups[(a['zona_origen'],a['zona_destino'],a['campana'],a['segmento'])].append(a)
 choices=[];pairs=[];dates=[];detail=[];zonal=[];record_selection={a['id_encuesta']:False for a in audit}
 for key,aa in sorted(groups.items()):
  zo,zd,camp,seg=key;gid='|'.join(map(str,key));fine=collections.defaultdict(list)
  for a in aa:fine[a['origen_detallado'],a['destino_detallado']].append(a)
  candidates=sorted({(a['control'],a['sentido_observado']) for a in aa})
  cc=[]
  for ctrl,sense in candidates:
   samples=[a for a in aa if a['control']==ctrl and a['sentido_observado']==sense];ss=[s for s in strata if (s['campana'],s['control'],s['sentido'],s['segmento'])==(camp,ctrl,sense,seg)]
   vv=[s for s in ss if s['factor_expansion'] is not None];planned=[s for s in ss if s['filas_aforo']>0 or s['entrevistas_estrato']>0];supported=sum(weights[a['id_encuesta']]['factor'] is not None for a in samples)
   compatible,mandatory=net.screen_geometry([a['id_encuesta'] for a in aa],ctrl,sense)
   physicalcoverage=all(compatible);mandatorycoverage=all(mandatory)
   priority={'E0701':0,'E1003':1,'E0702':2}.get(ctrl,100)
   # Calidad/exposición y cobertura, nunca mayor muestra o mayor flujo OD.
   rank=(not bool(vv and supported),not physicalcoverage,not mandatorycoverage,-len(vv)/len(planned) if planned else 0,-len(vv),priority,ctrl,sense)
   rec=dict(id_OD_zonal=gid,zona_origen=zo,zona_destino=zd,campana=camp,segmento=seg,control=ctrl,sentido_control=sense,entrevistas_compatibles_OD=len(samples),entrevistas_OD_con_factor=supported,estratos_validos=len(vv),estratos_presentes=len(planned),cubre_trayectorias_todos_OD_detallados=physicalcoverage,n_trayectorias_cubiertas=sum(compatible),n_trayectorias_contraste=len(compatible),obligatoria_en_red_chilena_modelada=mandatorycoverage,criterio='Factor compatible; cobertura geométrica conjunta; corte obligatorio; fracción/jornadas válidas; prioridad fija E0701,E1003,E0702. No maximiza entrevistas ni flujo OD.',fechas_validas='|'.join(sorted(s['fecha'] for s in vv)),seleccionada=False,uso='Alternativa; no sumar con otra pantalla del mismo OD',rango_decision=repr(rank),flujo_corredor_auxiliar_12h=None,cobertura='Solo fracción de ruta identificable del corredor; no mercado total Chile')
   cc.append((rank,rec,samples,vv));choices.append(rec)
  rank,best,selected,vv=min(cc,key=lambda x:x[0]);best['seleccionada']=True;best['uso']='Seleccionada para corredor auxiliar, no para demanda Chile completa'
  ctrl,sense=best['control'],best['sentido_control'];chosenids={a['id_encuesta'] for a in selected}
  for a in selected:record_selection[a['id_encuesta']]=True
  # Estimaciones alternativas de todos los cordones, por fecha y clase.
  for rank,rec,samples,vs in cc:
   nperiod=len(vs);wtotal=0;has=False
   for s in vs:
    rr=[a for a in samples if byid[a['id_encuesta']]['fecha']==s['fecha'] and weights[a['id_encuesta']]['factor'] is not None];n=len(rr);q=n*s['factor_expansion'];wtotal+=q;has=has or n>0
    dates.append(dict(id_OD_zonal=gid,zona_origen=zo,zona_destino=zd,campana=camp,segmento=seg,control=rec['control'],sentido_control=rec['sentido_control'],fecha=s['fecha'],seleccionada=rec['seleccionada'],n_entrevistas_corredor_aceptadas=n,N_estrato_original=s['N_entrevistas_originales_ventana'],aforo_clase_12h=s['aforo_vehiculos_12h'],factor=s['factor_expansion'],flujo_corredor_12h=q,estado='Cero muestral del estrato; no ausencia de demanda' if n==0 else 'Expandido proporcional condicional del corredor observado',id_estrato=s['id_estrato'],unidad='vehículos/12h del día indicado; NO demanda Chile completa'))
   rec['flujo_corredor_auxiliar_12h']=wtotal/nperiod if nperiod and has else None
  for (c1,s1),(c2,s2) in itertools.combinations(candidates,2):
   same=any(net.landpaths.get(a['id_encuesta']) and net.keynodes[c1] in net.landpaths[a['id_encuesta']] and net.keynodes[c2] in net.landpaths[a['id_encuesta']] for a in aa)
   relation='En serie para al menos un recorrido OD: riesgo de contar el mismo viaje' if same else 'Ramas o cobertura distinta; independencia no demostrada'
   pairs.append(dict(id_OD_zonal=gid,control_1=c1,sentido_1=s1,control_2=c2,sentido_2=s2,relacion=relation,se_suman=False,decision='Una sola pantalla; sin suma incluso si la red permite ramas no certificadas.'))
  nperiod=len(vv);qknown=0;hasq=False;nf=0;nd_unknown=0
  for (o,d),fa in sorted(fine.items()):
   selected_fine=[a for a in fa if a['id_encuesta'] in chosenids];weighted=[a for a in selected_fine if weights[a['id_encuesta']]['factor'] is not None]
   q=sum(weights[a['id_encuesta']]['factor'] for a in weighted)/nperiod if weighted and nperiod else None
   if q is not None:qknown+=q;hasq=True
   else:nd_unknown+=1
   nf+=len(weighted)
   r=dict(id_OD_zonal=gid,origen=o,destino=d,zona_origen=zo,zona_destino=zd,comuna_origen=fa[0]['comuna_origen'],comuna_destino=fa[0]['comuna_destino'],CUT_origen=fa[0]['CUT_origen'],CUT_destino=fa[0]['CUT_destino'],sentido_OD=o+' → '+d,campana=camp,segmento=seg,control=ctrl,sentido_control=sense,fechas_representadas=best['fechas_validas'],jornadas_validas=nperiod,entrevistas_cohorte_en_todos_controles=len(fa),entrevistas_pantalla_elegida=len(selected_fine),entrevistas_con_factor=len(weighted),flujo_corredor_auxiliar_12h=q,estado='Estimación parcial de fracción identificable, ruta total desconocida' if q is not None else 'Sin estimación: muestra/factor no compatible en pantalla elegida; no es cero',cobertura_espacial='Pantalla cubre trayectorias detalladas modeladas' if best['cubre_trayectorias_todos_OD_detallados'] else 'Pantalla parcial; no cubre todo el OD zonal',cobertura_temporal='Media de fechas válidas de esta pantalla y sentido,08–20; no24h, campaña completa ni año',unidad='vehículos de la clase / ventana de12h',ruta='Corredor chileno observado; itinerario íntegro por Chile no identificado')
   detail.append(r)
  zonal.append(dict(id_OD_zonal=gid,zona_origen=zo,zona_destino=zd,comuna_origen=aa[0]['comuna_origen'],comuna_destino=aa[0]['comuna_destino'],campana=camp,segmento=seg,sentido_OD=f'{zo} → {zd}',control=ctrl,sentido_control=sense,fechas_representadas=best['fechas_validas'],jornadas_validas=nperiod,entrevistas_revalidadas_corredor=len(aa),entrevistas_pantalla=len(selected),entrevistas_con_factor=nf,OD_detallados=len(fine),OD_detallados_sin_flujo=nd_unknown,flujo_corredor_auxiliar_12h=qknown if hasq else None,estado='Suma de subOD identificados en una MISMA pantalla y período; total país/ruta no identificado',cobertura='Parcial: fracción identificable del corredor en fechas válidas',unidad='vehículos/12h; no24h ni demanda anual'))
 return detail,zonal,choices,pairs,dates,record_selection
