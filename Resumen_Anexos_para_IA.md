# Resumen de Anexos para evaluar su utilidad con IA

## Propósito y alcance

La carpeta reúne estadísticas, mediciones, encuestas, modelos de transporte, costos de proyectos y cartografía. Su utilidad probable es apoyar el diagnóstico y la planificación de conectividad del sur de Chile, especialmente Los Lagos, Aysén y Magallanes, incluyendo conexiones con Argentina. Esta finalidad se infiere de su contenido; no se dispone aquí del informe principal que define el estudio.

Este resumen permite que otra IA identifique datos útiles y proponga análisis. Se basa en el inventario de archivos, nombres de hojas y muestras de planillas, atributos de algunas capas geográficas y contenido del documento Word. No equivale a una auditoría completa de valores, fórmulas, metodología o calidad. Si la IA recibe solo este resumen, puede evaluar utilidad potencial; para obtener resultados numéricos deberá acceder a los archivos originales.

Ruta original: `/home/nataly/Escritorio/Anexos`. Las rutas del inventario son relativas a esa carpeta y se mantienen utilizables si se copia la carpeta completa.

## Contenido por carpeta y utilidad potencial

| Carpeta | Datos presentes | Utilidad potencial |
|---|---|---|
| Cap 3 | Población Censo 2017 por territorio, sexo y edad; ingresos CASEN e INE; tasas de desocupación; PIB regional y sectorial; comercio exterior; pesca y acuicultura; turismo; flujos vehiculares; tráfico aéreo y fronterizo. | Caracterizar población y economía, estudiar evolución de tráfico y turismo, aportar variables explicativas a modelos de demanda. Los períodos y unidades difieren entre fuentes. |
| Cap 5 | Características y capacidad de naves, rampas portuarias, tiempos de navegación; servicios, vehículos, responsables y recorridos de transporte público; vuelos, horarios, tiempos y tarifas. | Describir oferta de transporte, comparar alternativas de viaje y examinar capacidad de infraestructura y servicios. El registro de transporte público contiene distintas clases de servicios, incluso taxis. |
| Cap 6 | Encuestas origen y destino, diccionarios de variables, mediciones de flujo en carreteras, pasos fronterizos y transbordadores; registros GPS con coordenadas, fechas, horas y referencias a videos. | Analizar patrones de viaje, composición vehicular y estacionalidad; relacionar recorridos con mediciones; preparar o verificar insumos del modelo. |
| Cap 7 | Red vial actual y de 2030, nodos, zonificación, centroides, puntos de pasada y rutas; atributos físicos, velocidades y costos; planillas HDM4. | Analizar conectividad, tiempos y costos de recorridos, construir una red y comparar escenarios de infraestructura. |
| Cap 8 | Matrices de viajes por origen y destino, temporada y tipo de vehículo; relaciones entre viajes, arcos y puntos de pasada; factores de proyección y matrices para 2030, 2040 y 2050. | Examinar demanda estimada y futura, distribución de viajes y supuestos de crecimiento. Las proyecciones son resultados de un modelo, no mediciones futuras. |
| Cap 9 | Proyectos, intervenciones viales, vínculo con conectividad, longitudes de caminos y puentes, costos unitarios y totales en UF y pesos. | Comparar inversiones y preparar una priorización al combinar costos con demanda, accesibilidad y beneficios que se puedan sustentar. |
| Cap 10 | Resúmenes de rutas de la red actual y de 2030 con origen, destino, tiempos y costos para vehículos livianos y pesados. | Comparar recorridos entre escenarios y detectar cambios en tiempos y costos. |
| SIG | Caminos, nodos, aeropuertos, puertos, transbordadores, fronteras y límites administrativos; salud, educación, turismo, patrimonio, energía, ciclovías; cobertura digital y acceso a servicios. | Cruzar transporte y territorio, localizar servicios y atractivos, estudiar accesibilidad y elaborar mapas. |

## Archivos para comenzar el análisis

