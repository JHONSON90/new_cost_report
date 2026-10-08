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
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ruta base configurable mediante variable de entorno con fallback a la ruta de red de Movimientos
DEFAULT_RUTA_MOVIMIENTOS = Path(
    os.getenv(
        "RUTA_MOVIMIENTOS_INVENTARIO",
        r"\\192.168.3.70\Costos\COSTOS 2026\INVENTARIOS\Movimientos"
    )
)
# Alias para mantener compatibilidad con código existente que referencie DEFAULT_RUTA_CONSUMOS
DEFAULT_RUTA_CONSUMOS = DEFAULT_RUTA_MOVIMIENTOS


def lectura_archivos_completa(
    ruta_base: str | Path | None = None,
    engine: str = "calamine"
) -> dict[str, pl.DataFrame]:
    """
    Lee y consolida todos los archivos de movimientos de inventario detallados por lote
    desde la carpeta especificada (por defecto ruta de red).

    Args:
        ruta_base: Directorio base de búsqueda. Si es None, utiliza la variable de entorno
                   'RUTA_MOVIMIENTOS_INVENTARIO' o DEFAULT_RUTA_MOVIMIENTOS.
        engine: Motor de lectura de Excel en Polars ('calamine', 'openpyxl', etc.).
                Por defecto 'calamine' (respaldado por fastexcel) por su alto rendimiento.

    Returns:
        dict con DataFrames de Polars:
            {
                'entradas': pl.DataFrame,    # Movimientos con TipoMovimiento == 'ENTRADA'
                'salidas': pl.DataFrame,     # Movimientos con TipoMovimiento == 'SALIDA'
                'movimientos': pl.DataFrame  # Consolidado general completo
            }
    """
    try:
        ruta = Path(ruta_base) if ruta_base is not None else DEFAULT_RUTA_MOVIMIENTOS
        if not ruta.exists():
            print(f"⚠ Advertencia: La ruta especificada no existe o no es accesible: {ruta}")
            return {
                'entradas': pl.DataFrame(),
                'salidas': pl.DataFrame(),
                'movimientos': pl.DataFrame()
            }

        # Búsqueda de archivos Excel en la carpeta (omitiendo archivos temporales de Excel ~$)
        patrones = ["*.xlsx", "*.xlsb", "*.xls"]
        archivos_encontrados: list[Path] = []
        for patron in patrones:
            archivos_encontrados.extend([f for f in ruta.glob(patron) if not f.name.startswith("~$")])

        archivos = sorted(set(archivos_encontrados))

        if not archivos:
            print(f"⚠ Advertencia: No se encontraron archivos de Excel en: {ruta}")
            return {
                'entradas': pl.DataFrame(),
                'salidas': pl.DataFrame(),
                'movimientos': pl.DataFrame()
            }

        print(f"📁 Se encontraron {len(archivos)} archivos en: {ruta}")

        # Configuración común para lectura de reportes Excel
        read_kwargs = {
            "sheet_name": "Reporte",
            "read_options": {"header_row": 6},
            "engine": engine or "calamine",
            "schema_overrides": {
                'Cantidad': pl.Int64,
                'Costo': pl.Float64,
                'ValorBruto': pl.Float64,
                'ValorTotal': pl.Float64,
                'ValorIva': pl.Float64,
                'ValorDescuento': pl.Float64,
            }
        }

        dataframes: list[pl.DataFrame] = []

        for archivo in archivos:
            try:
                df = pl.read_excel(archivo, **read_kwargs)
                # Trazabilidad del archivo origen
                df = df.with_columns(pl.lit(archivo.name).alias("ArchivoOrigen"))
                dataframes.append(df)
                print(f"  ✓ Leído: {archivo.name} ({len(df):,} filas)")
            except Exception as e:
                print(f"  ✗ Error leyendo '{archivo.name}': {e}")

        if not dataframes:
            print("⚠ Advertencia: Ningún archivo pudo ser cargado exitosamente.")
            return {
                'entradas': pl.DataFrame(),
                'salidas': pl.DataFrame(),
                'movimientos': pl.DataFrame()
            }

        # Consolidación diagonal para tolerar discrepancias menores en columnas entre archivos
        consolidado_general = pl.concat(dataframes, how="diagonal_relaxed")
        print(f"✓ Total general consolidado: {consolidado_general.shape[0]:,} filas y {consolidado_general.shape[1]} columnas")
        return consolidado_general

    #     # Segregación en entradas y salidas según TipoMovimiento
    #     if "TipoMovimiento" in consolidado_general.columns:
    #         consolidado_entradas = consolidado_general.filter(
    #             pl.col("TipoMovimiento").str.to_uppercase() == "ENTRADA"
    #         )
    #         consolidado_salidas = consolidado_general.filter(
    #             pl.col("TipoMovimiento").str.to_uppercase() == "SALIDA"
    #         )
    #         print(f"  - Entradas: {len(consolidado_entradas):,} registros")
    #         print(f"  - Salidas:  {len(consolidado_salidas):,} registros")
    #     else:
    #         print("⚠ Columna 'TipoMovimiento' no encontrada; asignando consolidado general a entradas")
    #         consolidado_entradas = consolidado_general
    #         consolidado_salidas = pl.DataFrame()

    #     return {
    #         'entradas': consolidado_entradas,
    #         'salidas': consolidado_salidas,
    #         'movimientos': consolidado_general
    #     }

    except Exception as error:
        print(f"Error durante la lectura de archivos: {error}")
        raise


if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    resultado = lectura_archivos_completa()
    print("\nResumen obtenido:")
    print("Resultado shape:", resultado.shape)
