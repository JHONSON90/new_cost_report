
import polars as pl
from pathlib import Path


<<<<<<< Updated upstream
def realizar_rentabilidad(limpieza_consumos_facturacion):
<<<<<<< HEAD
=======
def realizar_rentabilidad(entradas_facturacion, facturacion):
    #TODO QUITAR LAS DEVOLUCIONES OSEA LAS ENTRADAS PARA PODER TENER BIEN EL INFORME
>>>>>>> Stashed changes
=======
    #TODO QUITAR LAS DEVOLUCIONES OSEA LAS ENTRADAS PARA PODER TENER BIEN EL INFORME
>>>>>>> 4cd4d7f832ac007ad47594e455c8332115d8f964
    try:
        entradas_facturacion = entradas_facturacion.with_columns(
            pl.concat_str(['field_1', 'CodigoGenerico'], separator="-").alias("ADM-CodGen")
        )
<<<<<<< HEAD

<<<<<<< Updated upstream
        print(limpieza_consumos_facturacion.filter(
            pl.col('field_1') == 3105
        ).select('field_1', 'Nombre', 'CodigoGenerico','codigo', 'nombre', 'cantidad', 'Cantidad'))
            
=======

        limpieza_consumos_facturacion = facturacion.join(entradas_facturacion, on='ADM-CodGen', how='full').fill_null(0)
        print(f"columnas facturacion: \n {facturacion.columns}")
        print(f"columnas entradas: \n {entradas_facturacion.columns}")
        print(f"Columnas unidas: \n {limpieza_consumos_facturacion.columns}")
        #['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'tipo de insumo', 'Unidad', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Clasificacion_consumo', 'Municipio', 'Servicio', 'Tipo_servicio', 'Nombre', 'CodGrupo', 'Grupo', 'CodigoGenerico', 'EstadoArticulo', 'Cantidad', 'ValorUnitario', 'TotalBruto', 'ValorIVA', 'ValorDescuento', 'ValorTotal', 'ADM-CodGen', 'idadmision', 'nofactura', 'idusuario', 'nomtiposervicio', 'codigo', 'nombre', 'Especialidad', 'MedicoRealiza', 'cantidad', 'CantidadSolicitada', 'vrunitario', 'vrtotal', '# Identificacion', 'Servicio_Corregido', 'Comprobante_right', 'Numero_right', 'Fecha_right', 'NoDocumento_right', 'Proveedor_right', 'CentroCosto_right', 'Dependencia_right', 'Bodega_right', 'tipo insumo', 'Unidad_right', 'Usuario_right', 'User_right', 'FechaDigitacion_right', 'field_1_right', 'Clasificacion_consumo_right', 'Municipio_right', 'Servicio_right', 'Tipo_servicio_right', 'Nombre_right', 'CodGrupo_right', 'Grupo_right', 'CodigoGenerico_right', 'EstadoArticulo_right', 'Cantidad_right', 'ValorUnitario_right', 'TotalBruto_right', 'ValorIVA_right', 'ValorDescuento_right', 'ValorTotal_right', 'Especialidad_right', 'MedicoRealiza_right', 'Servicio_Corregido_right']

        # limpieza_consumos_facturacion = limpieza_consumos_facturacion.with_columns(
        #     (pl.col('Cantidad') - pl.col('Cantidad_right')).alias('Cantidad_neta'),
        #     (pl.col('ValorTotal') - pl.col('ValorTotal_right')).alias('ValorTotal_neta')
        # )

        # rentabilidad = limpieza_consumos_facturacion.group_by(['field_1', 'idadmision', 'nofactura','Nombre', 'CodigoGenerico']).agg(
        #     pl.col('ValorTotal_neta').sum().cast(pl.Int64).alias("Consumo"),
        #     pl.col('vrtotal').sum().cast(pl.Int64).alias("Facturacion"),
        #     pl.col('Cantidad_neta').sum().cast(pl.Int64).alias("Cantidad Consumo"),
        #     pl.col('cantidad').sum().cast(pl.Int64).alias("Cantidad Facturada"),
        #     (pl.col('vrtotal') - pl.col('ValorTotal_neta')).sum().cast(pl.Int64).alias("Diferencia"),
        #     (pl.col('Cantidad_neta') - pl.col('cantidad')).sum().cast(pl.Int64).alias("Diferencia Cantidad")
        # )
>>>>>>> Stashed changes
=======
>>>>>>> 4cd4d7f832ac007ad47594e455c8332115d8f964
    
    except Exception as e:
        print(f"Error en realizar_rentabilidad: {e}")
        raise

    return limpieza_consumos_facturacion


