import polars as pl 

def hacer_informe(facturacion, entrada_facturacion, consumos, entradas_consumos):
    #region CONSUMOS
    consumos_normales = consumos.clone()

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

    consumos_facturacion = facturacion.clone().with_columns(
        pl.when(pl.col('Servicio_Corregido').is_in(['pym', 'cronicos', 'terapias oncologicas', 'servicio farmaceutico']))
        .then(pl.col('Servicio_Corregido'))
        .otherwise(pl.col('Especialidad'))
        .alias('Especialidad')
    )

    servicio_farmaceutico_medicamentos = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Medicamentos"
    ).group_by(['Municipio', 'Especialidad']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad'], separator='-').alias('Centro Costo')
        )

    servicio_farmaceutico_dispositivos = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Especialidad']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad'], separator='-').alias('Centro Costo')
        )

    servicio_farmaceutico_suministros = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Especialidad']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad'], separator='-').alias('Centro Costo')
        )

    #region Entradas
    entradas_consumo = entradas_consumos.clone()

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

    devolucion_facturacion = entrada_facturacion.clone().with_columns(
        pl.when(pl.col('Servicio_Corregido').is_in(['pym', 'cronicos', 'terapias oncologicas', 'servicio farmaceutico']))
        .then(pl.col('Servicio_Corregido'))
        .otherwise(pl.col('Especialidad'))
        .alias('Especialidad')
    )

    devolucion_fact_medicamentos = devolucion_facturacion.filter(
        pl.col('Clasificacion_consumo') == "Medicamentos"
    ).group_by(['Municipio', 'Especialidad']).agg(
            pl.col('ValorTotal').sum().cast(pl.Int64)
        ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad'], separator='-').alias('Centro Costo')
        )

    devolucion_fact_dispositivos = devolucion_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Especialidad']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad'], separator='-').alias('Centro Costo')
        )

    devolucion_fact_suministros = devolucion_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Especialidad']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad'], separator='-').alias('Centro Costo')
        )

    consumos_medicamentos_sin_entradas = consumo_medicamentos.join(consumo_entradas_medicamentos, left_on='Centro Costo', right_on='Centro Costo', how='full').fill_null(0)
    consumos_dispositivos_sin_entradas = consumo_dispositivos.join(consumo_entradas_dispositivos, left_on='Centro Costo', right_on='Centro Costo', how='full').fill_null(0)
    consumos_suministros_sin_entradas = consumo_suministros.join(consumo_entradas_suministros, left_on='Centro Costo', right_on='Centro Costo', how='full').fill_null(0)

    facturacion_medicamentos_sin_devolucion = servicio_farmaceutico_medicamentos.join(devolucion_fact_medicamentos, left_on='Centro Costo', right_on='Centro Costo', how='full').fill_null(0)
    
    facturacion_dispositivos_sin_devolucion = servicio_farmaceutico_dispositivos.join(devolucion_fact_dispositivos, left_on='Centro Costo', right_on='Centro Costo', how='full').fill_null(0)
    facturacion_suministros_sin_devolucion = servicio_farmaceutico_suministros.join(devolucion_fact_suministros, left_on='Centro Costo', right_on='Centro Costo', how='full').fill_null(0)

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
    ).group_by(['Municipio', 'Especialidad']).agg(pl.col('ValorNeto').sum()
    ).select(['Municipio', 
    pl.col('Especialidad').alias("Servicio"),
    'ValorNeto'])

    facturacion_dispositivos_sin_devolucion = facturacion_dispositivos_sin_devolucion.with_columns(
        (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorNeto')
    ).group_by(['Municipio', 'Especialidad']).agg(pl.col('ValorNeto').sum()
    ).select(['Municipio', 
    pl.col('Especialidad').alias("Servicio"),
    'ValorNeto'])

    facturacion_suministros_sin_devolucion = facturacion_suministros_sin_devolucion.with_columns(
        (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorNeto')
    ).group_by(['Municipio', 'Especialidad']).agg(pl.col('ValorNeto').sum()
    ).select(['Municipio', 
    pl.col('Especialidad').alias("Servicio"),
    'ValorNeto'])

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
        'consumos_suministros': suministros_completo,
        }
