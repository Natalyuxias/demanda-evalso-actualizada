"""Tablas de presentación del mismo modelo oficial. No estima demanda ni elección.
Lee solo resultados agregados ya existentes; se integra desde calcular.py.
"""
from pathlib import Path
import hashlib,calendar,json
import pandas as pd
import numpy as np


def construir_tablas_equipo(R,C,b,d,costs,summary,byperiod,coverage):
    meta=[]
    def read(rel):
        p=R/rel;meta.append({'archivo':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'uso':'Resultado agregado heredado; no se reprocesan encuestas'})
        return pd.read_csv(p)
    e1='etapa1_lacustre_aristo_20261029/resultados/entrega_final/csv/'
    e2='etapa2_demanda_anual_20261029/resultados/entrega_final/csv/'
    ci='etapa1_terrestre_citra/resultados/cierre_final_04/csv/'
    ar_campaign=read(e1+'factores_y_N_fecha.csv')
    ar_od=read(e1+'matriz_por_fecha.csv')
    ci_campaign=read(ci+'matriz_localidades.csv')
    ci_factors=read(ci+'factores.csv')
    ci_flows=read(ci+'flujos_fecha_pantalla.csv')
    used=ci_flows[ci_flows.seleccionada.eq(True)]
    ci_factors=ci_factors[ci_factors.id_estrato.isin(used.id_estrato)].copy()
    ar_balance=read(e2+'aristo_balance_anual.csv')
    ar_month=read(e2+'aristo_mensual.csv')
    ci_month=read(e2+'citra_mensual_zonas.csv')
    ci_ann=read(e2+'citra_anual_localidades.csv')
    foreign_sample=read(e1+'extranjeros_indicadores_separados.csv')
    foreign_part=read(e2+'extranjeros_aportes_anuales.csv')
    foreign_cov=read(e2+'extranjeros_cobertura.csv')
    # Guía explicita denominadores y jerarquía; ninguna tabla combina niveles de observación.
    guide=pd.DataFrame([
      ['Frecuencia oficial','Ambos cruces11alta(dic–abr)/8baja(may–nov), por semana y sentido. Reemplaza14delnuevo, sin modificar contrastes históricos.'],
      ['Observado','Entrevistas y aforos de campañas, con su fecha/control/ventana. No son demanda anual ni se suman pantallas en serie.'],
      ['Referencia2026','Anualización ya aprobada y supuestos de cobertura heredados. Aporte en meses con perfil no equivale a anual completo.'],
      ['SBO','Misma demanda existente/proyectada conservada por procedencia; rutas tierra y ferryactual optimizado107min11/8. No constituye una nueva medición.'],
      ['CP','Desvío al nuevo cruce por curvas originales, resto en procedencia; inducción incremental repartida con esas mismas cuotas.'],
      ['Mercado compatible','Solo cohortes con captación calculable. Las participaciones se dividen por ese mercado, no por demanda regional desconocida.'],
      ['Residuales','Demanda conocida sin repartoCP calculable. Se conserva separada; los totales de rutasCP son aportes modelados y no la suman artificialmente.'],
      ['Vista del equipo','Tablas de presentación utilizan ARISTOB; A se conserva solo en hojas técnicas originales. No sumarA/B.'],
      ['Unidades','VL,CAM,VP ypeatones separados; VPheterogéneo no esVLestricto. Peatones no son pasajeros totales.'],
      ['Ambos sentidos','Las filasAmbos sentidos son agregados: no sumarlas con sus dos componentes. Días no se duplican; denominador porzarpe de ambos sentidos incluye dos exposiciones.'],
      ['Sensibilidades oficiales','Tres curvas conelasticidadcentral y±0,1concaptacióncentral. Frecuencias11/8en todos los casos oficiales.'],
      ['Históricos','Sensibilidades de navegación/frecuencia/tarifa previas se copian sin recalcular y se etiquetanNOOFICIALES. No se usa logitbinario ni multinomial.'],
      ['Extranjeros','Indicadores distintos y solapados. Los aportes parcialesexpandidos no se declaran totales anuales. No se trasladan proporciones a cada alternativa.'],
      ['Reproducción','python actualizacion_oficial_alternativas_20261029/codigo/calcular.py; actualiza el mismoExcel/HTML oficial.']
    ],columns=['concepto','definicion'])
    frequencies=[]
    for m in range(1,13):
        f=C['SBO']['frecuencia_alta'] if m in C['SBO']['meses_alta'] else C['SBO']['frecuencia_baja']
        fn=C['frecuencia_nuevo']['alta'] if m in C['frecuencia_nuevo_meses_alta'] else C['frecuencia_nuevo']['baja']
        frequencies.append({'mes':m,'dias_normalizados2026':calendar.monthrange(2026,m)[1],'actual_zarpes_semana_sentido':f,'nuevo_zarpes_semana_sentido':fn,'t_horario_actual_h':C['w_horario']*168/f,'t_horario_nuevo_h':C['w_horario']*168/fn,'estado':'VIGENTE; no espera física'})
    frequencies=pd.DataFrame(frequencies)
    # Referencia normalizada porOD y porcampaña se mantiene en tablas distintas.
    ref=b[(b.anio==2026)&b.version_referencia.eq('B')].copy()
    ref['estimacion_heredada']=ref.Q_heredada_expandida
    ref['imputacion_geografica']=ref.Q_OD_imputado_ARISTO
    ref['imputacion_temporal_adicional']=ref.Q_imputacion_temporal_adicional
    ref['dias_temporada']=ref.temporada.map({t:sum(calendar.monthrange(2026,m)[1] for m in ms) for t,ms in C['meses_temporada'].items()})
    refkeys=['fuente','origen','destino','zona_origen','zona_destino','segmento','unidad','temporada','direccion_cruce']
    refcols=['Q_referencia','estimacion_heredada','imputacion_geografica','imputacion_temporal_adicional']
    ref_od=ref.groupby(refkeys,dropna=False)[refcols].sum(min_count=1).reset_index()
    ref_od['dias_representados']=ref_od.temporada.map({t:sum(calendar.monthrange(2026,m)[1] for m in ms) for t,ms in C['meses_temporada'].items()})
    ref_od['estado']='Referencia2026, no observación. CITRA: cobertura geográfica parcial y factorhorario1,20; ARISTO: conservar clases de cada temporada.'
    ref_season=ref_od.groupby(['fuente','segmento','unidad','temporada','direccion_cruce'],dropna=False)[refcols].sum(min_count=1).reset_index()
    ref_season['dias_representados']=ref_season.temporada.map({t:sum(calendar.monthrange(2026,m)[1] for m in ms) for t,ms in C['meses_temporada'].items()})
    ref_season['aporte_diario_equivalente']=ref_season.Q_referencia/ref_season.dias_representados
    refannual=ref.groupby(['fuente','segmento','unidad'],dropna=False)[refcols].sum(min_count=1).reset_index()
    ar=ar_balance[ar_balance.escenario.str.lower().eq('central')&ar_balance.version.eq('B')&ar_balance.vista.eq('clases_originales')]
    strict=ar.groupby('segmento',dropna=False).flujo_fisico_anual.sum(min_count=1).rename('anual_ARISTO_completo_si_disponible').reset_index()
    refannual=refannual.merge(strict,on='segmento',how='left')
    refannual.loc[refannual.fuente.ne('ARISTO'),'anual_ARISTO_completo_si_disponible']=np.nan
    refannual['anual_CITRA_cubierto_con_supuestos']=refannual.Q_referencia.where(refannual.fuente.eq('CITRA'))
    refannual['anio']=2026
    refannual['alcance']=np.where(refannual.fuente.eq('CITRA'),'Anual del mercado cubierto:1,20yrellenoestacional ya aprobados; NO totalterrestre','Aporte de clases originales. Ver anualcompleto: VL/VPpueden representar períodos complementarios, no clases plenamenteobservadas todoelaño')
    # Hojasobservadas: cuentas de encuestas versus aforos separados para no duplicarFporOD.
    ar_campaign=ar_campaign.rename(columns={'F_total_filas_fecha':'embarques_medidos','N_entrevistas_fecha':'entrevistas_compatibles'})
    ar_campaign['fuente']='ARISTO';ar_campaign['periodo']='Exposición medida de la fecha; filas no necesariamente equivalen a unzarpe';ar_campaign['anual_2026']=np.nan
    ar_od['fuente']='ARISTO';ar_od['nivel']='OD en exposición medida, no anual';ar_od['dias_representados']='Fecha/ventana observada, no jornada24h acreditada'
    ci_campaign['fuente']='CITRA';ci_campaign['nivel']='FlujoA12h por pantalla seleccionada, no totalcorredor';ci_campaign['anual_2026']=np.nan
    ci_factors['fuente']='CITRA';ci_factors['advertencia']='Fpor estrato/control/sentido: no sumarlo porOD ni entre pantallas superpuestas'
    ci_ann=ci_ann[ci_ann.escenario.str.lower().eq('central')].copy()
    ci_ann['uso']='Referencia original Etapa2antesde supuestos posteriores1,20 yrelleno de temporadasEtapa5; no sumar conReferencia2026actual'
    # Fuenteestacional previa permitever coincidencia campaña/temporada y no fingir observaciones de invierno.
    season_provenance=ci_month[ci_month.escenario.str.lower().eq('central')].copy()
    season_provenance['fuente']='CITRA';season_provenance['uso']='Perfiles mensuales fuenteEtapa2,12h; tasasno se recalculan'
    ar_month=ar_month[ar_month.escenario.str.lower().eq('central')&ar_month.version.eq('B')&ar_month.vista.eq('clases_originales')]
    ar_prov=ar_month[['campana_fuente','temporada_destino','mes','segmento','unidad','invierno_es_proxy','fuente_imputacion_OD']].drop_duplicates()
    # Vistas de presentación paraequipo: soloB, mantener todoscasosoficiales.
    team=d[d.version_referencia.eq('B')&d.segmento.isin(['VL','CAM','VP','PEATON'])].copy()
    team['Q_compatible']=team.Q_referencia.where(team.p_nuevo.notna(),0.)
    team['SBO_tierra_compatible']=team.D_tierra_SBO.where(team.p_nuevo.notna(),0.)
    team['SBO_actual_compatible']=team.D_actual_SBO.where(team.p_nuevo.notna(),0.)
    nums=['Q_referencia','Q_compatible','SBO_tierra_compatible','SBO_actual_compatible','D_tierra_SBO','D_actual_SBO','D_tierra_CP_existente','D_actual_CP_existente','D_existente_nuevo','D_desviada_tierra','D_desviada_actual','D_inducida_incremental','D_inducida_tierra','D_inducida_actual','D_inducida_nuevo','D_tierra_CP_total','D_actual_CP_total','D_nuevo_CP_total','D_residual_existente']
    grp=['alternativa_proyecto','escenario_captacion','escenario_elasticidad','anio','segmento','unidad']
    annual=team.groupby(grp,dropna=False)[nums].sum(min_count=1).reset_index();annual['direccion_cruce']='Ambos sentidos';annual['temporada']='Anual';annual['dias_equivalentes']=365;annual['multiplicador_sentidos']=2
    period=team.groupby(grp+['temporada','direccion_cruce'],dropna=False)[nums].sum(min_count=1).reset_index()
    both=team.groupby(grp+['temporada'],dropna=False)[nums].sum(min_count=1).reset_index();both['direccion_cruce']='Ambos sentidos'
    period=pd.concat([period,both],ignore_index=True);period['multiplicador_sentidos']=np.where(period.direccion_cruce.eq('Ambos sentidos'),2,1)
    period['dias_equivalentes']=period.temporada.map({t:sum(calendar.monthrange(2026,m)[1] for m in ms) for t,ms in C['meses_temporada'].items()})
    exposures={t:sum(calendar.monthrange(2026,m)[1]*(C['SBO']['frecuencia_alta'] if m in C['SBO']['meses_alta'] else C['SBO']['frecuencia_baja'])/7 for m in ms) for t,ms in C['meses_temporada'].items()}
    period['zarpes_equivalentes_por_servicio']=period.temporada.map(exposures)*period.multiplicador_sentidos
    annual['zarpes_equivalentes_por_servicio']=sum(exposures.values())*2
    # Una fila por ruta; denominadorescompatibles explicitados.
    def route_table(x):
        out=[]
        for route,pretty in [('tierra','Terrestre por Chile'),('actual','Puerto Ibáñez–Chile Chico'),('nuevo','Bahía Jara–Levicán')]:
            q=x.copy();q['ruta_transporte']=pretty
            q['demanda_SBO_conocida']=q['D_'+route+'_SBO'] if route!='nuevo' else 0.
            q['demanda_SBO_compatible']=q['SBO_'+route+'_compatible'] if route!='nuevo' else 0.
            q['demanda_CP_existente']=q['D_'+route+'_CP_existente'] if route!='nuevo' else q.D_existente_nuevo
            q['demanda_CP_inducida']=q['D_inducida_'+route]
            q['demanda_CP_total_modelada']=q['D_'+route+'_CP_total']
            q['participacion_SBO_compatible']=q.demanda_SBO_compatible/q.Q_compatible.replace(0,np.nan)
            denominator=q.Q_compatible+q.D_inducida_incremental.fillna(0)
            q['participacion_CP_compatible']=q.demanda_CP_total_modelada/denominator.replace(0,np.nan)
            q['CP_diario_equivalente']=q.demanda_CP_total_modelada/q.dias_equivalentes
            q['CP_por_zarpe_equivalente']=np.nan if route=='tierra' else q.demanda_CP_total_modelada/q.zarpes_equivalentes_por_servicio
            q['frecuencia']='No aplica' if route=='tierra' else '11alta/8baja porsemana/sentido'
            q['alcance']='SBOconocida incluye residual; CPycuotas solo mercado compatible. No restarCPdeSBOtotal como beneficio; usarSBOcompatible.'
            out.append(q[grp+['temporada','direccion_cruce','ruta_transporte','demanda_SBO_conocida','demanda_SBO_compatible','demanda_CP_existente','demanda_CP_inducida','demanda_CP_total_modelada','participacion_SBO_compatible','participacion_CP_compatible','Q_compatible','D_residual_existente','CP_diario_equivalente','CP_por_zarpe_equivalente','dias_equivalentes','zarpes_equivalentes_por_servicio','frecuencia','alcance']])
        return pd.concat(out,ignore_index=True)
    annual_dir=team.groupby(grp+['direccion_cruce'],dropna=False)[nums].sum(min_count=1).reset_index()
    annual_dir['temporada']='Anual';annual_dir['dias_equivalentes']=365;annual_dir['multiplicador_sentidos']=1
    annual_dir['zarpes_equivalentes_por_servicio']=sum(exposures.values())
    routes_ann=route_table(pd.concat([annual,annual_dir],ignore_index=True));routes_period=route_table(period)
    central=(team.escenario_captacion.eq('central')&team.escenario_elasticidad.eq('central')&team.alternativa_proyecto.eq('A1'))
    # SBO es independiente delproyecto: exportar una vez, sin triplicarla.
    sbobase=team[central]
    sbok=['anio','segmento','unidad'];sboper=sbobase.groupby(sbok+['temporada','direccion_cruce'],dropna=False)[['D_tierra_SBO','D_actual_SBO','Q_referencia','Q_compatible','D_residual_existente']].sum(min_count=1).reset_index()
    sboboth=sbobase.groupby(sbok+['temporada'],dropna=False)[['D_tierra_SBO','D_actual_SBO','Q_referencia','Q_compatible','D_residual_existente']].sum(min_count=1).reset_index();sboboth['direccion_cruce']='Ambos sentidos'
    sboper=pd.concat([sboper,sboboth],ignore_index=True)
    sboann=sbobase.groupby(sbok,dropna=False)[['D_tierra_SBO','D_actual_SBO','Q_referencia','Q_compatible','D_residual_existente']].sum(min_count=1).reset_index();sboann['definicion']='Total conocido de referencia sinproyecto: compatible+residual; no totalesregionales'
    provenance=annual[grp+['Q_referencia','Q_compatible','D_desviada_tierra','D_desviada_actual','D_inducida_nuevo','D_nuevo_CP_total','D_residual_existente']].copy()
    provenance['porcentaje_captacion_existente_compatible']=(provenance.D_desviada_tierra+provenance.D_desviada_actual)/provenance.Q_compatible.replace(0,np.nan)
    provenance['nuevo_total_sobre_referencia_compatible']=provenance.D_nuevo_CP_total/provenance.Q_compatible.replace(0,np.nan)
    # Extranjería: no extrapolar a proyectos cuando no hay correspondenciaOD-indicador.
    sm=foreign_sample.groupby(['indicador','categoria_indicador'],dropna=False).entrevistas_validas.sum().reset_index()
    fs=[]
    for ind in sm.indicador.unique():
        q=sm[sm.indicador.eq(ind)];foreigncat=q.categoria_indicador.astype(str).isin(['Extranjera','True']);n=int(q.entrevistas_validas.sum())
        fs.append({'indicador':ind,'universo_aplicable_muestra':n,'identificado_extranjero_o_internacional':int(q.loc[foreigncat,'entrevistas_validas'].sum()),'identificado_otro_valor':int(q.loc[~foreigncat,'entrevistas_validas'].sum()),'fuera_del_universo_indicador':264-n,'demanda_anual_extranjera_completa':np.nan,'estado':'No sumar entreindicadores: pueden identificar lasmismaspersonas; otrovalor no significa residencianacional'})
    fs.append({'indicador':'residencia_extranjera','universo_aplicable_muestra':np.nan,'identificado_extranjero_o_internacional':np.nan,'identificado_otro_valor':np.nan,'fuera_del_universo_indicador':np.nan,'demanda_anual_extranjera_completa':np.nan,'estado':'No hay clasificación agregada país de residencia enentregasfinales. Existencia de LugarResidencia enformulario no proporciona país validado.'})
    fs=pd.DataFrame(fs).rename(columns={'identificado_extranjero_o_internacional':'entrevistas_indicador_positivo','identificado_otro_valor':'entrevistas_otro_valor'})
    fp=foreign_part[foreign_part.escenario.str.lower().eq('central')].copy();fp['unidad']=fp.segmento.map({'VL':'vehículos','CAM':'vehículos','VP':'unidades privadas heterogéneas','PEATON':'personas_peatones','MOTO':'motocicletas','BICI':'bicicletas'})
    fp['demanda_anual_extranjera_completa']=np.nan;fp['estado_anual']='Aporte expandido en mesescaracterizados, no anual completo; no aplicar aCP ni aotraunidad'
    fc=foreign_cov[foreign_cov.escenario.str.lower().eq('central')].copy();fc['sin_caracterizacion_anual']=fc.sin_caracterizacion_anual.clip(lower=0)
    fa=routes_ann[routes_ann.escenario_captacion.eq('central')&routes_ann.escenario_elasticidad.eq('central')&routes_ann.direccion_cruce.eq('Ambos sentidos')].copy()
    foreign_alt=[]
    for ind in ['nacionalidad_declarada','patente_vehicular','OD_internacional','residencia']:
        q=fa[grp+['ruta_transporte','demanda_CP_total_modelada']].copy();q['indicador']=ind;q['demanda_anual_identificada_extranjera']=np.nan;q['demanda_no_identificada_como_extranjera']=np.nan;q['demanda_clasificacion_no_desagregable']=q.demanda_CP_total_modelada
        q['estado']='No estimable la partición delCP: no hay enlaceOD/indicador suficientemente respaldado. No equivale a afirmar que todos los usuarios reales son desconocidos.';foreign_alt.append(q)
    foreign_alt=pd.concat(foreign_alt,ignore_index=True)
    # Sensibilidades guardadas, sin ejecutarlas otra vez ni presentarlas como oficiales.
    histp=R/'etapa5_ampliacion_peatones_20261029/resultados/ampliacion_peatones_sensibilidad.xlsx'
    with pd.ExcelFile(histp) as w:historical=pd.read_excel(w,'Sensibilidad operacional')
    historical=historical[historical.version_referencia.eq('B')].copy();historical['estado']='HISTORICO EXPLORATORIO, NO OFICIAL VIGENTE';historical['frecuencia_de_su_base']='Actual14/12; nuevo14, variante21; NO11/8común';historical['navegacion_de_su_base']='Actual120/nuevo80, variantes160/40; no configuracionesA1/A2/A3';historical['fuente']=str(histp)
    meta.append({'archivo':str(histp),'sha256':hashlib.sha256(histp.read_bytes()).hexdigest(),'uso':'Contraste histórico sin modificar, NO estimación oficial'})
    gp=R/'etapa3_ajuste_elasticidades_20261029/resultados/entrega_final/proyecciones_ajustadas_2026_2050.xlsx'
    with pd.ExcelFile(gp) as w:growth=pd.read_excel(w,'Resumen lacustre anual')
    growth=growth[growth.version.eq('B')&growth.anio.isin(C['anios'])].copy();growth['uso']='Contraste de proyección de referencia, no captación nueva. Oficial usa crecimiento central; no sumar escenarios.'
    meta.append({'archivo':str(gp),'sha256':hashlib.sha256(gp.read_bytes()).hexdigest(),'uso':'Proyecciones ya existentes; no recalculadas'})
    # Validaciones deagregación: son tablas, no nuevas auditorías.
    assert np.allclose(provenance.D_nuevo_CP_total,provenance.D_desviada_tierra+provenance.D_desviada_actual+provenance.D_inducida_nuevo.fillna(0),equal_nan=True)
    known=routes_ann.demanda_CP_total_modelada.notna()
    shares=routes_ann[routes_ann.direccion_cruce.eq('Ambos sentidos')].groupby(grp,dropna=False).participacion_CP_compatible.sum(min_count=1)
    assert np.allclose(shares.dropna(),1)
    assert frequencies.actual_zarpes_semana_sentido.equals(frequencies.nuevo_zarpes_semana_sentido)
    extra={
      'Guia de lectura':guide,'Frecuencias vigentes':frequencies,'Referencia anual 2026':refannual,'Referencia OD 2026':ref_od,'Referencia estacional':ref_season,
      'Campanas ARISTO':ar_campaign,'OD campana ARISTO':ar_od,'Campanas CITRA':ci_campaign,'Aforos y factores CITRA':ci_factors,'Base CITRA Etapa2':ci_ann,
      'Trazabilidad meses CITRA':season_provenance,'Trazabilidad meses ARISTO':ar_prov,'SBO anual':sboann,'SBO estacional':sboper,
      'CP rutas anual':routes_ann,'CP rutas estacional':routes_period,'Captacion procedencia':provenance,
      'Extranjeros muestra':fs,'Extranjeros referencia':fp,'Extranjeros cobertura':fc,'Extranjeros alternativas':foreign_alt,
      'Sensibilidades historicas':historical,'Crecimiento referencia':growth,'Fuentes tablas equipo':pd.DataFrame(meta)}
    return extra,{'fuentes':meta,'validaciones_tablas':3}


