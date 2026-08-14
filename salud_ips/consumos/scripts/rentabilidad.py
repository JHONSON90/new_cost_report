
import polars as pl
from pathlib import Path


def realizar_rentabilidad(entradas_facturacion, facturacion):
    #TODO QUITAR LAS DEVOLUCIONES OSEA LAS ENTRADAS PARA PODER TENER BIEN EL INFORME
    try:
        entradas_facturacion = entradas_facturacion.with_columns(
            pl.concat_str(['field_1', 'CodigoGenerico'], separator="-").alias("ADM-CodGen")
        )

        limpieza_consumos_facturacion = facturacion.join(entradas_facturacion, on='ADM-CodGen', how='full').fill_null(0)

    except Exception as e:
        print(f"Error en realizar_rentabilidad: {e}")
        raise

    return limpieza_consumos_facturacion
