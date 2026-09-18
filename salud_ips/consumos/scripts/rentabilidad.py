
import polars as pl
from pathlib import Path


def realizar_rentabilidad(entradas_facturacion, facturacion):
    # print(f'Columnas entradas_facturacion: {entradas_facturacion.columns}')
    # print(f'Columnas facturacion: {facturacion.columns}')

#Columnas entradas_facturacion: ['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'tipo insumo', 'Unidad', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Clasificacion_consumo', 'Municipio', 'Servicio', 'Tipo_servicio', 'Nombre', 'CodGrupo', 'Grupo', 'CodigoGenerico', 'EstadoArticulo', 'Cantidad', 'ValorUnitario', 'TotalBruto', 'ValorIVA', 'ValorDescuento', 'ValorTotal', 'ADM-CodGen', 'Especialidad', 'MedicoRealiza', 'Servicio_Corregido', 'idadmision', 'nofactura', 'idusuario', 'nomtiposervicio', 'codigo', 'nombre', 'cantidad', 'CantidadSolicitada', 'vrunitario', 'vrtotal', 'Especialidad_right', 'MedicoRealiza_right', 'MedicoOrdena', '# Identificacion']

#Columnas facturacion: ['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'admision', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'tipo de insumo', 'CodGrupo', 'Grupo', 'CodArticulo', 'Articulo', 'Cantidad', 'ValorUnitario', 'TotalBruto', 'ValorIVA', 'ValorDescuento', 'ValorTotal', 'Unidad', 'LaboratorioMarca', 'Observacion', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Clasificacion_consumo', 'Municipio', 'Servicio', 'Tipo_servicio', 'Nombre', 'CodigoGenerico', 'EstadoArticulo', 'ADM-CodGen', 'idadmision', 'nofactura', 'idusuario', 'nomtiposervicio', 'codigo', 'nombre', 'cantidad', 'CantidadSolicitada', 'vrunitario', 'vrtotal', 'Especialidad', 'MedicoRealiza', 'MedicoOrdena', '# Identificacion', 'Servicio_Corregido']
    entradas_facturacion = entradas_facturacion.select(['field_1', 'CodigoGenerico', 'Cantidad', 'ValorUnitario', 'TotalBruto', 'ValorIVA', 'ValorDescuento', 'ValorTotal'])

    #TODO QUITAR LAS DEVOLUCIONES OSEA LAS ENTRADAS PARA PODER TENER BIEN EL INFORME
    try:
        entradas_facturacion = entradas_facturacion.with_columns(
            pl.concat_str(['field_1', 'CodigoGenerico'], separator="-").alias("ADM-CodGen")
        )

        limpieza_consumos_facturacion = facturacion.join(entradas_facturacion, on='ADM-CodGen', how='full').fill_null(0)

        limpieza_consumos_facturacion = limpieza_consumos_facturacion.with_columns(
            (pl.col('Cantidad') - pl.col('Cantidad_right')).alias('Cantidad_Neta'),
            (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('Total_Neto')
        )

        limpieza_consumos_facturacion = limpieza_consumos_facturacion.with_columns(
            (pl.col('cantidad') - pl.col('Cantidad_Neta')).alias('Diferencia_Cantidad'),
            (pl.col('vrtotal') - pl.col('Total_Neto')).alias('Diferencia_Total')
        )

        rentabilidad = limpieza_consumos_facturacion.group_by(['field_1', 'idadmision','nofactura', 'CodigoGenerico', 'Nombre']).agg(
            pl.col('Cantidad_Neta').sum().alias('Cantidad_Consumida'),
            pl.col('Total_Neto').sum().alias('Total_Consumido'),
            pl.col('cantidad').sum().alias('Cantidad_Facturada'),
            pl.col('vrtotal').sum().alias('Total_Facturado'),
            pl.col('Diferencia_Cantidad').sum().alias('Diferencia_Cantidad_Total'),
            pl.col('Diferencia_Total').sum().alias('Diferencia_Total_Total')
        )

    except Exception as e:
        print(f"Error en realizar_rentabilidad: {e}")
        raise

    return rentabilidad
