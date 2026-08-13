"""
Módulo de Análisis Financiero - Paso 8 del Pipeline SaludIPS.

Genera 3 métricas clave para toma de decisiones:
1. Varianza de Costo Unitario por Proveedor
2. Eficiencia de Stock por Servicio
3. Gap Facturación vs Consumo Real
"""
import polars as pl
from pathlib import Path
import pandas as pd


def calcular_varianza_proveedor(consumos: pl.DataFrame) -> pl.DataFrame:
    """
    Detecta proveedores con precios anómalos vs mediana del mercado.
    
    Args:
        consumos: DataFrame con columnas CodigoGenerico, Nombre, Proveedor, 
                  ValorUnitario, Cantidad, ValorTotal, Municipio, Servicio
    
    Returns:
        DataFrame con métricas de variabilidad por proveedor/producto
    """
    # Filtrar solo registros con proveedor y precio válido
    df = consumos.filter(
        pl.col("Proveedor").is_not_null() & 
        (pl.col("Proveedor") != "") &
        pl.col("ValorUnitario").is_not_null() &
        (pl.col("ValorUnitario") > 0)
    )
    
    if df.is_empty():
        return _empty_varianza_schema()
    
    # Agrupar por producto y proveedor
    varianza = df.group_by(["CodigoGenerico", "Nombre", "Proveedor", "Municipio", "Servicio"]).agg(
        pl.col("ValorUnitario").median().alias("Costo_Mediano"),
        pl.col("ValorUnitario").mean().alias("Costo_Promedio"),
        pl.col("ValorUnitario").std().alias("Desv_Estandar"),
        pl.col("ValorUnitario").min().alias("Costo_Minimo"),
        pl.col("ValorUnitario").max().alias("Costo_Maximo"),
        pl.col("Cantidad").sum().alias("Volumen_Total"),
        pl.col("ValorTotal").sum().alias("Valor_Total_Comprado"),
        pl.col("Comprobante").n_unique().alias("Num_Transacciones")
    )
    
    # Calcular métricas derivadas
    varianza = varianza.with_columns(
        # Coeficiente de variación (CV) - medida relativa de dispersión
        (pl.col("Desv_Estandar") / pl.col("Costo_Mediano")).alias("CV_Costo"),
        
        # Rango porcentual
        ((pl.col("Costo_Maximo") - pl.col("Costo_Minimo")) / pl.col("Costo_Mediano")).alias("Rango_Porcentual"),
        
        # Diferencia absoluta max-min
        (pl.col("Costo_Maximo") - pl.col("Costo_Minimo")).alias("Diferencia_Absoluta"),
        
        # Precio vs mediana del mercado (todos los proveedores)
        pl.col("Costo_Promedio").alias("Precio_Promedio_Proveedor")
    )
    
    # Calcular mediana de mercado por producto (todos los proveedores)
    mediana_mercado = varianza.group_by(["CodigoGenerico", "Nombre"]).agg(
        pl.col("Costo_Mediano").median().alias("Mediana_Mercado")
    )
    
    varianza = varianza.join(mediana_mercado, on=["CodigoGenerico", "Nombre"], how="left")
    
    # Desviación vs mercado
    varianza = varianza.with_columns(
        ((pl.col("Costo_Promedio") - pl.col("Mediana_Mercado")) / pl.col("Mediana_Mercado")).alias("Desviacion_Vs_Mercado_Pct"),
        (pl.col("Costo_Promedio") - pl.col("Mediana_Mercado")).alias("Desviacion_Vs_Mercado_Abs")
    )
    
    # Clasificación de riesgo
    varianza = varianza.with_columns(
        pl.when(pl.col("CV_Costo") > 0.3).then(pl.lit("ALTO_RIESGO"))
         .when(pl.col("CV_Costo") > 0.15).then(pl.lit("MEDIO_RIESGO"))
         .otherwise(pl.lit("NORMAL")).alias("Nivel_Riesgo_Variabilidad"),
        
        pl.when(pl.col("Desviacion_Vs_Mercado_Pct").abs() > 0.25).then(pl.lit("PRECIO_ANOMALO"))
         .when(pl.col("Desviacion_Vs_Mercado_Pct").abs() > 0.10).then(pl.lit("PRECIO_ALERTA"))
         .otherwise(pl.lit("PRECIO_NORMAL")).alias("Alerta_Precio_Mercado"),
        
        pl.when(pl.col("Volumen_Total") < 10).then(pl.lit("BAJO_VOLUMEN"))
         .when(pl.col("Volumen_Total") < 100).then(pl.lit("VOLUMEN_MEDIO"))
         .otherwise(pl.lit("ALTO_VOLUMEN")).alias("Clasificacion_Volumen")
    )
    
    # Ordenar por mayor riesgo y volumen
    return varianza.sort(["Nivel_Riesgo_Variabilidad", "Volumen_Total"], descending=[True, True])


