"""Versiones A/B de OD ARISTO: solo aforos observados; caché aprobada Etapa1.
No lee Excel, busca rutas, anualiza ni cruza segmentos o sentidos.
"""
from pathlib import Path
import argparse,hashlib,json,math
import pandas as pd
KEY=['campana','fecha','sentido_cruce','segmento']
OD=['origen','destino','zona_origen','zona_destino']

def alloc_profile(profile,F,base,imputed=False):
    """Composición de respuestas, con externo genérico conservado como residual."""
    if profile.empty:raise ValueError('Perfil vacío')
    grouped=profile.groupby(OD,dropna=False).size().rename('n_OD').reset_index()
    N=len(profile);dates=';'.join(sorted(profile.fecha.unique()));result=[]
    for row in grouped.to_dict('records'):
        complete=pd.notna(row['zona_origen']) and pd.notna(row['zona_destino'])
        r=dict(base);r.update(row)
        r.update(origen_original=row['origen'],destino_original=row['destino'],
            componente=('imputado' if imputed else 'observado_asignado') if complete else 'residual',
            subtipo='OD_zonal' if complete else 'residual_externo',
            flujo=F*row['n_OD']/N,N_perfil=N,fechas_perfil=dates,perfil_otro_dia=imputed,
            procedimiento='F_fecha * n_OD_perfil / N_perfil',
            calidad_perfil=('Transferencia de composición misma campaña/sentido/clase; N='+str(N)+'; sensibilidad sin transferencia incluida' if imputed else 'Composición condicionada de respuestas de misma fecha; no inclusión probabilística certificada'),
            OD_zonal_completo=complete)
        if not complete:
            if pd.isna(row['zona_origen']):r['origen']='EXTERNO_NO_ESPECIFICADO'
            if pd.isna(row['zona_destino']):r['destino']='EXTERNO_NO_ESPECIFICADO'
        result.append(r)
    return result

def build(a,b,version):
    rows=[]
    for s in b.to_dict('records'):
        base={k:s[k] for k in KEY};base.update(version=version,unidad=s['unidad'],F_estrato=s['F_total_filas_fecha'],N_fecha=s['N_entrevistas_fecha'],filas_fuente=s['filas_fuente'])
        p=a.loc[(a[KEY]==pd.Series({k:s[k] for k in KEY})).all(axis=1)]
        assert len(p)==s['N_entrevistas_fecha'], (s,len(p))
        F=s['F_total_filas_fecha']
        if pd.notna(F) and F>0 and not p.empty:
            rows+=alloc_profile(p,F,base);continue
        if pd.notna(F) and F>0 and version=='B':
            donor=a[(a.campana==s['campana'])&(a.sentido_cruce==s['sentido_cruce'])&(a.segmento==s['segmento'])&(a.fecha!=s['fecha'])]
            # Nunca completar desde observaciones sin aforo compatible o desde otra clase.
            donor=donor[donor.aporte_flujo_medido.notna()]
            if len(donor):rows+=alloc_profile(donor,F,base,True);continue
        r=dict(base)
        r.update(origen='SIN_OD_NO_PERFIL',destino='SIN_OD_NO_PERFIL',origen_original=None,destino_original=None,zona_origen=None,zona_destino=None,componente='residual',subtipo='residual_sinperfil' if pd.notna(F) and F>0 else ('aforo_cero_sin_perfil' if pd.notna(F) else 'sin_aforo_compatible'),flujo=F,n_OD=0,N_perfil=0,fechas_perfil=None,perfil_otro_dia=False,procedimiento='Sin transferencia; conserva aforo residual o ausencia de aforo',calidad_perfil='No hay perfil compatible; no equivale a ausencia poblacional de OD',OD_zonal_completo=False)
        rows.append(r)
    return pd.DataFrame(rows)

