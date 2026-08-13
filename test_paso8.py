"""
Script de prueba para validar el Paso 8 - Análisis Financiero.
"""
import polars as pl
from pathlib import Path
import sys

sys.path.insert(0, r"F:\EDISON\computador\VARIOS EDISON\PROHIBIDO NO TOCAR\CursoPrepHenry\Automatizaciones_bot_sin_apis")

from salud_ips.consumos.scripts.analisis_financiero import generar_informe_financiero


def crear_datos_mock():
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


def test_paso8():
    print("=" * 60)
    print("TEST PASO 8: ANÁLISIS FINANCIERO")
    print("=" * 60)

    consumos, entradas, facturacion = crear_datos_mock()
    print(f"Consumos: {consumos.height} filas")
    print(f"Entradas: {entradas.height} filas")
    print(f"Facturacion: {facturacion.height} filas")

    ruta_salida = Path(tempfile.gettempdir()) / "test_analisis_financiero.xlsx"

    try:
        resultado = generar_informe_financiero(
            consumos=consumos,
            entradas=entradas,
            facturacion=facturacion,
            ruta_salida=ruta_salida
        )

        print(f"\n[OK] ÉXITO: Archivo generado en {ruta_salida}")
        print(f"  Tamaño: {ruta_salida.stat().st_size / 1024:.1f} KB")

        # Verificar hojas
        import pandas as pd
        xls = pd.ExcelFile(ruta_salida)
        print(f"  Hojas: {xls.sheet_names}")

        for sheet in xls.sheet_names:
            df = pd.read_excel(ruta_salida, sheet_name=sheet)
            print(f"    - {sheet}: {df.shape[0]} filas x {df.shape[1]} cols")

        # Verificar claves del resultado
        print(f"\n  Claves en resultado: {list(resultado.keys())}")
        for k, v in resultado.items():
            print(f"    - {k}: {v.height} filas")

        return True

    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import tempfile
    ok = test_paso8()
    sys.exit(0 if ok else 1)