def calcular_eficiencia_stock(consumos: pl.DataFrame, entradas: pl.DataFrame) -> pl.DataFrame:
    """
    Calcula ratio de eficiencia: Consumo Neto / Entradas (Compras).
    Identifica servicios con sobre-stock o desabastecimiento.
    
    Args:
        consumos: DataFrame salidas (consumo real)
        entradas: DataFrame entradas (compras/recepciones)
    
    Returns:
        DataFrame con eficiencia por Municipio/Servicio/Clasificación
    """
    # Preparar consumos: agrupar por clave de análisis
    keys = ["Municipio", "Servicio", "Clasificacion_consumo", "CodigoGenerico", "Nombre"]
    
    cons_agg = consumos.group_by(keys).agg(
        pl.col("ValorTotal").sum().alias("Consumo_Valor"),
        pl.col("Cantidad").sum().alias("Consumo_Cantidad"),
        pl.col("ValorUnitario").mean().alias("Costo_Promedio_Consumo")
    )
    
    # Preparar entradas: misma granularidad
    ent_agg = entradas.group_by(keys).agg(
        pl.col("ValorTotal").sum().alias("Entradas_Valor"),
        pl.col("Cantidad").sum().alias("Entradas_Cantidad"),
        pl.col("ValorUnitario").mean().alias("Costo_Promedio_Entrada")
    )
    
    # Full join para capturar productos solo en consumos o solo en entradas
    eficiencia = cons_agg.join(ent_agg, on=keys, how="full").fill_null(0)
    
    # Métricas de eficiencia
    eficiencia = eficiencia.with_columns(
        # Consumo neto = lo que realmente se usó
        (pl.col("Consumo_Valor")).alias("Consumo_Neto_Valor"),
        (pl.col("Consumo_Cantidad")).alias("Consumo_Neto_Cantidad"),
        
        # Compras totales
        (pl.col("Entradas_Valor")).alias("Compras_Totales_Valor"),
        (pl.col("Entradas_Cantidad")).alias("Compras_Totales_Cantidad"),
        
        # Ratios de eficiencia (evitar división por cero)
        pl.when(pl.col("Entradas_Valor") > 0)
         .then(pl.col("Consumo_Valor") / pl.col("Entradas_Valor"))
         .otherwise(pl.lit(None)).alias("Ratio_Eficiencia_Valor"),
        
        pl.when(pl.col("Entradas_Cantidad") > 0)
         .then(pl.col("Consumo_Cantidad") / pl.col("Entradas_Cantidad"))
         .otherwise(pl.lit(None)).alias("Ratio_Eficiencia_Cantidad"),
        
        # Diferencia absoluta (negativo = compraron más de lo que consumen)
        (pl.col("Consumo_Valor") - pl.col("Entradas_Valor")).alias("Diferencia_Valor"),
        (pl.col("Consumo_Cantidad") - pl.col("Entradas_Cantidad")).alias("Diferencia_Cantidad"),
        
        # Diferencia en costo unitario
        (pl.col("Costo_Promedio_Consumo") - pl.col("Costo_Promedio_Entrada")).alias("Diff_Costo_Unitario")
    )
    
    # Clasificación de estado de inventario
    eficiencia = eficiencia.with_columns(
        pl.when(pl.col("Consumo_Neto_Valor") > pl.col("Compras_Totales_Valor"))
         .then(pl.lit("DESABASTECIMIENTO"))
         .when(pl.col("Ratio_Eficiencia_Valor").is_null())
         .then(pl.lit("SIN_COMPRAS"))
         .when(pl.col("Ratio_Eficiencia_Valor") < 0.5)
         .then(pl.lit("SOBRE_STOCK_CRITICO"))
         .when(pl.col("Ratio_Eficiencia_Valor") < 0.7)
         .then(pl.lit("SOBRE_STOCK"))
         .when(pl.col("Ratio_Eficiencia_Valor") < 0.9)
         .then(pl.lit("STOCK_ELEVADO"))
         .when(pl.col("Ratio_Eficiencia_Valor") <= 1.1)
         .then(pl.lit("OPTIMO"))
         .otherwise(pl.lit("DESABASTECIMIENTO_LEVE"))
         .alias("Estado_Inventario"),
        
        # Alerta financiera: valor de stock muerto (comprado pero no consumido)
        pl.when(pl.col("Diferencia_Valor") < 0)
         .then(pl.col("Diferencia_Valor").abs())
         .otherwise(pl.lit(0))
         .alias("Valor_Stock_Muerto"),
        
        # Alerta: compras a precio mayor que consumo (posible error)
        pl.when(pl.col("Diff_Costo_Unitario") < -0.05)
         .then(pl.lit("COMPRA_CARA"))
         .when(pl.col("Diff_Costo_Unitario") > 0.05)
         .then(pl.lit("CONSUMO_CARO"))
         .otherwise(pl.lit("NORMAL"))
         .alias("Alerta_Costo_Unitario")
    )
    
    # Resumen por Municipio/Servicio/Clasificación (sin detalle de producto)
    resumen = eficiencia.group_by(["Municipio", "Servicio", "Clasificacion_consumo"]).agg(
        pl.col("Consumo_Neto_Valor").sum().alias("Total_Consumo_Valor"),
        pl.col("Compras_Totales_Valor").sum().alias("Total_Compras_Valor"),
        pl.col("Consumo_Neto_Cantidad").sum().alias("Total_Consumo_Cantidad"),
        pl.col("Compras_Totales_Cantidad").sum().alias("Total_Compras_Cantidad"),
        pl.col("Valor_Stock_Muerto").sum().alias("Total_Stock_Muerto_Valor"),
        pl.col("Diferencia_Valor").sum().alias("Diferencia_Neta_Valor"),
        pl.col("Diferencia_Cantidad").sum().alias("Diferencia_Neta_Cantidad"),
        pl.col("Estado_Inventario").mode().first().alias("Estado_Predominante"),
        pl.col("Alerta_Costo_Unitario").filter(pl.col("Alerta_Costo_Unitario") != "NORMAL").count().alias("Productos_Con_Alerta_Costo"),
        pl.col("CodigoGenerico").n_unique().alias("Num_Productos_Unicos")
    ).with_columns(
        pl.when(pl.col("Total_Compras_Valor") > 0)
         .then(pl.col("Total_Consumo_Valor") / pl.col("Total_Compras_Valor"))
         .otherwise(pl.lit(None)).alias("Ratio_Eficiencia_Global"),
        
        (pl.col("Total_Stock_Muerto_Valor") / pl.col("Total_Compras_Valor") * 100)
         .alias("Pct_Stock_Muerto_Sobre_Compras")
    )
    
    # Retornar ambos niveles: detalle y resumen
    return {
        "detalle_producto": eficiencia.sort(["Estado_Inventario", "Valor_Stock_Muerto"], descending=[True, True]),
        "resumen_servicio": resumen.sort("Total_Stock_Muerto_Valor", descending=True)
    }


