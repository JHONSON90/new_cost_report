
import polars as pl
from pathlib import Path


def realizar_rentabilidad(limpieza_consumos_facturacion):
    #TODO QUITAR LAS DEVOLUCIONES OSEA LAS ENTRADAS PARA PODER TENER BIEN EL INFORME
    try:
        rentabilidad = limpieza_consumos_facturacion.group_by(['field_1', 'idadmision', 'nofactura','Nombre', 'CodigoGenerico']).agg(
            pl.col('ValorTotal').sum().cast(pl.Int64).alias("Consumo"),
            pl.col('vrtotal').sum().cast(pl.Int64).alias("Facturacion"),
            pl.col('Cantidad').sum().cast(pl.Int64).alias("Cantidad Consumo"),
            pl.col('cantidad').sum().cast(pl.Int64).alias("Cantidad Facturada"),
            (pl.col('vrtotal') - pl.col('ValorTotal')).sum().cast(pl.Int64).alias("Diferencia"),
            (pl.col('Cantidad') - pl.col('cantidad')).sum().cast(pl.Int64).alias("Diferencia Cantidad")
        )
    
    except Exception as e:
        print(f"Error en realizar_rentabilidad: {e}")
        raise

    return rentabilidad


