# Etapa 1 empírica de CITRA

> Antecedente conservado. El usuario autorizó después cambiar el resultado principal a demanda observada del corredor, con alta confianza inferida y límites explícitos. El estado vigente está en [cierre de viabilidad CITRA](12_cierre_citra_corredor.md). Los resultados de esta ejecución estricta no se sobrescribieron.

Esta etapa cierra las 29 homologaciones aprobadas y revalida las 112 entrevistas que el filtro anterior denominaba tierra confirmada. Los ocho extremos ambiguos del lote revisado permanecen pendientes. Los originales, las coordenadas y las decisiones anteriores se conservan.

La matriz principal exige evidencia suficiente del itinerario completo por Chile. Las fuentes disponibles no permiten identificarlo: un control chileno puede ser compatible con un recorrido mixto que incluya pasos argentinos. Los campos de ruta y pasos efectivos no están en las EOD CITRA entregadas. El resultado principal es **no identificado**, nunca demanda cero. No se utilizan probabilidades del logit ni imputaciones de Etapa 13.

El análisis local entrega además una estimación auxiliar de la fracción del corredor chileno observado, con su propia selección de pantallas, exposición y limitaciones. No se publica su detalle ni se lo denomina demanda de itinerarios íntegramente chilenos. La existencia de un recorrido en red por Argentina tampoco se interpreta como uso observado de ese país; la red no certifica habilitación del paso en cada fecha.

## Decisiones de implementación

- La homologación es una capa adicional por registro/extremo. Solo se aplican las 29 claves autorizadas. El texto, JSON y coordenadas originales no se desplazan; Puerto Río Tranquilo conserva la alerta del límite.
- Se reconstruyen la red física y los puntos EOD desde los archivos geográficos originales. Los conectores zonales nominales y los arcos acuáticos no forman parte de la red carretera. El enlace entre terminales solo sirve para comprobar una alternativa de itinerario, sin estimar demanda lacustre.
- Se distingue interceptación observada de ruta inferida. Se comprueban punto, sentido, extremos, red y compatibilidad de alternativas. Las distancias producen testigos reproducibles, sin asumir que se eligió el camino más corto.
- La expansión usa `w=F/N` por campaña, fecha, sección, sentido, clase y ventana 08–20. El denominador contiene todas las entrevistas originales compatibles, antes de filtrar área o ruta. No se usan conteos urbanos ni factores temporales de 24 horas.
- Duplicados no resueltos, intervalos repetidos, fechas u horas inconsistentes y muestra mayor que aforo mantienen el estrato sin expansión. No se eliminan registros para forzar un balance.
- Se elige un cordón por OD zonal ordenado, campaña y clase para preservar la coherencia de la agregación de localidades. El rango prioriza factor compatible, cobertura geométrica, corte obligatorio y exposición válida; no mayor muestra o mayor flujo OD.
- Las estimaciones por control alternativo se conservan sin sumarlas. Los controles en serie no son demanda adicional. La independencia de ramas debe demostrarse antes de sumar.
- Un OD detallado sin muestra compatible en la pantalla elegida conserva flujo faltante. Las tablas diarias identifican por separado el cero muestral del estimador proporcional; no representa inexistencia poblacional.

## Archivos locales producidos

El generador escribe cuatro Excel, CSV auditables, el informe HTML y las validaciones en una carpeta nueva elegida por el usuario:

1. Homologación cerrada y aplicación de las 29 decisiones.
2. Matrices principales y auxiliares, detalladas y por zonas ARISTO.
3. Auditoría individual de las 112 entrevistas y testigos de itinerarios posibles.
4. Pantallas, estimaciones alternativas por jornada, factores y universo del denominador.

Estos archivos contienen claves, coordenadas o celdas pequeñas y quedan fuera de GitHub. El [resumen público](../results/etapa1_citra/resumen_publico.json) contiene únicamente alcance global y método.

## Reproducción con insumos privados

La reproducción requiere los originales CITRA y SIG, la capa geográfica de la etapa anterior y las decisiones de alcance/aprobación. Las capas previas tienen scripts y hashes propios: no se sustituyen por un resultado de demanda. El generador coteja sus claves y hashes con las entrevistas originales y vuelve a calcular los aforos, factores, rutas y pantallas.

Primero se congelan los insumos existentes; el comando se detiene si intenta sobrescribir decisiones:

```bash
python scripts/etapa1_citra/preparar_decisiones.py \
  --base-anterior /ruta/privada/base_completa_filtrada.csv \
  --propuestas-geograficas /ruta/privada/propuestas_por_extremo.csv \
  --salida data/private/etapa1_citra_decisiones
```

Después se ejecuta la etapa en una carpeta nueva:

```bash
python scripts/etapa1_citra/correr_etapa1.py \
  --anexos /ruta/a/Anexos \
  --homologacion-previa /ruta/privada/homologacion_geografica_etapa1 \
  --decisiones data/private/etapa1_citra_decisiones \
  --salida outputs/etapa1_citra/NUEVA_EJECUCION
```

Los archivos originales esperados son los dos libros EOD CITRA con sus hojas `EOD` y `Flujos`, el KMZ de mediciones, los cuatro conjuntos SIG de red/nodos/puntos de pasada/zonificación y la capa administrativa IDE. La tabla `Zonas` ARISTO es un sistema distinto de los ID de `BBDD-2`; no se intercambian sus códigos.

Las dependencias de lectura están en `requirements.txt`. Las pruebas nuevas usan exclusivamente datos sintéticos:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
.venv/bin/python scripts/13_validar_repositorio.py --indice
```

No se dispone de un protocolo completo que certifique selección/no respuesta ni de itinerarios individuales. El balance `N*w=F` verifica aritmética, no representatividad. La exposición corresponde a fechas y ventanas de 12 horas compatibles, sin anualización. Identificar el bloque principal requiere información adicional de itinerario/pasos, o una decisión explícita de estudiar el corredor parcial con otro alcance poblacional.

## Conservación del trabajo exploratorio

Las etapas 07–15 y sus resultados anteriores permanecen. El logit, sus probabilidades, captación, inducción y mercados imputados son antecedentes exploratorios; no constituyen la estimación principal de esta nueva metodología. Las siguientes etapas de estacionalidad, proyecciones, costos, captación e inducción no se ejecutan aquí.