def calcular_gap_facturacion_consumo(facturacion: pl.DataFrame, consumos: pl.DataFrame) -> pl.DataFrame:
    """
    Calcula brecha entre lo facturado (ingreso) y lo consumido (costo real) por paciente/servicio.
    Identifica sub-facturación, sobre-facturación y facturas sin cerrar.
    
    Args:
        facturacion: DataFrame con facturación (idadmision, CodigoGenerico, vrtotal, etc.)
        consumos: DataFrame con consumos dispensados (idadmision/ADM-CodGen, ValorTotal, etc.)
    
    Returns:
        Dict con 3 DataFrames: gap por paciente, resumen por servicio, alertas críticas
    """
    # Preparar facturación: agrupar por admisión y producto
    fact_keys = ["idadmision", "CodigoGenerico", "Nombre"]
    fact_agg = facturacion.group_by(fact_keys).agg(
        pl.col("vrtotal").sum().alias("Facturado_Valor"),
        pl.col("cantidad").sum().alias("Facturado_Cantidad"),
        pl.col("vrunitario").mean().alias("Precio_Facturado_Prom"),
        pl.col("Especialidad").first().alias("Especialidad"),
        pl.col("Servicio_Corregido").first().alias("Servicio_Corregido"),
        pl.col("Municipio").first().alias("Municipio"),
        pl.col("MedicoRealiza").first().alias("MedicoRealiza"),
        pl.col("nofactura").first().alias("No_Factura")
    )
    
    # Preparar consumos: necesitan campo de admisión (field_1 o ADM-CodGen)
    # Buscar columna de admisión en consumos
    adm_col = None
    for col in ["field_1", "ADM-CodGen", "idadmision"]:
        if col in consumos.columns:
            adm_col = col
            break
    
    if adm_col is None:
        print("⚠ No se encontró columna de admisión en consumos. Gap no calculable.")
        return _empty_gap_schema()
    
    # Extraer idadmision del campo compuesto si es necesario
    cons_prep = consumos.clone()
    if adm_col == "ADM-CodGen":
        cons_prep = cons_prep.with_columns(
            pl.col("ADM-CodGen").str.split("-").list.get(0).cast(pl.Int64, strict=False).alias("idadmision")
        )
    elif adm_col == "field_1":
        cons_prep = cons_prep.with_columns(
            pl.col("field_1").cast(pl.Int64, strict=False).alias("idadmision")
        )
    
    cons_agg = cons_prep.filter(pl.col("idadmision").is_not_null()).group_by(
        ["idadmision", "CodigoGenerico", "Nombre"]
    ).agg(
        pl.col("ValorTotal").sum().alias("Consumido_Valor"),
        pl.col("Cantidad").sum().alias("Consumido_Cantidad"),
        pl.col("ValorUnitario").mean().alias("Costo_Unitario_Prom")
    )
    
    # Join facturación vs consumo
    gap = fact_agg.join(cons_agg, on=["idadmision", "CodigoGenerico", "Nombre"], how="full").fill_null(0)
    
    # Métricas de gap
    gap = gap.with_columns(
        (pl.col("Facturado_Valor") - pl.col("Consumido_Valor")).alias("Margen_Bruto"),
        (pl.col("Facturado_Cantidad") - pl.col("Consumido_Cantidad")).alias("Diferencia_Cantidad"),
        
        pl.when(pl.col("Consumido_Valor") > 0)
         .then(pl.col("Facturado_Valor") / pl.col("Consumido_Valor"))
         .otherwise(pl.lit(None)).alias("Ratio_Fact_Consumo"),
        
        pl.when(pl.col("Facturado_Valor") > 0)
         .then((pl.col("Facturado_Valor") - pl.col("Consumido_Valor")) / pl.col("Facturado_Valor") * 100)
         .otherwise(pl.lit(None)).alias("Margen_Porcentual"),
        
        # Precio facturado vs costo real
        (pl.col("Precio_Facturado_Prom") - pl.col("Costo_Unitario_Prom")).alias("Spread_Precio_Costo")
    )
    
    # Clasificación por paciente-producto
    gap = gap.with_columns(
        pl.when(pl.col("Facturado_Valor") == 0)
         .then(pl.lit("SIN_FACTURAR"))
         .when(pl.col("Consumido_Valor") == 0)
         .then(pl.lit("FACTURADO_SIN_CONSUMO"))
         .when(pl.col("Ratio_Fact_Consumo").is_null())
         .then(pl.lit("INDETERMINADO"))
         .when(pl.col("Ratio_Fact_Consumo") < 0.7)
         .then(pl.lit("SUB_FACTURACION_CRITICA"))
         .when(pl.col("Ratio_Fact_Consumo") < 0.9)
         .then(pl.lit("SUB_FACTURACION"))
         .when(pl.col("Ratio_Fact_Consumo") <= 1.1)
         .then(pl.lit("EQUILIBRADO"))
         .when(pl.col("Ratio_Fact_Consumo") <= 1.5)
         .then(pl.lit("SOBRE_FACTURACION"))
         .otherwise(pl.lit("SOBRE_FACTURACION_CRITICA"))
         .alias("Estado_Facturacion"),
        
        # Alerta de spread anómalo
        pl.when(pl.col("Spread_Precio_Costo").abs() > pl.col("Costo_Unitario_Prom") * 0.5)
         .then(pl.lit("SPREAD_ANOMALO"))
         .otherwise(pl.lit("NORMAL"))
         .alias("Alerta_Spread")
    )
    
    # Resumen por Municipio/Servicio/Especialidad
    resumen_servicio = gap.group_by(["Municipio", "Servicio_Corregido", "Especialidad"]).agg(
        pl.col("Facturado_Valor").sum().alias("Total_Facturado"),
        pl.col("Consumido_Valor").sum().alias("Total_Consumido"),
        pl.col("Margen_Bruto").sum().alias("Margen_Total"),
        pl.col("Ratio_Fact_Consumo").median().alias("Ratio_Mediano"),
        pl.col("Margen_Porcentual").median().alias("Margen_Mediano_Pct"),
        pl.col("idadmision").n_unique().alias("Pacientes_Atendidos"),
        pl.col("No_Factura").n_unique().alias("Facturas_Unicas"),
        pl.col("Estado_Facturacion").filter(pl.col("Estado_Facturacion").is_in([
            "SUB_FACTURACION_CRITICA", "SUB_FACTURACION", "SOBRE_FACTURACION", "SOBRE_FACTURACION_CRITICA"
        ])).count().alias("Registros_Con_Alerta"),
        pl.col("Estado_Facturacion").filter(pl.col("Estado_Facturacion") == "SIN_FACTURAR").count().alias("Productos_Sin_Facturar"),
        pl.col("Alerta_Spread").filter(pl.col("Alerta_Spread") == "SPREAD_ANOMALO").count().alias("Spreads_Anomalos")
    ).with_columns(
        pl.when(pl.col("Total_Consumido") > 0)
         .then(pl.col("Total_Facturado") / pl.col("Total_Consumido"))
         .otherwise(pl.lit(None)).alias("Ratio_Global")
    ).with_columns(
        pl.when(pl.col("Ratio_Global") < 0.8).then(pl.lit("SUB_FACTURACION_SERVICIO"))
         .when(pl.col("Ratio_Global") > 1.3).then(pl.lit("SOBRE_FACTURACION_SERVICIO"))
         .otherwise(pl.lit("EQUILIBRADO_SERVICIO")).alias("Alerta_Servicio")
    )
    
    # Alertas críticas: pacientes con alta sub-facturación
    alertas_paciente = gap.filter(
        pl.col("Estado_Facturacion").is_in(["SUB_FACTURACION_CRITICA", "SIN_FACTURAR"])
    ).group_by(["idadmision", "Municipio", "Servicio_Corregido", "Especialidad", "MedicoRealiza"]).agg(
        pl.col("Margen_Bruto").sum().alias("Margen_Perdido_Total"),
        pl.col("Facturado_Valor").sum().alias("Facturado_Paciente"),
        pl.col("Consumido_Valor").sum().alias("Consumido_Paciente"),
        pl.col("CodigoGenerico").n_unique().alias("Productos_Afectados"),
        pl.col("No_Factura").first().alias("Factura_Principal")
    ).sort("Margen_Perdido_Total")
    
    return {
        "detalle_paciente_producto": gap.sort(["Estado_Facturacion", "Margen_Bruto"]),
        "resumen_servicio": resumen_servicio.sort("Margen_Total"),
        "alertas_paciente": alertas_paciente
    }


