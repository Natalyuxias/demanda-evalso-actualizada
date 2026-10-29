"""Corrección mínima de atribución: reutiliza resultados ya calculados deEtapa6.
DesdeAnexos: python etapa6_cierre_incremental_20261029/codigo/corregir.py
No recalcula costos, crecimiento, elasticidades ni captación. pandas,numpy,openpyxl.
"""
from pathlib import Path
import argparse,hashlib,json
import pandas as pd
import numpy as np
P=Path(__file__).resolve().parent.parent;R=P.parent
ap=argparse.ArgumentParser();ap.add_argument('--entrada',type=Path,default=R/'etapa6_demanda_inducida_20261029/resultados/demanda_inducida_etapa6.xlsx');ap.add_argument('--salida',type=Path,default=P/'resultados');args=ap.parse_args();O=args.salida;O.mkdir(parents=True,exist_ok=True)
source_hash=hashlib.sha256(args.entrada.read_bytes()).hexdigest()
with pd.ExcelFile(args.entrada) as w:
 original=pd.read_excel(w,'Calculo por conexion');elastic=pd.read_excel(w,'Elasticidades');foreign=pd.read_excel(w,'Indicadores extranjeros');previous_summary=pd.read_excel(w,'Comparacion elasticidades')
d=original.copy()
# Mantener explícitamente el cálculo anterior como referencia; cambiar únicamente lo autorizado.
changed=['D_inducida','D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_inducida_sin_asignar','D_nuevo_total_aporte_estimado','D_tierra_total_aporte_estimado','D_actual_total_aporte_estimado','D_inducida_con_mejora_min_SBO','D_inducida_sin_mejora_min_SBO','D_nuevo_inducido_con_mejora_min_SBO','estado_induccion']
d=d.rename(columns={c:'anterior_'+c for c in changed})
d['D_inducida']=d.D_inducida_incremento_minimo_proyecto
# Exactamente el procedimiento vectorizado guardado en el script deEtapa6.
d['D_inducida_nuevo']=d.D_inducida*d.P_nuevo
d['D_inducida_tierra']=d.D_inducida*d.P_tierra
d['D_inducida_actual']=d.D_inducida*d.P_actual
d['D_inducida_sin_asignar']=d.D_inducida.where(~d.participaciones_validas,0.).where(d.D_inducida.notna())
zero=d.D_inducida.eq(0)
d.loc[zero,['D_inducida_nuevo','D_inducida_tierra','D_inducida_actual','D_inducida_sin_asignar']]=0.
for alt,existing in [('nuevo','D_desviada_nuevo_existente'),('tierra','D_tierra_CP_existente'),('actual','D_actual_CP_existente')]:
 d['D_'+alt+'_total_aporte_estimado']=d[existing].fillna(0)+d['D_inducida_'+alt].fillna(0)
 d.loc[d[existing].isna()&d['D_inducida_'+alt].isna(),'D_'+alt+'_total_aporte_estimado']=np.nan
