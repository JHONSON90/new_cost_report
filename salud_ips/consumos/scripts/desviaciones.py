# import polars as pl
# import traceback


# def desviaciones(consumos):
#     try:
#     #region desviaciones
#     # ['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'CodGrupo', 'Grupo', 'CodArticulo', 'Articulo', 'Cantidad', 'ValorUnitario', 'TotalBruto', 'ValorIVA', 'ValorDescuento', 'ValorTotal', 'Unidad', 'LaboratorioMarca', 'Observacion', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Clasificacion_consumo', 'Municipio', 'Servicio', 'Tipo_servicio', 'Nombre', 'CodigoGenerico', 'EstadoArticulo', 'ADM-CodGen']
#     #sacar moda por producto en cantidades
#         consumos_desviaciones = consumos.with_columns(
#             pl.col('Cantidad')
#             .mode()
#             .sort()
#             .first()
#             .over('CodigoGenerico')
#             .alias('Cantidad_moda'),
#             pl.col('Cantidad')
#             .max()
#             .sort()
#             .first()
#             .over('CodigoGenerico')
#             .alias('Cantidad_maximo'),
#             pl.col('Cantidad')
#             .mean()
#             .sort()
#             .first()
#             .over('CodigoGenerico')
#             .alias('Cantidad_media'),
#             pl.col('Cantidad')
#             .std()
#             .sort()
#             .first()
#             .over('CodigoGenerico')
#             .alias('Cantidad_std'),
#             pl.col('Cantidad')
#             .min()
#             .sort()
#             .first()
#             .over('CodigoGenerico')
#             .alias('Cantidad_minimo')
#         )

#         consumos_desviaciones = consumos_desviaciones.with_columns(
#             (pl.col('Cantidad') - pl.col('Cantidad_moda')).abs().alias("Desviacion_moda"),
#             (pl.col('Cantidad') - pl.col('Cantidad_media')).abs().alias("Desviacion_media"),
#             (pl.col('Cantidad') - pl.col('Cantidad_std')).abs().alias("Desviacion_std"),
#             (pl.col('Cantidad') - pl.col('Cantidad_maximo')).abs().alias("Desviacion_maximo"),
#             (pl.col('Cantidad') - pl.col('Cantidad_minimo')).abs().alias("Desviacion_minimo")
#         )

#         consumos_desviaciones = consumos_desviaciones.with_columns(
#             pl.when(pl.col('Desviacion_moda') > 0).then(pl.lit("ALERTA"))
#             .when(pl.col('Desviacion_moda') == 0).then(pl.lit("OK"))
#             .alias("Alerta_desviacion_moda"),
#             pl.when(pl.col('Desviacion_media') > 0).then(pl.lit("ALERTA"))
#             .when(pl.col('Desviacion_media') == 0).then(pl.lit("OK"))
#             .alias("Alerta_desviacion_media"),
#             pl.when(pl.col('Desviacion_std') > 0).then(pl.lit("ALERTA"))
#             .when(pl.col('Desviacion_std') == 0).then(pl.lit("OK"))
#             .alias("Alerta_desviacion_std"),
#         )

#         consumos_desviaciones = consumos_desviaciones.select(['Comprobante', 'Numero', 'Fecha', 'NoDocumento','CentroCosto', 'Dependencia', 'Bodega', 'CodGrupo', 'Grupo', "CodigoGenerico", "Nombre", 'Cantidad','ValorTotal','Cantidad_moda','Cantidad_maximo','Cantidad_media','Cantidad_std','Cantidad_minimo','Desviacion_moda','Desviacion_media','Desviacion_std','Desviacion_maximo','Desviacion_minimo','Alerta_desviacion_moda','Alerta_desviacion_media','Alerta_desviacion_std'])
#         #print(consumos_desviaciones.head(20))

#         #sacar solo desviaciones con alerta de acuerdo a la moda
#         datos_desviaciones = consumos_desviaciones.filter(pl.col('Alerta_desviacion_moda') == 'ALERTA')

#         #print(consumos_desviaciones.head(20))
#         return datos_desviaciones
#     except Exception as e:
#         print(f"Error en el calculo de desviaciones: {e}")
#         traceback.print_exc()
#         raise


import polars as pl
import traceback