def generar_informe_financiero(
    consumos: pl.DataFrame,
    entradas: pl.DataFrame,
    facturacion: pl.DataFrame,
    ruta_salida: Path
) -> dict:
    """
    Función principal que genera el informe financiero completo (3 hojas Excel).
    
    Args:
        consumos: DataFrame de consumos/salidas (limpieza_consumos_facturacion + salidas_consumo)
        entradas: DataFrame de entradas (entradas_facturacion + entradas_consumo)
        facturacion: DataFrame de facturación (consumos_de_facturacion con facturación join)
        ruta_salida: Path donde guardar el Excel
    
    Returns:
        Dict con los 3 DataFrames generados para uso posterior
    """
    print("\n" + "=" * 60)
    print("PASO 8: ANÁLISIS FINANCIERO")
    print("=" * 60)
    
    # 1. Varianza Proveedor
    print("  [1/4] Calculando varianza de costo por proveedor...")
    varianza_proveedor = calcular_varianza_proveedor(consumos)
    print(f"      -> {varianza_proveedor.height} combinaciones producto-proveedor analizadas")
    
    # 2. Eficiencia Stock
    print("  [2/4] Calculando eficiencia de stock...")
    eficiencia_result = calcular_eficiencia_stock(consumos, entradas)
    eficiencia_detalle = eficiencia_result["detalle_producto"]
    eficiencia_resumen = eficiencia_result["resumen_servicio"]
    print(f"      -> {eficiencia_detalle.height} productos, {eficiencia_resumen.height} servicios analizados")
    
    # 3. Gap Facturación vs Consumo
    print("  [3/4] Calculando gap facturación vs consumo...")
    gap_result = calcular_gap_facturacion_consumo(facturacion, consumos)
    gap_detalle = gap_result["detalle_paciente_producto"]
    gap_resumen = gap_result["resumen_servicio"]
    gap_alertas = gap_result["alertas_paciente"]
    print(f"      -> {gap_detalle.height} registros, {gap_alertas.height} alertas de paciente")
    
    # 4. Análisis Compras vs Ventas vs Consumo (REGISTRO DE COMPRA FARMACIA)
    # Intentar detectar si hay datos de compras en los consumos/entradas
    # El documento "REGISTRO DE COMPRA FARMACIA" debería estar en entradas o ser fuente separada
    compras_data = None
    # Buscar en entradas comprobantes de compra (case-insensitive)
    if "Comprobante" in entradas.columns:
        mask_compra = entradas["Comprobante"].str.to_lowercase().str.contains("compra|entrada")
        if mask_compra.any():
            compras_data = entradas.filter(mask_compra)
    
    if compras_data is not None and compras_data.height > 0:
        print("  [4/4] Calculando análisis compras vs ventas vs consumo...")
        compras_result = calcular_analisis_compras(compras_data, facturacion, consumos)
        compras_detalle = compras_result["detalle_compras_ventas_consumo"]
        compras_resumen = compras_result["resumen_servicio_compras"]
        compras_top_muerto = compras_result["top_stock_muerto"]
        print(f"      -> {compras_detalle.height} productos, {compras_resumen.height} servicios")
        has_compras = True
    else:
        print("  [4/4] Sin datos de compras detectados (REGISTRO DE COMPRA FARMACIA no encontrado en entradas)")
        has_compras = False
        compras_detalle = pl.DataFrame()
        compras_resumen = pl.DataFrame()
        compras_top_muerto = pl.DataFrame()
    
    # Escribir Excel con todas las hojas
    print(f"  -> Guardando en: {ruta_salida}")
    with pd.ExcelWriter(str(ruta_salida), engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formatos comunes
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#2F5496', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        alert_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        ok_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        money_format = workbook.add_format({'num_format': '#,##0', 'border': 1})
        pct_format = workbook.add_format({'num_format': '0.0%', 'border': 1})
        ratio_format = workbook.add_format({'num_format': '0.00', 'border': 1})
        
        # HOJA 1: Varianza Proveedor
        _write_sheet(writer, "1_Varianza_Proveedor", varianza_proveedor.to_pandas(), 
                     header_format, money_format, pct_format, ratio_format,
                     highlight_cols=["Nivel_Riesgo_Variabilidad", "Alerta_Precio_Mercado"])
        
        # HOJA 2-3: Eficiencia Stock (detalle + resumen)
        _write_sheet(writer, "2_Eficiencia_Stock_Detalle", eficiencia_detalle.to_pandas(),
                     header_format, money_format, pct_format, ratio_format,
                     highlight_cols=["Estado_Inventario", "Alerta_Costo_Unitario"])
        _write_sheet(writer, "3_Eficiencia_Stock_Resumen", eficiencia_resumen.to_pandas(),
                     header_format, money_format, pct_format, ratio_format,
                     highlight_cols=["Estado_Predominante", "Alerta_Servicio"])
        
        # HOJA 4-6: Gap Facturación (detalle + resumen + alertas)
        _write_sheet(writer, "4_Gap_Fact_Consumo_Detalle", gap_detalle.to_pandas(),
                     header_format, money_format, pct_format, ratio_format,
                     highlight_cols=["Estado_Facturacion", "Alerta_Spread"])
        _write_sheet(writer, "5_Gap_Fact_Consumo_Resumen", gap_resumen.to_pandas(),
                     header_format, money_format, pct_format, ratio_format,
                     highlight_cols=["Alerta_Servicio"])
        _write_sheet(writer, "6_Alertas_Pacientes_Criticos", gap_alertas.to_pandas(),
                     header_format, money_format, pct_format, ratio_format,
                     highlight_cols=[])
        
        # HOJA 7-9: Análisis Compras vs Ventas vs Consumo (si hay datos)
        if has_compras:
            _write_sheet(writer, "7_Compras_Ventas_Consumo_Detalle", compras_detalle.to_pandas(),
                         header_format, money_format, pct_format, ratio_format,
                         highlight_cols=["Alerta_Margen", "Alerta_Eficiencia_Compra", "Alerta_Rotacion_Venta"])
            _write_sheet(writer, "8_Compras_Ventas_Resumen_Servicio", compras_resumen.to_pandas(),
                         header_format, money_format, pct_format, ratio_format,
                         highlight_cols=[])
            _write_sheet(writer, "9_Top_Stock_Muerto_Estimado", compras_top_muerto.to_pandas(),
                         header_format, money_format, pct_format, ratio_format,
                         highlight_cols=["Alerta_Eficiencia_Compra", "Alerta_Margen"])
    
    n_hojas = 9 if has_compras else 6
    print(f"  [OK] Informe financiero generado con {n_hojas} hojas en: {ruta_salida.name}")
    
    result = {
        "varianza_proveedor": varianza_proveedor,
        "eficiencia_stock_detalle": eficiencia_detalle,
        "eficiencia_stock_resumen": eficiencia_resumen,
        "gap_fact_consumo_detalle": gap_detalle,
        "gap_fact_consumo_resumen": gap_resumen,
        "alertas_pacientes_criticos": gap_alertas
    }
    
    if has_compras:
        result.update({
            "compras_ventas_consumo_detalle": compras_detalle,
            "compras_ventas_resumen_servicio": compras_resumen,
            "top_stock_muerto_estimado": compras_top_muerto
        })
    
    return result


def _write_sheet(writer, sheet_name, df, header_format, money_format, pct_format, ratio_format, highlight_cols=None):
    """Helper para escribir hoja con formato consistente."""
    if df.empty:
        df = df.head(1)  # Escribir al menos headers
    
    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    worksheet = writer.sheets[sheet_name[:31]]
    
    # Formatear headers
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    
    # Auto-ajustar ancho de columnas (robusto a NaN, float, Arrow arrays)
    for i, col in enumerate(df.columns):
        try:
            # Convertir a string de forma segura manejando NaN
            col_str = df[col].fillna('').astype(str)
            max_len = max(col_str.str.len().max(), len(col)) + 2
        except Exception:
            # Fallback: ancho fijo si falla el cálculo
            max_len = 20
        worksheet.set_column(i, i, min(max_len, 40))
    
    # Formateo condicional para columnas de alerta
    if highlight_cols:
        for col_name in highlight_cols:
            if col_name in df.columns:
                col_idx = df.columns.get_loc(col_name)
                worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': 'ALTO_RIESGO',
                    'format': writer.book.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                })
                worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': 'CRITICO',
                    'format': writer.book.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                })
                worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': 'SOBRE_STOCK',
                    'format': writer.book.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
                })
                worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': 'DESABASTECIMIENTO',
                    'format': writer.book.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                })
                worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': 'OPTIMO',
                    'format': writer.book.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
                })
                worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                    'type': 'text',
                    'criteria': 'containing',
                    'value': 'EQUILIBRADO',
                    'format': writer.book.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
                })


