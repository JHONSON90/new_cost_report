import polars as pl 

def hacer_informe(consumos, entradas):
    #region CONSUMOS
    consumos_normales = consumos.filter(
        pl.col("Comprobante").is_in(["SALIDAS INTERNAS ALMACEN", "SALIDAS INTERNAS FARMACIA"])
    )

    consumos_normales = consumos_normales.with_columns(
        Municipio = pl.col("CentroCosto").str.slice(0, 3),
        Servicio = pl.col("CentroCosto")
                    .str.slice(3)
                    .str.split("-")
                    .list.get(0)
                    .str.strip_chars(),
        Tipo_servicio = pl.col("CentroCosto")
                    .str.split("-")
                    .list.get(1)
                    .str.strip_chars()
    )

    consumos_normales = consumos_normales.with_columns(
        pl.when(pl.col('CodArticulo').str.starts_with("1") == True).then(pl.lit("Medicamentos"))
        .when(pl.col('CodArticulo').str.starts_with("2") == True).then(pl.lit("Dispositivos Medicos"))
        .when(pl.col('CodArticulo').str.starts_with("3") == True).then(pl.lit("Suministros"))
        .otherwise(pl.lit("OTRO"))
        .alias("Clasificacion_consumo")
    )

    consumo_medicamentos = consumos_normales.filter(
        pl.col("Clasificacion_consumo") == "Medicamentos"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    consumo_dispositivos = consumos_normales.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )
    

    consumo_suministros = consumos_normales.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    consumos_facturacion = consumos.filter(
        pl.col("Comprobante") == 'SISTEMA DISPENSACION FARMACIA'
    )

    consumos_facturacion = consumos_facturacion.with_columns(
        pl.col('NoDocumento').str.splitn("ADM: ", 2)
        .struct.field('field_1')
        .str.strip_chars()
        .cast(pl.Int32)
    ).with_columns(
        pl.when(pl.col('CodArticulo').str.starts_with("1") == True).then(pl.lit("Medicamentos"))
        .when(pl.col('CodArticulo').str.starts_with("2") == True).then(pl.lit("Dispositivos Medicos"))
        .when(pl.col('CodArticulo').str.starts_with("3") == True).then(pl.lit("Suministros"))
        .otherwise(pl.lit("OTRO"))
        .alias("Clasificacion_consumo")
    ).with_columns(
        Municipio = pl.col("CentroCosto").str.slice(0, 3),
        Servicio = pl.col("CentroCosto")
                    .str.slice(3)
                    .str.split("-")
                    .list.get(0)
                    .str.strip_chars(),
        Tipo_servicio = pl.col("CentroCosto")
                    .str.split("-")
                    .list.get(1)
                    .str.strip_chars()
    )

    servicio_farmaceutico_medicamentos = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Medicamentos"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    servicio_farmaceutico_dispositivos = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    servicio_farmaceutico_suministros = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )


    #region Entradas
    entradas = entradas.with_columns(
            pl.when(pl.col('CodArticulo').str.starts_with("1") == True).then(pl.lit("Medicamentos"))
            .when(pl.col('CodArticulo').str.starts_with("2") == True).then(pl.lit("Dispositivos Medicos"))
            .when(pl.col('CodArticulo').str.starts_with("3") == True).then(pl.lit("Suministros"))
            .otherwise(pl.lit("OTRO"))
            .alias("Clasificacion_consumo")
        ).with_columns(
            Municipio = pl.col("CentroCosto").str.slice(0, 3),
            Servicio = pl.col("CentroCosto")
                        .str.slice(3)
                        .str.split("-")
                        .list.get(0)
                        .str.strip_chars(),
            Tipo_servicio = pl.col("CentroCosto")
                        .str.split("-")
                        .list.get(1)
                        .str.strip_chars()
        )

    entradas_consumo = entradas.filter(
        pl.col("Comprobante").is_in(["ENTRADAS INTERNAS FARMACIA", 'ENTRADAS INTERNAS SIMA', 'ENTRADAS INTERNAS ALMACEN'])
    )

    consumo_entradas_medicamentos = entradas_consumo.filter(
        pl.col('Clasificacion_consumo') == "Medicamentos"
    ).group_by(['Municipio', 'Servicio']).agg(
            pl.col('ValorTotal').sum().cast(pl.Int64)
        ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    consumo_entradas_dispositivos = entradas_consumo.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    consumo_entradas_suministros = entradas_consumo.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    devolucion_facturacion = entradas.filter(
        pl.col("Comprobante") == 'SISTEMA ANULACION DISPENSACION FARMACIA'
    )

    devolucion_fact_medicamentos = devolucion_facturacion.filter(
        pl.col('Clasificacion_consumo') == "Medicamentos"
    ).group_by(['Municipio', 'Servicio']).agg(
            pl.col('ValorTotal').sum().cast(pl.Int64)
        ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    devolucion_fact_dispositivos = devolucion_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    devolucion_fact_suministros = devolucion_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Servicio'], separator='-').alias('Centro Costo')
        )

    consumos_medicamentos_sin_entradas = consumo_medicamentos.join(consumo_entradas_medicamentos, left_on='Centro Costo', right_on='Centro Costo', how='left').fill_null(0)
    consumos_dispositivos_sin_entradas = consumo_dispositivos.join(consumo_entradas_dispositivos, left_on='Centro Costo', right_on='Centro Costo', how='left').fill_null(0)
    consumos_suministros_sin_entradas = consumo_suministros.join(consumo_entradas_suministros, left_on='Centro Costo', right_on='Centro Costo', how='left').fill_null(0)

    facturacion_medicamentos_sin_devolucion = servicio_farmaceutico_medicamentos.join(devolucion_fact_medicamentos, left_on='Centro Costo', right_on='Centro Costo', how='left').fill_null(0)
    facturacion_dispositivos_sin_devolucion = servicio_farmaceutico_dispositivos.join(devolucion_fact_dispositivos, left_on='Centro Costo', right_on='Centro Costo', how='left').fill_null(0)
    facturacion_suministros_sin_devolucion = servicio_farmaceutico_suministros.join(devolucion_fact_suministros, left_on='Centro Costo', right_on='Centro Costo', how='left').fill_null(0)

    consumos_medicamentos_sin_entradas = consumos_medicamentos_sin_entradas.with_columns(
        (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorNeto')
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    consumos_dispositivos_sin_entradas = consumos_dispositivos_sin_entradas.with_columns(
        (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorNeto')
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    consumos_suministros_sin_entradas = consumos_suministros_sin_entradas.with_columns(
        (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorNeto')
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    facturacion_medicamentos_sin_devolucion = facturacion_medicamentos_sin_devolucion.with_columns(
        (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorNeto')
    ).group_by('Municipio').agg(pl.col('ValorNeto').sum()).with_columns(
        pl.lit("servicio farmaceutico").alias("Servicio")
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    facturacion_dispositivos_sin_devolucion = facturacion_dispositivos_sin_devolucion.with_columns(
        (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorNeto')
    ).group_by('Municipio').agg(pl.col('ValorNeto').sum()).with_columns(
        pl.lit("servicio farmaceutico").alias("Servicio")
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    facturacion_suministros_sin_devolucion = facturacion_suministros_sin_devolucion.with_columns(
        (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorNeto')
    ).group_by('Municipio').agg(pl.col('ValorNeto').sum()).with_columns(
        pl.lit("servicio farmaceutico").alias("Servicio")
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    #union facturacion con consumos
    medicamentos_completo = pl.concat([
        consumos_medicamentos_sin_entradas,
        facturacion_medicamentos_sin_devolucion
    ]).group_by(['Municipio', 'Servicio']).agg(pl.col('ValorNeto').sum()).sort(['Municipio', 'Servicio'])

    dispositivos_completo = pl.concat([
        consumos_dispositivos_sin_entradas,
        facturacion_dispositivos_sin_devolucion
    ]).group_by(['Municipio', 'Servicio']).agg(pl.col('ValorNeto').sum()).sort(['Municipio', 'Servicio'])

    suministros_completo = pl.concat([
        consumos_suministros_sin_entradas,
        facturacion_suministros_sin_devolucion
    ]).group_by(['Municipio', 'Servicio']).agg(pl.col('ValorNeto').sum()).sort(['Municipio', 'Servicio'])

    return {
        'consumos_medicamentos': medicamentos_completo,
        'consumos_dispositivos': dispositivos_completo,
        'consumos_suministros': suministros_completo
        }
