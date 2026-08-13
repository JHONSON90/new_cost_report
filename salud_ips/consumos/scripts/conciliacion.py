# import polars as pl
# from pathlib import Path

# def conciliar_informacion(rutas: dict = None, resultados_informes: dict = None):
#     try:
#         if rutas is not None:
#             ruta_consumos = Path(rutas['salidas'])
#             ruta_entradas = Path(rutas['entradas'])
#         else:
#             print(f"Error: No se definieron las rutas")
#             return None
#         consumos_completo = pl.read_excel(str(ruta_consumos), read_options={"header_row": 6})
#         entradas_completo = pl.read_excel(str(ruta_entradas), read_options={"header_row": 6})

        
#     except Exception as e:
#         print(f"Error: {e}")
#         return None

#     medicamentos_procesado = resultados_informes['consumos_medicamentos'].clone()
#     dispositivos_procesado = resultados_informes['consumos_dispositivos'].clone()
#     suministros_procesado = resultados_informes['consumos_suministros'].clone()

#     consumos_completo = consumos_completo.filter(
#         pl.col("Comprobante").is_in(['SISTEMA DISPENSACION FARMACIA', 'SALIDAS INTERNAS ALMACEN', 'SALIDAS INTERNAS FARMACIA'])
#     )

#     entradas_completo = entradas_completo.filter(
#         pl.col("Comprobante").is_in(['SISTEMA ANULACION DISPENSACION FARMACIA', 'ENTRADAS INTERNAS FARMACIA', 'ENTRADAS INTERNAS SIMA', 'ENTRADAS INTERNAS ALMACEN'])
#     )

#     comsumos_completo = consumos_completo.select(['ValorTotal']).sum().item()
#     entradas_completo = entradas_completo.select(['ValorTotal']).sum().item()

#     print(f"Consumos: {comsumos_completo}")
#     print(f"Entradas: {entradas_completo}")

#     total_limpio = consumos_completo - entradas_completo

#     print(f"Total Limpio: {total_limpio}")

#     medicamentos_procesado = medicamentos_procesado.select(pl.col('ValorNeto').sum().item())
#     dispositivos_procesado = dispositivos_procesado.select(pl.col('ValorNeto').sum().item())
#     suministros_procesado = suministros_procesado.select(pl.col('ValorNeto').sum().item())

#     print(f"Medicamentos: {medicamentos_procesado}")
#     print(f"Dispositivos: {dispositivos_procesado}")
#     print(f"Suministros: {suministros_procesado}")

#     total_procesado = medicamentos_procesado + dispositivos_procesado + suministros_procesado

#     print(f"Total Procesado: {total_procesado}")

#     diferencia = total_limpio - total_procesado

#     if diferencia == 0:
#         print(f"✓ Conciliacion exitosa")
#     else:
#         print(f"✗ Conciliacion fallida y la diferencia es de {diferencia}")

# scripts/conciliacion.py
import math
import polars as pl
from pathlib import Path

HEADER_ROW = 6
COMPROBANTES_CONSUMO = [
    'SISTEMA DISPENSACION FARMACIA',
    'SALIDAS INTERNAS ALMACEN',
    'SALIDAS INTERNAS FARMACIA',
]
COMPROBANTES_ENTRADA = [
    'SISTEMA ANULACION DISPENSACION FARMACIA',
    'ENTRADAS INTERNAS FARMACIA',
    'ENTRADAS INTERNAS SIMA',
    'ENTRADAS INTERNAS ALMACEN',
]
TOLERANCIA = 50.01  # margen aceptable en pesos por redondeo


def _leer_y_sumar_valor(
    ruta: Path,
    comprobantes_validos: list[str],
    columna_comprobante: str = "Comprobante",
    columna_valor: str = "ValorTotal",
) -> float:
    """Lee un excel, filtra por comprobante y devuelve la suma como float. DRY helper."""
    df = pl.read_excel(str(ruta), read_options={"header_row": HEADER_ROW})

    if columna_valor not in df.columns:
        raise KeyError(f"Columna '{columna_valor}' no encontrada en {ruta.name}")

    # Cast explícito: evita que un valor mal tipado degrade la columna a str
    df = df.with_columns(
        pl.col(columna_valor).cast(pl.Float64, strict=False)
    )

    total = (
        df.filter(pl.col(columna_comprobante).is_in(comprobantes_validos))
        .select(pl.col(columna_valor).sum())
        .item()
    )
    return total or 0.0


def _sumar_valor_neto(df: pl.DataFrame, columna: str = "ValorNeto") -> float:
    """Suma segura de un DataFrame ya procesado, devuelve float (no DataFrame)."""
    if columna not in df.columns:
        raise KeyError(f"Columna '{columna}' no encontrada en el informe procesado")
    return df.select(pl.col(columna).sum()).item() or 0.0


def conciliar_informacion(rutas: dict, resultados_informes: dict) -> dict:
    """
    Concilia el total limpio (consumos - entradas) contra el total procesado
    (medicamentos + dispositivos + suministros).

    Returns:
        dict con totales y resultado de la conciliación, o None si falla la lectura.
    """
    if rutas is None:
        print("Error: No se definieron las rutas")
        return None

    try:
        ruta_consumos = Path(rutas["salidas"])
        ruta_entradas = Path(rutas["entradas"])

        total_consumos = _leer_y_sumar_valor(ruta_consumos, COMPROBANTES_CONSUMO)
        total_entradas = _leer_y_sumar_valor(ruta_entradas, COMPROBANTES_ENTRADA)
    except Exception as e:
        print(f"Error leyendo/filtrando archivos: {e}")
        return None

    total_limpio = total_consumos - total_entradas
    print(f"Consumos: {total_consumos:,.2f}")
    print(f"Entradas: {total_entradas:,.2f}")
    print(f"Total Limpio: {total_limpio:,.2f}")

    total_medicamentos = _sumar_valor_neto(resultados_informes["consumos_medicamentos"])
    total_dispositivos = _sumar_valor_neto(resultados_informes["consumos_dispositivos"])
    total_suministros = _sumar_valor_neto(resultados_informes["consumos_suministros"])
    total_procesado = total_medicamentos + total_dispositivos + total_suministros

    print(f"Medicamentos: {total_medicamentos:,.2f}")
    print(f"Dispositivos: {total_dispositivos:,.2f}")
    print(f"Suministros: {total_suministros:,.2f}")
    print(f"Total Procesado: {total_procesado:,.2f}")

    diferencia = total_limpio - total_procesado
    exitosa = math.isclose(diferencia, 0.0, abs_tol=TOLERANCIA)

    if exitosa:
        print("✓ Conciliación exitosa")
    else:
        print(f"✗ Conciliación fallida. Diferencia: {diferencia:,.2f}")

    return {
        "total_consumos": total_consumos,
        "total_entradas": total_entradas,
        "total_limpio": total_limpio,
        "total_procesado": total_procesado,
        "diferencia": diferencia,
        "conciliacion_exitosa": exitosa,
    }


    
