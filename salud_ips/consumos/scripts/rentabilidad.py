
import polars as pl
from pathlib import Path


def realizar_rentabilidad(limpieza_consumos_facturacion):
    try:
        rentabilidad = limpieza_consumos_facturacion.group_by(['field_1', 'idadmision', 'nofactura','Nombre', 'CodigoGenerico']).agg(
            pl.col('ValorTotal').sum().cast(pl.Int64).alias("Consumo"),
            pl.col('vrtotal').sum().cast(pl.Int64).alias("Facturacion"),
            pl.col('Cantidad').sum().cast(pl.Int64).alias("Cantidad Consumo"),
            pl.col('cantidad').sum().cast(pl.Int64).alias("Cantidad Facturada"),
            (pl.col('vrtotal') - pl.col('ValorTotal')).sum().cast(pl.Int64).alias("Diferencia"),
            (pl.col('Cantidad') - pl.col('cantidad')).sum().cast(pl.Int64).alias("Diferencia Cantidad")
        )

        print(limpieza_consumos_facturacion.filter(
            pl.col('field_1') == 3105
        ).select('field_1', 'Nombre', 'CodigoGenerico','codigo', 'nombre', 'cantidad', 'Cantidad'))
            
    
    except Exception as e:
        print(f"Error en realizar_rentabilidad: {e}")
        raise

    return rentabilidad


