# Conectividad lacustre Bahía Jara–Levicán

Este proyecto estima la demanda del nuevo cruce del Lago General Carrera para apoyar su evaluación social. La referencia combina la demanda lacustre de ARISTO y la cobertura terrestre parcial de CITRA, manteniendo sus diferencias de unidad, exposición y calidad.

La configuración oficial compara tres alternativas de infraestructura **por separado**, cada una contra la misma situación base optimizada (SBO). No se suman sus demandas ni se supone que los tres proyectos operen simultáneamente.

## Entrega oficial y reproducción

La ejecución parametrizada se encuentra en [actualizacion_oficial_alternativas_20261029](actualizacion_oficial_alternativas_20261029/).

| Elemento | Ubicación |
|---|---|
| Excel de demanda y costos | [resultados/demanda_oficial_tres_alternativas.xlsx](actualizacion_oficial_alternativas_20261029/resultados/demanda_oficial_tres_alternativas.xlsx) |
| Comparación de alternativas | [resultados/informe_alternativas_oficiales.html](actualizacion_oficial_alternativas_20261029/resultados/informe_alternativas_oficiales.html) |
| Implementación | [codigo/calcular.py](actualizacion_oficial_alternativas_20261029/codigo/calcular.py) |
| Parámetros editables | [codigo/configuracion.json](actualizacion_oficial_alternativas_20261029/codigo/configuracion.json) |

Para revisar la entrega, empiece por **LEER PRIMERO** en el Excel. Las hojas principales, en orden, son:

1. **Demanda actual 2026:** ARISTO y CITRA separados, por temporada y segmento, con aportes anuales, unidades y cobertura.
2. **Demanda anual:** resultados centrales de las tres rutas para A1, A2 y A3, evaluadas por separado.
3. **Demanda estacional:** temporada y sentido, con equivalentes diarios y por zarpe.
4. **Captacion e induccion:** procedencia de los desvíos, inducción incremental y total del nuevo cruce.
5. **Sensibilidades:** casos vigentes y parámetros; los contrastes históricos están separados y marcados como no vigentes.
6. **Insumos evaluacion social:** detalle por OD, procedencia, proyecto, ruta, temporada, segmento y año; demanda SBO/CP, distancias, tiempos, COV privados, tarifas y CG disponibles.

Las hojas grises al final conservan el respaldo técnico. Las tablas principales utilizan una sola referencia aprobada; no suman versiones ni escenarios. **0** es un cero calculado; **—** significa no aplicable; **ND**, información insuficiente. La demanda fuera del soporte se presenta como cantidad separada. No sumar los totales de ambos sentidos con sus componentes, ni las alternativas entre sí.

El CG combina costos monetarios privados y un VST social común; no es un costo social puro. Los costos de recursos y COV sociales aún no calculados permanecen **ND**. Las tarifas están separadas y no deben contarse como consumo adicional de recursos. Los indicadores muestrales de extranjeros no permiten una desagregación anual por alternativa; los restantes viajes no se consideran automáticamente nacionales.

Para actualizar **solo la presentación**, sin recalcular demanda ni costos:

```bash
python actualizacion_oficial_alternativas_20261029/codigo/presentar_resultados.py
```

Este comando lee el Excel oficial existente, conserva los valores de sus hojas técnicas, reorganiza las tablas y reemplaza el mismo Excel e informe HTML. No lee encuestas, no modifica configuraciones y no ejecuta el modelo. Verifica que los valores de respaldo permanezcan iguales, admitiendo únicamente el redondeo de almacenamiento de Excel.

Para reproducir el cálculo completo autorizado en la etapa anterior, desde `Anexos`:

```bash
python actualizacion_oficial_alternativas_20261029/codigo/calcular.py
```

La ejecución reutiliza las entregas anteriores. No requiere reprocesar EOD, reconstruir la red vial, recalibrar modelos de elección ni volver a estimar las proyecciones. Los archivos originales y las entregas históricas se conservan en sus carpetas.

