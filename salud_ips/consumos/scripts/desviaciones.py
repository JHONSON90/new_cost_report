import polars as pl


def desviaciones(consumos):

    #region desviaciones
    # ['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'CodGrupo', 'Grupo', 'CodArticulo', 'Articulo', 'Cantidad', 'ValorUnitario', 'TotalBruto', 'ValorIVA', 'ValorDescuento', 'ValorTotal', 'Unidad', 'LaboratorioMarca', 'Observacion', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Clasificacion_consumo', 'Municipio', 'Servicio', 'Tipo_servicio', 'Nombre', 'CodigoGenerico', 'EstadoArticulo', 'ADM-CodGen']

    #sacar moda por producto en cantidades

    consumos_desviaciones = consumos.with_columns(
        pl.col('Cantidad')
        .mode()
        .sort()
        .first()
        .over('CodArticulo')
        .alias('Cantidad_moda'),
        pl.col('Cantidad')
        .max()
        .sort()
        .first()
        .over('CodArticulo')
        .alias('Cantidad_maximo'),
        pl.col('Cantidad')
        .mean()
        .sort()
        .first()
        .over('CodArticulo')
        .alias('Cantidad_media'),
        pl.col('Cantidad')
        .std()
        .sort()
        .first()
        .over('CodArticulo')
        .alias('Cantidad_std'),
        pl.col('Cantidad')
        .min()
        .sort()
        .first()
        .over('CodArticulo')
        .alias('Cantidad_minimo')
    )

    consumos_desviaciones = consumos_desviaciones.with_columns(
        (pl.col('Cantidad') - pl.col('Cantidad_moda')).abs().alias("Desviacion_moda"),
        (pl.col('Cantidad') - pl.col('Cantidad_media')).abs().alias("Desviacion_media"),
        (pl.col('Cantidad') - pl.col('Cantidad_std')).abs().alias("Desviacion_std"),
        (pl.col('Cantidad') - pl.col('Cantidad_maximo')).abs().alias("Desviacion_maximo"),
        (pl.col('Cantidad') - pl.col('Cantidad_minimo')).abs().alias("Desviacion_minimo")
    )

    consumos_desviaciones = consumos_desviaciones.with_columns(
        pl.when(pl.col('Desviacion_moda') > 0).then(pl.lit("ALERTA"))
        .when(pl.col('Desviacion_moda') == 0).then(pl.lit("OK"))
        .alias("Alerta_desviacion_moda"),
        pl.when(pl.col('Desviacion_media') > 0).then(pl.lit("ALERTA"))
        .when(pl.col('Desviacion_media') == 0).then(pl.lit("OK"))
        .alias("Alerta_desviacion_media"),
        pl.when(pl.col('Desviacion_std') > 0).then(pl.lit("ALERTA"))
        .when(pl.col('Desviacion_std') == 0).then(pl.lit("OK"))
        .alias("Alerta_desviacion_std"),
    )

    consumos_desviaciones = consumos_desviaciones.select(['Comprobante', 'Numero', 'Fecha', 'NoDocumento','CentroCosto', 'Dependencia', 'Bodega', 'CodGrupo', 'Grupo', 'CodArticulo', 'Articulo', 'Cantidad','ValorTotal','Cantidad_moda','Cantidad_maximo','Cantidad_media','Cantidad_std','Cantidad_minimo','Desviacion_moda','Desviacion_media','Desviacion_std','Desviacion_maximo','Desviacion_minimo','Alerta_desviacion_moda','Alerta_desviacion_media','Alerta_desviacion_std'])
    #print(consumos_desviaciones.head(20))

    #sacar solo desviaciones con alerta de acuerdo a la moda
    datos_desviaciones = consumos_desviaciones.filter(pl.col('Alerta_desviacion_moda') == 'ALERTA')

    #print(consumos_desviaciones.head(20))
    return datos_desviaciones
    #guardar datos con desviaciones
    #datos_desviaciones.write_excel("consumos_desviaciones_24-06-2026.xlsx")