def calcular_analisis_compras(compras: pl.DataFrame, facturacion: pl.DataFrame, consumos: pl.DataFrame) -> dict:
    """
    Análisis de compras vs facturación vs consumo.
    Usa el documento 'REGISTRO DE COMPRA FARMACIA' para:
    1. Comparar precio de compra vs precio de venta (facturación)
    2. Calcular margen unitario y total
    3. Verificar si lo comprado se consume (cruce con salidas)
    4. Complementar eficiencia de stock con costos unitarios reales
    
    Args:
        compras: DataFrame con columnas CodigoGenerico, Nombre, ValorUnitario (precio compra), 
                 Cantidad, ValorTotal, Proveedor, Municipio, Servicio, Fecha
        facturacion: DataFrame con facturación (vrtotal, cantidad, vrunitario, CodigoGenerico, etc.)
        consumos: DataFrame con salidas/consumo real (ValorUnitario, Cantidad, ValorTotal, CodigoGenerico, etc.)
    
    Returns:
        Dict con 3 DataFrames para 3 hojas Excel
    """
    print("  [4/4] Calculando análisis compras vs ventas vs consumo...")
    
    # Normalizar columnas de compras
    compras_norm = compras.clone()
    # Asegurar columnas estándar
    if "ValorUnitario" not in compras_norm.columns and "PrecioCompra" in compras_norm.columns:
        compras_norm = compras_norm.rename({"PrecioCompra": "ValorUnitario"})
    
    # Agrupar compras por producto/servicio/municipio
    keys_compra = ["CodigoGenerico", "Nombre", "Municipio", "Servicio"]
    compras_agg = compras_norm.group_by(keys_compra).agg(
        pl.col("ValorUnitario").mean().alias("Precio_Compra_Prom"),
        pl.col("ValorUnitario").median().alias("Precio_Compra_Mediana"),
        pl.col("ValorUnitario").min().alias("Precio_Compra_Min"),
        pl.col("ValorUnitario").max().alias("Precio_Compra_Max"),
        pl.col("Cantidad").sum().alias("Compras_Cantidad"),
        pl.col("ValorTotal").sum().alias("Compras_Valor"),
        pl.col("Proveedor").n_unique().alias("Num_Proveedores"),
        pl.col("Proveedor").mode().first().alias("Proveedor_Principal")
    )
    
    # Agrupar facturación por producto
    keys_fact = ["CodigoGenerico", "Nombre", "Municipio", "Servicio"]
    fact_agg = facturacion.group_by(keys_fact).agg(
        pl.col("vrunitario").mean().alias("Precio_Venta_Prom"),
        pl.col("vrunitario").median().alias("Precio_Venta_Mediana"),
        pl.col("vrtotal").sum().alias("Facturacion_Valor"),
        pl.col("cantidad").sum().alias("Facturacion_Cantidad")
    )
    
    # Agrupar consumos reales por producto
    cons_agg = consumos.group_by(keys_compra).agg(
        pl.col("ValorUnitario").mean().alias("Costo_Consumo_Prom"),
        pl.col("Cantidad").sum().alias("Consumo_Cantidad"),
        pl.col("ValorTotal").sum().alias("Consumo_Valor")
    )
    
    # Join compras -> facturación -> consumo
    analisis = compras_agg.join(fact_agg, on=keys_compra, how="left")
    analisis = analisis.join(cons_agg, on=keys_compra, how="left").fill_null(0)
    
    # Calcular métricas de margen y variación
    analisis = analisis.with_columns(
        # Margen unitario: precio venta - precio compra
        (pl.col("Precio_Venta_Prom") - pl.col("Precio_Compra_Prom")).alias("Margen_Unitario_Prom"),
        (pl.col("Precio_Venta_Mediana") - pl.col("Precio_Compra_Mediana")).alias("Margen_Unitario_Mediana"),
        
        # % Margen sobre costo
        pl.when(pl.col("Precio_Compra_Prom") > 0)
         .then((pl.col("Precio_Venta_Prom") - pl.col("Precio_Compra_Prom")) / pl.col("Precio_Compra_Prom") * 100)
         .otherwise(pl.lit(None)).alias("Margen_Porcentual_Prom"),
        
        # Margen total
        (pl.col("Facturacion_Valor") - pl.col("Compras_Valor")).alias("Margen_Total"),
        
        # % Margen total
        pl.when(pl.col("Compras_Valor") > 0)
         .then((pl.col("Facturacion_Valor") - pl.col("Compras_Valor")) / pl.col("Compras_Valor") * 100)
         .otherwise(pl.lit(None)).alias("Margen_Total_Pct"),
        
        # Diferencia cantidad comprada vs facturada
        (pl.col("Compras_Cantidad") - pl.col("Facturacion_Cantidad")).alias("Diff_Cant_Compra_Venta"),
        
        # Diferencia cantidad comprada vs consumida
        (pl.col("Compras_Cantidad") - pl.col("Consumo_Cantidad")).alias("Diff_Cant_Compra_Consumo"),
        
        # Ratio consumo/compra (eficiencia de compra)
        pl.when(pl.col("Compras_Cantidad") > 0)
         .then(pl.col("Consumo_Cantidad") / pl.col("Compras_Cantidad"))
         .otherwise(pl.lit(None)).alias("Ratio_Consumo_Compra"),
        
        # Ratio venta/compra
        pl.when(pl.col("Compras_Cantidad") > 0)
         .then(pl.col("Facturacion_Cantidad") / pl.col("Compras_Cantidad"))
         .otherwise(pl.lit(None)).alias("Ratio_Venta_Compra"),
        
        # Spread compra vs costo consumo real
        (pl.col("Precio_Compra_Prom") - pl.col("Costo_Consumo_Prom")).alias("Spread_Compra_Consumo"),
    )
    
    # Clasificaciones de alerta
    analisis = analisis.with_columns(
        # Alerta margen
        pl.when(pl.col("Margen_Porcentual_Prom").is_null())
         .then(pl.lit("SIN_VENTA"))
         .when(pl.col("Margen_Porcentual_Prom") < 0)
         .then(pl.lit("PERDIDA"))
         .when(pl.col("Margen_Porcentual_Prom") < 10)
         .then(pl.lit("MARGEN_BAJO"))
         .when(pl.col("Margen_Porcentual_Prom") < 30)
         .then(pl.lit("MARGEN_NORMAL"))
         .otherwise(pl.lit("MARGEN_ALTO"))
         .alias("Alerta_Margen"),
        
        # Alerta consumo vs compra
        pl.when(pl.col("Compras_Cantidad") == 0)
         .then(pl.lit("SIN_COMPRA"))
         .when(pl.col("Ratio_Consumo_Compra").is_null())
         .then(pl.lit("SIN_CONSUMO"))
         .when(pl.col("Ratio_Consumo_Compra") < 0.5)
         .then(pl.lit("SOBRE_COMPRA_CRITICA"))
         .when(pl.col("Ratio_Consumo_Compra") < 0.8)
         .then(pl.lit("SOBRE_COMPRA"))
         .when(pl.col("Ratio_Consumo_Compra") <= 1.1)
         .then(pl.lit("OPTIMO"))
         .otherwise(pl.lit("DESABASTECIMIENTO"))
         .alias("Alerta_Eficiencia_Compra"),
        
        # Alerta venta vs compra
        pl.when(pl.col("Ratio_Venta_Compra").is_null())
         .then(pl.lit("SIN_VENTA"))
         .when(pl.col("Ratio_Venta_Compra") < 0.7)
         .then(pl.lit("BAJA_ROTACION_VENTA"))
         .when(pl.col("Ratio_Venta_Compra") <= 1.2)
         .then(pl.lit("NORMAL"))
         .otherwise(pl.lit("VENTA_SUPERIOR_COMPRA"))
         .alias("Alerta_Rotacion_Venta"),
        
        # Valor de stock muerto (comprado - consumido) * precio compra
        (pl.when(pl.col("Diff_Cant_Compra_Consumo") > 0).then(pl.col("Diff_Cant_Compra_Consumo")).otherwise(0) * pl.col("Precio_Compra_Prom")).alias("Valor_Stock_Muerto_Estimado")
    )
    
    # Resumen por servicio/municipio
    resumen_servicio = analisis.group_by(["Municipio", "Servicio"]).agg(
        pl.col("Compras_Valor").sum().alias("Total_Compras"),
        pl.col("Facturacion_Valor").sum().alias("Total_Facturacion"),
        pl.col("Consumo_Valor").sum().alias("Total_Consumo"),
        pl.col("Margen_Total").sum().alias("Margen_Total_Servicio"),
        pl.col("Valor_Stock_Muerto_Estimado").sum().alias("Total_Stock_Muerto"),
        pl.col("Margen_Porcentual_Prom").median().alias("Margen_Mediano_Pct"),
        pl.col("Ratio_Consumo_Compra").median().alias("Eficiencia_Mediana"),
        pl.col("Alerta_Margen").filter(pl.col("Alerta_Margen").is_in(["PERDIDA", "MARGEN_BAJO"])).count().alias("Productos_Margen_Bajo"),
        pl.col("Alerta_Eficiencia_Compra").filter(pl.col("Alerta_Eficiencia_Compra").is_in(["SOBRE_COMPRA_CRITICA", "SOBRE_COMPRA"])).count().alias("Productos_Sobre_Compra"),
        pl.col("CodigoGenerico").n_unique().alias("Num_Productos")
    ).with_columns(
        pl.when(pl.col("Total_Compras") > 0)
         .then(pl.col("Total_Facturacion") / pl.col("Total_Compras"))
         .otherwise(pl.lit(None)).alias("Ratio_Venta_Compra_Servicio"),
        pl.when(pl.col("Total_Compras") > 0)
         .then(pl.col("Total_Consumo") / pl.col("Total_Compras"))
         .otherwise(pl.lit(None)).alias("Ratio_Consumo_Compra_Servicio")
    )
    
    # Top productos con mayor stock muerto
    top_stock_muerto = analisis.filter(pl.col("Valor_Stock_Muerto_Estimado") > 0).sort(
        "Valor_Stock_Muerto_Estimado", descending=True
    ).head(50).select([
        "CodigoGenerico", "Nombre", "Municipio", "Servicio", "Proveedor_Principal",
        "Precio_Compra_Prom", "Precio_Venta_Prom", "Margen_Unitario_Prom", "Margen_Porcentual_Prom",
        "Compras_Cantidad", "Consumo_Cantidad", "Diff_Cant_Compra_Consumo",
        "Valor_Stock_Muerto_Estimado", "Alerta_Eficiencia_Compra", "Alerta_Margen"
    ])
    
    print(f"      -> {analisis.height} productos, {resumen_servicio.height} servicios, {top_stock_muerto.height} top stock muerto")
    
    return {
        "detalle_compras_ventas_consumo": analisis.sort(["Alerta_Margen", "Margen_Total"], descending=[True, True]),
        "resumen_servicio_compras": resumen_servicio.sort("Total_Stock_Muerto", descending=True),
        "top_stock_muerto": top_stock_muerto
    }


