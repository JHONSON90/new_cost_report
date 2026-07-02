import polars as pl 

def hacer_informe(consumos):
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
    )

    consumo_dispositivos = consumos_normales.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    )

    consumo_suministros = consumos_normales.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
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
    )

    servicio_farmaceutico_dispositivos = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Dispositivos Medicos"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    )

    servicio_farmaceutico_suministros = consumos_facturacion.filter(
        pl.col("Clasificacion_consumo") == "Suministros"
    ).group_by(['Municipio', 'Servicio']).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
    )
    #TODO: HACER LOGICA DE LA DEVOLUCION PARA TENER EL TOTAL DE MEDICAMENTOS DISPOSITIVOS Y SUMINISTROS
    medicamentos = pl.concat([consumo_medicamentos, servicio_farmaceutico_medicamentos])
    dispositivos = pl.concat([consumo_dispositivos, servicio_farmaceutico_dispositivos])
    suministros = pl.concat([consumo_suministros, servicio_farmaceutico_suministros])

    return medicamentos, dispositivos, suministros