def informe_equipo(C,tables,summary,coverage,checks,metadata):
    def html(df):return df.to_html(index=False,border=0,na_rep='No estimable',float_format=lambda x:f'{x:,.2f}')
    s=summary[summary.version_referencia.eq('B')&summary.escenario_captacion.eq('central')&summary.escenario_elasticidad.eq('central')&summary.segmento.isin(['VL','CAM','VP','PEATON'])]
    pivot=s.pivot(index=['anio','segmento','unidad'],columns='alternativa_proyecto',values='D_nuevo_CP_total').reset_index()
    r=tables['CP rutas anual'];r=r[r.escenario_captacion.eq('central')&r.escenario_elasticidad.eq('central')&r.direccion_cruce.eq('Ambos sentidos')]
    cap=tables['Captacion procedencia'];cap=cap[cap.escenario_captacion.eq('central')&cap.escenario_elasticidad.eq('central')]
    sens=summary[summary.version_referencia.eq('B')&summary.anio.eq(2026)&summary.segmento.isin(['VL','CAM','VP','PEATON'])]
    ref=tables['Referencia anual 2026'];ref=ref[ref.segmento.isin(['VL','CAM','VP','PEATON'])]
    return f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Consolidación oficial de demanda</title><style>body{{font:16px system-ui;max-width:1450px;margin:30px auto;padding:0 20px;color:#17364a}}p{{line-height:1.5}}table{{border-collapse:collapse;display:block;overflow:auto;font-size:12px;margin:16px 0}}th,td{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#eaf2f7}}details{{margin:20px 0}}summary{{font-weight:bold;cursor:pointer}}</style>
<h1>Consolidación oficial de demanda · Bahía Jara–Levicán</h1>
<p><b>Frecuencia definitiva común para ambos cruces: 11 zarpes por semana y sentido en diciembre–abril y 8 en mayo–noviembre.</b> Se reemplazó el parámetro anterior del nuevo cruce y se recalcularon los resultados oficiales en estas mismas ubicaciones. Las fuentes y los contrastes históricos permanecen intactos.</p>
<h2>1. Cómo leer la demanda</h2>{html(tables['Guia de lectura'].iloc[:10])}
<h2>2. Demanda de referencia normalizada2026</h2>{html(ref)}<p>La demanda observada de campaña y los factores están separados en las hojas CampañasARISTO/CITRA y AforosyfactoresCITRA. La referencia2026 no es un conteo anual observado. Las clases VL/VP deARISTO tienen definiciones y coberturas temporales distintas; cuando no hay anual completo, el campo correspondiente queda faltante. CITRA es solo el mercado cubierto, con las imputaciones previamente aceptadas.</p>
<h2>3. Frecuencias y alternativas vigentes</h2>{html(tables['Frecuencias vigentes'])}{html(pd.DataFrame(C['alternativas']))}
<p>SBOcomún: terrestre y PuertoIbáñez–ChileChico con CapitánWellmann,107min yfrecuencia11/8. Conproyecto coexisten esas dos rutas sin cambios y una nueva alternativa, evaluando A1/A2/A3por separado. Navegación43/39/39min; anticipación2hvehículos/1hpeatones como referenciaoperador transferida; desembarque30min para todos. No se diferencia tiempo por rampa. VST10047; COVARISTO/HDM4; accesos31,14/24,62/22,60km. Buses coordinados son hipotéticos y mantienen su tarifa por distancia.</p>
<h2>4. SBO: demanda anual por ruta</h2>{html(tables['SBO anual'])}<p>Las tablas estacionales separan Norte→Sur,Sur→Norte y ambos sentidos. El total conocido es mercado compatible más residual; no toda la demanda regional. El repartoCPsolo se conoce para el soporte y no convierte los residuales en ceros.</p>
<h2>5. Comparación central del nuevo cruce</h2>{html(pivot)}<p>Incluye demanda desviada existente más inducción incremental asignada al nuevo. Los proyectos son mutuamente excluyentes; no sumar sus columnas ni unidades distintas. VP no es VL estricto; los peatones no son todos los pasajeros.</p>
<details><summary>Demanda anual central de las tres rutas — todos los años y alternativas</summary>{html(r[['alternativa_proyecto','anio','segmento','unidad','ruta_transporte','demanda_SBO_conocida','demanda_SBO_compatible','demanda_CP_existente','demanda_CP_inducida','demanda_CP_total_modelada','participacion_CP_compatible','D_residual_existente']])}</details>
<details><summary>Procedencia anual de la demanda del nuevo cruce</summary>{html(cap[['alternativa_proyecto','anio','segmento','D_desviada_tierra','D_desviada_actual','D_inducida_nuevo','D_nuevo_CP_total','porcentaje_captacion_existente_compatible']])}</details>
<h2>6. Sensibilidades oficiales</h2>{html(sens[['alternativa_proyecto','escenario_captacion','escenario_elasticidad','segmento','D_existente_nuevo','D_inducida_nuevo','D_nuevo_CP_total']])}<p>Las curvas y elasticidades no cambiaron. Todos estos casos usan frecuencia11/8común. El Excel conserva además sensibilidades operacionales anteriores y proyecciones de crecimiento, expresamente marcadas como históricos/no vigentes cuando sus parámetros difieren. No se usan los logits exploratorios para esta estimación.</p>
<h2>7. Usuarios extranjeros: qué se puede afirmar</h2>{html(tables['Extranjeros muestra'])}<p>Nacionalidad, patente, OD internacional y residencia son indicadores distintos y solapados. No se suman como personas extranjeras diferentes. Extranjerosreferencia conserva los aportes expandidos en meses caracterizados, sin presentarlos como un anual completo. No hay enlace defendible para repartir nacionalidades entre las rutasCP: las magnitudes anuales poralternativa se marcan no estimables y no se aplican proporciones generales. Clasificación no desagregable enCP no significa que todas las personas encuestadas carecieran de información.</p>
<h2>8. Cobertura, exposición y límites</h2>{html(coverage[coverage.version_referencia.eq('B')])}<p>Los equivalentes diarios y porzarpe son promedios del soporte, no horas punta. En filas Ambos sentidos se suman los flujos y se divide por dos exposiciones de servicio; por sentido se usa una. La penalización0,25×168/f es inconveniencia por frecuencia, no espera física medida. Los costos de colaexterna no valorada conservan sus restricciones y se excluyen de inducción. El empalme norte heredado sigue siendo una aproximación; no se reconstruyó la red.</p>
<h2>9. Validaciones y archivos</h2>{html(checks)}<p>Además se verificaron las agregaciones de las tablas del equipo, las cuotas del mercado compatible y la igualdad de frecuencias de ambos cruces. <a href="demanda_oficial_tres_alternativas.xlsx">Excel oficial completo</a>. Reproducción:<code>python actualizacion_oficial_alternativas_20261029/codigo/calcular.py</code>. El READMEprincipal y codigo/configuracion.json definen las ubicaciones y parámetros vigentes. Esta consolidación no estima capacidad ni beneficios sociales.</p></html>'''