- `SIG/TABLA DE SHAPEFILES ACTUALIZADO.xlsx`: catálogo con región, nombre de cobertura, tipo de entidad, sistema de referencia, descripción y fuente. Es el punto de entrada para interpretar la cartografía.
- `Cap 6/BBDD EOD/Base de datos agregada.xlsx`: incluye hojas de bases de encuestas, registros válidos, puntos de medición y tablas por transbordadores, fronteras y carretera.
- `Cap 6/BBDD EOD/DiccionarioAPP.xlsx`: ayuda a interpretar las variables del levantamiento de encuestas.
- `Cap 6/Mediciones de flujo/Consolidado Flujos.xlsx`: integra conteos por modo, lugar, fecha, temporada y sentido de viaje.
- `Cap 7/SIG Red_Vial_Final/Red_Vial_Final.xlsx` y su capa `.shp`: atributos de la red vial que permiten vincular rutas, nodos, longitudes, velocidades y costos.
- `Cap 7/HDM4/Costos_Red_Vial_Actual.xlsx` y `Costos_Red_Vial2030.xlsx`: insumos para comparar condiciones y costos de las redes.
- `Cap 8/Matrices Situación Actual.xlsx`: viajes estimados por zona de origen y destino, con hojas de primavera, verano y otoño para VL y VP.
- `Cap 8/Factores de proyección de flujos.xlsx`: hojas PIB, Aéreo, Ruta y Fronteras. La hoja PIB declara histórico 1996–2025 y proyección 2026–2050 en escenarios Base y Optimista.
- `Cap 8/Matrices 2030 Tend.xlsx`, `Matrices 2040 Tend.xlsx` y `Matrices 2050 Tend.xlsx`: hojas con campos `i`, `j` y `viajes_ajustados`.
- `Cap 9/Planilla PPTT 4.xlsx`: hoja Costos Proyectos, con costos en UF y pesos; declara UF de 39.643,59 pesos al 01/12/2025. Esta es una referencia de la planilla, no un valor actual verificado.
- `Cap 10/Resumen_Rutas_Red_Vial_Actual.xlsx` y `Resumen_Rutas_Red_Vial_2030.xlsx`: resultados resumidos para contrastar escenarios.

## Ejemplos concretos de datos y claves de relación

| Conjunto | Campos observados | Relación o análisis posible |
|---|---|---|
| Red vial final | RUTA, CURVATURA, PENDIENTE, TIPO_PAVIM, ESTADO_PAV, NUM_PISTAS, LONGITUD, ID_Arco, Nodo_A, Nodo_B, velocidades y costos VL y VP. | Vincular arcos con nodos y recorridos; comparar longitud, velocidad y costo. La capa contiene 695 registros según su cabecera DBF. |
| Encuestas procesadas del Cap 8 | ID, versión o temporada, lugar de encuesta, sentido, día, hora, tipo de usuario, origen, destino y zonas. | Agrupar viajes y relacionarlos con zonas y puntos de control. |
| Flujos consolidados | Origen, destino, ruta, temporada, fecha, peatones y categorías de vehículos. | Comparar demanda observada por fecha, lugar y categoría. |
| GPS de noviembre 2025 | Archivo, Latitud, Longitud, fecha, hora y Fecha_Hora. | Reconstruir recorridos y asociar referencias de video. La capa Shape_GPS_nov_2025 tiene 67.089 registros según su cabecera DBF. Una referencia de video no demuestra que el video esté incluido. |
| Establecimientos de salud | Identificadores, tipo, nombre, dirección, comuna, región, latitud y longitud. | Evaluar acceso territorial a servicios y enlazar con límites administrativos. |
| Cobertura móvil 5G | Códigos territoriales, región, provincia, comuna, MEDICION, ORDEN_MED y SOC_24. | Examinar cobertura por territorio una vez interpretadas las variables con sus metadatos. |

Claves candidatas: códigos de comuna o CUT, identificadores de zona, ID_Arco y códigos de nodo. Antes de cruzar archivos, verificar que cada clave representa la misma entidad, versión territorial y escenario. No unir zonas del modelo con comunas solo porque sus códigos se parecen. VL y VP se usan para vehículos livianos y pesados; otras siglas, como PIJA o PNC, requieren consultar los diccionarios o el informe metodológico.

## Formatos y lectura

Inventario previo a crear este resumen: 550 archivos y 1.169.376.472 bytes, aproximadamente 1,17 GB en unidades decimales.