d['estado_induccion_corregida']=np.select([d.D_inducida.isna(),d.D_inducida.eq(0),~d.participaciones_validas],['Fuera soporte de inducción: conservar faltante','Sin incremento atribuible al proyecto','Inducción incremental sin participaciones válidas: sin asignar'],default='Inducción incremental distribuida con participaciones guardadas')
d['diferencia_inducida_vs_preliminar']=d.D_inducida-d.anterior_D_inducida
d['diferencia_total_nuevo_vs_preliminar']=d.D_nuevo_total_aporte_estimado-d.anterior_D_nuevo_total_aporte_estimado
keys=['version_referencia','version','fuente','id_flujo','origen','destino','zona_origen','zona_destino','temporada','segmento','unidad','componente','subtipo','anio','escenario_elasticidad']
metrics=['Q_referencia','D_desviada_nuevo_existente','D_desviada_tierra_existente','D_desviada_actual_existente','D_tierra_CP_existente','D_actual_CP_existente','D_existente_residual','D_base_sin_soporte_induccion','D_inducida','D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_inducida_sin_asignar','D_nuevo_total_aporte_estimado','D_tierra_total_aporte_estimado','D_actual_total_aporte_estimado','anterior_D_inducida','anterior_D_inducida_nuevo','anterior_D_nuevo_total_aporte_estimado','diferencia_inducida_vs_preliminar','diferencia_total_nuevo_vs_preliminar']
od=d.groupby(keys,dropna=False)[metrics].sum(min_count=1).reset_index()
summary=od.groupby(['version_referencia','escenario_elasticidad','anio','segmento','unidad'],dropna=False)[metrics].sum(min_count=1).reset_index()
notes=pd.DataFrame([
 {'decision':'Inducción principal','detalle':'Se adopta sin recalcular D_inducida_incremento_minimo_proyecto deEtapa6 anterior. La inducción bruta anterior permanece como referencia.'},
 {'decision':'Distribución idéntica','detalle':'Inducciónincremental×P_tierra/P_actual/P_nuevo guardadas. Sin cuotas válidas, permanece sin asignar; inducción0se asigna como0. No nuevasfunciones de elección ni parámetros.'},
 {'decision':'Existente y desviada','detalle':'No se modifica ninguna cantidad existente ni su captación. Tampoco cambian costos, crecimiento, buses o probabilidades.'},
 {'decision':'Sensibilidades','detalle':'Menor/central/mayor conservan exactamente las elasticidades y costos anteriores. Las cantidades incrementales se recuperan ya calculadas para cada escenario, no se vuelven a estimar.'},
 {'decision':'A/B y unidades','detalle':'ARISTOA/Bindependientes, Bprincipal. No sumar versiones,VPconVLni peatonesconvehículos. Las subcohortesvirtuales comunales mantienen sus pesos y agregación deEtapa5.'},
 {'decision':'Totales y faltantes','detalle':'Totalnuevo=existente desviada+inducida incremental asignada. Los totales son aportes estimables del mercado cubierto, no mercado terrestre total. Los residuales y la inducción no estimable conservan sus faltantes.'},
 {'decision':'Extranjeros','detalle':'Se conservan tablas agregadas e indicadores originales disponibles; no se asigna nacionalidad/residencia a los nuevos viajes ni aODsin correspondencia.'},
 {'decision':'Cierre','detalle':'Esta corrección sustituye la inducción principal preliminar enestaentrega. Los archivosanteriores no se sobrescriben. No incluye capacidad, costosoperacionales o beneficios sociales.'},
 {'decision':'Reproducción','detalle':'DesdeAnexos:python etapa6_cierre_incremental_20261029/codigo/corregir.py. Opcionales --entrada libro_anterior.xlsx --salida carpeta_nueva. No ejecutarEtapas1–5.'}
])
# Comprobaciones mínimas del cambio, sin auditoría de fuentes originales.
checks=[]
checks.append({'validacion':'Inducciónprincipal igual a columna incremental ya calculada','cumple':np.allclose(d.D_inducida,original.D_inducida_incremento_minimo_proyecto,equal_nan=True)})
immutable=['Q_referencia','D_desviada_nuevo_existente','D_desviada_tierra_existente','D_desviada_actual_existente','D_tierra_CP_existente','D_actual_CP_existente','P_nuevo','P_tierra','P_actual','CG_SBO','CG_CP','epsilon_CG','factor_crecimiento_existente']
checks.append({'validacion':'Existente, desviada, costos, probabilidades y elasticidades intactos','cumple':all(np.allclose(d[c],original[c],equal_nan=True) for c in immutable)})
known=d.D_inducida.notna()
checks.append({'validacion':'Conservación en reparto de inducción incremental','cumple':np.allclose(d.loc[known,['D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_inducida_sin_asignar']].fillna(0).sum(axis=1),d.loc[known,'D_inducida'])})
checks.append({'validacion':'Asignaciónalnuevo coincide con diagnóstico anterior','cumple':np.allclose(d.D_inducida_nuevo,original.D_inducida_incremental_nuevo,equal_nan=True)})
checks.append({'validacion':'Totalnuevo usa existente+incremental asignada','cumple':np.allclose(d.loc[known,'D_nuevo_total_aporte_estimado'],d.loc[known,'D_desviada_nuevo_existente'].fillna(0)+d.loc[known,'D_inducida_nuevo'].fillna(0),equal_nan=True)})
wide=d.pivot(index='id_base',columns='escenario_elasticidad',values='D_inducida')
checks.append({'validacion':'Mayor magnitud de elasticidad no reduce inducción','cumple':((wide.menor_induccion<=wide.central+1e-10)&(wide.central<=wide.mayor_induccion+1e-10)).where(wide.notna().all(axis=1),True).all()})
checks.append({'validacion':'Losresiduales mantienen inducción faltante','cumple':d.D_inducida.isna().equals(original.D_inducida_incremento_minimo_proyecto.isna())})
checks.append({'validacion':'Mismos registros y escenarios','cumple':len(d)==len(original) and d[['id_base','escenario_elasticidad']].equals(original[['id_base','escenario_elasticidad']])})
checks.append({'validacion':'Entrega anterior intacta','cumple':hashlib.sha256(args.entrada.read_bytes()).hexdigest()==source_hash})
checks=pd.DataFrame(checks);assert checks.cumple.all(),checks[~checks.cumple].to_dict('records')
trace=pd.DataFrame([{'archivo':str(args.entrada),'sha256':source_hash,'hojas':'Calculo por conexion,Elasticidades,Indicadores extranjeros,Comparacion elasticidades'}])
sheets={'Resumen corregido':summary,'Comparacion elasticidades':summary,'Demanda por OD':od,'Distribucion por conexion':d,'Elasticidades conservadas':elastic,'Supuestos y cierre':notes,'Indicadores extranjeros':foreign,'Resumen anterior referencia':previous_summary,'Validaciones':checks,'Trazabilidad':trace}
with pd.ExcelWriter(O/'demanda_inducida_incremental_final.xlsx',engine='openpyxl') as w:
 for name,df in sheets.items():
  df.to_excel(w,sheet_name=name,index=False);ws=w.book[name];ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions
  for col in ws.columns:
   ws.column_dimensions[col[0].column_letter].width=min(48,max(14,len(str(col[0].value or ''))+2))
   for cell in col[1:]:
    if isinstance(cell.value,float):cell.number_format='#,##0.0000'
