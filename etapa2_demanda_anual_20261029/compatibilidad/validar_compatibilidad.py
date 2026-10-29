"""Valida bases de consolidacion; no suma universos o unidades incompatibles."""
from pathlib import Path
import argparse,json,hashlib
import pandas as pd

def run(terrestre,lacustre_base,out):
    terrestre,lacustre_base,out=Path(terrestre),Path(lacustre_base),Path(out)
    out.mkdir(parents=True,exist_ok=True)
    t=pd.read_csv(terrestre);l=pd.read_csv(lacustre_base)
    k=['zona_origen','zona_destino','segmento','escenario','anio']
    assert not t.duplicated(k).any()
    assert t.demanda_anual24h.isna().all()
    assert t.loc[t.demanda_anual_ventana12h.notna(),'dias_con_perfil_o_proxy'].eq(365).all()
    assert t.loc[t.dias_con_perfil_o_proxy.lt(365),'demanda_anual_ventana12h'].isna().all()
    table=[dict(segmento_CITRA='VL',segmento_ARISTO='VL',compatibilidad_fisica='Condicionada',
                razon='Vehiculos livianos; verificar mismos subtipos y exclusiones; ARISTOVPnoequivaleVL'),
           dict(segmento_CITRA='CAM',segmento_ARISTO='CAM',compatibilidad_fisica='Condicionada',
                razon='Camiones; conciliar ejes/furgones y no agregar toneladas a vehiculos'),
           dict(segmento_CITRA=None,segmento_ARISTO='VP',compatibilidad_fisica='No sumable a VL',
                razon='Privados agrega categoriasfisicas heterogeneas; no es vehiculo liviano puro'),
           dict(segmento_CITRA=None,segmento_ARISTO='PEATON',compatibilidad_fisica='Sin bloque terrestre equivalente',
                razon='Personas peatones; ausenciaCITRAnoesdemanda cero'),
           dict(segmento_CITRA=None,segmento_ARISTO='MOTO',compatibilidad_fisica='Sin bloque terrestre equivalente',
                razon='Motocicletas; no imputar desdeVL'),
           dict(segmento_CITRA=None,segmento_ARISTO='BICI',compatibilidad_fisica='Sin bloque terrestre equivalente',
                razon='Bicicletas; no imputar desdeVL'),
           dict(segmento_CITRA=None,segmento_ARISTO='BUS_TP',compatibilidad_fisica='Sin bloque terrestre equivalente',
                razon='Buses no pasajeros; no sumarocupantes ni entrevistasdepaxbus como buses')]
    pd.DataFrame(table).to_csv(out/'compatibilidad_segmentos.csv',index=False)
    result=dict(esquema_canonico=['fuente','version_OD','alternativa_observada','nivel_geografico','origen_original','destino_original',
              'origen','destino','zona_origen','zona_destino','segmento','unidad_fisica','anio','mes','escenario',
              'flujo','unidad_temporal','ventana_observada','campana_fuente','fecha_fuente','control','sentido_control',
              'alcance_espacial','estado_dato','imputacion_geografica','imputacion_temporal','factor_crecimiento'],
        prohibicion_suma_actual=True,
        causa='CITRAestimaanual deventana08a20 (24hnoidentificado);ARISTOestimaoperaciones debarcaza porfechas/frecuencias. '
              'Aunconvehiculos iguales, no son unidades temporales homogéneas para sumarterrestre+lacustre.',
        puede_consolidar_tabla_larga=True,puede_sumar_como_mercado_total=False,
        comparacion_permitida='Contraste con etiquetas explicitas de ventana/exposicion, sin total modal/mercado conjunto',
        reglas=['No combinar escenarios distintos enunasuma.',
                'No sumar versionesOD_A yOD_B:representanmismoaforo con tratamiento deperfil diferente.',
                'Celdas sin OD o zona conservar como residuos; no distribuir desdeotra fuente.',
                'CITRAestacorredor parcial,ARISTOcruceactual: mantenerfuente ymecanismodeobservacion; no es disponibilidadcomun de alternativas.',
                'No transformar localidades de unacomuna en cabecera; codigosBBDD2noson55zonas.',
                'Anuales zonales deperfiles propios ysumasdesubODcomunes tienen soportesdiferentes: no forzarbalanceconimputaciones.',
                'No sumar aforo peatonal y vehiculoscomo personas; pasajeros totales desconocidos.',
                'Perfiles extranjeros se mantienen como indicadores independientes; no restar automaticamente nacionalidad/patente/ODinternacional de demanda fisica.',
                'Anualizacion describeaño normalizado, no crecimiento; factorcrecimiento1.'],
        pruebas=dict(citra_clave_unica=True,citra_24h_faltante=True,citra_anual_solo365diasproxy=True,
                     citra_parcial_no_convertido_aanual=True,
                     segmentos_lacustres_observados=sorted(l.segmento.dropna().unique()),
                     segmentos_citra_observados=sorted(t.segmento.dropna().unique())),
        fuentes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [terrestre,lacustre_base]})
    (out/'esquema_y_validacion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--terrestre-anual',required=True);p.add_argument('--lacustre-base',required=True);p.add_argument('--salida',required=True);a=p.parse_args()
    print(json.dumps(run(a.terrestre_anual,a.lacustre_base,a.salida),ensure_ascii=False,indent=2))