| Formato | Cantidad | Cómo interpretarlo |
|---|---:|---|
| .xlsx | 54 | Libros Excel con bases, tablas dinámicas, fórmulas y matrices; uno es temporal y comienza con ~$; quedan 53 libros no temporales. |
| .xls | 1 | Libro Excel antiguo de costos HDM4. |
| .xlsb | 1 | Libro Excel binario de metadatos GPS. |
| .shp | 61 | Capas vectoriales de puntos, líneas o polígonos. |
| .gpkg | 3 | Bases geográficas GeoPackage: puntos GPS y rutas de la red actual y de 2030. Las tablas examinadas declaran EPSG 4326. |
| .qgz | 4 | Proyectos QGIS; referencian capas y configuraciones de visualización. |
| .pdf | 2 | Anuario de turismo 2023 e informe de intensidad turística y destinos 2018, identificados por sus nombres. |
| .docx | 1 | Cálculos de tiempos de navegación entre Puerto Montt, Puerto Yungay y Puerto Natales, según ruta, mes y velocidad. |

Los shapefiles necesitan archivos compañeros: `.dbf` guarda atributos, `.shx` el índice, `.prj` las coordenadas y `.cpg` la codificación. También existen índices `.sbn`, `.sbx` y `.qix`, metadatos `.xml` y `.qmd`, archivos de configuración `desktop.ini` y bloqueos `.lock`. No contar cada componente como un conjunto de datos independiente ni separarlos al copiar una capa.

Los Excel se pueden leer con Excel, LibreOffice o bibliotecas compatibles con cada variante; las capas y los proyectos con QGIS. Para extracción automática, conservar hojas, encabezados multinivel, unidades y diccionarios. Las fórmulas y los valores almacenados deben distinguirse: algunas bibliotecas leen valores calculados previamente y no recalculan el libro.

## Comprobaciones que afectan las conclusiones

1. Separar mediciones, estadísticas externas, resultados calculados y proyecciones. Las matrices de situación actual contienen viajes estimados y no deben tratarse como conteos directos.
2. Verificar períodos, unidades, frecuencia y cobertura territorial. Hay población de 2017, ingresos de 2006–2020, flujos históricos, levantamientos de 2025 y escenarios futuros. La fecha del nombre de un archivo no certifica la fecha de todos sus datos.
3. Resolver versiones antes de sumar o comparar. Existen Anexo A y Anexo B con y sin Rev B, y archivos Arcos con sentido en Cap 7 y Cap 8. No asumir que son duplicados idénticos ni que Rev B es automáticamente la versión autorizada.
4. Consultar diccionarios para valores faltantes, categorías, sentido de viaje, factores de expansión y unidades de tiempo y costo. Verificar si los flujos son diarios, horarios o de otro período.
5. Revisar la correspondencia estacional: las matrices actuales usan Primavera, Verano y Otoño, mientras algunos factores contienen Invierno y las hojas tendenciales usan P, V e I. Confirmar su interpretación antes de comparar.
6. Revisar etiquetas de fórmulas y hojas: el libro Matrices 2050.xlsx conserva nombres de hojas que incluyen 25-30 y 26-30. Puede ser reutilización de nombres; no demuestra por sí sola que los cálculos correspondan a 2030 o que estén incorrectos.
7. Comprobar geometrías, coordenadas, conectividad de nodos, direcciones de los arcos y rutas a archivos al abrir proyectos QGIS. Las capas pueden usar diferentes sistemas de referencia.
8. El registro de transporte público contiene RUT, nombres y domicilios de responsables. Para el análisis de oferta suelen bastar variables de servicios, flota, recorridos y territorio; omitir identificadores personales de resultados compartidos cuando no sean necesarios.
9. No inferir rentabilidad social o causalidad solo a partir de costos y flujos. Para esas conclusiones se necesitan supuestos y metodología de evaluación, beneficios y escenarios comparables.

## Encargo sugerido para otra IA

Analiza este resumen y, cuando estén disponibles, los archivos originales. Determina qué conjuntos aportan mayor valor para estudiar transporte y conectividad del sur de Chile. Distingue contenido confirmado, utilidad potencial e información que todavía requiere verificación.

Entrega:

1. Una priorización de conjuntos de datos, con ruta, pregunta que permite responder, variables útiles y razón de su prioridad.
2. Una propuesta de cruces entre archivos, indicando claves y validaciones necesarias.
3. Análisis factibles de demanda, estacionalidad, accesibilidad, tiempos de viaje, costos y escenarios futuros.
4. Problemas concretos de calidad o interpretación que puedan cambiar los resultados, sustentados en los archivos que examines.
5. Conclusiones que ya puedan sostenerse y conclusiones para las que falten datos o metodología.

