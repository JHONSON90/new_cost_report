"""
Test de integración de los pasos 3-8 directamente desde el paquete consumos.
Ejecutar desde: salud_ips/consumos/
"""
import polars as pl
from pathlib import Path
import tempfile
import sys

# Ajustar path para imports relativos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from informes_consumo import ConsumoPipeline


def crear_datos_mock_pipeline():
    base = {
        "Municipio": ["001", "001", "001", "002", "002", "002"],
        "Servicio": ["FAR", "FAR", "ALM", "FAR", "FAR", "ALM"],
        "Clasificacion_consumo": ["Medicamentos", "Dispositivos Medicos", "Suministros"] * 2,
        "CodigoGenerico": [1001, 2001, 3001, 1001, 2002, 3002],
        "Nombre": ["Paracetamol 500mg", "Jeringa 10ml", "Guantes Latex", "Paracetamol 500mg", "Cateter Foley", "Algodon 50g"],
    }

    n = 30
    consumos_fact = pl.DataFrame({
        **{k: (v * (n // 6 + 1))[:n] for k, v in base.items()},
        "Proveedor": ["PROV_A", "PROV_B", "PROV_C"] * 10,
        "ValorUnitario": [1000, 500, 200, 1100, 550, 220] * 5,
        "Cantidad": [10, 5, 20, 8, 3, 15] * 5,
        "ValorTotal": [10000, 2500, 4000, 8800, 1650, 3300] * 5,
        "field_1": [1001, 1002, 1003] * 10,
        "ADM-CodGen": [f"1001-1001", f"1002-2001", f"1003-3001"] * 10,
        "ValorIVA": [1900, 475, 760, 1672, 313, 627] * 5,
        "ValorDescuento": [0] * n,
        "TotalBruto": [10000, 2500, 4000, 8800, 1650, 3300] * 5,
        "Comprobante": ["SISTEMA DISPENSACION FARMACIA"] * 15 + ["SALIDAS INTERNAS FARMACIA"] * 15,
        "CentroCosto": ["001FAR", "001FAR", "001ALM", "002FAR", "002FAR", "002ALM"] * 5,
        "Dependencia": ["FARMACIA"] * n,
        "Bodega": ["PRINCIPAL"] * n,
        "CodGrupo": ["G01", "G02", "G03"] * 10,
        "Grupo": ["ANALGESICOS", "MATERIAL CURACION", "INSUMOS"] * 10,
        "Unidad": ["UND", "UND", "CAJ"] * 10,
        "LaboratorioMarca": ["LAB_A", "LAB_B", "LAB_C"] * 10,
        "Observacion": [""] * n,
        "Usuario": ["USER1"] * n,
        "User": ["USER1"] * n,
        "FechaDigitacion": ["2024-01-15"] * n,
        "EstadoArticulo": ["ACTIVO"] * n,
        "Tipo_servicio": ["AMB"] * n,
        "Especialidad": ["FARMACIA", "FARMACIA", "ENFERMERIA", "FARMACIA", "UROLOGIA", "CIRUGIA"] * 5,
        "Servicio_Corregido": ["servicio farmaceutico"] * n,
        "MedicoRealiza": ["Dr. A", "Dr. B", "Dr. C", "Dr. D", "Dr. E", "Dr. F"] * 5,
        "NoDocumento": [""] * n,
        "nofactura": [f"FAC-{i:04d}" for i in range(1, n+1)],
        "idadmision": [1001, 1002, 1003] * 10,
        "cantidad": [10, 5, 20, 8, 3, 15] * 5,
        "CantidadSolicitada": [10, 5, 20, 8, 3, 15] * 5,
        "vrunitario": [1200, 600, 250, 1250, 1333, 220] * 5,
        "vrtotal": [12000, 3000, 5000, 10000, 4000, 3300] * 5,
    })

    anulados = pl.DataFrame({
        **{k: v[:2] for k, v in base.items()},
        "Proveedor": ["PROV_A", "PROV_B"],
        "ValorUnitario": [1000, 500],
        "Cantidad": [10, 5],
        "ValorTotal": [10000, 2500],
        "Comprobante": ["SISTEMA DISPENSACION FARMACIA"] * 2,
        "CentroCosto": ["001FAR", "001FAR"],
        "Dependencia": ["FARMACIA"] * 2,
        "Bodega": ["PRINCIPAL"] * 2,
        "CodGrupo": ["G01", "G02"],
        "Grupo": ["ANALGESICOS", "MATERIAL CURACION"],
        "Unidad": ["UND", "UND"],
        "LaboratorioMarca": ["LAB_A", "LAB_B"],
        "Observacion": [""] * 2,
        "Usuario": ["USER1"] * 2,
        "User": ["USER1"] * 2,
        "FechaDigitacion": ["2024-01-15"] * 2,
        "EstadoArticulo": ["ACTIVO"] * 2,
        "Tipo_servicio": ["AMB"] * 2,
        "Especialidad": ["FARMACIA", "FARMACIA"],
        "Servicio_Corregido": ["servicio farmaceutico"] * 2,
        "MedicoRealiza": [None, None],
        "NoDocumento": [""] * 2,
    })

    limpieza_fact = consumos_fact.clone()

    salidas = pl.DataFrame({
        **{k: (v * (n // 6 + 1))[:n] for k, v in base.items()},
        "Proveedor": ["INTERNO"] * n,
        "ValorUnitario": [1000, 500, 200, 1100, 550, 220] * 5,
        "Cantidad": [10, 5, 20, 8, 3, 15] * 5,
        "ValorTotal": [10000, 2500, 4000, 8800, 1650, 3300] * 5,
        "Comprobante": ["SALIDAS INTERNAS FARMACIA"] * 15 + ["SALIDAS INTERNAS ALMACEN"] * 15,
        "CentroCosto": ["001FAR", "001FAR", "001ALM", "002FAR", "002FAR", "002ALM"] * 5,
        "Dependencia": ["FARMACIA"] * 15 + ["ALMACEN"] * 15,
        "Bodega": ["PRINCIPAL"] * n,
        "CodGrupo": ["G01", "G02", "G03"] * 10,
        "Grupo": ["ANALGESICOS", "MATERIAL CURACION", "INSUMOS"] * 10,
        "Unidad": ["UND", "UND", "CAJ"] * 10,
        "LaboratorioMarca": ["LAB_A", "LAB_B", "LAB_C"] * 10,
        "Observacion": [""] * n,
        "Usuario": ["USER3"] * n,
        "User": ["USER3"] * n,
        "FechaDigitacion": ["2024-01-15"] * n,
        "EstadoArticulo": ["ACTIVO"] * n,
        "Tipo_servicio": ["AMB"] * n,
        "Servicio": ["FAR", "FAR", "ALM", "FAR", "FAR", "ALM"] * 5,
        "Clasificacion_consumo": ["Medicamentos", "Dispositivos Medicos", "Suministros"] * 10,
        "NoDocumento": [""] * n,
    })

    entradas_fact = pl.DataFrame({
        **{k: (v * (10 // 6 + 1))[:10] for k, v in base.items()},
        "Proveedor": ["PROV_A", "PROV_B"] * 5,
        "ValorUnitario": [1050, 480] * 5,
        "Cantidad": [15, 8] * 5,
        "ValorTotal": [15750, 3840] * 5,
        "Comprobante": ["SISTEMA ANULACION DISPENSACION FARMACIA"] * 10,
        "CentroCosto": ["001FAR", "001FAR"] * 5,
        "Dependencia": ["FARMACIA"] * 10,
        "Bodega": ["PRINCIPAL"] * 10,
        "CodGrupo": ["G01", "G02"] * 5,
        "Grupo": ["ANALGESICOS", "MATERIAL CURACION"] * 5,
        "Unidad": ["UND", "UND"] * 5,
        "LaboratorioMarca": ["LAB_A", "LAB_B"] * 5,
        "Observacion": [""] * 10,
        "Usuario": ["USER4"] * 10,
        "User": ["USER4"] * 10,
        "FechaDigitacion": ["2024-01-10"] * 10,
        "EstadoArticulo": ["ACTIVO"] * 10,
        "Tipo_servicio": ["AMB"] * 10,
        "Servicio": ["FAR", "FAR"] * 5,
        "Clasificacion_consumo": ["Medicamentos", "Dispositivos Medicos"] * 5,
        "NoDocumento": [""] * 10,
        "field_1": [1001, 1002] * 5,
    })

    n_ent = 25
    entradas_cons = pl.DataFrame({
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
        "Usuario": ["USER5"] * n_ent,
        "User": ["USER5"] * n_ent,
        "FechaDigitacion": ["2024-01-10"] * n_ent,
        "EstadoArticulo": ["ACTIVO"] * n_ent,
        "Tipo_servicio": ["AMB"] * n_ent,
        "Servicio": ["FAR", "FAR", "ALM", "FAR", "FAR", "ALM"] * 4 + ["FAR"],
        "Clasificacion_consumo": ["Medicamentos", "Dispositivos Medicos", "Suministros"] * 8 + ["Medicamentos"],
        "NoDocumento": [""] * n_ent,
        "tipo insumo": ["MEDICAMENTO", "DISPOSITIVO", "SUMINISTRO"] * 8 + ["MEDICAMENTO"],
    })

    return (
        consumos_fact, anulados, limpieza_fact, salidas, entradas_fact, entradas_cons
    )


def test_integration():
    print("=" * 70)
    print("TEST INTEGRACION PASOS 3-8 (desde paquete consumos)")
    print("=" * 70)

    pipeline = ConsumoPipeline("01/01/2024", "31/01/2024")

    (pipeline.consumos_de_facturacion,
     pipeline.anulados_limpieza,
     pipeline.limpieza_consumos_facturacion,
     pipeline.salidas_consumo,
     pipeline.entradas_facturacion,
     pipeline.entradas_consumo) = crear_datos_mock_pipeline()

    temp_dir = Path(tempfile.gettempdir()) / "test_pipeline_saludips"
    temp_dir.mkdir(parents=True, exist_ok=True)
    pipeline.ruta_informes = temp_dir
    pipeline.rutas_descargadas = {
        "salidas": temp_dir / "salidas.xlsx",
        "entradas": temp_dir / "entradas.xlsx"
    }

    print(f"\nDatos inyectados:")
    print(f"  consumos_facturacion: {pipeline.consumos_de_facturacion.height} filas")
    print(f"  salidas_consumo: {pipeline.salidas_consumo.height} filas")
    print(f"  entradas_facturacion: {pipeline.entradas_facturacion.height} filas")
    print(f"  entradas_consumo: {pipeline.entradas_consumo.height} filas")

    try:
        # Paso 3: Auditoría
        print("\n" + "-" * 50)
        print("EJECUTANDO PASO 3: AUDITORÍA")
        print("-" * 50)
        inconsistencias = pipeline.paso_3_auditoria()
        print(f"Inconsistencias: {inconsistencias.height} registros")

        # Paso 4: Desviaciones
        print("\n" + "-" * 50)
        print("EJECUTANDO PASO 4: DESVIACIONES")
        print("-" * 50)
        desviaciones = pipeline.paso_4_desviaciones()
        print(f"Alertas desviación: {desviaciones.height} registros")

        # Paso 5: Informe
        print("\n" + "-" * 50)
        print("EJECUTANDO PASO 5: INFORME FINAL")
        print("-" * 50)
        informe = pipeline.paso_5_informe()
        print(f"Hojas informe: {list(informe.keys())}")

        # Paso 6: Rentabilidad
        print("\n" + "-" * 50)
        print("EJECUTANDO PASO 6: RENTABILIDAD")
        print("-" * 50)
        rentabilidad = pipeline.informe_rentabilidad()
        print(f"Rentabilidad: {rentabilidad.height} filas, {rentabilidad.width} cols")

        # Paso 8: Análisis Financiero
        print("\n" + "-" * 50)
        print("EJECUTANDO PASO 8: ANÁLISIS FINANCIERO")
        print("-" * 50)
        analisis = pipeline.paso_8_analisis_financiero()
        print(f"Hojas análisis: {list(analisis.keys())}")

        print("\n" + "=" * 70)
        print("[OK] INTEGRACIÓN PASOS 3-8 EXITOSA")
        print("=" * 70)
        print(f"\nArchivos generados en: {temp_dir}")
        for f in temp_dir.iterdir():
            if f.is_file():
                print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

        return True

    except Exception as e:
        print(f"\n[ERROR] INTEGRACIÓN FALLIDA: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = test_integration()
    sys.exit(0 if ok else 1)