def desviaciones(consumos: pl.DataFrame) -> pl.DataFrame:
    """
    Calcula desviaciones estadísticas por CodigoGenerico.
    Retorna DataFrame con alertas (puede ser vacío si no hay desviaciones).
    NUNCA retorna None.
    """
    try:
        # 1. VALIDACIÓN TEMPRANA: Rechazar nulos en clave de agrupación
        if consumos["CodigoGenerico"].null_count() > 0:
            nulos = consumos.filter(pl.col("CodigoGenerico").is_null()).height
            print(f"[WARN] ADVERTENCIA: {nulos} registros con CodigoGenerico=nulo. Excluidos de análisis.")
            consumos = consumos.filter(pl.col("CodigoGenerico").is_not_null())
        
        if consumos.is_empty():
            print("[WARN] No hay datos válidos para calcular desviaciones.")
            # Retornar DataFrame vacío con esquema correcto
            return pl.DataFrame({
                'Comprobante': [], 'Numero': [], 'Fecha': [], 'NoDocumento': [],
                'CentroCosto': [], 'Dependencia': [], 'Bodega': [], 'CodGrupo': [], 'Grupo': [],
                'CodigoGenerico': [], 'Nombre': [], 'Cantidad': [], 'ValorTotal': [],
                'Cantidad_moda': [], 'Cantidad_maximo': [], 'Cantidad_media': [],
                'Cantidad_std': [], 'Cantidad_minimo': [],
                'Desviacion_moda': [], 'Desviacion_media': [], 'Desviacion_std': [],
                'Desviacion_maximo': [], 'Desviacion_minimo': [],
                'Alerta_desviacion_moda': [], 'Alerta_desviacion_media': [], 'Alerta_desviacion_std': []
            })
        
        # 2. ESTADÍSTICAS ROBUSTAS: fill_null(std=0) para grupos de 1 registro
        consumos_desviaciones = consumos.with_columns(
            pl.col('Cantidad').mode().sort().first().over('CodigoGenerico').alias('Cantidad_moda'),
            pl.col('Cantidad').max().over('CodigoGenerico').alias('Cantidad_maximo'),
            pl.col('Cantidad').mean().over('CodigoGenerico').alias('Cantidad_media'),
            pl.col('Cantidad').std().over('CodigoGenerico').fill_null(0).alias('Cantidad_std'),
            pl.col('Cantidad').min().over('CodigoGenerico').alias('Cantidad_minimo')
        )
        
        # 3. DESVIACIONES ABSOLUTAS
        consumos_desviaciones = consumos_desviaciones.with_columns(
            (pl.col('Cantidad') - pl.col('Cantidad_moda')).abs().alias("Desviacion_moda"),
            (pl.col('Cantidad') - pl.col('Cantidad_media')).abs().alias("Desviacion_media"),
            (pl.col('Cantidad') - pl.col('Cantidad_std')).abs().alias("Desviacion_std"),
            (pl.col('Cantidad') - pl.col('Cantidad_maximo')).abs().alias("Desviacion_maximo"),
            (pl.col('Cantidad') - pl.col('Cantidad_minimo')).abs().alias("Desviacion_minimo")
        )
        
        # 4. ALERTAS CON UMBRAL MÍNIMO (evita alertas por redondeo)
        UMBRAL = 1e-6
        consumos_desviaciones = consumos_desviaciones.with_columns(
            pl.when(pl.col('Desviacion_moda') > UMBRAL).then(pl.lit("ALERTA"))
             .otherwise(pl.lit("OK")).alias("Alerta_desviacion_moda"),
            pl.when(pl.col('Desviacion_media') > UMBRAL).then(pl.lit("ALERTA"))
             .otherwise(pl.lit("OK")).alias("Alerta_desviacion_media"),
            pl.when(pl.col('Desviacion_std') > UMBRAL).then(pl.lit("ALERTA"))
             .otherwise(pl.lit("OK")).alias("Alerta_desviacion_std"),
        )
        
        # 5. SELECCIÓN COLUMNAS CANÓNICAS
        cols_out = ['Comprobante', 'Numero', 'Fecha', 'NoDocumento','CentroCosto', 
                    'Dependencia', 'Bodega', 'CodGrupo', 'Grupo', "CodigoGenerico", "Nombre",
                    'Cantidad','ValorTotal','Cantidad_moda','Cantidad_maximo','Cantidad_media',
                    'Cantidad_std','Cantidad_minimo','Desviacion_moda','Desviacion_media',
                    'Desviacion_std','Desviacion_maximo','Desviacion_minimo',
                    'Alerta_desviacion_moda','Alerta_desviacion_media','Alerta_desviacion_std']
        
        consumos_desviaciones = consumos_desviaciones.select(cols_out)
        
        # 6. FILTRO ALERTAS (retorna DataFrame vacío si no hay, NO None)
        datos_desviaciones = consumos_desviaciones.filter(pl.col('Alerta_desviacion_moda') == 'ALERTA')
        
        print(f"[OK] Desviaciones calculadas: {consumos_desviaciones.height} registros totales, "
              f"{datos_desviaciones.height} alertas generadas")
        
        return datos_desviaciones
        
    except Exception as e:
        print(f"[ERROR] Error en calculo de desviaciones: {e}")
        traceback.print_exc()
        raise