Si solo recibes el resumen, no inventes cifras, resultados de modelos ni validaciones de los originales. Si la pregunta de negocio no está definida, organiza la utilidad según diagnóstico territorial, modelación de transporte y evaluación de inversiones. Cita rutas y hojas para que cada afirmación pueda revisarse.

## Inventario de archivos principales

Se incluyen libros no temporales, documentos, capas principales, GeoPackages y proyectos QGIS. Se omiten aquí los componentes auxiliares de las capas.

### Cap 10

- `Cap 10/Resumen_Rutas_Red_Vial_2030.xlsx`
- `Cap 10/Resumen_Rutas_Red_Vial_Actual.xlsx`

### Cap 3

- `Cap 3/Actividades económicas/CCNN2018_PIB_REGIONAL.xlsx`
- `Cap 3/Actividades económicas/CCNN2018_PIB_XII_ACT.xlsx`
- `Cap 3/Actividades económicas/CCNN2018_PIB_XI_ACT.xlsx`
- `Cap 3/Actividades económicas/CCNN2018_PIB_X_ACT.xlsx`
- `Cap 3/Actividades económicas/Cosechas-centros-de-cultivo-por-region-2024.xlsx`
- `Cap 3/Actividades económicas/Desembarque-artesanal-por-region-2024.xlsx`
- `Cap 3/Actividades económicas/PIB CCNN2018_P0_V2.xlsx`
- `Cap 3/Actividades económicas/imcomex_subrei_anual_2024.xlsx`
- `Cap 3/Empleo/EMPLEO_TDNRM2.xlsx`
- `Cap 3/Flujos vehiculares/Ej.BBDD_PNC.xlsx`
- `Cap 3/Flujos vehiculares/Flujos_Vehiculares_PNC_2024-2022-2020-2018-2016-2014.xlsx`
- `Cap 3/Ingreso/INE ESIngresos/esi-hogares-con-becas_2010-2020.xlsx`
- `Cap 3/Ingreso/Ingresos CASEN/Ingreso_Casen_2006-2020.xlsx`
- `Cap 3/Ingreso/Ingresos CASEN/Ingreso_Casen_en_Pandemia_2020_revisada2022_09.xlsx`
- `Cap 3/Pasos Fronterizos/EOD_Cardenal_Samoré_2018.xlsx`
- `Cap 3/Pasos Fronterizos/Trafico Terrestre Año 2018 al 2025.xlsx`
- `Cap 3/Población/Censo Cantidad-de-Personas-por-Sexo-y-Edad.xlsx`
- `Cap 3/Población/Población comunal Censo 2017.xlsx`
- `Cap 3/Tráfico aéreo/BD_Trafico_aereo-2014-2025.xlsx`
- `Cap 3/Turismo/Informe-de-Intensidad-Turística-y-Definición-de-Destinos-Turísticos-2018-1.pdf`
- `Cap 3/Turismo/Resumen-destinos-turístico-en-Excel.xlsx`
- `Cap 3/Turismo/anuario-turismo-2023.pdf`
- `Cap 3/Turismo/cuadros-anuario-de-turismo-ano-2023.xlsx`
- `Cap 3/Turismo/series-mensuales-encuesta-mensual-de-alojamiento-turistico-(emat)-julio-2016-a-la-fecha.xlsx`

### Cap 5

- `Cap 5/Infraestructura portuaria/Anexo A (Rev B).xlsx`
- `Cap 5/Infraestructura portuaria/Anexo A.xlsx`
- `Cap 5/Infraestructura portuaria/Anexo B (Rev B).xlsx`
- `Cap 5/Infraestructura portuaria/Anexo B.xlsx`
- `Cap 5/Infraestructura portuaria/Anexo C.docx`
- `Cap 5/Transporte Público Buses/Registro Transporte Público - Agosto 2025.xlsx`
- `Cap 5/Transporte aéreo/Catastro Tte. Aéreo Primavera.xlsx`

### Cap 6