Los resultados se presentan para 2026, 2030, 2040 y 2050. Las hojas de parámetros, cobertura y validaciones del Excel y el informe acompañante precisan el alcance de cada estimación; este README no sustituye esos controles.

## Situación base optimizada común

La SBO ofrece dos rutas: terrestre íntegramente por Chile y Puerto Ibáñez–Chile Chico. La sustitución de La Tehuelche por una nave tipo Capitán Wellmann pertenece a la SBO y no constituye un beneficio exclusivo de Bahía Jara–Levicán.

| Parámetro del servicio actual | Configuración |
|---|---|
| Navegación | 107 minutos |
| Frecuencia alta, diciembre–abril | 11 zarpes por semana y sentido |
| Frecuencia baja, mayo–noviembre | 8 zarpes por semana y sentido |
| Presentación de VL, CAM y VP | 2 horas de referencia |
| Presentación de peatones | 1 hora de referencia |
| Desembarque | 30 minutos |

La anticipación procede de la referencia del operador ya documentada. Su transferencia al nuevo cruce se mantiene como supuesto explícito, no como una medición de duración del embarque. No se añaden otros 15 minutos de embarque a esa anticipación.

La decisión de utilizar 30 minutos de desembarque se aplica al servicio actual y a los tres proyectos. No se introduce una diferencia de tiempos entre rampa fija y linkspan.

## Tres alternativas oficiales

| Proyecto | Acceso norte | Longitud | Embarcación de referencia | Infraestructura | Navegación |
|---|---|---:|---|---|---:|
| 1. Convencional | P-20a | 31,14 km | Tipo La Tehuelche | Rampa fija | 43 min |
| 2. Rápida con linkspan | P-20d | 24,62 km | Tipo Capitán Wellmann / nueva barcaza MOP | Puente basculante | 39 min |
| 3. Rápida con rampa fija | P-20b | 22,60 km | Tipo Capitán Wellmann / nueva barcaza MOP | Muelles y rampa fija | 39 min |

La distancia lacustre de referencia es de 7,3 millas náuticas. La frecuencia oficial común **11/8** reemplaza las anteriores referencias a 14 para el nuevo cruce. Cada nuevo servicio utiliza **11 zarpes semanales por sentido en diciembre–abril y 8 en mayo–noviembre**, exactamente igual al cruce actual y una embarcación adicional independiente. La frecuencia óptima, la flota necesaria y su capacidad se evalúan posteriormente.

En cada situación con proyecto coexisten la ruta terrestre, Puerto Ibáñez–Chile Chico con los atributos de la SBO y **una** de las alternativas nuevas. Los costos de las dos rutas existentes son iguales entre SBO y con proyecto.

Se conserva la construcción vial previa: accesos separados de los tramos compartidos, velocidades por tipo de camino y COV de ARISTO/HDM-4. El acceso de ripio utiliza la referencia de 50 km/h. La continuidad del empalme norte sigue siendo una aproximación heredada de los recorridos disponibles; no debe interpretarse como una nueva verificación del trazado.

## Fuentes y límites de cobertura

**ARISTO** aporta las encuestas y conteos del cruce Puerto Ibáñez–Chile Chico, la red vial, costos y antecedentes de proyección. Las tablas BBDD-1 y BBDD-2 se enlazan por `ID 2`; no son entrevistas independientes que puedan sumarse.

**CITRA** aporta EOD y aforos de algunos corredores terrestres. Su clasificación de ruta conserva la diferencia entre evidencia directa e inferencia topológica. La cobertura continúa siendo parcial: un factor horario no completa los OD ni las ramas que nunca se midieron.

La referencia CITRA conserva el factor supuesto 12→24 horas de 1,20 y las imputaciones temporales ya documentadas. Esas cantidades no se presentan como aforos observados de 24 horas ni como toda la demanda terrestre del proyecto.

Se mantienen los OD detallados y las zonas de modelación ARISTO. Los identificadores administrativos de BBDD-2 no equivalen a las 55 zonas del modelo. Río Ibáñez es una comuna y no se transforma automáticamente en Puerto Ibáñez.

