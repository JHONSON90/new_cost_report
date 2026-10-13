import polars as pl

def analisis_consumos_mensuales(consumos_netos: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """
    Analiza los consumos mensuales de los productos, permitiendo identificar patrones de consumo.
    Genera 5 entregables analíticos.
    """
    if consumos_netos.is_empty():
        print("⚠ No hay registros de consumos para analizar.")
        return {}

    cols = consumos_netos.columns
    def col_or_0(name):
        return pl.col(name) if name in cols else pl.lit(0.0)

    consumos = consumos_netos.with_columns(
        pl.col("Fecha").dt.month().alias("Mes"),
        (col_or_0('Cantidad_SDF - SISTEMA DISPENSACION FARMACIA') + 
         col_or_0('Cantidad_SIN - SALIDAS INTERNAS FARMACIA') + 
         col_or_0('Cantidad_SIA - SALIDAS INTERNAS ALMACEN') - 
         col_or_0('Cantidad_SADF - SISTEMA ANULACION DISPENSACION FARMACIA') - 
         col_or_0('Cantidad_EIS - ENTRADAS INTERNAS SIMA')).alias('Cantidad_Total'),
        
        (col_or_0('ValorTotal_SDF - SISTEMA DISPENSACION FARMACIA') + 
         col_or_0('ValorTotal_SIN - SALIDAS INTERNAS FARMACIA') + 
         col_or_0('ValorTotal_SIA - SALIDAS INTERNAS ALMACEN') - 
         col_or_0('ValorTotal_SADF - SISTEMA ANULACION DISPENSACION FARMACIA') - 
         col_or_0('ValorTotal_EIS - ENTRADAS INTERNAS SIMA')).alias('Valor_Total')
    ).sort("Mes")

    filas_prod = ["CodigoGenerico", "GrupoInventario", "Generico"]
    
    # Hoja 1: Consumo_Mensual_Cantidades
    df_cant = consumos.group_by(filas_prod + ["Mes"]).agg(pl.sum("Cantidad_Total"))
    pivot_cant = df_cant.pivot(on="Mes", index=filas_prod, values="Cantidad_Total", aggregate_function="sum").fill_null(0)
    mes_cols = sorted([c for c in pivot_cant.columns if c not in filas_prod], key=lambda x: int(x) if str(x).isdigit() else str(x))
    
    pivot_cant = pivot_cant.with_columns(
        pl.sum_horizontal(mes_cols).alias("Total_Cantidad"),
        pl.mean_horizontal(mes_cols).alias("Promedio_Mensual"),
        pl.min_horizontal(mes_cols).alias("Minimo_Mensual"),
        pl.max_horizontal(mes_cols).alias("Maximo_Mensual")
    ).select(filas_prod + mes_cols + ["Total_Cantidad", "Promedio_Mensual", "Minimo_Mensual", "Maximo_Mensual"])
    
    # Hoja 2: Consumo_Mensual_Valores
    df_val = consumos.group_by(filas_prod + ["Mes"]).agg(pl.sum("Valor_Total"))
    pivot_val = df_val.pivot(on="Mes", index=filas_prod, values="Valor_Total", aggregate_function="sum").fill_null(0)
    mes_cols_val = sorted([c for c in pivot_val.columns if c not in filas_prod], key=lambda x: int(x) if str(x).isdigit() else str(x))
    
    pivot_val = pivot_val.with_columns(
        pl.sum_horizontal(mes_cols_val).alias("Total_Valor"),
        pl.mean_horizontal(mes_cols_val).alias("Promedio_Valor"),
        pl.min_horizontal(mes_cols_val).alias("Minimo_Valor"),
        pl.max_horizontal(mes_cols_val).alias("Maximo_Valor")
    ).select(filas_prod + mes_cols_val + ["Total_Valor", "Promedio_Valor", "Minimo_Valor", "Maximo_Valor"])
    
    # Hoja 3: Clasificacion_ABC_Pareto
    abc = consumos.group_by(filas_prod).agg(pl.sum("Valor_Total").alias("Valor_Total_Consumido"))
    abc = abc.sort("Valor_Total_Consumido", descending=True)
    total_consumo = abc["Valor_Total_Consumido"].sum()
    
    if total_consumo and total_consumo > 0:
        abc = abc.with_columns(
            (pl.col("Valor_Total_Consumido") / total_consumo).alias("Porcentaje_Participacion")
        ).with_columns(
            pl.col("Porcentaje_Participacion").cum_sum().alias("Porcentaje_Acumulado")
        ).with_columns(
            pl.when(pl.col("Porcentaje_Acumulado") <= 0.80).then(pl.lit("A"))
              .when(pl.col("Porcentaje_Acumulado") <= 0.95).then(pl.lit("B"))
              .otherwise(pl.lit("C")).alias("Clasificacion_ABC")
        )
    else:
        abc = abc.with_columns(
            pl.lit(0.0).alias("Porcentaje_Participacion"),
            pl.lit(0.0).alias("Porcentaje_Acumulado"),
            pl.lit("C").alias("Clasificacion_ABC")
        )
        
    # Hoja 4: Variabilidad_por_Bodega
    filas_bodega = ["Bodega", "CodigoGenerico", "GrupoInventario", "Generico"]
    df_var = consumos.group_by(filas_bodega + ["Mes"]).agg(pl.sum("Cantidad_Total"))
    pivot_var = df_var.pivot(on="Mes", index=filas_bodega, values="Cantidad_Total", aggregate_function="sum").fill_null(0)
    mes_cols_var = sorted([c for c in pivot_var.columns if c not in filas_bodega], key=lambda x: int(x) if str(x).isdigit() else str(x))
    
    std_df = df_var.group_by(filas_bodega).agg(
        pl.col("Cantidad_Total").std().fill_null(0).alias("Desviacion_Estandar")
    )
    pivot_var = pivot_var.join(std_df, on=filas_bodega, how="left").fill_null(0)
    
    pivot_var = pivot_var.with_columns(
        pl.mean_horizontal(mes_cols_var).alias("Promedio_Mensual")
    ).with_columns(
        pl.when(pl.col("Promedio_Mensual") > 0)
          .then(pl.col("Desviacion_Estandar") / pl.col("Promedio_Mensual"))
          .otherwise(pl.lit(0.0)).alias("Coeficiente_Variacion")
    ).with_columns(
        pl.when(pl.col("Coeficiente_Variacion") <= 0.25).then(pl.lit("Estable"))
          .when(pl.col("Coeficiente_Variacion") <= 0.50).then(pl.lit("Variable"))
          .otherwise(pl.lit("Erratica")).alias("Tipo_Demanda")
    ).select(filas_bodega + mes_cols_var + ["Promedio_Mensual", "Desviacion_Estandar", "Coeficiente_Variacion", "Tipo_Demanda"])
    
    # Hoja 5: Consumo_por_Bodega
    pivot_bodega = df_var.pivot(on="Mes", index=filas_bodega, values="Cantidad_Total", aggregate_function="sum").fill_null(0)
    mes_cols_bodega = sorted([c for c in pivot_bodega.columns if c not in filas_bodega], key=lambda x: int(x) if str(x).isdigit() else str(x))
    
    pivot_bodega = pivot_bodega.with_columns(
        pl.sum_horizontal(mes_cols_bodega).alias("Total_Cantidad"),
        pl.mean_horizontal(mes_cols_bodega).alias("Promedio_Mensual")
    ).select(filas_bodega + mes_cols_bodega + ["Total_Cantidad", "Promedio_Mensual"])
    
    return {
        "Consumo_Mensual_Cantidades": pivot_cant,
        "Consumo_Mensual_Valores": pivot_val,
        "Clasificacion_ABC_Pareto": abc,
        "Variabilidad_por_Bodega": pivot_var,
        "Consumo_por_Bodega": pivot_bodega
    }