- `Cap 6/BBDD EOD/Base de datos agregada.xlsx`
- `Cap 6/BBDD EOD/DiccionarioAPP.xlsx`
- `Cap 6/Mediciones de flujo/Consolidado Flujos.xlsx`
- `Cap 6/Trakcs GPS/FMU_6_al_8nov25/Datos_Capa.xlsx`
- `Cap 6/Trakcs GPS/FMU_6_al_8nov25/Metadatos.xlsb`
- `Cap 6/Trakcs GPS/FMU_6_al_8nov25/Puntos_QGis.gpkg`
- `Cap 6/Trakcs GPS/FMU_6_al_8nov25/Shape_GPS_nov_2025.shp`
- `Cap 6/Trakcs GPS/FMU_6_al_8nov25/TourSur_nov25.qgz`

### Cap 7

- `Cap 7/Arcos con sentido.xlsx`
- `Cap 7/HDM4/COPER HDM4 PRIVADO Dic 2025.xls`
- `Cap 7/HDM4/Costos_Red_Vial2030.xlsx`
- `Cap 7/HDM4/Costos_Red_Vial_Actual.xlsx`
- `Cap 7/SIG Red_Vial_Final/CentroidesZonas.shp`
- `Cap 7/SIG Red_Vial_Final/Nodos_Puntos_Pasada.shp`
- `Cap 7/SIG Red_Vial_Final/Nodos_Puntos_Pasada.xlsx`
- `Cap 7/SIG Red_Vial_Final/Nodos_RedVial.shp`
- `Cap 7/SIG Red_Vial_Final/Nodos_RedVial2030.shp`
- `Cap 7/SIG Red_Vial_Final/RED VIAL FINAL.qgz`
- `Cap 7/SIG Red_Vial_Final/Red_Vial_2030.shp`
- `Cap 7/SIG Red_Vial_Final/Red_Vial_Final.shp`
- `Cap 7/SIG Red_Vial_Final/Red_Vial_Final.xlsx`
- `Cap 7/SIG Red_Vial_Final/Rutas_OD.qgz`
- `Cap 7/SIG Red_Vial_Final/SIG_RUTAS_OD/Rutas_Red_Vial_2030.gpkg`
- `Cap 7/SIG Red_Vial_Final/SIG_RUTAS_OD/Rutas_Red_Vial_Final.gpkg`
- `Cap 7/SIG Red_Vial_Final/Zonificación.shp`

### Cap 8

- `Cap 8/Arcos con sentido.xlsx`
- `Cap 8/BBDD_para_Pijas_actualizada_EOD_Final.xlsx`
- `Cap 8/EOD_Puntos_Pasada_Final.xlsx`
- `Cap 8/Factores de proyección de flujos.xlsx`
- `Cap 8/Matrices 2030 Tend.xlsx`
- `Cap 8/Matrices 2030.xlsx`
- `Cap 8/Matrices 2040 Tend.xlsx`
- `Cap 8/Matrices 2040.xlsx`
- `Cap 8/Matrices 2050 Tend.xlsx`
- `Cap 8/Matrices 2050.xlsx`
- `Cap 8/Matrices Situación Actual.xlsx`
- `Cap 8/PIJA Final.xlsx`

### Cap 9

- `Cap 9/Planilla PPTT 4.xlsx`

### SIG