Las aproximaciones de costos, localidades representativas y conexiones hipotéticas permanecen identificadas. Los OD externos, los viajes largos y los residuales se conservan, incluso cuando no cuentan con soporte para estimar captación o inducción.

## Metodología vigente

### Demanda existente y crecimiento

Las Etapas 1 y 2 construyen y anualizan bloques separados de demanda lacustre y terrestre. ARISTO conserva las versiones A, con residual explícito, y B, con distribución OD imputada cuando existe respaldo. No se suman ambas versiones.

La Etapa 3 aplica crecimiento mediante:

```text
Q_t = Q_2026 × (PIB_t / PIB_2026)^beta_PIB
```

La trayectoria central de PIB es común a los escenarios propios. La actualización oficial reutiliza el crecimiento central ya calculado; no aplica crecimiento por segunda vez. Las elasticidades-PIB son distintas de las elasticidades respecto del costo generalizado utilizadas para inducción.

### Costos generalizados

El costo de comparación combina componentes monetarios privados con un VST social común de $10.047 por persona-hora. No es un costo social puro.

```text
CG = COV + tarifas + VST × personas_por_unidad × tiempo_total
tiempo_total = tiempo_vial + navegación + presentación + desembarque + horario
horario = 0,25 × (168 / zarpes_semanales_por_sentido)
```

La penalización horaria representa inconveniencia por frecuencia; no se interpreta como espera física medida. La presentación incluye el componente previo al embarque y no se duplica.

Los COV proceden de `Cap 7/HDM4/Costos_Red_Vial_Actual.xlsx`, hojas `Costos_Red_Vial` y `Tipos de arcos`, con las salvedades de categoría y precios documentadas. Se mantienen separados COV, tarifas y tiempo. Los COV privados de diciembre de 2025 se homogeneizaron convencionalmente a enero de 2026 en la Etapa 4; esa convención se conserva explícita.

### Captación por escenarios

La metodología principal de la Etapa 5 aplica curvas por tramos a los ahorros relativos de costo de cada alternativa de procedencia:

```text
A = (CG_origen − CG_nuevo) / CG_origen
D_desviada = D_existente × p_captacion(A, segmento, escenario)
```

Los nudos de las curvas conservadora, central y alta son supuestos editables del proyecto, no elasticidades calibradas. La captación responde de forma monótona a las mejoras de costo. Los viajes restantes permanecen en su alternativa original y se distingue el desvío desde tierra del desvío desde la barcaza actual.

Las cuotas positivas del escenario alto sin ahorro de costo representan un supuesto de atractivo no observado. Los costos de núcleo con cola común no valorada requieren el tratamiento por cotas ya documentado, sin inventar un costo absoluto externo.

### Peatones y buses coordinados

Se conserva el escenario hipotético Chile Chico–Bahía Jara–Levicán–Coyhaique y su inverso, junto con las conexiones y aproximaciones comunales documentadas. El acceso norte, su tiempo y la tarifa del bus cambian según P-20a, P-20d o P-20b.

Los buses no se presentan como servicios existentes o comprometidos. Sus tarifas se estiman mediante referencias comparables; la coordinación evita otra penalización completa de espera. La demanda sin conexión suficiente sigue siendo residual. Los costos operacionales del sistema de buses deben incorporarse en la evaluación posterior.

### Demanda inducida incremental

La Etapa 6 final separa los viajes nuevos de los viajes que solo cambian de ruta. Se conserva el procedimiento de inducción incremental atribuible a la mejora del mínimo de costo disponible con proyecto, descontando la mejora que ya podía obtenerse en la SBO.

La inducción incremental se distribuye con las mismas participaciones de transferencia del escenario correspondiente. No se asigna automáticamente toda la inducción al nuevo cruce ni se recalibra un modelo de elección.

| Segmento | Menor inducción | Central | Mayor inducción |
|---|---:|---:|---:|
| VL, VP y peatones | −0,254 | −0,354 | −0,454 |
| CAM | −0,006 | −0,106 | −0,206 |

