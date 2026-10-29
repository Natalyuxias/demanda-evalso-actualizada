"""Integra escenarios anuales desde entregas aprobadas; no ejecuta modelos previos.

ARISTO: distribución de F conocido con versiones A/B; CITRA: jamás recibe OD de
ARISTO ni magnitud del mercado no observado. Años normalizados, no tráfico anual
efectivamente medido. Las dos vistas de privados no son aditivas.
"""
from pathlib import Path
import argparse
import calendar
import hashlib
import json
import math
import shutil
import time

import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill

FKEY = ['campana', 'sentido_cruce', 'segmento']
SCENARIOS = ['conservador', 'central', 'alto']
OUTPUT_SEASON = {1:'Verano',2:'Verano',3:'Otoño',4:'Otoño',5:'Otoño',6:'Invierno',7:'Invierno',8:'Invierno',9:'Primavera',10:'Primavera',11:'Primavera',12:'Verano'}
PRIVATE = ['VL','MOTO','BICI','VP']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frame_records(d):
    return d.astype(object).where(pd.notna(d), None).to_dict('records')


def workbook(path, sheets):
    w = Workbook(write_only=True)
    for name, frame in sheets.items():
        s = w.create_sheet(name); s.freeze_panes = 'B2'; cells = []
        for i, col in enumerate(frame.columns, 1):
            s.column_dimensions[__import__('openpyxl').utils.get_column_letter(i)].width = min(54, max(17, len(col)+2))
            c=WriteOnlyCell(s,col); c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='225D65'); cells.append(c)
        s.append(cells)
        for row in frame_records(frame):
            vals=[]
            for v in row.values():
                c=WriteOnlyCell(s,v)
                if isinstance(v,str):
                    assert len(v)<=32767; c.data_type='s'
                vals.append(c)
            s.append(vals)
        s.auto_filter.ref=f'A1:{__import__("openpyxl").utils.get_column_letter(len(frame.columns))}{len(frame)+1}'
    w.save(path)


def corrected_factors(factors, ratios, vp):
    """Sensibilidad externa I/P vial aplicada a mayo; NO patrón ferry observado."""
    f=factors.copy()
    chosen=ratios[ratios.anio.eq(2024)&ratios.PC.eq(64)&ratios.rama.eq(1)].set_index('segmento')
    rcam=float(chosen.loc['CAM','ratio_Invierno_Primavera'])
    rvp=float(vp[vp.PC.eq(64)&vp.rama.eq(1)].iloc[0].ratio_Invierno_Primavera)
    f['ratio_invierno_sensibilidad_externa']=1.
    winter=f.mes.isin([6,7,8])&f.escenario.eq('conservador')
    f.loc[winter&f.segmento.eq('CAM'),'ratio_invierno_sensibilidad_externa']=rcam
    f.loc[winter&f.segmento.isin(['VP','PRIVADOS_COMPATIBLES']),'ratio_invierno_sensibilidad_externa']=rvp
    f['coef_mes_final']=f.coef_mes_desde_flujo_fecha*f.ratio_invierno_sensibilidad_externa
    f['justificacion_proxy_invierno']='Normal de mayo como proxy; sin reducción adicional identificada'
    mask=winter&f.segmento.isin(['CAM','VP','PRIVADOS_COMPATIBLES'])
    f.loc[mask,'justificacion_proxy_invierno']='Stress externo PNC2024 PC64 rama1 Invierno/Primavera, aplicado sobre mayo. NO ratio invierno/otoño lacustre medido; sin extrapolación de OD terrestre.'
    f['temporada_destino']=f.mes.map(OUTPUT_SEASON)
    return f


def add_private_view(d):
    d=d.copy(); d['vista']='clases_originales'; d['segmento_original']=d.segmento
    broad=d[d.segmento.isin(PRIVATE)].copy()
    broad['segmento']='PRIVADOS_COMPATIBLES'; broad['vista']='privados_compatibles_no_aditiva'
    broad['unidad']='unidades privadas agregadas (VL+moto+bicicleta); no VL estricto'
    return pd.concat([d,broad],ignore_index=True)


