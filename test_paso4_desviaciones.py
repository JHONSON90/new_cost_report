"""
Test para validar el Paso 4 - Análisis de Desviaciones corregido.
"""
import polars as pl
import sys

sys.path.insert(0, r"F:\EDISON\computador\VARIOS EDISON\PROHIBIDO NO TOCAR\CursoPrepHenry\Automatizaciones_bot_sin_apis")

from salud_ips.consumos.scripts.desviaciones import desviaciones


def test_desviaciones_caso_normal():
    """Test con datos que generan alertas."""
    print("=" * 60)
    print("TEST PASO 4: DESVIACIONES - CASO CON ALERTAS")
    print("=" * 60)
    
    df = pl.DataFrame({
        "CodigoGenerico": [1001, 1001, 1001, 1001, 2001, 2001],
        "Nombre": ["Med A", "Med A", "Med A", "Med A", "Med B", "Med B"],
        "Cantidad": [10, 10, 10, 50, 5, 5],  # 50 es outlier para Med A
        "ValorTotal": [1000, 1000, 1000, 5000, 500, 500],
        "CentroCosto": ["001FAR"] * 6,
        "Comprobante": ["TEST"] * 6,
        "Numero": [1, 2, 3, 4, 5, 6],
        "Fecha": ["2024-01-01"] * 6,
        "NoDocumento": [""] * 6,
        "Dependencia": [""] * 6,
        "Bodega": [""] * 6,
        "CodGrupo": [""] * 6,
        "Grupo": [""] * 6,
    })
    
    result = desviaciones(df)
    print(f"Registros totales procesados: 6")
    print(f"Alertas generadas: {result.height}")
    print(f"Columnas: {result.columns}")
    
    if result.height > 0:
        print("Alertas detectadas:")
        alertas = result.select(["CodigoGenerico", "Nombre", "Cantidad", "Cantidad_moda", "Desviacion_moda", "Alerta_desviacion_moda"])
        for row in alertas.iter_rows(named=True):
            print(f"  {row}")
    
    assert result.height == 1, f"Esperaba 1 alerta, got {result.height}"
    assert result["Alerta_desviacion_moda"][0] == "ALERTA"
    print("\n[OK] Test caso normal PASADO")
    return True


def test_desviaciones_sin_alertas():
    """Test donde todos los valores son iguales (sin alertas)."""
    print("\n" + "=" * 60)
    print("TEST PASO 4: DESVIACIONES - SIN ALERTAS")
    print("=" * 60)
    
    df = pl.DataFrame({
        "CodigoGenerico": [1001, 1001, 2001],
        "Nombre": ["Med A", "Med A", "Med B"],
        "Cantidad": [10, 10, 5],
        "ValorTotal": [1000, 1000, 500],
        "CentroCosto": ["001FAR"] * 3,
        "Comprobante": ["TEST"] * 3,
        "Numero": [1, 2, 3],
        "Fecha": ["2024-01-01"] * 3,
        "NoDocumento": [""] * 3,
        "Dependencia": [""] * 3,
        "Bodega": [""] * 3,
        "CodGrupo": [""] * 3,
        "Grupo": [""] * 3,
    })
    
    result = desviaciones(df)
    print(f"Registros totales procesados: 3")
    print(f"Alertas generadas: {result.height}")
    
    assert result.height == 0, f"Esperaba 0 alertas, got {result.height}"
    assert isinstance(result, pl.DataFrame), "Debe retornar DataFrame, no None"
    print("\n[OK] Test sin alertas PASADO")
    return True


def test_desviaciones_un_registro():
    """Test con un solo registro por grupo (std = null -> fill_null(0))."""
    print("\n" + "=" * 60)
    print("TEST PASO 4: DESVIACIONES - UN REGISTRO POR GRUPO")
    print("=" * 60)
    
    df = pl.DataFrame({
        "CodigoGenerico": [1001, 2001, 3001],
        "Nombre": ["Med A", "Med B", "Med C"],
        "Cantidad": [10, 5, 20],
        "ValorTotal": [1000, 500, 2000],
        "CentroCosto": ["001FAR"] * 3,
        "Comprobante": ["TEST"] * 3,
        "Numero": [1, 2, 3],
        "Fecha": ["2024-01-01"] * 3,
        "NoDocumento": [""] * 3,
        "Dependencia": [""] * 3,
        "Bodega": [""] * 3,
        "CodGrupo": [""] * 3,
        "Grupo": [""] * 3,
    })
    
    result = desviaciones(df)
    print(f"Registros totales procesados: 3")
    print(f"Alertas generadas: {result.height}")
    
    assert result.height == 0, f"Esperaba 0 alertas (todos iguales a su moda), got {result.height}"
    assert isinstance(result, pl.DataFrame)
    print("\n[OK] Test un registro PASADO")
    return True


def test_desviaciones_con_nulos():
    """Test con CodigoGenerico nulos (deben ser excluidos con warning)."""
    print("\n" + "=" * 60)
    print("TEST PASO 4: DESVIACIONES - CON CODIGOGENERICO NULOS")
    print("=" * 60)
    
    df = pl.DataFrame({
        "CodigoGenerico": [1001, 1001, None, None],
        "Nombre": ["Med A", "Med A", "Med B", "Med B"],
        "Cantidad": [10, 10, 5, 5],
        "ValorTotal": [1000, 1000, 500, 500],
        "CentroCosto": ["001FAR"] * 4,
        "Comprobante": ["TEST"] * 4,
        "Numero": [1, 2, 3, 4],
        "Fecha": ["2024-01-01"] * 4,
        "NoDocumento": [""] * 4,
        "Dependencia": [""] * 4,
        "Bodega": [""] * 4,
        "CodGrupo": [""] * 4,
        "Grupo": [""] * 4,
    })
    
    result = desviaciones(df)
    print(f"Registros totales procesados: 4 (2 con nulos)")
    print(f"Alertas generadas: {result.height}")
    
    assert result.height == 0, f"Esperaba 0 alertas, got {result.height}"
    assert isinstance(result, pl.DataFrame)
    print("\n[OK] Test con nulos PASADO")
    return True


def test_desviaciones_dataframe_vacio():
    """Test con DataFrame vacío."""
    print("\n" + "=" * 60)
    print("TEST PASO 4: DESVIACIONES - DATAFRAME VACIO")
    print("=" * 60)
    
    df = pl.DataFrame({
        "CodigoGenerico": [],
        "Nombre": [],
        "Cantidad": [],
        "ValorTotal": [],
        "CentroCosto": [],
        "Comprobante": [],
        "Numero": [],
        "Fecha": [],
        "NoDocumento": [],
        "Dependencia": [],
        "Bodega": [],
        "CodGrupo": [],
        "Grupo": [],
    })
    
    result = desviaciones(df)
    print(f"Registros totales procesados: 0")
    print(f"Alertas generadas: {result.height}")
    
    assert result.height == 0
    assert isinstance(result, pl.DataFrame)
    print("\n[OK] Test DataFrame vacío PASADO")
    return True


if __name__ == "__main__":
    try:
        test_desviaciones_caso_normal()
        test_desviaciones_sin_alertas()
        test_desviaciones_un_registro()
        test_desviaciones_con_nulos()
        test_desviaciones_dataframe_vacio()
        
        print("\n" + "=" * 60)
        print("TODOS LOS TESTS DEL PASO 4 PASARON [OK]")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)