Estas elasticidades de demanda respecto de CG y sus sensibilidades de ±0,1 son supuestos transferidos. Los escenarios de captación y los de elasticidad se etiquetan separadamente para no confundir respuesta de ruta, crecimiento e inducción.

## Organización de carpetas

| Carpeta | Función |
|---|---|
| `Cap 3`, `Cap 5`–`Cap 10`, `SIG`, `Estudios de consultoras` | Antecedentes originales técnicos, operacionales y geográficos; conservación local |
| `eod aysen` | Fuentes CITRA reservadas |
| `demanda_lago_github` | Código, documentación y resultados históricos del proyecto inicial |
| `diagnostico_etapa1_2026-10-28`, `homologacion_geografica_etapa1` | Diagnóstico y correspondencias geográficas |
| `etapa1_lacustre_aristo_20261029`, `etapa1_terrestre_citra` | Reconstrucción empírica y límites de cada fuente |
| `etapa2_demanda_anual_20261029` | Estacionalidad, anualización y bloques de referencia |
| `etapa3_proyecciones_20261029`, `etapa3_ajuste_elasticidades_20261029` | Proyecciones previas y ajuste final de elasticidades-PIB |
| `etapa4_costos_generalizados_20261029` | Atributos y costos anteriores a la actualización oficial |
| `etapa5_transferencia_principal_20261029` | Captación principal por curvas de transferencia |
| `etapa5_ampliacion_peatones_20261029` | Conectividad peatonal y sensibilidades operacionales anteriores |
| `etapa6_demanda_inducida_20261029`, `etapa6_cierre_incremental_20261029` | Inducción preliminar y corrección incremental final |
| `actualizacion_oficial_alternativas_20261029` | Configuración común y comparación oficial de las tres alternativas |

## Resultados conservados como exploratorios

`etapa5_captacion_20261029` conserva la primera regla de ahorro relativo. `etapa5_logit_preliminar_20261029` conserva el logit multinomial supuesto como contraste metodológico; no es la metodología principal.

Las Etapas 07–13 del proyecto inicial, incluido el logit jerárquico y sus imputaciones, permanecen como antecedentes exploratorios. No completan automáticamente la demanda observada de las entregas actuales.

`exploracion_tiempos_barcaza_20261029` contrasta tiempos declarados o previstos. No sustituye los parámetros operacionales oficiales ni identifica separadamente espera, embarque y desembarque.

## Conservación, privacidad y próximos pasos

No modificar originales ni borrar entregas anteriores. No publicar microdatos, identificadores, coordenadas personales, credenciales o archivos reservados. La existencia local de un Excel o una carpeta no implica autorización para divulgar su contenido en GitHub.

Los resultados distinguen observado, expandido, imputado, supuesto y fuera de soporte. Los faltantes no equivalen a cero. Vehículos, unidades VP y personas se mantienen separados; nacionalidad, patente y OD internacional tampoco se consideran equivalentes a residencia.

La siguiente etapa utiliza esta demanda para revisar capacidad y frecuencia operacional. Después corresponde completar inversión, operación y mantenimiento —incluidos buses y tecnologías portuarias— y la evaluación social. Los flujos equivalentes por día o zarpe son referencias para esa revisión, no una prueba de suficiencia de capacidad.

## Consolidación para el equipo

El Excel oficial se actualiza en su ubicación existente. Incluye guía de lectura, campañas observadas, referencia anual2026, SBO, tablas de las tres rutas por alternativa/año/temporada/sentido, procedencia, sensibilidades y extranjeros. Las tablas para compartir utilizan ARISTOB; A permanece como contraste independiente. Las sensibilidades operacionales históricas se identifican expresamente como **no vigentes**: conservan los parámetros con que se calcularon y no representan la frecuencia oficial11/8.

La desagregación de extranjeros de cada rutaCP no se estima si falta una correspondencia defendible entre indicadores y OD; no se aplican proporciones generales. Los indicadores de nacionalidad, patente, ODinternacional y residencia no se suman ni se consideran equivalentes.
