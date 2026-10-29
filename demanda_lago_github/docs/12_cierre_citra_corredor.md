# Cierre de viabilidad de CITRA: corredor terrestre observado

**Conclusión B: utilizable parcialmente.** CITRA aporta una referencia terrestre por ciertos OD, clases, pantallas y jornadas medidas. La cobertura incompleta y los contrastes entre controles impiden presentarla como demanda terrestre total o como estimación puntual incuestionada de cada celda. Se recomienda conservar CITRA terrestre y ARISTO lacustre como bloques independientes, con faltantes explícitos y sin sumarlos automáticamente.

Esta entrega sucede al [diagnóstico estricto anterior](11_etapa1_citra_empirica.md), que exigía identificar itinerarios íntegramente por Chile. Sus archivos y resultados se conservan. El objetivo autorizado ahora es la demanda del corredor observado: la existencia matemática de un recorrido argentino no veta por sí sola una inferencia de alta confianza sobre el terrestre chileno.

## Evidencia y categorías

- **A: alta confianza inferida.** OD homologado pertinente, control y sentido compatibles, corredor chileno acreditado, sin alternativa lacustre compatible o evidencia internacional contradictoria. Se comparan distancias y cruces de las alternativas ya documentadas. La convergencia respalda una inferencia cualitativa; no supone elección universal del camino más corto ni aplica un porcentaje o umbral de desvío calibrado para obtener resultados.
- **B: corredor incierto.** Alternativas plausibles, evidencia internacional o información insuficiente para atribuir el recorrido a Chile. La ausencia de casos en una categoría no significa incertidumbre nula.
- **C: excluido.** OD no determinado o evidencia de punto/sentido/trayectoria incompatible. Se conserva la entrevista y su motivo en auditoría.

Los tiempos comparables, las esperas y la habilitación fronteriza por fecha/clase no están acreditados; se conservan desconocidos. A no es una ruta declarada, una probabilidad de elección, un itinerario íntegramente chileno certificado ni demanda capturable por el proyecto.

Se mantiene la homologación cerrada y los pendientes sin imputar. No se volvió a abrir revisión manual ni se asignaron localidades a cabeceras comunales. Las coordenadas y decisiones originales permanecen como evidencia separada.

## Expansión y pantallas

`Q_OD,s = F_s × n_OD,s / N_s`, con F y N de la misma fecha, sección EOD, sentido, clase y ventana 08–20. N contiene todas las entrevistas originales compatibles antes de filtrar el proyecto. Se reutilizan los factores validados, conservando los estratos inconsistentes sin expansión y sus motivos. No se utilizan aforos urbanos como reemplazo.

Una sola pantalla por OD zonal ordenado/campaña/segmento mantiene coherencia entre localidades y zonas. La selección fija prioriza factor disponible, cobertura geométrica y exposición; no maximiza flujo o entrevistas. Las alternativas se conservan para contraste. Los controles en serie no se suman y no se presume independencia de ramas.

Las matrices por fecha muestran el estimador de cada jornada. El resumen por campaña es la media de las fechas válidas de la misma pantalla, incluyendo jornadas con cero muestral. No representa toda la campaña, 24 horas o un año. Sin muestra expandible en la pantalla elegida, la celda detallada permanece faltante. Los ceros del estimador no son ceros estructurales de demanda.

La auditoría detectó discrepancias entre controles comparables; quedan visibles en los Excel locales. No se decide cuál estima mejor sin evidencia adicional ni se promedian para ocultarlas. Por ello la selección es una referencia condicionada y debe acompañarse del contraste de pantalla. No se publica el detalle numérico de celdas pequeñas.

## Reproducción y rendimiento

Los módulos nuevos están en `scripts/etapa1_citra/cierre/`. Requieren los insumos privados y la caché validada de la entrega anterior. El generador anterior permite reconstruir esa caché desde originales, con las decisiones y capa geográfica aprobadas; ver [comandos previos](11_etapa1_citra_empirica.md).

Desde la carpeta privada Anexos, indicando la ubicación de este repositorio, ejecutar las revisiones en carpetas nuevas. Aforos, rutas y pantallas son independientes y pueden correr en paralelo; cobertura utiliza otro cupo disponible. Ninguno recalcula rutas.

```bash
python demanda_lago_github/scripts/etapa1_citra/cierre/auditar_aforos.py \
  --cache etapa1_terrestre_citra/resultados/entrega_02 \
  --salida REVISION_NUEVA/aforos
python demanda_lago_github/scripts/etapa1_citra/cierre/clasificar_rutas.py \
  --auditoria etapa1_terrestre_citra/resultados/entrega_02/csv/auditoria_112.csv \
  --salida REVISION_NUEVA/rutas/entrega_final
python demanda_lago_github/scripts/etapa1_citra/cierre/analizar_pantallas.py \
  --cache etapa1_terrestre_citra/resultados/entrega_02 \
  --salida REVISION_NUEVA/pantallas
python demanda_lago_github/scripts/etapa1_citra/cierre/auditar_cobertura.py \
  --base etapa1_terrestre_citra \
  --salida REVISION_NUEVA/cobertura
python demanda_lago_github/scripts/etapa1_citra/cierre/estimar_corredor.py \
  --cache etapa1_terrestre_citra/resultados/entrega_02 \
  --revision REVISION_NUEVA \
  --salida ENTREGA_NUEVA
```

La integración coteja los CSV reutilizados con las hojas de los Excel firmados por hash, verifica las fuentes originales y compara los campos de las entrevistas conservadas. Reconcilia localidades con zonas, A+B con corredor, N/factores con el cálculo anterior y la selección única de pantallas. No reconstruye red, no busca caminos y no ejecuta modelos anteriores. Cada tarea escribe en su propia carpeta; la integración exige una salida inexistente.

El informe HTML, las matrices y cuatro Excel detallados son locales. Los scripts no contienen claves individuales ni flujos de las celdas reservadas. El [resumen público de cierre](../results/citra_cierre/resumen_publico.json) divulga únicamente método y conclusión.

## Decisión para continuar

Usar CITRA como evidencia terrestre parcial, conservando la incertidumbre de ruta y de muestreo y la sensibilidad de las pantallas discrepantes. Mantener ARISTO lacustre independiente. No rellenar mercados faltantes con logit, comunas completas o porcentajes arbitrarios. Esta etapa cierra la viabilidad de CITRA; no se inicia estacionalidad, proyecciones, captación o inducción.

La alternativa exclusivamente ARISTO no se implementa: la referencia terrestre histórica también tiene cobertura de control y ventana parcial, por lo que no completaría automáticamente el terrestre total. La conclusión B permite conservar la información empírica de CITRA sin atribuirle cobertura que no tiene.
