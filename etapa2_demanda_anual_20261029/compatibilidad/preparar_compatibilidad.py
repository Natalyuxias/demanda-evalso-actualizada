"""Compatibilidad ARISTO/CITRA desde las entregas cerradas, sin sumar flujos."""
from pathlib import Path
import argparse
import hashlib
import json
import math

import pandas as pd


KEY = ['campana', 'zona_origen', 'zona_destino', 'segmento']
FIELDS = [
    ('fuente', 'ARISTO / CITRA', 'Fuente independiente; nunca factorizar una con proporciones OD de la otra'),
    ('bloque', 'lacustre_actual / terrestre_corredor', 'El ferry actual no es Bahía Jara–Levicán'),
    ('version_OD', 'A / B / no_aplica', 'A lacustre preserva residual; B distribuye solamente flujo físico medido'),
    ('escenario', 'conservador / central / alto / observado', 'Incertidumbre de exposición y anualización, no crecimiento o captación'),
    ('anio_referencia', 'entero', 'Calendario normalizado; no tráfico anual efectivamente observado'),
    ('mes', '1–12 o faltante para anual', 'Correspondencia explícita con temporada/fuente de perfil'),
    ('temporada_destino', 'Verano / Otoño / Invierno / Primavera', 'Invierno aproximado desde otoño sigue siendo proxy'),
    ('campana_fuente', 'etiqueta original', 'No rotular una observación otoñal como invierno medido'),
    ('zona_origen', '1–55 o faltante', 'Código modelación ARISTO; no ID geográfico BBDD-2'),
    ('zona_destino', '1–55 o faltante', 'Los residuales no reciben zona inventada'),
    ('origen_detalle', 'texto original/referencial', 'No transformar la comuna a una localidad no observada'),
    ('destino_detalle', 'texto original/referencial', 'Mantener escala y advertencias de geocodificación'),
    ('sentido_OD', 'origen → destino', 'No sustituye sentido del cruce o sentido de control'),
    ('sentido_control', 'código/ferry declarado', 'Respetar codificación de cada fuente/campaña'),
    ('segmento', 'VL / CAM / VP / PEATON / MOTO / BICI / OTRO_PASAJERO', 'VP otoño no equivale a VL cuatro ruedas'),
    ('unidad', 'unidad física de clase', 'Vehículos, peatones, motos/bicis y pasajeros no identificados no se suman'),
    ('vista', 'componentes / privados_compatibles', 'Vista agregada alternativa no sumable con sus componentes'),
    ('fechas_observadas', 'lista ISO', 'No confundir fechas de muestra con representatividad mensual'),
    ('pantalla', 'control elegido o ferry', 'CITRA conserva una pantalla por flujo y las alternativas separadas'),
    ('exposicion_observada', 'embarques fechados / ventana08–20', 'Exposiciones diferentes, no total conjunto automático'),
    ('flujo_observado_asignado', 'numérico o faltante', 'Asignación OD mediante muestra del mismo estrato, no universo certificado'),
    ('flujo_imputado_OD', 'numérico o faltante', 'Solo ARISTO bajo límites de donante compatibles'),
    ('flujo_residual', 'numérico o faltante', 'F conocido sin OD; no mercado terrestre desconocido inventado'),
    ('subtipo_residual', 'externo_no_especificado / sin_perfil / conteo_desconocido', 'No fusionar incertidumbre geográfica con falta de conteo'),
    ('imputacion_temporal', 'booleano y descripción', 'Proxy primavera/otoño/invierno y exposición programada explícitos'),
    ('factor_12_24', 'numérico compatible o faltante', 'Sin respaldo, demanda de24h no estimable'),
    ('demanda_anual_12h', 'numérico o faltante', 'CITRA: referencia anual de ventana, no día completo'),
    ('demanda_anual_24h', 'numérico o faltante', 'No rellenar si falta factor horario compatible'),
    ('demanda_anual_operacional', 'numérico o faltante', 'ARISTO: escenario de operaciones, no servicio efectivamente ejecutado certificado'),
    ('nivel_confianza', 'observado / condicionado / proxy / no_estimable', 'No certeza individual ni representatividad certificada'),
    ('cobertura', 'texto', 'Partes no observadas permanecen desconocidas, no ceros'),
    ('fuente_imputacion_OD', 'misma fuente o faltante', 'ARISTO no puede completar OD terrestres'),
    ('evidencia', 'archivo/hoja/filas/páginas', 'Fuente original y cache validada diferenciadas'),
    ('permite_total_conjunto', 'False', 'No sumar exposiciones/fuentes incompletas para un mercado artificialmente completo'),
]


def missing(x):
    return x is None or bool(pd.isna(x))


def validar_reglas(rows):
    """Validaciones semánticas reutilizables, sin estimar ni completar demanda."""
    for r in rows:
        terrestrial = r.get('fuente') == 'CITRA' or r.get('bloque') == 'terrestre_corredor'
        imputed = r.get('flujo_imputado_OD')
        if terrestrial and r.get('fuente_imputacion_OD') == 'ARISTO' and not missing(imputed) and imputed > 0:
            raise ValueError('CITRA no puede completarse con proporciones OD de ARISTO')
        if r.get('segmento') == 'VP' and r.get('unidad') == 'vehiculos_livianos_4_ruedas':
            raise ValueError('VP agregado no equivale a VL estricto')
        if terrestrial and not missing(r.get('demanda_anual_24h')) and missing(r.get('factor_12_24')):
            raise ValueError('No identificar24h desde12h sin factor compatible')
        if r.get('subtipo_residual') in ['externo_no_especificado', 'sin_perfil']:
            if not missing(r.get('zona_origen')) and not missing(r.get('zona_destino')):
                raise ValueError('Residual desconocido no debe recibir un OD zonal completo inventado')
    return True