def _empty_varianza_schema() -> pl.DataFrame:
    return pl.DataFrame({
        "CodigoGenerico": [], "Nombre": [], "Proveedor": [], "Municipio": [], "Servicio": [],
        "Costo_Mediano": [], "Costo_Promedio": [], "Desv_Estandar": [], "Costo_Minimo": [], "Costo_Maximo": [],
        "Volumen_Total": [], "Valor_Total_Comprado": [], "Num_Transacciones": [], "CV_Costo": [],
        "Rango_Porcentual": [], "Diferencia_Absoluta": [], "Precio_Promedio_Proveedor": [],
        "Mediana_Mercado": [], "Desviacion_Vs_Mercado_Pct": [], "Desviacion_Vs_Mercado_Abs": [],
        "Nivel_Riesgo_Variabilidad": [], "Alerta_Precio_Mercado": [], "Clasificacion_Volumen": []
    })


def _empty_gap_schema() -> dict:
    empty = pl.DataFrame({
        "idadmision": [], "CodigoGenerico": [], "Nombre": [], "Municipio": [], "Especialidad": [],
        "Servicio_Corregido": [], "MedicoRealiza": [], "No_Factura": [],
        "Facturado_Valor": [], "Consumido_Valor": [], "Margen_Bruto": [], "Ratio_Fact_Consumo": [],
        "Margen_Porcentual": [], "Spread_Precio_Costo": [], "Estado_Facturacion": [], "Alerta_Spread": []
    })
    return {
        "detalle_paciente_producto": empty,
        "resumen_servicio": empty,
        "alertas_paciente": empty
    }
