"""Escenarios temporales CITRA de ventana12h; nunca identifica 24h o demanda total."""
import argparse,calendar,hashlib,json,shutil
from pathlib import Path
import pandas as pd

EST={12:'Verano',1:'Verano',2:'Verano',3:'Otoño',4:'Otoño',5:'Otoño',6:'Invierno',7:'Invierno',8:'Invierno',9:'Primavera',10:'Primavera',11:'Primavera'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pnc_ratios(pnc, out):
    old=out.parent
    oldmeta=old/'supuestos_validacion.json'
    if oldmeta.exists() and (old/'PNC_ratios_estacionales.csv').exists():
        m=json.loads(oldmeta.read_text())
        if m.get('fuentes',{}).get(str(pnc))==sha(pnc):
            for f in ['PNC_fuente_PC63_PC64.csv','PNC_ratios_estacionales.csv']:
                shutil.copyfile(old/f,out/f)
            return pd.read_csv(out/'PNC_ratios_estacionales.csv')
    raw=pd.read_excel(pnc,sheet_name='BBDD')
    raw['fila_Excel']=raw.index+2
    d=raw[(raw['REGIÓN']==11)&raw.PC.isin([63,64])&raw['AÑO'].isin([2018,2020,2022,2024])].copy()
    colsVL=['AUTOS','CAMIONETAS'];colsCAM=['CAMIONES\n2 EJES','CAMIONES\nMAS 2 EJES','SEMI\nREMOLQUE','REMOLQUE']
    for seg,cols in [('VL',colsVL),('CAM',colsCAM)]:
        vals=d[cols].apply(pd.to_numeric,errors='coerce')
        d[seg]=vals.sum(axis=1,min_count=len(cols))
    d.to_csv(out/'PNC_fuente_PC63_PC64.csv',index=False)
    rows=[]
    for (year,pc,rama),g in d.groupby(['AÑO','PC','RAMA']):
        for seg in ['VL','CAM']:
            z=g.set_index('MUESTRA')[seg]
            winter=z.get('I');spring=z.get('P');summer=z.get('V')
            ratio=winter/spring if pd.notna(winter) and pd.notna(spring) and spring>0 else None
            rows.append(dict(anio=year,PC=pc,rama=rama,segmento=seg,Invierno=winter,Primavera=spring,Verano=summer,
                             ratio_Invierno_Primavera=ratio,ratio_Invierno_Verano=winter/summer if pd.notna(winter) and pd.notna(summer) and summer>0 else None,
                             seleccionado_sensibilidad_2024=year==2024,
                             uso='Solo contraste:2020 condiciones de pandemia, no elegido' if year==2020 else 'Proxy de forma estacional, no factor12a24 ni medidaCITRA',
                             limite='PNCagregado por rama, sin sentidoCITRA, intervalo08a20 ni OD; VLaproximaautos+camionetas; CAMagrupa4categorias publicadas',
                             filas_fuente='|'.join(map(str,g.fila_Excel))))
    r=pd.DataFrame(rows);r.to_csv(out/'PNC_ratios_estacionales.csv',index=False)
    return r

def project(table,nivel,out,ratios,year):
    keys=['zona_origen','zona_destino','segmento']
    if nivel=='localidades':keys=['origen','destino']+keys
    rows=[];annual=[];support=[]
    for key,g in table.groupby(keys,dropna=False,sort=True):
        meta=dict(zip(keys,key));meta['nivel']=nivel
        for c in ['comuna_origen','comuna_destino']:
            if c in g:meta[c]=g.iloc[0][c]
        by={r.campana:r for r in g.itertuples()};have={c for c,r in by.items() if pd.notna(r.flujo_corredor_12h)}
        paired={'Verano','Otoño'}.issubset(have)
        support.append(dict(meta,campanas_con_flujo='|'.join(sorted(have)),dos_campanas=paired,
                            pantallas='|'.join(sorted(set(g.control))),
                            advertencia='Ningun ano observado completo; dos campanas solo habilitan escenario bajo supuestos' if paired else 'Sin dos campanas: anual faltante y aporte parcial de meses con perfil propio'))
        for scenario in ['Conservador','Central','Alto']:
            target=[]
            for month in range(1,13):
                season=EST[month];days=calendar.monthrange(year,month)[1]
                source=season if season in ['Verano','Otoño'] else ('Otoño' if paired else None)
                r=by.get(source);q=None;qa=None;qb=None;factor=1.;pc=None;rs=None
                available=r is not None and pd.notna(r.flujo_corredor_12h)
                if available:
                    if season=='Invierno' and scenario=='Conservador':
                        pc=64 if r.control=='E1003' else 63
                        rr=ratios[(ratios.anio==2024)&(ratios.PC==pc)&(ratios.segmento==r.segmento)]
                        assert len(rr)==1
                        factor=float(rr.iloc[0].ratio_Invierno_Primavera);rs=f'PNC2024 PC{pc} rama{int(rr.iloc[0].rama)} Invierno/Primavera'
                    q=float(r.flujo_corredor_12h)*factor
                    qa=float(r.flujo_A_12h)*factor if pd.notna(r.flujo_A_12h) else None
                    qb=float(r.flujo_B_12h)*factor if pd.notna(r.flujo_B_12h) else None
                imputed=season in ['Invierno','Primavera'] and available
                rec=dict(meta,escenario=scenario,anio=year,mes=month,estacion=season,dias_mes=days,
                         campana_fuente=source,control_fuente=r.control if available else None,
                         sentido_control_fuente=r.sentido_control if available else None,
                         fechas_muestra=r.fechas_representadas if available else None,
                         flujo_diario_ventana12h=q,flujo_diario_A12h=qa,flujo_diario_B12h=qb,
                         factor_estacional=factor if available else None,fuente_factor=rs,
                         aporte_mes_ventana12h=q*days if q is not None else None,
                         aporte_mes_A12h=qa*days if qa is not None else None,
                         aporte_mes_B12h=qb*days if qb is not None else None,
                         flujo_24h=None,factor_12_24=None,imputacion_temporal=imputed,
                         estado=('Perfil de campana extrapolado a dias del mes; no conteo mensual observado' if available and not imputed else
                                 'Proxy temporal Otono/CITRA y,si aplica,formaestacionalPNC; no observacion' if imputed else 'No estimable:perfil propio ausente; no se completa con otroOD'),
                         dias_no_laborales='Se transfiere perfil de jornadasmuestreadas a todoslosdias; no se acredita factortipodia',
                         definicion_escenario='Invierno PNC2024 como sensibilidad' if scenario=='Conservador' else 'Invierno y primavera igual Otono; Alto coincide con Central por falta de otro extremo superior respaldado',
                         cobertura='Fraccion del corredor identificada en cohorte112; no demanda terrestre total ni capturable',
                         advertencia_pantallas='|'.join(sorted(set(g.advertencia_entre_controles.dropna()))))
                rows.append(rec);target.append(rec)
            valid=[r for r in target if r['aporte_mes_ventana12h'] is not None]
            n=sum(r['dias_mes'] for r in valid);partial=sum(r['aporte_mes_ventana12h'] for r in valid) if valid else None
            annual.append(dict(meta,escenario=scenario,anio=year,dias_con_perfil_o_proxy=n,
                               dias_con_campana_propia=sum(r['dias_mes'] for r in valid if not r['imputacion_temporal']),
                               dias_proxy_invierno_primavera=sum(r['dias_mes'] for r in valid if r['imputacion_temporal']),
                               aporte_parcial_meses_con_perfil_12h=partial,
                               aporte_meses_con_campana_propia_12h=sum(r['aporte_mes_ventana12h'] for r in valid if not r['imputacion_temporal']) if valid else None,
                               demanda_anual_ventana12h=partial if n==365 and paired else None,
                               demanda_anual24h=None,
                               estado='Escenario anual de ventana12h bajo proxies; no estimacion24h' if n==365 and paired else 'Anual no estimable; aporte parcial de meses representados',
                               pantallas_entre_campanas='|'.join(sorted(set(g.control))),
                               soporte_OD_detallado='Puede variar entre campanas; no igualdad automatica con anualizacion detallada' if nivel=='zonas' else 'Mismo par nominal; registros geograficos originales conservados',
                               suma_de_flujos_de_fuentes_distintas_prohibida=True))
    pd.DataFrame(rows).to_csv(out/f'meses_{nivel}.csv',index=False)
    pd.DataFrame(annual).to_csv(out/f'anuales_{nivel}.csv',index=False)
    pd.DataFrame(support).to_csv(out/f'cobertura_temporal_{nivel}.csv',index=False)
    return pd.DataFrame(annual)

def run(src,pnc,out,year=2026):
    assert year==2026, 'Esta entrega usa el calendario2026 autorizado; otra base requiere declarar un nuevo escenario'
    src,pnc,out=Path(src),Path(pnc),Path(out);out.mkdir(parents=True,exist_ok=True)
    valid=json.loads((src/'resumen_validacion.json').read_text());assert all(valid['verificaciones'].values())
    ratios=pnc_ratios(pnc,out)
    # VP es un agregado heterogeneo (incluye motos y bicicletas), distinto de VL.
    pnc_cache=pd.read_csv(out/'PNC_fuente_PC63_PC64.csv')
    vp=[]
    for (pc,rama),g in pnc_cache[pnc_cache['AÑO'].eq(2024)].groupby(['PC','RAMA']):
        xx=g[['AUTOS','CAMIONETAS','MOTOS','BICICLETAS']].apply(pd.to_numeric,errors='coerce').sum(axis=1,min_count=4)
        vals=dict(zip(g.MUESTRA,xx))
        vp.append(dict(PC=pc,rama=rama,anio=2024,componente='VP_proxy_vial_heterogeneo_NO_VL',
                       Invierno=vals.get('I'),Primavera=vals.get('P'),
                       ratio_Invierno_Primavera=vals.get('I')/vals.get('P') if vals.get('P',0)>0 else None,
                       uso='Solo sensibilidad de forma estacional de autos+camionetas+motos+bicis; no representa patron observado de barcaza ni peatones'))
    pd.DataFrame(vp).to_csv(out/'PNC_proxy_VP2024.csv',index=False)
    shutil.copyfile(src/'csv/comparaciones_controles.csv',out/'contrastes_pantallas_conservados.csv')
    z=pd.read_csv(src/'csv/matriz_zonas_ARISTO.csv');d=pd.read_csv(src/'csv/matriz_localidades.csv')
    az=project(z,'zonas',out,ratios,year);ad=project(d,'localidades',out,ratios,year)
    # Agregacion anual coherente solo de localidades con ambas campanas. No fuerza
    # igualdad con perfiles zonales, que incorporan distintos subOD segun campana.
    agg=ad.groupby(['zona_origen','zona_destino','segmento','escenario','anio'],dropna=False).agg(
        anual12h_subOD_con_dos_campanas=('demanda_anual_ventana12h',lambda x:x.sum(min_count=1)),
        subOD_con_anual=('demanda_anual_ventana12h','count'),subOD_total=('demanda_anual_ventana12h','size')).reset_index()
    agg['alcance']='Subconjunto de localidades comunes a ambas campanas; no total zonal'
    agg.to_csv(out/'zonas_desde_localidades_anualizables.csv',index=False)
    assert az.demanda_anual24h.isna().all() and ad.demanda_anual24h.isna().all()
    assert len(z)==13 and len(d)==25
    assert az.loc[az.demanda_anual_ventana12h.notna(),'dias_con_perfil_o_proxy'].eq(365).all()
    kk=['zona_origen','zona_destino','segmento']
    pivot=az.pivot(index=kk,columns='escenario',values='demanda_anual_ventana12h')
    assert pivot.Central.equals(pivot.Alto)
    check=(pivot.Conservador<=pivot.Central+1e-10)|pivot.Central.isna()
    assert check.all()
    validation=dict(sin_flujo24h=True,cinco_celdas_zonales_y_cuatro_detalladas_con_dos_campanas=bool(
                    az.demanda_anual_ventana12h.notna().sum()==15 and ad.demanda_anual_ventana12h.notna().sum()==12),
                    solo_anual_con365dias_de_perfil_proxy=True,sin_suma_pantallas=True,
                    alto_igual_central_sin_incremento_inventado=True,conservador_no_supera_central=True,
                    sin_frecuencia_barcaza_ni_ARISTO_OD=True)
    assert all(validation.values())
    (out/'validaciones_temporales.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    manifest=dict(anio=year,ventana='08:00-20:00',horas24_identificadas=False,
        anualizacion_observada_completa=False,
        celdas_originales_zonas=len(z),celdas_originales_localidades=len(d),
        escenarios=['Conservador','Central','Alto'],alto_igual_central_por_falta_de_otro_extremo_justificado=True,
        OD_zonales_clase=len(az)//3,OD_zonales_clase_ambas_campanas=int(az.demanda_anual_ventana12h.notna().sum()/3),
        OD_localidad_clase=len(ad)//3,OD_localidad_clase_ambas_campanas=int(ad.demanda_anual_ventana12h.notna().sum()/3),
        OD_localidad_clase_con_algun_flujo=int(ad.aporte_parcial_meses_con_perfil_12h.notna().sum()/3),
        convencion_meses={'Verano':[12,1,2],'Otono':[3,4,5],'Invierno':[6,7,8],'Primavera':[9,10,11]},
        decisiones=['Escenario central aplica perfil de verano90dias y otono275dias; no implica365observados.',
          'Primavera e invierno no observadosCITRA: proxyOtono autorizado, separado como imputaciontemporal.',
          'Solo celdas con verano y otono con flujo reciben escenario anual365dias. Las demas conservan parcial90o92dias.',
          'Transferencia a sabados/domingos no esta validada; multiplicar por dias calendario es supuesto explicito, no expansion observada.',
          'Sensibilidad invierno usa razonInvierno/Primavera2024PNCde mismafamilia vial, clases aproximadas y sin sentido: no factorcertificado porcontrol.',
          'PNC63rama2como proxyRuta7/E0701,E0702;PNC64rama1como proxyRuta265/E1003; no se afirma co-localizacion.',
          'PerfilesPNCpublicados pueden incluir expansiondiurna: ratio transferidoa12h soloformasestacionales bajo supuesto, no identifica factor12a24.',
          'No se mezclan ARISTOOD ni logit; no se suman controles; contrastes6.72 permanecen como incertidumbre.',
          'Alto coincide con Central: no se inventa incremento porcentual ni se cambia pantalla para maximizar flujo. Contrastes entre controles se conservan aparte, no son intervalo de confianza.',
          'Zonal31a39CAM tiene2campanas pero distintaslocalidades. Anualzonas no reconcilia automaticamente con subODcomunes; se entrega agregaciondetallada aparte.'],
        soporte_horario={'coeficientes_generales_MOP':'Verano1.46,Invierno1.29,Primavera1.35 documentados previamente; no compatibles porcontrol/sentido/clase08a20 para caso base',
                         'urbanos_CITRA':'Perfiles07a21 o07a23/veq; sin equivalencia demostrada a seccionesEOD interurbanas; no aplicados',
                         '24h':'No estimable desde aforos disponibles; campos permanecen null'},
        fuentes={str(p):sha(p) for p in [src/'csv/matriz_zonas_ARISTO.csv',src/'csv/matriz_localidades.csv',src/'csv/comparaciones_controles.csv',src/'resumen_validacion.json',pnc]})
    (out/'supuestos_validacion.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fuente-citra',required=True);p.add_argument('--pnc',required=True);p.add_argument('--salida',required=True);p.add_argument('--anio',type=int,default=2026);a=p.parse_args()
    print(json.dumps(run(a.fuente_citra,a.pnc,a.salida,a.anio),ensure_ascii=False,indent=2))