def main():
    p = argparse.ArgumentParser(); p.add_argument('--anexos', type=Path, default=Path('.'))
    p.add_argument('--salida', type=Path, required=True); args = p.parse_args()
    root, out = args.anexos, args.salida
    if (out/'resumen_compatibilidad.json').exists(): raise FileExistsError('Elegir carpeta nueva')
    out.mkdir(parents=True, exist_ok=True)
    ap = root/'etapa1_lacustre_aristo_20261029/resultados/entrega_final/csv/matriz_zonas_ARISTO.csv'
    cp = root/'etapa1_terrestre_citra/resultados/cierre_final_04/csv/matriz_zonas_ARISTO.csv'
    dp = root/'etapa1_terrestre_citra/resultados/cierre_final_04/csv/auditoria_112.csv'
    ar, ct, audit = (pd.read_csv(x) for x in [ap, cp, dp])
    assert not ar.duplicated(KEY).any() and not ct.duplicated(KEY).any()
    for frame in [ar, ct]:
        assert frame.zona_origen.between(1, 55).all() and frame.zona_destino.between(1, 55).all()
    ak = ar[KEY+['flujo_asignado_exposicion_medida']].copy()
    ck = ct[KEY+['flujo_corredor_12h']].copy()
    ak['ARISTO_registrado'] = True; ck['CITRA_registrado'] = True
    merged = ak.merge(ck, on=KEY, how='outer', validate='one_to_one')
    merged['ARISTO_estimacion_disponible'] = merged.flujo_asignado_exposicion_medida.notna()
    merged['CITRA_estimacion_disponible'] = merged.flujo_corredor_12h.notna()
    merged['estado'] = ['Ambas fuentes con referencia, exposiciones distintas' if a and c else 'Solo lacustre con flujo; terrestre desconocido/no cubierto' if a else 'Solo terrestre con flujo; no inferir ausencia lacustre' if c else 'Solo estructura muestral sin flujo compatible' for a, c in zip(merged.ARISTO_estimacion_disponible, merged.CITRA_estimacion_disponible)]
    merged['permite_sumar_directamente'] = False
    merged['razon'] = 'Ferry: filas de embarque; terrestre: medias de12h en otras fechas y cobertura parcial. Anualización no elimina diferencia de universo.'
    merged.to_csv(out/'compatibilidad_OD_campana_clase.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(FIELDS, columns=['campo', 'dominio', 'regla']).to_csv(out/'diccionario_base_unificada.csv', index=False, encoding='utf-8-sig')
    eligible = audit[audit.categoria.isin(['A', 'B'])]
    tests = {
        'zonas_ARISTO_1_55_en_ambos_bloques': True,
        'claves_fuente_unicas_antes_de_contraste': True,
        'CITRA_109_elegibles': len(eligible) == 109,
        'ninguna_alternativa_ferry_compatible_en_cohorte_CITRA_elegible': not eligible.alternativa_barcaza_compatible.any(),
        'CITRA_ruta_completa_no_observada': not eligible.itinerario_integro_por_Chile_observado.any(),
        'CITRA_solo_VL_CAM': set(ct.segmento) <= {'VL', 'CAM'},
        'VP_no_unido_con_VL_por_codigo': not ((merged.segmento == 'VP') & merged.CITRA_estimacion_disponible).any(),
        'sin_total_conjunto_automatico': not merged.permite_sumar_directamente.any(),
    }
    assert all(tests.values()), tests
    summary = {
        'claves_ARISTO_registradas': len(ar), 'claves_ARISTO_con_flujo': int(ar.flujo_asignado_exposicion_medida.notna().sum()),
        'claves_CITRA_registradas': len(ct), 'claves_CITRA_con_flujo': int(ct.flujo_corredor_12h.notna().sum()),
        'claves_union': len(merged), 'claves_registradas_en_ambas': int((merged.ARISTO_registrado.eq(True) & merged.CITRA_registrado.eq(True)).sum()),
        'claves_con_flujo_en_ambas': int((merged.ARISTO_estimacion_disponible & merged.CITRA_estimacion_disponible).sum()),
        'solo_ARISTO_con_flujo': int((merged.ARISTO_estimacion_disponible & ~merged.CITRA_estimacion_disponible).sum()),
        'solo_CITRA_con_flujo': int((~merged.ARISTO_estimacion_disponible & merged.CITRA_estimacion_disponible).sum()),
        'CITRA_sin_muestra_ferry_compatible': len(eligible),
        'pruebas': tests,
        'interpretacion_doble_conteo': 'La ausencia de alternativa ferry compatible en los controles/sentidos ya auditados apoya separar bloques; no prueba itinerario individual observado ni permite deduplicacion por identidad entre fuentes.',
        'VP_compatible_alternativo': 'Puede sumarse VL+MOTO+BICI de primavera/verano como privados compatibles con VP de Normal, en vista alternativa. No convertir VP en VL ni sumar esa vista a sus componentes.',
        'integracion': 'Concatenar bloques con fuente/unidad/exposicion/estado. Clave comun no autoriza sumar flujos. No usar distribucion ARISTO para desconocidos CITRA.',
        'fuentes_sha256': {str(x): hashlib.sha256(x.read_bytes()).hexdigest() for x in [ap, cp, dp]},
    }
    (out/'resumen_compatibilidad.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['fuentes_sha256']}, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