def apply_lake(d, factors):
    x=add_private_view(d).merge(factors,on=FKEY,how='left',validate='many_to_many',suffixes=('','_factor'))
    assert x.mes.notna().all()
    x['aporte_mes']=x.flujo*x.coef_mes_final
    x['campana_fuente']=x.campana
    x['naturaleza_anual']='Estimación temporal condicionada; ninguna cifra anual fue observada directamente'
    x['fuente_imputacion_OD']=x.componente.eq('imputado').map({True:'ARISTO misma campaña/sentido/clase',False:'No imputado OD'})
    x['sumable_con_otras_vistas']=False
    return x


def annual_lake(months, factors):
    keys=['version','escenario','vista','sentido_cruce','segmento','unidad','origen','destino','zona_origen','zona_destino','componente','subtipo']
    annual=months.groupby(keys,dropna=False).agg(aporte_anual_en_meses_con_perfil=('aporte_mes',lambda s:s.sum(min_count=1)),
           meses_OD_con_aporte=('mes','nunique'),campanas_del_componente=('campana',lambda s:'|'.join(sorted(set(s)))),
           meses_del_componente=('mes',lambda s:'|'.join(map(str,sorted(set(s)))))).reset_index()
    cover=factors.groupby(['escenario','sentido_cruce','segmento']).mes.nunique().rename('meses_cubiertos_clase').reset_index()
    annual=annual.merge(cover,on=['escenario','sentido_cruce','segmento'],validate='many_to_one')
    annual['demanda_anual_operacional_componente']=annual.aporte_anual_en_meses_con_perfil.where(annual.meses_cubiertos_clase.eq(12))
    annual['estado']='Aporte OD anual condicionado al perfil; otros OD sin asignar se conservan en residual. No es censo del OD.'
    annual.loc[annual.meses_cubiertos_clase.lt(12),'estado']='Anual estricto no estimable por falta de clase compatible en meses; aporte parcial separado'
    annual['anio']=2026
    annual['fuente']='ARISTO'; annual['bloque']='lacustre_actual'; annual['exposicion']='Operación ordinaria programada anual normalizada, cumplimiento asumido, no bitácora efectiva'
    return annual


def service_balance(months):
    keys=['version','escenario','vista','sentido_cruce','segmento','mes']
    monthly=months.groupby(keys,dropna=False).aporte_mes.sum(min_count=1).rename('flujo_fisico_mes').reset_index()
    parts=months.pivot_table(index=keys,columns='componente',values='aporte_mes',aggfunc=lambda s:s.sum(min_count=1),dropna=True).reset_index()
    for c in ['observado_asignado','imputado','residual']:
        if c not in parts:parts[c]=0.
    monthly=monthly.merge(parts,on=keys,how='left',validate='one_to_one')
    for c in ['observado_asignado','imputado','residual']:
        monthly[c]=monthly[c].fillna(0).where(monthly.flujo_fisico_mes.notna())
    annual=monthly.groupby(keys[:-1]).agg(flujo_fisico_meses_cubiertos=('flujo_fisico_mes',lambda s:s.sum(min_count=1)),
            meses_con_valor=('flujo_fisico_mes','count'),meses_representados=('mes','nunique'),
            observado_OD_anualizado=('observado_asignado',lambda s:s.sum(min_count=1)),
            imputado_OD_anualizado=('imputado',lambda s:s.sum(min_count=1)),
            residual_anualizado=('residual',lambda s:s.sum(min_count=1))).reset_index()
    annual['flujo_fisico_anual']=annual.flujo_fisico_meses_cubiertos.where(annual.meses_con_valor.eq(12))
    annual['proporcion_OD_imputada']=annual.imputado_OD_anualizado/annual.flujo_fisico_anual.where(annual.flujo_fisico_anual.ne(0))
    annual['proporcion_residual']=annual.residual_anualizado/annual.flujo_fisico_anual.where(annual.flujo_fisico_anual.ne(0))
    annual['advertencia']='No sumar vistas ni clases de personas/vehículos. Todos los valores anuales son escenarios, no conteos anuales.'
    return monthly,annual


