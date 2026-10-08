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
        .when((pl.col("Especialidad") == "") | (pl.col("Especialidad").is_null()))
        .then(pl.col('Servicio_Corregido'))
        .otherwise(pl.col('Especialidad'))
        .alias('Especialidad_Corregida')
    )

    #para_revisar_consumos_facturacion = consumos_facturacion

    # with pl.Config(tbl_cols=-1, tbl_width_chars=1000):
    #     print(consumos_facturacion.filter(pl.col("field_1") == 241387))

    servicio_farmaceutico_medicamentos = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Medicamentos"
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad_Corregida'], separator='-').alias('Centro Costo')
        )

    servicio_farmaceutico_dispositivos = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad_Corregida'], separator='-').alias('Centro Costo')
        )

    servicio_farmaceutico_suministros = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad_Corregida'], separator='-').alias('Centro Costo')
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
        .when((pl.col("Especialidad") == "") | (pl.col("Especialidad").is_null()))
        .then(pl.col('Servicio_Corregido'))
        .otherwise(pl.col('Especialidad'))
        .alias('Especialidad_Corregida')
    )
    # para_revisar_entradas = devolucion_facturacion.clone()
    # para_revisar_consumos_facturacion = para_revisar_consumos_facturacion.join(para_revisar_entradas, on="ADM-CodGen", how="full", suffix="_Entradas")
    # #generamos un csv con esta informacion
    # para_revisar_consumos_facturacion.write_csv("revision_cruces_consumosvsentradas.csv", )
    # print("se genero archivo revisalo!!!!")


    # with pl.Config(tbl_cols=-1, tbl_width_chars=1000):
    #     print(devolucion_facturacion.filter(pl.col("field_1") == 241387))

    devolucion_fact_medicamentos = devolucion_facturacion.filter(
        pl.col('Clasificacion_consumo') == "Medicamentos"
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
            pl.col('ValorTotal').sum().cast(pl.Int64)
        ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad_Corregida'], separator='-').alias('Centro Costo')
        )

    devolucion_fact_dispositivos = devolucion_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad_Corregida'], separator='-').alias('Centro Costo')
        )

    devolucion_fact_suministros = devolucion_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    ).with_columns(
            pl.concat_str(['Municipio', 'Especialidad_Corregida'], separator='-').alias('Centro Costo')
        )

    consumos_medicamentos_sin_entradas = consumo_medicamentos.join(
        consumo_entradas_medicamentos, left_on='Centro Costo', right_on='Centro Costo', how='full'
    ).with_columns(
        pl.coalesce([pl.col("Municipio"), pl.col("Municipio_right")]).alias("Municipio"),
        pl.coalesce([pl.col("Servicio"), pl.col("Servicio_right")]).alias("Servicio"),
        (pl.col('ValorTotal').fill_null(0) - pl.col('ValorTotal_right').fill_null(0)).alias('ValorNeto')
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    consumos_dispositivos_sin_entradas = consumo_dispositivos.join(
        consumo_entradas_dispositivos, left_on='Centro Costo', right_on='Centro Costo', how='full'
    ).with_columns(
        pl.coalesce([pl.col("Municipio"), pl.col("Municipio_right")]).alias("Municipio"),
        pl.coalesce([pl.col("Servicio"), pl.col("Servicio_right")]).alias("Servicio"),
        (pl.col('ValorTotal').fill_null(0) - pl.col('ValorTotal_right').fill_null(0)).alias('ValorNeto')
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    consumos_suministros_sin_entradas = consumo_suministros.join(
        consumo_entradas_suministros, left_on='Centro Costo', right_on='Centro Costo', how='full'
    ).with_columns(
        pl.coalesce([pl.col("Municipio"), pl.col("Municipio_right")]).alias("Municipio"),
        pl.coalesce([pl.col("Servicio"), pl.col("Servicio_right")]).alias("Servicio"),
        (pl.col('ValorTotal').fill_null(0) - pl.col('ValorTotal_right').fill_null(0)).alias('ValorNeto')
    ).select(['Municipio', 'Servicio', 'ValorNeto'])

    facturacion_medicamentos_sin_devolucion = servicio_farmaceutico_medicamentos.join(
        devolucion_fact_medicamentos, left_on='Centro Costo', right_on='Centro Costo', how='full'
    ).with_columns(
        pl.coalesce([pl.col("Municipio"), pl.col("Municipio_right")]).alias("Municipio"),
        pl.coalesce([pl.col("Especialidad_Corregida"), pl.col("Especialidad_Corregida_right")]).alias("Especialidad_Corregida"),
        (pl.col('ValorTotal').fill_null(0) - pl.col('ValorTotal_right').fill_null(0)).alias('ValorNeto')
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
        pl.col('ValorNeto').sum()
    ).select([
        'Municipio', 
        pl.col('Especialidad_Corregida').alias("Servicio"),
        'ValorNeto'
    ])

    facturacion_dispositivos_sin_devolucion = servicio_farmaceutico_dispositivos.join(
        devolucion_fact_dispositivos, left_on='Centro Costo', right_on='Centro Costo', how='full'
    ).with_columns(
        pl.coalesce([pl.col("Municipio"), pl.col("Municipio_right")]).alias("Municipio"),
        pl.coalesce([pl.col("Especialidad_Corregida"), pl.col("Especialidad_Corregida_right")]).alias("Especialidad_Corregida"),
        (pl.col('ValorTotal').fill_null(0) - pl.col('ValorTotal_right').fill_null(0)).alias('ValorNeto')
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
        pl.col('ValorNeto').sum()
    ).select([
        'Municipio', 
        pl.col('Especialidad_Corregida').alias("Servicio"),
        'ValorNeto'
    ])

    facturacion_suministros_sin_devolucion = servicio_farmaceutico_suministros.join(
        devolucion_fact_suministros, left_on='Centro Costo', right_on='Centro Costo', how='full'
    ).with_columns(
        pl.coalesce([pl.col("Municipio"), pl.col("Municipio_right")]).alias("Municipio"),
        pl.coalesce([pl.col("Especialidad_Corregida"), pl.col("Especialidad_Corregida_right")]).alias("Especialidad_Corregida"),
        (pl.col('ValorTotal').fill_null(0) - pl.col('ValorTotal_right').fill_null(0)).alias('ValorNeto')
    ).group_by(['Municipio', 'Especialidad_Corregida']).agg(
        pl.col('ValorNeto').sum()
    ).select([
        'Municipio', 
        pl.col('Especialidad_Corregida').alias("Servicio"),
        'ValorNeto'
    ])

    #union facturacion con consumos
    medicamentos_completo = pl.concat([
        consumos_medicamentos_sin_entradas,
        facturacion_medicamentos_sin_devolucion
    ]).group_by(['Municipio', 'Servicio']).agg(pl.col('ValorNeto').sum()).sort(['Municipio', 'Servicio'])

    dispositivos_completo = facturacion_dispositivos_sin_devolucion.group_by(['Municipio', 'Servicio']).agg(pl.col('ValorNeto').sum()).sort(['Municipio', 'Servicio'])

    dispositivos_consumos_final = consumos_dispositivos_sin_entradas.group_by(['Municipio', 'Servicio']).agg(pl.col('ValorNeto').sum()).sort(['Municipio', 'Servicio'])
    
    suministros_completo = pl.concat([
        consumos_suministros_sin_entradas,
        facturacion_suministros_sin_devolucion
    ]).group_by(['Municipio', 'Servicio']).agg(pl.col('ValorNeto').sum()).sort(['Municipio', 'Servicio'])

    return {
        'consumos_medicamentos': medicamentos_completo,
        'consumos_dispositivos_formulados': dispositivos_completo,
        'consumo_dispositivos': dispositivos_consumos_final,
        'consumos_suministros': suministros_completo,
        }