main=summary[(summary.version_referencia=='B')&(summary.escenario_elasticidad=='central')&summary.segmento.isin(['VL','VP','CAM','PEATON'])]
sens=summary[(summary.version_referencia=='B')&(summary.anio==2026)&summary.segmento.isin(['VL','VP','CAM','PEATON'])]
page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Cierre demanda inducida incremental</title><style>body{{font:16px system-ui;max-width:1250px;margin:32px auto;padding:0 20px;color:#17374a}}p{{line-height:1.5}}table{{border-collapse:collapse;display:block;overflow:auto;font-size:12px}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#eaf2f7}}</style><h1>Cierre de la Etapa 6 · Inducción incremental</h1>
<p>Se adopta como demanda inducida principal la columna <code>D_inducida_incremento_minimo_proyecto</code> ya calculada. La distribución utiliza exactamente las participaciones guardadas de la Etapa 5. No se modifican demanda existente, captación, costos, buses, crecimiento ni elasticidades. Los cálculos preliminares quedan como referencia.</p>
<h2>Resultados centrales — referencia ARISTO B</h2>{main[['anio','segmento','unidad','D_desviada_nuevo_existente','D_inducida','D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_nuevo_total_aporte_estimado']].to_html(index=False,border=0,na_rep='Sin estimación',float_format=lambda v:f'{v:,.3f}')}
<h2>Comparación de elasticidades en 2026</h2>{sens[['escenario_elasticidad','segmento','D_inducida','D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_nuevo_total_aporte_estimado']].to_html(index=False,border=0,na_rep='Sin estimación',float_format=lambda v:f'{v:,.3f}')}
<h2>Comparación con la entrega anterior</h2>{main[['anio','segmento','anterior_D_inducida','D_inducida','anterior_D_nuevo_total_aporte_estimado','D_nuevo_total_aporte_estimado','diferencia_total_nuevo_vs_preliminar']].to_html(index=False,border=0,na_rep='Sin estimación',float_format=lambda v:f'{v:,.3f}')}
<p>La diferencia corresponde únicamente a retirar la inducción preliminar que no representaba un incremento adicional del mínimo de costo causado por el proyecto. La inducción incremental no se asigna toda al nuevo cruce: se multiplica por las mismas cuotas de tierra, barcaza actual y nuevo servicio. Las cantidades fuera de soporte permanecen faltantes.</p>
<h2>Supuestos y cierre</h2><p>Se mantienen los tres valores de elasticidad por segmento: −0,254/−0,354/−0,454 para VL, VP y peatones; −0,006/−0,106/−0,206 para camiones. No se confunden con elasticidades de crecimiento PIB. Los totales son aportes del mercado cubierto y de los supuestos ya documentados, no una matriz terrestre completa. VP conserva su unidad heterogénea; los peatones no son todos los pasajeros. Las versiones A/B no se suman.</p>
<p>Con esta corrección queda cerrada la estimación de demanda para continuar con capacidad operacional. No se calcula capacidad ni beneficios sociales en esta ejecución.</p>
<h2>Validaciones y reproducción</h2>{checks.to_html(index=False,border=0)}<p><a href="demanda_inducida_incremental_final.xlsx">Descargar Excel</a>. Desde Anexos: <code>python etapa6_cierre_incremental_20261029/codigo/corregir.py</code>. Fuente anterior conservada y verificada por huella.</p></html>'''
(O/'informe_cierre_demanda.html').write_text(page,encoding='utf-8')
print(json.dumps({'validaciones':len(checks),'central2026':main[main.anio.eq(2026)][['segmento','D_desviada_nuevo_existente','D_inducida','D_inducida_nuevo','D_nuevo_total_aporte_estimado']].to_dict('records')},ensure_ascii=False))