def monthly_foreign(original, factors, balances):
    m=original.merge(factors,on=FKEY,validate='many_to_many',suffixes=('','_factor'))
    m['aporte_mes_indicador']=m.flujo_asignado_exposicion_medida*m.coef_mes_final
    keys=['escenario','sentido_cruce','segmento','indicador','categoria_indicador']
    a=m.groupby(keys,dropna=False).agg(aporte_indicador_meses_cubiertos=('aporte_mes_indicador',lambda s:s.sum(min_count=1)),
               meses_con_indicador=('mes','nunique')).reset_index()
    b=balances[balances.version.eq('A')&balances.vista.eq('clases_originales')][['escenario','sentido_cruce','segmento','flujo_fisico_anual','flujo_fisico_meses_cubiertos']]
    a=a.merge(b,on=['escenario','sentido_cruce','segmento'],validate='many_to_one')
    a['fraccion_asignada_sobre_total_anual_clase']=a.aporte_indicador_meses_cubiertos/a.flujo_fisico_anual.where(a.flujo_fisico_anual.ne(0))
    a['interpretacion']='Fracción asociada al indicador por perfil conocido; no total de extranjeros, residencia ni nacionalidad de ocupantes. Parte sin caracterización permanece desconocida.'
    a['imputacion_caracteristicas_B']=False
    coverage=a.groupby(['escenario','sentido_cruce','segmento','indicador']).agg(total_caracterizado_perfil=('aporte_indicador_meses_cubiertos',lambda s:s.sum(min_count=1)),
             fisico_anual=('flujo_fisico_anual','first')).reset_index()
    coverage['sin_caracterizacion_anual']=coverage.fisico_anual-coverage.total_caracterizado_perfil
    coverage['nota']='Incluye falta de muestra de la clase en fechas, además de estados desconocidos explícitos. No se imputan nacionalidad o patente desde donantes OD.'
    return m,a,coverage


def unified(la, cz):
    l=la.rename(columns={'version':'version_OD','aporte_anual_en_meses_con_perfil':'aporte_parcial','demanda_anual_operacional_componente':'demanda_anual_operacional'}).copy()
    l['nivel']='zonas'; l['demanda_anual_ventana12h']=None; l['demanda_anual24h']=None; l['permite_total_conjunto']=False
    c=cz.copy(); c['escenario']=c.escenario.str.lower(); c['fuente']='CITRA'; c['bloque']='terrestre_corredor'; c['version_OD']='no_aplica'
    c['vista']='clases_originales'; c['componente']='corredor_estimado_sin_imputacion_OD'; c['subtipo']='cobertura_parcial_del_mercado'
    c['origen']=c.comuna_origen; c['destino']=c.comuna_destino; c['sentido_cruce']='No aplica; ver pantallas y sentidos originales'
    c['aporte_parcial']=c.aporte_parcial_meses_con_perfil_12h; c['demanda_anual_operacional']=None
    c['unidad']='vehículos de la clase / año en ventana08–20, no24h'; c['exposicion']='12 horas; perfil de días muestreados y proxies temporales'
    c['permite_total_conjunto']=False; c['fuente_imputacion_OD']='Ninguna: ARISTO no completa CITRA'
    wanted=['fuente','bloque','version_OD','escenario','vista','nivel','zona_origen','zona_destino','origen','destino','sentido_cruce','segmento','unidad','componente','subtipo','aporte_parcial','demanda_anual_operacional','demanda_anual_ventana12h','demanda_anual24h','exposicion','estado','permite_total_conjunto']
    for d in [l,c]:
        for col in wanted:
            if col not in d:d[col]=None
    return pd.concat([l[wanted],c[wanted]],ignore_index=True)


def wide_reference(la, cz):
    keys=['escenario','zona_origen','zona_destino','segmento']
    l=la[la.vista.eq('clases_originales')&la.zona_origen.notna()&la.zona_destino.notna()].copy()
    l=l.groupby(['version']+keys,dropna=False).agg(lacustre_anual_asignado=('demanda_anual_operacional_componente',lambda s:s.sum(min_count=1)),
              lacustre_aporte_parcial=('aporte_anual_en_meses_con_perfil',lambda s:s.sum(min_count=1))).reset_index()
    c=cz.copy();c['escenario']=c.escenario.str.lower()
    c=c[keys+['demanda_anual_ventana12h','demanda_anual24h','estado']].rename(columns={'estado':'cobertura_terrestre'})
    versions=[]
    for v in ['A','B']:
        x=l[l.version.eq(v)].merge(c,on=keys,how='outer',validate='one_to_one'); x['version']=v
        x['total_combinado']=None;x['permite_sumar_bloques']=False
        x['regla']='Faltante no equivale a cero. Lacustre operacional y terrestre12h no son exposiciones directamente sumables.'
        versions.append(x)
    return pd.concat(versions,ignore_index=True)