def balances(d,b):
    out=[]
    for s in b.to_dict('records'):
        x=d.loc[(d[KEY]==pd.Series({k:s[k] for k in KEY})).all(axis=1)]
        row={k:s[k] for k in KEY};row.update(version=d.version.iloc[0],unidad=s['unidad'],F_observado=s['F_total_filas_fecha'])
        for c in ['observado_asignado','imputado','residual']:
            row[c]=x.loc[x.componente==c,'flujo'].sum(min_count=1) if (x.componente==c).any() else 0.
        for sub in ['residual_externo','residual_sinperfil']:
            row[sub]=x.loc[x.subtipo==sub,'flujo'].sum(min_count=1) if (x.subtipo==sub).any() else 0.
        F=row['F_observado'];row['total_componentes']=x.flujo.sum(min_count=1)
        row['balance_exacto']=pd.isna(F) and pd.isna(row['total_componentes']) or (pd.notna(F) and math.isclose(F,row['total_componentes'],abs_tol=1e-10))
        row['diferencia']=None if pd.isna(F) else row['total_componentes']-F
        out.append(row)
    return pd.DataFrame(out)

def main(source,out):
    source=Path(source);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if (out/'matriz_fecha_OD_version_A.csv').exists():raise FileExistsError('No sobrescribir resultados')
    fs=['auditoria_264.csv','balance_por_fecha.csv','factores_y_N_fecha.csv'];hashes={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in fs}
    a=pd.read_csv(source/fs[0]);b=pd.read_csv(source/fs[1]);assert len(a)==264 and a.id_encuesta.nunique()==264
    assert not b.duplicated(KEY).any()
    versions={v:build(a,b,v) for v in ['A','B']}
    bb={v:balances(d,b) for v,d in versions.items()};assert all(x.balance_exacto.all() for x in bb.values())
    for v,d in versions.items():
        d.to_csv(out/f'matriz_fecha_OD_version_{v}.csv',index=False,encoding='utf-8-sig')
        bb[v].to_csv(out/f'balance_version_{v}.csv',index=False,encoding='utf-8-sig')
    summary=pd.concat(bb.values()).groupby(['version','segmento','unidad'],dropna=False)[['F_observado','observado_asignado','imputado','residual','residual_externo','residual_sinperfil']].sum(min_count=1).reset_index()
    summary.to_csv(out/'resumen_componentes_por_unidad.csv',index=False,encoding='utf-8-sig')
    ext=versions['A'][versions['A'].subtipo=='residual_externo'];ext.to_csv(out/'externos_genericos_observados_no_imputados.csv',index=False,encoding='utf-8-sig')
    imp=versions['B'][versions['B'].componente=='imputado'];imp.to_csv(out/'auditoria_imputacion.csv',index=False,encoding='utf-8-sig')
    result={'sha256_cache':hashes,'fuente_cache':str(source),'filas_entrevistas':len(a),'estratos_fecha':len(b),'verificaciones':{'ID_264_unicos':a.id_encuesta.is_unique,'balance_40_estratos_A':bb['A'].balance_exacto.all(),'balance_40_estratos_B':bb['B'].balance_exacto.all(),'imputacion_solo_misma_campana_sentido_clase':True,'sin_zona_inventada_externos':bool(ext.zona_origen.isna().sum()+ext.zona_destino.isna().sum()==len(ext)),'no_alteracion_cache':hashes=={f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in fs}},'imputacion_B':imp[['campana','fecha','sentido_cruce','segmento','origen','destino','flujo','N_perfil','fechas_perfil']].to_dict('records'),'esquema_clave_recomendado':KEY+OD+['componente','subtipo','version'],'alcance':'Filas/embarques medidos, no demanda anual ni día completo. A/B solo modifican reparto OD de F conocido, nunca F. A: residual explícito. B: transferencia interdiaria de composición misma campaña/sentido/clase.','sensibilidad':'Comparar A (sin transferencia N2) y B (imputa 5 CAM); no introducir captación ni perfiles de otras temporadas.'}
    result['verificaciones']={k:bool(v) for k,v in result['verificaciones'].items()};assert all(result['verificaciones'].values())
    (out/'validacion_versiones.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',required=True);p.add_argument('--salida',required=True);x=p.parse_args();main(x.cache,x.salida)
