# Consolidación lacustre observada de ARISTO

La nueva referencia conserva los conteos de embarque del transbordador Puerto Ibáñez–Chile Chico y asigna OD condicionalmente usando encuestas de la misma fecha, sentido y clase. No estima demanda del nuevo cruce, una jornada completa, estaciones completas o demanda anual. CITRA permanece como referencia terrestre parcial, independiente y sin modificaciones.

## Método y evidencia

Los originales son `Cap 6/BBDD EOD/Base de datos agregada.xlsx`, `DiccionarioAPP.xlsx` y `Cap 6/Mediciones de flujo/Consolidado Flujos.xlsx`. Se enlaza BBDD-1 con BBDD-2 (solo válidas) por `ID 2` uno a uno; no se suman ambas hojas. La tabla `Zonas` del anexo original del Capítulo 8 proporciona las 55 zonas; sus códigos son distintos de los identificadores geográficos BBDD-2. Se preservan textos, coordenadas y escalas originales sin convertir comunas en localidades.

`Q_OD,d = F_d × n_OD,d / N_d`. El estrato principal es fecha/campaña/sentido/clase. F contiene exclusivamente las filas de embarque medidas; N todas las respuestas válidas compatibles, también los OD parciales. Si no hay muestra en una fecha, su flujo queda sin OD: no se toma perfil de otro día. La agrupación de campaña conserva las exposiciones fechadas y no es un promedio diario o estacional.

F/N es un coeficiente de asignación de composición, no un ponderador individual certificado. Hay estratos con más respuestas que vehículos contados; no se acredita una respuesta por vehículo ni la representatividad/no respuesta. La patente solo expresa categoría nacional/extranjera. No se deduplican personas o vehículos inventando identificadores.

La fila de conteo no identifica inequívocamente un zarpe. Los horarios de planificación de encuestas no demuestran el vínculo entre fila y salida. Por ello no se aplica automáticamente la media por fila a una frecuencia semanal. Las referencias operacionales 11/8 y la frecuencia original de TD Transb se conservan como escenarios y comparación histórica, fuera de la matriz observada.

## Clases y limitaciones

- En primavera/verano se distinguen VL, carga, peatones, motos y bicicletas. En Otoño, la EOD ofrece privados agregados: se conserva VP sin desagregar artificialmente a VL. No se suman VP y sus componentes.
- Los peatones medidos no equivalen a todos los pasajeros. Ocupantes y tamaño de grupo permanecen descriptivos; falta certificar unidad de selección, unicidad de grupos y dominios excluyentes. Total de pasajeros no identificado.
- Nacionalidad declarada, patente y OD internacional son indicadores separados, con desconocidos e intersecciones. Los extranjeros permanecen en la demanda física. Los flujos por indicador conservan la unidad de clase, sin llamarlos personas extranjeras totales o residentes.
- Los agregados originales con componentes blancos se conservan según el procedimiento de ARISTO, con advertencia; un blanco no se declara cero observado. Las discrepancias Excel/Informe se documentan sin escoger cifras para ocultarlas.
- Los OD genéricos sin zona no se imputan; su participación queda en el residual. Los viajes largos se conservan como usuarios del ferry, sin afirmar captación por el proyecto.
- No se identifica por fila servicio especial o carga peligrosa; no se inventa una cuota para excluirlos. No se completa invierno ni se anualiza.

## Trabajo anterior preservado

Se revisaron `scripts/07_matrices_od_referencia.py`, `config_matrices_od.json` y sus salidas sin ejecutarlos ni reemplazarlos. Se reutiliza la interceptación, enlace de hojas y conservación condicional de flujos. La referencia histórica usaba media por fila como por zarpe, frecuencias y perfiles estacionales; el nuevo principal retiene exposición medida y estratificación por fecha. La aritmética histórica se reconstruye solo como contraste, con su unidad diaria condicionada claramente separada.

Los resultados de las Etapas 11–13 no completan esta matriz. La menor cantidad de celdas no implica pérdida de entrevistas: la tabla histórica también incluía estructura sin muestra y la nueva agrupa por zonas y conserva los incompletos aparte.

## Reproducción y archivos

Los cuatro Excel y el HTML detallado permanecen en la carpeta privada nueva `etapa1_lacustre_aristo_20261029/resultados/entrega_final/`, fuera de Git. Contienen matrices zonales y originales, auditoría de encuestas, aforos/coeficientes, balances, comparación con 07 y pasajeros/extranjeros.

El paquete local incluye los scripts de las cuatro tareas y `integracion/reproducir_lacustre.py`. Desde Anexos:

```bash
python etapa1_lacustre_aristo_20261029/integracion/reproducir_lacustre.py \
  --anexos . --salida /ruta/NUEVA_EJECUCION_ARISTO
```

El comando congela código y hashes, limita a dos procesos, ejecuta microdatos/comparación en paralelo y, una vez disponibles los microdatos, aforos/usuarios en paralelo. Después integra. No reconstruye red ni ejecuta 07–13. La salida debe ser nueva.

El integrador compartible está en `scripts/lacustre_aristo/` y consume las tablas privadas validadas. Para reutilizar las lecturas ya realizadas:

```bash
python scripts/lacustre_aristo/consolidar_aristo.py \
  --anexos /ruta/Anexos \
  --revision /ruta/Anexos/etapa1_lacustre_aristo_20261029 \
  --salida /ruta/NUEVA_ENTREGA
```

Los scripts de extracción y contraste con tablas del Informe se distribuyen en el paquete local, junto con sus evidencias reservadas. Git contiene método, integrador y pruebas sintéticas, sin conteos de celdas ni microdatos. Los manifiestos registran hashes de fuentes, resultados y código. No se puede reproducir una demanda observada únicamente con los archivos públicos si faltan los originales privados.

## Decisión para continuar

La matriz es utilizable como bloque lacustre observado con asignación OD condicionada. Para integrarla posteriormente con CITRA deben conciliarse períodos y unidades: CITRA usa ventanas de 12 horas de otras jornadas, y ARISTO los embarques fechados. Otoño VP requiere conservar su diferencia con VL. No se sumaron fuentes ni se estimó captación, inducción o crecimiento.

Fuentes metodológicas: Informe Final ARISTO, §§2.2.5–2.2.6 pp.6–7; §6.1.1.1 pp.157–158; tabla78 p.173; tabla107 pp.187–188; tabla138 p.207; tabla169 p.223. La bibliografía y referencias a hojas/filas están en el informe local.
