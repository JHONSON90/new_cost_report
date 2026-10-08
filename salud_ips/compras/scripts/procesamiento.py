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


def procesamiento(
    datos: pl.DataFrame | dict[str, pl.DataFrame] | None = None
) -> dict[str, pl.DataFrame]:
    """
    Procesa, limpia y clasifica los movimientos de inventario confirmados.
    Calcula dataframes neteados para compras, movimientos iniciales, ajustes,
    préstamos, traslados y consumos.

    Args:
        datos: DataFrame de movimientos consolidado (o dict que contenga 'movimientos').
               Si es None, se invoca automáticamente lectura_archivos_completa().

    Returns:
        dict con los DataFrames procesados y neteados.
    """
    print("\n" + "=" * 60)
    print("PASO 2: PROCESAMIENTO DE ARCHIVOS")
    print("=" * 60)

    # Si no se suministran datos, se invocan desde el paso 1 (lectura)
    if datos is None:
        try:
            from .lectura_archivos import lectura_archivos_completa
        except ImportError:
            from lectura_archivos import lectura_archivos_completa

        print("ℹ No se recibieron datos en memoria; ejecutando lectura_archivos_completa()...")
        datos = lectura_archivos_completa()

    # Si se recibe como diccionario, extraer el DataFrame de movimientos
    if isinstance(datos, dict):
        datos = datos.get("movimientos", datos.get("entradas"))

    if datos is None or datos.is_empty():
        print("⚠ Advertencia: El conjunto de datos para procesamiento está vacío.")
        return {}

    # Homogeneización de comprobantes y filtrado de confirmados
    datos = datos.with_columns(
        pl.when((pl.col("TipoMovimiento") == "SALIDA") & (pl.col("Comprobante") == "TEB - TRASLADOS ENTRE BODEGAS"))
        .then(pl.lit("SALIDA POR TRASLADO"))
        .when((pl.col("TipoMovimiento") == "ENTRADA") & (pl.col("Comprobante") == "TEB - TRASLADOS ENTRE BODEGAS"))
        .then(pl.lit("ENTRADA POR TRASLADO"))
        .otherwise(pl.col("Comprobante"))
        .alias("Comprobante_corregido")
    ).filter(
        pl.col("Estado") == "CONFIRMADO"
    ).with_columns(
        pl.col("Fecha").str.slice(0, 10).str.to_date("%d/%m/%Y").alias("Fecha")
    )

    datos = datos.with_columns(
        pl.col("Fecha").dt.year().alias("Año"),
        pl.col("Fecha").dt.month().alias("Mes"),
        pl.col("Fecha").dt.day().alias("Dia"),
        pl.col("Cantidad").cast(pl.Int64, strict=False),
        pl.col("ValorTotal").cast(pl.Float64, strict=False)
    )

    # Clasificación por tipo de comprobante
    compras_aprovechamientos = datos.filter(
        pl.col("Comprobante_corregido").is_in([
            'RMC - REGISTRO DE COMPRA FARMACIA',
            'DC - DEVOLUCION DE COMPRA',
            'EDO - ENTRADAS DONACIONES',
            'EAP - ENTRADAS POR APROVECHAMIENTO'
        ])
    )

    movimientos_iniciales = datos.filter(
        pl.col("Comprobante_corregido").is_in([
            'MIA - MOVIMIENTO INICIAL',
            'MIS - MOVIMIENTO INICIAL DE SALIDA'
        ])
    )

    ajustes = datos.filter(
        pl.col("Comprobante_corregido").is_in([
            'EAS - ENTRADAS AJUSTES SOBRANTES',
            'SAF - SALIDAS AJUSTES FALTANTES'
        ])
    )

    prestamos_realizados = datos.filter(
        pl.col("Comprobante_corregido").is_in([
            'SPOE - SALIDAS POR PRESTAMOS A OTRAS ENTIDADES',
            'EDP - ENTRADAS POR DEVOLUCION A PRESTAMOS',
            'EPS - ENTRADAS PRESTAMOS SIIGO'
        ])
    )

    prestamos_recibidos = datos.filter(
        pl.col("Comprobante_corregido").is_in([
            'EPOE - ENTRADAS POR PRESTAMOS DE OTRAS ENTIDADES',
            'SDP - SALIDAS POR DEVOLUCION DE PRESTAMOS',
            'SPS - SALIDAS PRESTAMOS SIIGO'
        ])
    )

    traslados = datos.filter(
        pl.col("Comprobante_corregido").is_in([
            'ENTRADA POR TRASLADO',
            'SALIDA POR TRASLADO'
        ])
    )

    consumos = datos.filter(
        pl.col("Comprobante_corregido").is_in([
            'SADF - SISTEMA ANULACION DISPENSACION FARMACIA',
            'SDF - SISTEMA DISPENSACION FARMACIA',
            'SIA - SALIDAS INTERNAS ALMACEN',
            'SIN - SALIDAS INTERNAS FARMACIA',
            'EIS - ENTRADAS INTERNAS SIMA'
        ])
    )

    print(f"  - Registros confirmados: {datos.shape[0]:,}")
    print(f"  - Compras y aprovechamientos: {compras_aprovechamientos.shape[0]:,}")
    print(f"  - Movimientos iniciales: {movimientos_iniciales.shape[0]:,}")
    print(f"  - Ajustes: {ajustes.shape[0]:,}")
    print(f"  - Préstamos realizados: {prestamos_realizados.shape[0]:,}")
    print(f"  - Préstamos recibidos: {prestamos_recibidos.shape[0]:,}")
    print(f"  - Traslados: {traslados.shape[0]:,}")
    print(f"  - Consumos: {consumos.shape[0]:,}")

    pendientes = (
        datos.shape[0]
        - compras_aprovechamientos.shape[0]
        - movimientos_iniciales.shape[0]
        - ajustes.shape[0]
        - prestamos_realizados.shape[0]
        - prestamos_recibidos.shape[0]
        - traslados.shape[0]
        - consumos.shape[0]
    )
    print(f"  - Registros pendientes por clasificar: {pendientes:,}")

    # Pivot y cálculo de netos
    idx_cols = ["Fecha", "Bodega", "CodigoGenerico", "GrupoInventario", "Generico", "Tercero", 'Comprobante_corregido']

    neto_compras = compras_aprovechamientos.pivot(
        on="Comprobante", index=idx_cols, values=['Cantidad', 'ValorTotal'], aggregate_function="sum"
    ).fill_null(0)

    neto_mov_iniciales = movimientos_iniciales.pivot(
        on="Comprobante", index=idx_cols, values=['Cantidad', 'ValorTotal'], aggregate_function="sum"
    ).fill_null(0)

    neto_ajustes = ajustes.pivot(
        on="Comprobante", index=idx_cols, values=['Cantidad', 'ValorTotal'], aggregate_function="sum"
    ).fill_null(0)

    neto_prestamos_realizados = prestamos_realizados.pivot(
        on="Comprobante", index=idx_cols, values=['Cantidad', 'ValorTotal'], aggregate_function="sum"
    ).fill_null(0)

    neto_prestamos_recibidos = prestamos_recibidos.pivot(
        on="Comprobante", index=idx_cols, values=['Cantidad', 'ValorTotal'], aggregate_function="sum"
    ).fill_null(0)

    neto_traslados = traslados.pivot(
        on="Comprobante_corregido", index=idx_cols, values=['Cantidad', 'ValorTotal'], aggregate_function="sum"
    ).fill_null(0)

    neto_consumos = consumos.pivot(
        on="Comprobante", index=idx_cols, values=['Cantidad', 'ValorTotal'], aggregate_function="sum"
    ).fill_null(0)

    print(f"  ✓ Neto compras: {neto_compras.height:,} registros agrupados")
    print(f"  ✓ Neto movimientos iniciales: {neto_mov_iniciales.height:,} registros agrupados")
    print(f"  ✓ Neto ajustes: {neto_ajustes.height:,} registros agrupados")
    print(f"  ✓ Neto préstamos realizados: {neto_prestamos_realizados.height:,} registros agrupados")
    print(f"  ✓ Neto préstamos recibidos: {neto_prestamos_recibidos.height:,} registros agrupados")
    print(f"  ✓ Neto traslados: {neto_traslados.height:,} registros agrupados")
    print(f"  ✓ Neto consumos: {neto_consumos.height:,} registros agrupados")

    return {
        "compras_aprovechamientos": compras_aprovechamientos,
        "neto_compras": neto_compras,
        "neto_mov_iniciales": neto_mov_iniciales,
        "neto_ajustes": neto_ajustes,
        "neto_prestamos_realizados": neto_prestamos_realizados,
        "neto_prestamos_recibidos": neto_prestamos_recibidos,
        "neto_traslados": neto_traslados,
        "neto_consumos": neto_consumos
    }


if __name__ == "__main__":
    res = procesamiento()
    print("\n✓ Resumen Paso 2:")
    for k, df in res.items():
        print(f"  - {k}: {df.shape}")