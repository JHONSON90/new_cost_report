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
    # pyrefly: ignore [missing-import]
    from procesamiento import procesamiento


def analisis_prestamos(prestamos_realizados: pl.DataFrame, prestamos_recibidos: pl.DataFrame):

    """
    Analiza los prestamos tanto realizados como recibidos, calculando el valor unitario de cada compra,
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
    print("PASO 4: ANÁLISIS DE PRESTAMOS REALIZADOS Y RECIBIDOS")
    print("=" * 60)

    # Si no se suministran datos procesados, se invoca el paso previo
    if datos_procesados is None:
        print("ℹ No se recibieron datos procesados; ejecutando procesamiento()...")
        datos_procesados = procesamiento()

    prestamos_realizados = datos_procesados.get("neto_prestamos_realizados")
    prestamos_recibidos = datos_procesados.get("neto_prestamos_recibidos")
    if prestamos_realizados is None or prestamos_realizados.is_empty() or prestamos_recibidos is None or prestamos_recibidos.is_empty():
        print("⚠ Advertencia: No hay registros de prestamos realizados y recibidos para analizar.")
        return {}

    print("Comenzando el análisis de prestamos...")

    columnas_base = ['Bodega', 'CodigoGenerico', 'GrupoInventario', 'Generico', "Tercero"]

    prestamos_realizados = prestamos_realizados.with_columns(
        (pl.col('Cantidad_SPOE - SALIDAS POR PRESTAMOS A OTRAS ENTIDADES') - pl.col('Cantidad_EPS - ENTRADAS PRESTAMOS SIIGO') - pl.col('Cantidad_EDP - ENTRADAS POR DEVOLUCION A PRESTAMOS')).alias('SaldoPrestamos_realizados'),
        (pl.col('ValorTotal_SPOE - SALIDAS POR PRESTAMOS A OTRAS ENTIDADES') - pl.col('ValorTotal_EPS - ENTRADAS PRESTAMOS SIIGO') - pl.col('ValorTotal_EDP - ENTRADAS POR DEVOLUCION A PRESTAMOS')).alias('Saldo_Prestamos_Realizados')
    )

    prestamos_realizados = prestamos_realizados.group_by(columnas_base).agg(
        pl.col('SaldoPrestamos_realizados').sum().alias('SaldoPrestamos_realizados'),
        pl.col('Saldo_Prestamos_Realizados').sum().alias('Saldo_Prestamos_Realizados')
    )

    prestamos_recibidos = prestamos_recibidos.with_columns(
        (pl.col('Cantidad_EPOE - ENTRADAS POR PRESTAMOS DE OTRAS ENTIDADES') - pl.col('Cantidad_SDP - SALIDAS POR DEVOLUCION DE PRESTAMOS') - pl.col('Cantidad_SPS - SALIDAS PRESTAMOS SIIGO')).alias('SaldoPrestamos_recibidos'),
        (pl.col('ValorTotal_EPOE - ENTRADAS POR PRESTAMOS DE OTRAS ENTIDADES') - pl.col('ValorTotal_SDP - SALIDAS POR DEVOLUCION DE PRESTAMOS') - pl.col('ValorTotal_SPS - SALIDAS PRESTAMOS SIIGO')).alias('Saldo_Prestamos_Recibidos')
    )

    prestamos_recibidos = prestamos_recibidos.group_by(columnas_base).agg(
        pl.col('SaldoPrestamos_recibidos').sum().alias('SaldoPrestamos_recibidos'),
        pl.col('Saldo_Prestamos_Recibidos').sum().alias('Saldo_Prestamos_Recibidos')
    )

    return {
        "prestamos_realizados": prestamos_realizados,
        "prestamos_recibidos": prestamos_recibidos
    }



# =====================================================================
# BLOQUE DE PRUEBAS LOCALES (DESARROLLO)
# =====================================================================
# Este bloque SOLO se ejecuta cuando corres este archivo directamente:
#     python salud_ips/compras/scripts/compras.py
# Permite probar toda la cadena (lectura -> procesamiento -> compras)
# desde aquí sin tener que ir a ejecutar el pipeline completo.
#
# Cuando termines tus pruebas y todo esté validado:
# Puedes BORRAR o comentar todo este bloque (desde la línea del `if`
# hasta el final) fácilmente, dejando el código completamente limpio
# para que la ejecución se haga únicamente desde pipeline_compras.py.
# =====================================================================
if __name__ == "__main__":
    print("\n" + "▶" * 30 + " MODO DE PRUEBAS LOCALES (COMPRAS.PY) " + "◀" * 30)

    # 1. Ejecutar análisis completo (se invocan automáticamente Paso 1 y Paso 2)
    resultados = analisis_prestamos()

    # 2. Inspeccionar los resultados de cada entregable
    print("\n" + "=" * 60)
    print("RESUMEN DE ENTREGABLES OBTENIDOS")
    print("=" * 60)
    for nombre, df in resultados.items():
        print(f"\n★ Entregable: [{nombre}]")
        print(f"  Dimensiones: {df.shape[0]:,} filas x {df.shape[1]} columnas")
    print("\n" + "▶" * 30 + " PRUEBA LOCAL FINALIZADA EXITOSAMENTE " + "◀" * 30)