- `SIG/Coberturas/ARISTO/Dashcam/FMU_6_al_8nov25/Fecha_2025-11-06.shp`
- `SIG/Coberturas/ARISTO/Dashcam/FMU_6_al_8nov25/Fecha_2025-11-06_line.shp`
- `SIG/Coberturas/ARISTO/Dashcam/FMU_6_al_8nov25/Fecha_2025-11-07.shp`
- `SIG/Coberturas/ARISTO/Dashcam/FMU_6_al_8nov25/Fecha_2025-11-07_line.shp`
- `SIG/Coberturas/ARISTO/Dashcam/FMU_6_al_8nov25/Fecha_2025-11-08.shp`
- `SIG/Coberturas/ARISTO/Dashcam/FMU_6_al_8nov25/Fecha_2025-11-08_line.shp`
- `SIG/Coberturas/ARISTO/Nodos/Nodos_Argentina.shp`
- `SIG/Coberturas/ARISTO/Nodos/Nodos_Chile.shp`
- `SIG/Coberturas/ARISTO/Nodos/Nodos_Límite.shp`
- `SIG/Coberturas/ARISTO/Nodos/Vías_Argentina.shp`
- `SIG/Coberturas/ARISTO/Nodos/Vías_Chile.shp`
- `SIG/Coberturas/ARISTO/Nodos_2/Nodos_Intersecciones_Argentina.shp`
- `SIG/Coberturas/ARISTO/Nodos_2/Nodos_Intersecciones_Chile.shp`
- `SIG/Coberturas/ARISTO/Pasos_Fronterizos.shp`
- `SIG/Coberturas/ARISTO/Rutas_Aéreas.shp`
- `SIG/Coberturas/ARISTO/Transbordadores.shp`
- `SIG/Coberturas/DIFROL/Límite_Internacional.shp`
- `SIG/Coberturas/IDE/COMUNAS.shp`
- `SIG/Coberturas/IDE/REGIONES.shp`
- `SIG/Coberturas/IGN (Instituto Geográfico Nacional Argentina)/Provincias_Argentina.shp`
- `SIG/Coberturas/IGN (Instituto Geográfico Nacional Argentina)/Red_Vial_Nacional.shp`
- `SIG/Coberturas/IGN (Instituto Geográfico Nacional Argentina)/Red_Vial_Provincial.shp`
- `SIG/Coberturas/MINEDUC/Establecimientos_Educacionales2025.shp`
- `SIG/Coberturas/MINSAL/Establecimientos_Salud.shp`
- `SIG/Coberturas/MIN_CULTURA/Monumento_Arqueológico.shp`
- `SIG/Coberturas/MIN_CULTURA/Puntos_Monumentos_Nacionales.shp`
- `SIG/Coberturas/MIN_ENERGIA/Estación_de_Servicio.shp`
- `SIG/Coberturas/MIN_ENERGIA/Terminal_Marítimo.shp`
- `SIG/Coberturas/MOP/Infraestructura_Portuaria_y_Costera.shp`
- `SIG/Coberturas/MOP/Red_Aeroportuaria.shp`
- `SIG/Coberturas/MOP/Red_Vial.shp`
- `SIG/Coberturas/SECTRA/Ciclovías.shp`
- `SIG/Coberturas/SERNATUR/Atractivos_Turísticos.shp`
- `SIG/Coberturas/SERNATUR/Circuitos_Turísticos.shp`
- `SIG/Coberturas/SERNATUR/Destinos_Interés.shp`
- `SIG/Coberturas/SERNATUR/Zonas_Interés_Turístico.shp`
- `SIG/Coberturas/SIET/Cobertura Móvil 3G (Porcentaje).shp`
- `SIG/Coberturas/SIET/Cobertura Móvil 4G (Porcentaje).shp`
- `SIG/Coberturas/SIET/Cobertura Móvil 5G (Porcentaje).shp`
- `SIG/Coberturas/SIET/Conexiones residenciales fijas de internet (Porcentaje).shp`
- `SIG/Coberturas/SIET/Distancia a centros de salud primaria (Metros).shp`
- `SIG/Coberturas/SIET/Distancia a establecimientos de enseñanza básica (Metros).shp`
- `SIG/Coberturas/SIET/Distancia a establecimientos de enseñanza media (Metros).shp`
- `SIG/Coberturas/SIET/Distancia a establecimientos de enseñanza parvularia (Metros).shp`
- `SIG/Coberturas/SIET/Distancia a servicios operativos de carabineros (Metros).shp`
- `SIG/Coberturas/SIET/Red Vial Pavimentada Bajo Administración Ministerial (Porcentaje).shp`
- `SIG/Coberturas/SIET/Traslado vehicular a centros de salud primaria (Minutos).shp`
- `SIG/Coberturas/SIET/Traslado vehicular a establecimientos de enseñanza básica (Minutos).shp`
- `SIG/Coberturas/SIET/Traslado vehicular a establecimientos de enseñanza media (Minutos).shp`
- `SIG/Coberturas/SIET/Traslado vehicular a establecimientos de enseñanza parvularia (Minutos).shp`
- `SIG/Coberturas/SIET/Traslado vehicular a servicios operativos de carabineros (Minutos).shp`
- `SIG/Coberturas/SUBDERE/GORE.shp`
- `SIG/Coberturas/SUBDERE/Municipios.shp`
- `SIG/Proyecto/Proyecto.qgz`
- `SIG/TABLA DE SHAPEFILES ACTUALIZADO.xlsx`

