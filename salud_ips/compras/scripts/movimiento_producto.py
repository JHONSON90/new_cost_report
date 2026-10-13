import polars as pl 

def analisis_movimientos_completos(compras : pl.DataFrame,movimientos_iniciales : pl.DataFrame,ajustes : pl.DataFrame,prestamos_realizados : pl.DataFrame,prestamos_recibidos : pl.DataFrame, consumos : pl.DataFrame, traslados : pl.DataFrame) -> pl.DataFrame:

    print("\n" + "=" * 60)
    print("PASO 5: ANÁLISIS DE MOVIMIENTOS COMPLETOS")
    print(f"★ Se reciben en compras: {compras.shape[0]} registros.")
    print(f"★ Se reciben en movimientos_iniciales: {movimientos_iniciales.shape[0]} registros.")
    print(f"★ Se reciben en ajustes: {ajustes.shape[0]} registros.")
    print(f"★ Se reciben en prestamos_realizados: {prestamos_realizados.shape[0]} registros.")
    print(f"★ Se reciben en prestamos_recibidos: {prestamos_recibidos.shape[0]} registros.")
    print(f"★ Se reciben en consumos: {consumos.shape[0]} registros.")
    print(f"★ Se reciben en traslados: {traslados.shape[0]} registros.")
    print("=" * 60)

    compras = compras.with_columns(
        (pl.col('Cantidad_EAP - ENTRADAS POR APROVECHAMIENTO') + pl.col('Cantidad_RMC - REGISTRO DE COMPRA FARMACIA') + pl.col('Cantidad_EDO - ENTRADAS DONACIONES') - pl.col('Cantidad_DC - DEVOLUCION DE COMPRA')).alias('Cantidad_total_compras'), 
        (pl.col('ValorTotal_EAP - ENTRADAS POR APROVECHAMIENTO') + pl.col('ValorTotal_RMC - REGISTRO DE COMPRA FARMACIA') + pl.col('ValorTotal_EDO - ENTRADAS DONACIONES') - pl.col('ValorTotal_DC - DEVOLUCION DE COMPRA')).alias('ValorTotal_total_compras'),
    )

    movimientos_iniciales = movimientos_iniciales.with_columns(
        (pl.col('Cantidad_MIA - MOVIMIENTO INICIAL') - pl.col('Cantidad_MIS - MOVIMIENTO INICIAL DE SALIDA')).alias('Cantidad_total_movimientos_iniciales'),
        (pl.col('ValorTotal_MIA - MOVIMIENTO INICIAL') - pl.col('ValorTotal_MIS - MOVIMIENTO INICIAL DE SALIDA')).alias('ValorTotal_total_movimientos_iniciales'),
    )
    if 'Cantidad_EASC - ENTRADAS AJUSTES SOBRANTES CONTEO' in ajustes.columns:
        ajustes = ajustes.with_columns(
            (pl.col('Cantidad_EAS - ENTRADAS AJUSTES SOBRANTES') + pl.col('Cantidad_EASC - ENTRADAS AJUSTES SOBRANTES CONTEO') - pl.col('Cantidad_SAF - SALIDAS AJUSTES FALTANTES') - pl.col('Cantidad_SAFC - SALIDAS AJUSTES FALTANTES CONTEO')).alias('Cantidad_total_ajustes'),
            (pl.col('ValorTotal_EAS - ENTRADAS AJUSTES SOBRANTES') + pl.col('ValorTotal_EASC - ENTRADAS AJUSTES SOBRANTES CONTEO') - pl.col('ValorTotal_SAF - SALIDAS AJUSTES FALTANTES') - pl.col('ValorTotal_SAFC - SALIDAS AJUSTES FALTANTES CONTEO')).alias('ValorTotal_total_ajustes')
        )
    else:
        ajustes = ajustes.with_columns(
            (pl.col('Cantidad_EAS - ENTRADAS AJUSTES SOBRANTES') - pl.col('Cantidad_SAF - SALIDAS AJUSTES FALTANTES')).alias('Cantidad_total_ajustes'),
            (pl.col('ValorTotal_EAS - ENTRADAS AJUSTES SOBRANTES') - pl.col('ValorTotal_SAF - SALIDAS AJUSTES FALTANTES')).alias('ValorTotal_total_ajustes')
        )


    prestamos_realizados = prestamos_realizados.with_columns(
        (pl.col('Cantidad_SPOE - SALIDAS POR PRESTAMOS A OTRAS ENTIDADES') - pl.col('Cantidad_EDP - ENTRADAS POR DEVOLUCION A PRESTAMOS') - pl.col('Cantidad_EPS - ENTRADAS PRESTAMOS SIIGO')).alias('Cantidad_total_prestamos_realizados'),
        (pl.col('ValorTotal_SPOE - SALIDAS POR PRESTAMOS A OTRAS ENTIDADES') - pl.col('ValorTotal_EDP - ENTRADAS POR DEVOLUCION A PRESTAMOS') - pl.col('ValorTotal_EPS - ENTRADAS PRESTAMOS SIIGO')).alias('ValorTotal_total_prestamos_realizados'),
    )

    prestamos_recibidos = prestamos_recibidos.with_columns(
        (pl.col('Cantidad_EPOE - ENTRADAS POR PRESTAMOS DE OTRAS ENTIDADES') - pl.col('Cantidad_SDP - SALIDAS POR DEVOLUCION DE PRESTAMOS') - pl.col('Cantidad_SPS - SALIDAS PRESTAMOS SIIGO')).alias('Cantidad_total_prestamos_recibidos'),
        (pl.col('ValorTotal_EPOE - ENTRADAS POR PRESTAMOS DE OTRAS ENTIDADES') - pl.col('ValorTotal_SDP - SALIDAS POR DEVOLUCION DE PRESTAMOS') - pl.col('ValorTotal_SPS - SALIDAS PRESTAMOS SIIGO')).alias('ValorTotal_total_prestamos_recibidos'),
    )

    consumos = consumos.with_columns(
        (pl.col('Cantidad_SDF - SISTEMA DISPENSACION FARMACIA') + pl.col('Cantidad_SIN - SALIDAS INTERNAS FARMACIA') - pl.col('Cantidad_SADF - SISTEMA ANULACION DISPENSACION FARMACIA')- pl.col('Cantidad_EIS - ENTRADAS INTERNAS SIMA')- pl.col('Cantidad_SIA - SALIDAS INTERNAS ALMACEN')).alias('Cantidad_total_consumos'),
        (pl.col('ValorTotal_SDF - SISTEMA DISPENSACION FARMACIA') + pl.col('ValorTotal_SIN - SALIDAS INTERNAS FARMACIA') - pl.col('ValorTotal_SADF - SISTEMA ANULACION DISPENSACION FARMACIA')- pl.col('ValorTotal_EIS - ENTRADAS INTERNAS SIMA') - pl.col('ValorTotal_SIA - SALIDAS INTERNAS ALMACEN')).alias('ValorTotal_total_consumos'),
    )

    traslados = traslados.with_columns(
        (pl.col('Cantidad_ENTRADA POR TRASLADO') - pl.col('Cantidad_SALIDA POR TRASLADO')).alias('Cantidad_total_traslados'),
        (pl.col('ValorTotal_ENTRADA POR TRASLADO') - pl.col('ValorTotal_SALIDA POR TRASLADO')).alias('ValorTotal_total_traslados'),
    )


    uniones= ["CodigoGenerico", "GrupoInventario", "Generico"]

    compras_agrupadas = compras.group_by(uniones).agg(
        pl.col("Cantidad_total_compras").sum().alias("Cantidad_total_compras"),
        pl.col("ValorTotal_total_compras").sum().alias("ValorTotal_total_compras"),
    )

    movimientos_iniciales_agrupadas = movimientos_iniciales.group_by(uniones).agg(
        pl.col("Cantidad_total_movimientos_iniciales").sum().alias("Cantidad_total_movimientos_iniciales"),
        pl.col("ValorTotal_total_movimientos_iniciales").sum().alias("ValorTotal_total_movimientos_iniciales"),
    )

    ajustes_agrupados = ajustes.group_by(uniones).agg(
        pl.col("Cantidad_total_ajustes").sum().alias("Cantidad_total_ajustes"),
        pl.col("ValorTotal_total_ajustes").sum().alias("ValorTotal_total_ajustes"),
    )

    prestamos_realizados_agrupados = prestamos_realizados.group_by(uniones).agg(
        pl.col("Cantidad_total_prestamos_realizados").sum().alias("Cantidad_total_prestamos_realizados"),
        pl.col("ValorTotal_total_prestamos_realizados").sum().alias("ValorTotal_total_prestamos_realizados"),
    )

    prestamos_recibidos_agrupados = prestamos_recibidos.group_by(uniones).agg(
        pl.col("Cantidad_total_prestamos_recibidos").sum().alias("Cantidad_total_prestamos_recibidos"),
        pl.col("ValorTotal_total_prestamos_recibidos").sum().alias("ValorTotal_total_prestamos_recibidos"),
    )

    consumos_agrupados = consumos.group_by(uniones).agg(
        pl.col("Cantidad_total_consumos").sum().alias("Cantidad_total_consumos"),
        pl.col("ValorTotal_total_consumos").sum().alias("ValorTotal_total_consumos"),
    )

    dfs_agrupados = [
        compras_agrupadas, movimientos_iniciales_agrupadas, ajustes_agrupados,
        prestamos_realizados_agrupados, prestamos_recibidos_agrupados, consumos_agrupados
    ]
    agrupado = pl.concat(dfs_agrupados, how="diagonal_relaxed").group_by(uniones).sum().fill_null(0)

    uniones_detallados = ["Bodega", "CodigoGenerico", "GrupoInventario", "Generico"]
    compras_detallados = compras.group_by(uniones_detallados).agg(
        pl.col("Cantidad_total_compras").sum().alias("Cantidad_total_compras"),
        pl.col("ValorTotal_total_compras").sum().alias("ValorTotal_total_compras"),
    )

    movimientos_iniciales_detallados = movimientos_iniciales.group_by(uniones_detallados).agg(
        pl.col("Cantidad_total_movimientos_iniciales").sum().alias("Cantidad_total_movimientos_iniciales"),
        pl.col("ValorTotal_total_movimientos_iniciales").sum().alias("ValorTotal_total_movimientos_iniciales"),
    )

    ajustes_detallados = ajustes.group_by(uniones_detallados).agg(
        pl.col("Cantidad_total_ajustes").sum().alias("Cantidad_total_ajustes"),
        pl.col("ValorTotal_total_ajustes").sum().alias("ValorTotal_total_ajustes"),
    )

    prestamos_realizados_detallados = prestamos_realizados.group_by(uniones_detallados).agg(
        pl.col("Cantidad_total_prestamos_realizados").sum().alias("Cantidad_total_prestamos_realizados"),
        pl.col("ValorTotal_total_prestamos_realizados").sum().alias("ValorTotal_total_prestamos_realizados"),
    )

    prestamos_recibidos_detallados = prestamos_recibidos.group_by(uniones_detallados).agg(
        pl.col("Cantidad_total_prestamos_recibidos").sum().alias("Cantidad_total_prestamos_recibidos"),
        pl.col("ValorTotal_total_prestamos_recibidos").sum().alias("ValorTotal_total_prestamos_recibidos"),
    )

    consumos_detallados = consumos.group_by(uniones_detallados).agg(
        pl.col("Cantidad_total_consumos").sum().alias("Cantidad_total_consumos"),
        pl.col("ValorTotal_total_consumos").sum().alias("ValorTotal_total_consumos"),
    )

    traslados_detallados = traslados.group_by(uniones_detallados).agg(
        pl.col("Cantidad_total_traslados").sum().alias("Cantidad_total_traslados"),
        pl.col("ValorTotal_total_traslados").sum().alias("ValorTotal_total_traslados"),
    )

    

    dfs_detallados = [
        compras_detallados, movimientos_iniciales_detallados, ajustes_detallados,
        prestamos_realizados_detallados, prestamos_recibidos_detallados,
        consumos_detallados, traslados_detallados
    ]
    detallado = pl.concat(dfs_detallados, how="diagonal_relaxed").group_by(uniones_detallados).sum().fill_null(0)

    return {
        "Movimiento_agrupado": agrupado,
        "Movimiento_detallado": detallado
    }

