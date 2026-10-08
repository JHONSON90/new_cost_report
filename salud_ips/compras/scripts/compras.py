import os
import sys
from pathlib import Path
import polars as pl

# Asegurar codificación utf-8 en consola para Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Importación relativa y absoluta tolerante
try:
    from .procesamiento import procesamiento
except ImportError:
    from procesamiento import procesamiento


def Analizando_compras(df_compras_aprovechamientos: pl.DataFrame):
    """
    Analiza las compras realizadas a los proveedores, calculando el valor unitario de cada compra,
    agrupando por proveedor, producto y fecha para obtener información detallada sobre las compras.

    Args:
        datos_procesados: Diccionario con los dataframes generados en Paso 2 (procesamiento).
                          Si es None, se invoca automáticamente el paso de procesamiento.

    Returns:
        dict con los entregables de análisis:
            - Informe_por_proveedor
            - Mayor_compra
            - producto_mas_comprado
            - comportamientos_mensuales
    """
    print("\n" + "=" * 60)
    print("PASO 3: ANÁLISIS DE COMPRAS Y PROVEEDORES")
    print("=" * 60)

    # Si no se suministran datos procesados, se invoca el paso previo
    if df_compras_aprovechamientos is None or df_compras_aprovechamientos.is_empty():
        print("⚠ Advertencia: No hay registros de compras y aprovechamientos para analizar.")
        return {}

    print("Comenzando el análisis de compras...")

    compras_proveedor = df_compras_aprovechamientos.filter(
        pl.col("Comprobante_corregido").is_in(['RMC - REGISTRO DE COMPRA FARMACIA', 'DC - DEVOLUCION DE COMPRA'])
    ).with_columns(
        pl.when((pl.col("Cantidad").is_null()) | (pl.col("Cantidad") == 0) | (pl.col("ValorTotal") == 0))
        .then(pl.lit(0.0))
        .otherwise((pl.col("ValorTotal") / pl.col("Cantidad")).cast(pl.Float64))
        .alias("valor_unitario_calculado")
    )

    idx_compras = ["Fecha", "Bodega", "CodigoGenerico", "GrupoInventario", "Generico", "Tercero", "Mes"]

    compras_proveedor = compras_proveedor.pivot(
        on="Comprobante_corregido",
        index=idx_compras,
        values=['Cantidad', 'ValorTotal'],
        aggregate_function="sum"
    ).fill_null(0)

    # Asegurar existencia de columnas esperadas tras el pivot
    col_cant_rmc = 'Cantidad_RMC - REGISTRO DE COMPRA FARMACIA'
    col_cant_dc = 'Cantidad_DC - DEVOLUCION DE COMPRA'
    col_val_rmc = 'ValorTotal_RMC - REGISTRO DE COMPRA FARMACIA'
    col_val_dc = 'ValorTotal_DC - DEVOLUCION DE COMPRA'

    cols_existentes = set(compras_proveedor.columns)
    columnas_faltantes = []
    if col_cant_rmc not in cols_existentes:
        columnas_faltantes.append(pl.lit(0).alias(col_cant_rmc))
    if col_cant_dc not in cols_existentes:
        columnas_faltantes.append(pl.lit(0).alias(col_cant_dc))
    if col_val_rmc not in cols_existentes:
        columnas_faltantes.append(pl.lit(0.0).alias(col_val_rmc))
    if col_val_dc not in cols_existentes:
        columnas_faltantes.append(pl.lit(0.0).alias(col_val_dc))
    if columnas_faltantes:
        compras_proveedor = compras_proveedor.with_columns(columnas_faltantes)

    compras_proveedor_neto = compras_proveedor.with_columns(
        (pl.col(col_cant_rmc) - pl.col(col_cant_dc)).alias('Cantidad_neta'),
        (pl.col(col_val_rmc) - pl.col(col_val_dc)).alias('ValorTotal_neto')
    ).select(['Fecha', 'Bodega', 'CodigoGenerico', 'GrupoInventario', 'Generico', 'Tercero', 'Mes', 'Cantidad_neta', 'ValorTotal_neto'])

    compras_proveedor_neto = compras_proveedor_neto.with_columns(
        pl.when((pl.col('Cantidad_neta').is_null()) | (pl.col('Cantidad_neta') == 0))
        .then(pl.lit(0.0))
        .otherwise((pl.col('ValorTotal_neto') / pl.col('Cantidad_neta')).cast(pl.Float64).round(2))
        .alias('valor_unitario_calculado')
    )

    # Entregable 1: Informe compras por vendedor/proveedor
    informe_compras_vendedor = compras_proveedor_neto.group_by(["Fecha", "Mes", 'Bodega', 'GrupoInventario', 'CodigoGenerico', 'Generico', "Tercero"]).agg(
        pl.col("valor_unitario_calculado").sum().alias("suma valor unitario"),
        pl.col("valor_unitario_calculado").count().alias("cantidad compras"),
        pl.col("valor_unitario_calculado").min().alias("valor unitario minimo"),
        pl.col("valor_unitario_calculado").max().alias("valor unitario maximo"),
        pl.col("valor_unitario_calculado").mean().alias("valor unitario promedio")
    ).fill_null(0)

    # Entregable 2: Ranking mayor compra
    mayor_compra = compras_proveedor_neto.group_by(['GrupoInventario', 'CodigoGenerico', 'Generico', "Tercero"]).agg(
        pl.col("Cantidad_neta").sum().alias("cantidad_comprada_neta"),
        pl.col("ValorTotal_neto").sum().alias("valor_total_comprado_neto"),
        pl.col("valor_unitario_calculado").mean().alias("valor_unitario_calculado_promedio"),
        pl.col("valor_unitario_calculado").max().alias("valor_unitario_calculado_maximo"),
        pl.col("valor_unitario_calculado").min().alias("valor_unitario_calculado_minimo"),
        pl.col("valor_unitario_calculado").count().alias("cantidad_registros"),
    ).sort(
        by="valor_total_comprado_neto", descending=True
    )

    # Entregable 3: Producto más comprado
    producto_mas_comprado = compras_proveedor_neto.group_by(['GrupoInventario', 'CodigoGenerico', 'Generico']).agg(
        pl.col("Cantidad_neta").sum().alias("cantidad_comprada_neta"),
        pl.col("ValorTotal_neto").sum().alias("valor_total_comprado_neto"),
        pl.col("valor_unitario_calculado").mean().alias("valor_unitario_calculado_promedio"),
        pl.col("valor_unitario_calculado").max().alias("valor_unitario_calculado_maximo"),
        pl.col("valor_unitario_calculado").min().alias("valor_unitario_calculado_minimo"),
        pl.col("Tercero").count().alias("cantidad_proveedores"),
    ).sort(
        by="cantidad_comprada_neta", descending=True
    )

    # Entregable 4: Comportamientos mensuales
    comportamiento_vunit = compras_proveedor_neto.pivot(
        on="Mes",
        index=['GrupoInventario', 'CodigoGenerico', 'Generico'],
        values="valor_unitario_calculado",
        aggregate_function="mean"
    ).fill_null(0)

    comportamiento_cant_neta = compras_proveedor_neto.pivot(
        on="Mes",
        index=['GrupoInventario', 'CodigoGenerico', 'Generico'],
        values=["Cantidad_neta", "ValorTotal_neto"],
        aggregate_function="sum"
    ).fill_null(0)

    cant_registros_compras = compras_proveedor_neto.pivot(
        on="Mes",
        index=['GrupoInventario', 'CodigoGenerico', 'Generico'],
        values="Cantidad_neta",
        aggregate_function="len"
    ).fill_null(0)

    comportamientos_mensuales = comportamiento_vunit.join(
        comportamiento_cant_neta, on=['GrupoInventario', 'CodigoGenerico', 'Generico'], suffix="_cant_neta"
    ).join(
        cant_registros_compras, on=['GrupoInventario', 'CodigoGenerico', 'Generico'], suffix="_cant_registros"
    ).fill_null(0)

    print("✓ Finalizando el análisis de compras")
    return {
        "Informe_por_proveedor": informe_compras_vendedor,
        "Mayor_compra": mayor_compra,
        "producto_mas_comprado": producto_mas_comprado,
        "comportamientos_mensuales": comportamientos_mensuales
    }