def main():
    start=time.monotonic();p=argparse.ArgumentParser();p.add_argument('--anexos',type=Path,required=True);p.add_argument('--etapa2',type=Path,required=True);p.add_argument('--salida',type=Path,required=True);args=p.parse_args()
    root,args2,out=args.anexos.resolve(),args.etapa2.resolve(),args.salida.resolve()
    if out.exists():raise FileExistsError('Salida existente: conservar y elegir otra carpeta')
    if shutil.disk_usage(out.parent if out.parent.exists() else Path('/tmp')).free<100*1024**2:raise RuntimeError('Espacio insuficiente: no comenzar escritura')
    protected=json.loads((args2/'integridad_referencias_antes.json').read_text())
    assert all(sha(root/x['archivo'])==x['sha256'] for x in protected)
    read=lambda path:pd.read_csv(path)
    f=read(args2/'lacustre_temporal/final/factores_mensuales_lacustres.csv')
    cp=args2/'terrestre_temporal/final'
    f=corrected_factors(f,read(cp/'PNC_ratios_estacionales.csv'),read(cp/'PNC_proxy_VP2024.csv'))
    od=pd.concat([read(args2/f'aristo_OD/resultados/matriz_fecha_OD_version_{v}.csv') for v in ['A','B']],ignore_index=True)
    months=apply_lake(od,f); annual=annual_lake(months,f);mb,ab=service_balance(months)
    seasonal=months.groupby(['version','escenario','vista','sentido_cruce','segmento','unidad','temporada_destino','campana','componente'],dropna=False).aporte_mes.sum(min_count=1).rename('aporte_temporada').reset_index()
    zonal=annual.groupby(['version','escenario','vista','sentido_cruce','segmento','unidad','zona_origen','zona_destino','componente','subtipo'],dropna=False).agg(
       aporte_anual_en_meses_con_perfil=('aporte_anual_en_meses_con_perfil',lambda s:s.sum(min_count=1)),
       demanda_anual_operacional_componente=('demanda_anual_operacional_componente',lambda s:s.sum(min_count=1))).reset_index()
    zonal['fuente']='ARISTO';zonal['bloque']='lacustre_actual';zonal['anio']=2026
    zonal['estado']='Anualización condicional de componentes OD. Residuales conservados y clases sin12meses con anual faltante.'
    cz,cd,cm,cmd=[read(cp/x) for x in ['anuales_zonas.csv','anuales_localidades.csv','meses_zonas.csv','meses_localidades.csv']]
    u=unified(zonal,cz);wide=wide_reference(zonal,cz)
    original_foreign=read(root/'etapa1_lacustre_aristo_20261029/resultados/entrega_final/csv/extranjeros_indicadores_separados.csv')
    fm,fa,fc=monthly_foreign(original_foreign,f,ab)
    mainview=ab[ab.vista.eq('privados_compatibles_no_aditiva')|~ab.segmento.isin(PRIVATE)]
    summary=mainview.groupby(['version','escenario','segmento']).agg(flujo_fisico_anual=('flujo_fisico_anual',lambda s:s.sum(min_count=1)),
                  aporte_parcial=('flujo_fisico_meses_cubiertos',lambda s:s.sum(min_count=1)),
                  observado_OD_anualizado=('observado_OD_anualizado',lambda s:s.sum(min_count=1)),
                  imputado_OD_anualizado=('imputado_OD_anualizado',lambda s:s.sum(min_count=1)),
                  residual_anualizado=('residual_anualizado',lambda s:s.sum(min_count=1))).reset_index()
    summary['fraccion_imputada_OD']=summary.imputado_OD_anualizado/summary.flujo_fisico_anual.where(summary.flujo_fisico_anual.ne(0))
    summary['fraccion_residual']=summary.residual_anualizado/summary.flujo_fisico_anual.where(summary.flujo_fisico_anual.ne(0))
    # Comparaciones de control: índices idénticos en A/B, sin rellenar NULL.
    pivot=mb.pivot(index=['escenario','vista','sentido_cruce','segmento','mes'],columns='version',values='flujo_fisico_mes')
    annualorder=ab.pivot(index=['version','vista','sentido_cruce','segmento'],columns='escenario',values='flujo_fisico_anual')
    strict=ab[ab.segmento.isin(['VL','MOTO','BICI','VP'])]
    balerr=mb.observado_asignado+mb.imputado+mb.residual-mb.flujo_fisico_mes
    checks={
      'referencias_aprobadas_intactas':all(sha(root/x['archivo'])==x['sha256'] for x in protected),
      'fisico_A_igual_B':bool((pivot.A-pivot.B).abs().dropna().lt(1e-8).all()&pivot.A.isna().equals(pivot.B.isna())),
      'balances_componentes_mensuales':bool(balerr.abs().dropna().lt(1e-8).all()),
      'escenarios_conservador_central_alto_ordenados':bool(((annualorder.conservador<=annualorder.central+1e-8)|(annualorder.central.isna())).all()&((annualorder.central<=annualorder.alto+1e-8)|(annualorder.central.isna())).all()),
      'VL_VP_moto_bici_sin_anual_estricto_inventado':bool(strict.flujo_fisico_anual.isna().all()),
      'privados_agregados_alternativos_12meses':bool(ab.loc[ab.segmento.eq('PRIVADOS_COMPATIBLES'),'meses_con_valor'].eq(12).all()),
      'CITRA_24h_sin_inventar':bool(cz.demanda_anual24h.isna().all()&cd.demanda_anual24h.isna().all()),
      'CITRA_no_recibe_OD_ARISTO':bool(u.loc[u.fuente.eq('CITRA'),'componente'].eq('corredor_estimado_sin_imputacion_OD').all()),
      'unificados_no_total_artificial':bool(wide.total_combinado.isna().all()&~wide.permite_sumar_bloques.any()),
      'externos_genericos_sin_zona_inventada':bool(od.loc[od.subtipo.eq('residual_externo'),'OD_zonal_completo'].eq(False).all()),
      'sin_crecimiento_induccion_captacion_logit':True,
      'calendario_365_dias':sum(calendar.monthrange(2026,m)[1] for m in range(1,13))==365,
    };assert all(checks.values()),checks
    out.mkdir(parents=True);(out/'csv').mkdir()
    tables={'aristo_mensual':months,'aristo_anual_detalle':annual,'aristo_anual_zonas':zonal,'aristo_temporadas':seasonal,
            'aristo_balance_mensual':mb,'aristo_balance_anual':ab,'aristo_resumen_escenarios':summary,'factores_lacustres_aplicados':f,
            'citra_anual_zonas':cz,'citra_anual_localidades':cd,'citra_mensual_zonas':cm,'base_unificada_anual':u,'referencia_por_OD_bloques_separados':wide,
            'extranjeros_mensual':fm,'extranjeros_aportes_anuales':fa,'extranjeros_cobertura':fc}
    for name,d in tables.items():d.to_csv(out/'csv'/f'{name}.csv',index=False,encoding='utf-8-sig')
    notes=pd.DataFrame([
      dict(tema='Anual referencia',detalle='Año2026normalizado, no crecimiento ni tráfico anual efectivamente observado. Todos los flujos anuales son estimaciones condicionadas.'),
      dict(tema='Versiones ARISTO',detalle='A conserva OD y residual. B transfiere únicamente composición compatible de F conocido; externos genéricos siguen fuera de zona. Versiones alternativas, no sumar.'),
      dict(tema='Invierno',detalle='Normal mayo proxy Jun–Ago; conservador usa stress PNC2024 I/P de clase compatible, NO razón invierno/otoño lacustre observada. Peatones sin ratio transferido.'),
      dict(tema='Unidades privadas',detalle='VL/MOTO/BICI solo6meses yVPsolo6: anual estricto faltante. VistaPRIVADOS_COMPATIBLES reúne categoríascomparables, NO se suma concomponentes.'),
      dict(tema='CITRA',detalle='Ventanas08–20 anualizadas solo bajo perfiles propios y proxies explícitos;24h y mercado no cubierto desconocidos. No utilizaOD ni proporcionesARISTO.'),
      dict(tema='Residuales y ceros',detalle='Residual lacustre tiene F físico conocido; desconocido terrestre no tiene una magnitud imputada. NULLnoescero. Aporteparcialnoesdemanda anualtotal.'),
      dict(tema='Extranjeros',detalle='Indicadores separados, no residencia ni extranjerosúnicos. No se imputan características personales a losODcompletados deB. Denominadores y partes sincaracterización separados.'),
    ])
    workbook(out/'01_lacustre_anual_A_B.xlsx',{'Leer primero':notes,'Anual zonas':zonal,'Anual detalle':annual,'Por temporada':seasonal,'Mensual':months,'Resumen escenarios':summary,'Balance anual':ab})
    workbook(out/'02_terrestre_anual_parcial.xlsx',{'Leer primero':notes,'Anual zonas':cz,'Anual localidades':cd,'Mensual zonas':cm,'Mensual localidades':cmd,'Comparaciones pantallas':read(root/'etapa1_terrestre_citra/cierre_final/pantallas/comparaciones_pantallas.csv'),'PNC estacional':read(cp/'PNC_ratios_estacionales.csv')})
    workbook(out/'03_base_unificada.xlsx',{'Leer primero':notes,'Base larga anual':u,'Bloques separados porOD':wide,'Diccionario':read(args2/'compatibilidad/resultados/diccionario_base_unificada.csv'),'Compatibilidad etapas1':read(args2/'compatibilidad/resultados/compatibilidad_OD_campana_clase.csv')})
    workbook(out/'04_supuestos_balances_extranjeros.xlsx',{'Leer primero':notes,'Factores aplicados':f,'Exposicion':read(args2/'lacustre_temporal/final/exposicion_por_campana_sentido.csv'),'Balance mensual':mb,'Balance anual':ab,'Escenarios':summary,'Extranjeros aportes':fa,'Extranjeros cobertura':fc,'PNC privados proxy':read(cp/'PNC_proxy_VP2024.csv'),'Validaciones':pd.DataFrame([dict(comprobacion=k,correcto=v) for k,v in checks.items()])})
    result={'verificaciones':checks,'anio':2026,'CITRA_zonas_anual12h_estimables_por_escenario':int(cz[cz.escenario.eq('Central')].demanda_anual_ventana12h.notna().sum()),
       'CITRA_localidades_anual12h_estimables_por_escenario':int(cd[cd.escenario.eq('Central')].demanda_anual_ventana12h.notna().sum()),
       'CITRA_anual24h_estimable':False,'pasajeros_totales_estimados':False,'entregas_anteriores_modificadas':False,
       'subida_GitHub_cancelada':True,'archivos':list(tables),'segundos_integracion':round(time.monotonic()-start,2)}
    (out/'validacion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    from informe_etapa2 import report
    report(out,args2,result,summary,cz,ab,wide)
    inputfiles=[]
    for directory in ['aristo_OD/resultados','lacustre_temporal/final','terrestre_temporal/final','compatibilidad/resultados']:
        inputfiles += [x for x in (args2/directory).rglob('*') if x.is_file()]
    inputfiles += list(Path(__file__).parent.glob('*.py'))
    inputfiles += [args2/'aristo_OD/construir_versiones_OD.py',args2/'lacustre_temporal/anualizacion_lacustre.py',args2/'terrestre_temporal/anualizar_citra.py',args2/'compatibilidad/preparar_compatibilidad.py']
    (out/'manifest_integridad.json').write_text(json.dumps({'fuentes':[{'archivo':str(x),'sha256':sha(x)} for x in inputfiles],
          'resultados':[{'archivo':str(x.relative_to(out)),'sha256':sha(x)} for x in out.rglob('*') if x.is_file()]},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
