"""Indicadores extranjeros y unidades de pasajeros: cache264 desde originales, sin expansion."""
from pathlib import Path
import argparse, hashlib, itertools, json
import pandas as pd

VEH=['Auto','Camioneta','Vehículo privado','Camión o furgón de carga','Moto']
def run(micro, diccionario, informe, salida):
    paths=[Path(micro),Path(diccionario),Path(informe)]
    metadata=json.loads((Path(micro).parent/'validacion_microdatos.json').read_text())
    assert all(metadata['verificaciones'].values())
    out=Path(salida);out.mkdir(parents=True,exist_ok=True)
    d=pd.read_csv(micro)
    assert len(d)==264 and d.id_encuesta.nunique()==264
    c=d[['id_encuesta','campana','sentido_cruce','b1__Día','b1__fila_BBDD1','b2__fila_BBDD2',
         'tipo_usuario_BBDD1','tipo_usuario_BBDD2','nacionalidad_declarada','patente_categoria_declarada',
         'ocupantes_vehiculo','tamano_grupo','b2__País','b2__País__2',
         'b1__Duplicada','b1__Validada']].copy()
    c['fuente_original']='Cap 6/BBDD EOD/Base de datos agregada.xlsx; BBDD-1 y BBDD-2 (solo válidas)'
    c['nacionalidad_estado']=c.nacionalidad_declarada.fillna('Desconocida')
    c['patente_estado']=c.patente_categoria_declarada.fillna('Desconocida')
    c['nacionalidad_extranjera_observada']=c.nacionalidad_estado.eq('Extranjera')
    c['patente_extranjera_observada']=c.patente_estado.eq('Extranjera')
    c['pais_OD_conocido']=c['b2__País'].notna() & c['b2__País__2'].notna()
    c['OD_internacional_observado']=c.pais_OD_conocido & (c['b2__País'].ne('Chile')|c['b2__País__2'].ne('Chile'))
    flags=['nacionalidad_extranjera_observada','patente_extranjera_observada','OD_internacional_observado']
    c['algun_indicador_NO_total_extranjeros']=c[flags].any(axis=1)
    c['ambas_nacionalidad_patente_desconocidas']=c.nacionalidad_estado.eq('Desconocida') & c.patente_estado.eq('Desconocida')
    c['clase_vehicular']=c.tipo_usuario_BBDD1.isin(VEH)
    c['ocupacion_valor_positivo_entero']=c.ocupantes_vehiculo.gt(0) & c.ocupantes_vehiculo.mod(1).eq(0)
    c['grupo_valor_positivo_entero']=c.tamano_grupo.gt(0)&c.tamano_grupo.mod(1).eq(0)
    c['alerta_moto_ocupacion_atipica']=c.tipo_usuario_BBDD1.eq('Moto') & c.ocupantes_vehiculo.gt(2)
    c['alerta_peaton_columna_ocupantes']=c.tipo_usuario_BBDD1.eq('Pasajero (peatón)') & c.ocupantes_vehiculo.notna()
    c['alerta_vehiculo_columna_grupo']=c.clase_vehicular & c.tamano_grupo.notna()
    c['uso_ocupacion']='Descriptivo de respuestas; no prueba vehiculo unico ni permite total pasajeros'
    c['uso_grupo']='No multiplicar aforo peatonal por grupo; mecanismo de seleccion y unicidad desconocidos'
    c.to_csv(out/'auditoria_usuarios_264.csv',index=False)
    # Todas las combinaciones se conservan, incluidas las intersecciones vacias.
    inter=[]
    for n,p,i in itertools.product([False,True],repeat=3):
        mask=(c[flags[0]]==n)&(c[flags[1]]==p)&(c[flags[2]]==i)
        inter.append(dict(nacionalidad_extranjera=n,patente_extranjera=p,OD_internacional=i,entrevistas=int(mask.sum())))
    pd.DataFrame(inter).to_csv(out/'intersecciones_indicadores.csv',index=False)
    c.groupby(['nacionalidad_estado','patente_estado','OD_internacional_observado'],dropna=False).size().reset_index(name='entrevistas').to_csv(out/'intersecciones_con_desconocidos.csv',index=False)
    summary=c.groupby('tipo_usuario_BBDD1',dropna=False).agg(
        entrevistas=('id_encuesta','size'),nacionalidad_disponible=('nacionalidad_declarada','count'),
        patente_disponible=('patente_categoria_declarada','count'),ocupacion_disponible=('ocupantes_vehiculo','count'),
        grupo_disponible=('tamano_grupo','count'),
        suma_valores_ocupacion_NO_total_personas=('ocupantes_vehiculo',lambda x:x.sum(min_count=1)),
        suma_valores_grupo_NO_total_personas=('tamano_grupo',lambda x:x.sum(min_count=1))).reset_index()
    summary.to_csv(out/'disponibilidad_campos_por_usuario.csv',index=False)
    c.groupby(['campana','sentido_cruce','tipo_usuario_BBDD1'],dropna=False).agg(
        entrevistas=('id_encuesta','size'),ocupacion_no_faltante=('ocupantes_vehiculo','count'),
        ocupacion_media_respuestas_NO_tasa_certificada=('ocupantes_vehiculo','mean'),
        grupo_no_faltante=('tamano_grupo','count'),grupo_media_respuestas=('tamano_grupo','mean')).reset_index().to_csv(out/'ocupacion_grupos_descriptivos.csv',index=False)
    peat=c.tipo_usuario_BBDD1.eq('Pasajero (peatón)')
    s=dict(entrevistas=264,peatones=int(peat.sum()),nacionalidad_declarada_no_faltante=int(c.nacionalidad_declarada.notna().sum()),
           nacionalidad_extranjera=int(c[flags[0]].sum()),patente_extranjera=int(c[flags[1]].sum()),
           OD_internacional=int(c[flags[2]].sum()),algun_indicador_NO_total_extranjeros=int(c[flags].any(axis=1).sum()),
           ambas_condiciones_nacionalidad_patente_desconocidas=int(c.ambas_nacionalidad_patente_desconocidas.sum()),
           nacionalidad_y_ODinternacional=int((c[flags[0]]&c[flags[2]]).sum()),
           patente_y_ODinternacional=int((c[flags[1]]&c[flags[2]]).sum()),
           vehiculares_ocupacion_completa=int((c.clase_vehicular&c.ocupantes_vehiculo.notna()).sum()),
           vehiculares=int(c.clase_vehicular.sum()),peatones_grupo_disponible=int((peat&c.tamano_grupo.notna()).sum()),
           peatones_grupo_faltante=int((peat&c.tamano_grupo.isna()).sum()),
           total_personas_estimado=False,total_pasajeros=None,
           conclusiones=[
             'Nacionalidad declarada, categoria nacional/extranjera de patente y pais OD son variables distintas. No equivalen a residencia ni nacionalidad de todos los ocupantes.',
             'La patente disponible es una categoria, no un identificador vehicular. No permite eliminar respuestas repetidas del mismo vehiculo ni demostrar una respuesta por vehiculo.',
             'N puede superar F por respuesta multiple, cobertura temporal, clase o conteo; conservar sin deduplicar/imputar. Factor F/N menor que uno es asignacion condicional, no prueba de diseno muestral.',
             'Peatones:81 con tamano de grupo,18 sin el. No reemplazar grupo con ocupantes de otro campo. No sumar tamanos como personas unicas sin identidad de grupo.',
             'Una moto declara7 ocupantes: conservar literal y senalar alerta; no usar tasa automatica ni corregir a2.',
             'Seis entrevistas de pasajeros de bus/VAN/transfer no equivalen a seis vehiculos. Campos de ocupacion no cubren a todos ni certifican todos los pasajeros.',
             'No puede estimarse total completo de pasajeros de la nave con estas respuestas sin certificar unidad de seleccion y dominios excluyentes. Aforos de vehiculos y peatones quedan separados.'
           ],
           formulas_condicionales=[
             dict(formula='Q_OD_peaton=F_peaton*n_OD/N_respuestas_peaton',estado='Asignacion OD condicionada a representatividad de respuestas individuales; no ponderador oficial',aplicacion='Mantener denominador completo compatible y N/F auditado; F es personas peatonales, no multiplicar por grupo'),
             dict(formula='Q_OD_peaton_grupos=F_peaton*sum(g_OD)/sum(g)',estado='NO aplicar',aplicacion='Solo si se demuestra representante unico por grupo y mecanismo de muestreo por grupos; hay18 grupos faltantes'),
             dict(formula='P_ocupantes_clase=F_vehiculos_clase*media_ocupacion_clase',estado='NO aplicar automaticamente',aplicacion='Requiere una respuesta por vehiculo, ocupacion valida, representatividad y mismo estrato; no demostrados'),
             dict(formula='P_total=P_peatones+P_ocupantes_vehiculos+P_buses',estado='NO identificado',aplicacion='Requiere cobertura completa y categorias excluyentes; aforo peatones debe excluir ocupantes ya contados')
           ],
           referencias=[
             dict(archivo='Cap6/BBDD EOD/DiccionarioAPP.xlsx',hoja='Hoja1',filas='4-13 modos;14-21 nacionalidad y patente;92-123 recorridos declarados',uso='Categorias diferentes de nacionalidad y patente'),
             dict(archivo='Informe ARISTO.pdf',PDF_pagina=170,pagina_impresa=157,seccion='6.1.1.1',uso='Diseno formulario, nacionalidad para peatones, patente para vehiculos'),
             dict(archivo='Informe ARISTO.pdf',PDF_pagina=171,pagina_impresa=158,seccion='6.1.1.1',uso='Ocupantes autos/camionetas/motos/camiones y grupo peatones/paxbus'),
             dict(archivo='Informe ARISTO.pdf',PDF_pagina=20,pagina_impresa=7,seccion='2.2.5-2.2.6',uso='Tasas ocupacion y grupos; marco de expansion'),
             dict(archivo='Informe ARISTO.pdf',PDF_pagina=220,pagina_impresa=207,seccion='Tabla138',uso='Bicicletas sumadas a peatones en cuadro agregado'),
             dict(archivo='Informe ARISTO.pdf',PDF_pagina=236,pagina_impresa=223,seccion='Tabla169',uso='Bicicletas sumadas a peatones en cuadro agregado')],
           sha256_fuentes_originales_vinculadas=metadata['sha256_fuentes'],
           fuentes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    assert s['nacionalidad_extranjera']==5 and s['patente_extranjera']==10 and s['OD_internacional']==13
    assert sum(r['entrevistas'] for r in inter)==264
    (out/'usuarios_resumen.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
    return s

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--microdatos',required=True);p.add_argument('--diccionario',required=True);p.add_argument('--informe',required=True);p.add_argument('--salida',required=True);a=p.parse_args()
    print(json.dumps(run(a.microdatos,a.diccionario,a.informe,a.salida),ensure_ascii=False,indent=2))
