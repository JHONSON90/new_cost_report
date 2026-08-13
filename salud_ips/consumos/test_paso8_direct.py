"""
Test directo del Paso 8 (analisis_financiero) y Paso 4 (desviaciones) 
sin dependencias de playwright.
"""
import polars as pl
from pathlib import Path
import tempfile
import sys

# Importar directamente los módulos que no dependen de playwright
from scripts.desviaciones import desviaciones
from scripts.analisis_financiero import generar_informe_financiero


def crear_datos_test():
    base = {
        "Municipio": ["001", "001", "001", "002", "002", "002"],
        "Servicio": ["FAR", "FAR", "ALM", "FAR", "FAR", "ALM"],
        "Clasificacion_consumo": ["Medicamentos", "Dispositivos Medicos", "Suministros"] * 2,
        "CodigoGenerico": [1001, 2001, 3001, 1001, 2002, 3002],
        "Nombre": ["Paracetamol 500mg", "Jeringa 10ml", "Guantes Latex", "Paracetamol 500mg", "Cateter Foley", "Algodon 50g"],
    }

    n_cons = 30
    consumos = pl.DataFrame({
        **{k: (v * (n_cons // 6 + 1))[:n_cons] for k, v in base.items()},
        "Proveedor": ["PROV_A", "PROV_B", "PROV_C"] * 10,
        "ValorUnitario": [1000, 500, 200, 1100, 550, 220] * 5,
        "Cantidad": [10, 5, 20, 8, 3, 15] * 5,
        "ValorTotal": [10000, 2500, 4000, 8800, 1650, 3300] * 5,
        "field_1": [1001, 1002, 1003] * 10,
        "ADM-CodGen": [f"1001-1001", f"1002-2001", f"1003-3001"] * 10,
        "ValorIVA": [1900, 475, 760, 1672, 313, 627] * 5,
        "ValorDescuento": [0] * n_cons,
        "TotalBruto": [10000, 2500, 4000, 8800, 1650, 3300] * 5,
        "Comprobante": ["SISTEMA DISPENSACION FARMACIA"] * 15 + ["SALIDAS INTERNAS FARMACIA"] * 15,
        "CentroCosto": ["001FAR", "001FAR", "001ALM", "002FAR", "002FAR", "002ALM"] * 5,
        "Dependencia": ["FARMACIA"] * n_cons,
        "Bodega": ["PRINCIPAL"] * n_cons,
        "CodGrupo": ["G01", "G02", "G03"] * 10,
        "Grupo": ["ANALGESICOS", "MATERIAL CURACION", "INSUMOS"] * 10,
        "Unidad": ["UND", "UND", "CAJ"] * 10,
        "LaboratorioMarca": ["LAB_A", "LAB_B", "LAB_C"] * 10,
        "Observacion": [""] * n_cons,
        "Usuario": ["USER1"] * n_cons,
        "User": ["USER1"] * n_cons,
        "FechaDigitacion": ["2024-01-15"] * n_cons,
        "EstadoArticulo": ["ACTIVO"] * n_cons,
        "Tipo_servicio": ["AMB"] * n_cons,
        "Numero": list(range(1, n_cons + 1)),
        "Fecha": ["2024-01-15"] * n_cons,
        "NoDocumento": [""] * n_cons,
    })

    n_ent = 25
    entradas = pl.DataFrame({
        **{k: (v * (n_ent // 6 + 1))[:n_ent] for k, v in base.items()},
        "Proveedor": ["PROV_A", "PROV_B", "PROV_C"] * 8 + ["PROV_A"],
        "ValorUnitario": [1050, 480, 190, 1150, 520, 210] * 4 + [1050],
        "Cantidad": [15, 8, 30, 12, 5, 25] * 4 + [15],
        "ValorTotal": [15750, 3840, 5700, 13800, 2600, 5250] * 4 + [15750],
        "Comprobante": ["ENTRADAS INTERNAS FARMACIA"] * n_ent,
        "CentroCosto": ["001FAR", "001FAR", "001ALM", "002FAR", "002FAR", "002ALM"] * 4 + ["001FAR"],
        "Dependencia": ["ALMACEN"] * n_ent,
        "Bodega": ["PRINCIPAL"] * n_ent,
        "CodGrupo": ["G01", "G02", "G03"] * 8 + ["G01"],
        "Grupo": ["ANALGESICOS", "MATERIAL CURACION", "INSUMOS"] * 8 + ["ANALGESICOS"],
        "Unidad": ["UND", "UND", "CAJ"] * 8 + ["UND"],
        "LaboratorioMarca": ["LAB_A", "LAB_B", "LAB_C"] * 8 + ["LAB_A"],
        "Observacion": [""] * n_ent,
        "Usuario": ["USER2"] * n_ent,
        "User": ["USER2"] * n_ent,
        "FechaDigitacion": ["2024-01-10"] * n_ent,
        "EstadoArticulo": ["ACTIVO"] * n_ent,
        "tipo insumo": ["MEDICAMENTO", "DISPOSITIVO", "SUMINISTRO"] * 8 + ["MEDICAMENTO"],
    })

    n_fact = 20
    facturacion = pl.DataFrame({
        **{k: (v * (n_fact // 6 + 1))[:n_fact] for k, v in base.items()},
        "idadmision": [1001, 1002, 1003, 1004, 1005] * 4,
        "CodigoGenerico": [1001, 2001, 3001, 1001, 2002] * 4,
        "Nombre": ["Paracetamol 500mg", "Jeringa 10ml", "Guantes Latex", "Paracetamol 500mg", "Cateter Foley"] * 4,
        "vrtotal": [12000, 3000, 5000, 10000, 4000] * 4,
        "cantidad": [10, 5, 20, 8, 3] * 4,
        "vrunitario": [1200, 600, 250, 1250, 1333] * 4,
        "Especialidad": ["FARMACIA", "FARMACIA", "ENFERMERIA", "FARMACIA", "UROLOGIA"] * 4,
        "Servicio_Corregido": ["servicio farmaceutico"] * 20,
        "Municipio": ["001", "001", "001", "002", "002"] * 4,
        "MedicoRealiza": ["Dr. A", "Dr. B", "Dr. C", "Dr. D", "Dr. E"] * 4,
        "nofactura": [f"FAC-{i:04d}" for i in range(1, 21)],
    })

    return consumos, entradas, facturacion


def test_paso4_directo():
    print("=" * 60)
    print("TEST DIRECTO PASO 4: DESVIACIONES")
    print("=" * 60)

    consumos, _, _ = crear_datos_test()

    # Test 1: Con alertas
    print("\n[Test 1] Datos con outlier (debe generar 1 alerta)")
    # Modificar un valor para crear outlier
    consumos_test = consumos.clone()
    consumos_test = consumos_test.with_columns(
        pl.when((pl.col("CodigoGenerico") == 1001) & (pl.col("Cantidad") == 10))
        .then(50)
        .otherwise(pl.col("Cantidad"))
        .alias("Cantidad")
    )

    result = desviaciones(consumos_test)
    print(f"  Alertas generadas: {result.height}")
    assert result.height >= 1, "Debe detectar al menos 1 alerta"
    print("  [OK]")

    # Test 2: Sin alertas - crear datos donde cada grupo tiene misma cantidad
    print("\n[Test 2] Datos uniformes (0 alertas)")
    consumos_uniforme = pl.DataFrame({
        "CodigoGenerico": [1001, 1001, 2001, 2001],
        "Nombre": ["Med A", "Med A", "Med B", "Med B"],
        "Cantidad": [10, 10, 5, 5],  # Misma cantidad dentro de cada grupo
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
    result = desviaciones(consumos_uniforme)
    print(f"  Alertas generadas: {result.height}")
    assert result.height == 0, "No debe haber alertas con datos uniformes"
    print("  [OK]")

    # Test 3: Con nulos
    print("\n[Test 3] Datos con CodigoGenerico nulos")
    consumos_nulos = consumos.clone()
    consumos_nulos = consumos_nulos.with_columns(
        pl.when(pl.col("CodigoGenerico") == 3001)
        .then(None)
        .otherwise(pl.col("CodigoGenerico"))
        .alias("CodigoGenerico")
    )
    result = desviaciones(consumos_nulos)
    print(f"  Alertas generadas: {result.height} (nulos excluidos)")
    print("  [OK]")

    print("\n[OK] TODOS LOS TESTS PASO 4 PASARON")
    return True


def test_paso8_directo():
    print("\n" + "=" * 60)
    print("TEST DIRECTO PASO 8: ANÁLISIS FINANCIERO")
    print("=" * 60)

    consumos, entradas, facturacion = crear_datos_test()

    ruta_salida = Path(tempfile.gettempdir()) / "test_paso8_directo.xlsx"

    print("\nEjecutando generar_informe_financiero()...")
    resultado = generar_informe_financiero(
        consumos=consumos,
        entradas=entradas,
        facturacion=facturacion,
        ruta_salida=ruta_salida
    )

    print(f"\nArchivo generado: {ruta_salida}")
    print(f"Tamaño: {ruta_salida.stat().st_size / 1024:.1f} KB")

    # Verificar hojas
    import pandas as pd
    xls = pd.ExcelFile(ruta_salida)
    print(f"Hojas: {xls.sheet_names}")

    for sheet in xls.sheet_names:
        df = pd.read_excel(ruta_salida, sheet_name=sheet)
        print(f"  - {sheet}: {df.shape[0]} filas x {df.shape[1]} cols")

    # Verificar claves
    print(f"\nClaves resultado: {list(resultado.keys())}")
    for k, v in resultado.items():
        print(f"  - {k}: {v.height} filas")

    # Validaciones básicas
    assert "varianza_proveedor" in resultado
    assert "eficiencia_stock_detalle" in resultado
    assert "eficiencia_stock_resumen" in resultado
    assert "gap_fact_consumo_detalle" in resultado
    assert "gap_fact_consumo_resumen" in resultado
    assert "alertas_pacientes_criticos" in resultado
    assert "compras_ventas_consumo_detalle" in resultado
    assert "compras_ventas_resumen_servicio" in resultado
    assert "top_stock_muerto_estimado" in resultado

    assert len(xls.sheet_names) == 9, f"Esperaba 9 hojas, got {len(xls.sheet_names)}"

    print("\n[OK] TEST PASO 8 PASADO - 9 hojas generadas correctamente")
    return True


if __name__ == "__main__":
    try:
        test_paso4_directo()
        test_paso8_directo()

        print("\n" + "=" * 60)
        print("TODOS LOS TESTS DIRECTOS PASARON [OK]")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)