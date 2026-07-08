"""
Módulo principal de orquestación del pipeline de reportes de consumo SaludIPS.

Contiene:
- ConsumoPipeline: Clase orquestadora que ejecuta los 5 pasos del pipeline.
- leer_informes_consumos: Función utilitaria para lectura directa de archivos.
- alistamiento_para_informes: Función de resumen por municipio/servicio.
"""
from datetime import time
from pathlib import Path
import re
import sys
import traceback

import polars as pl

# ──────────────────────────────────────────────
# Imports de los módulos del pipeline
# ──────────────────────────────────────────────
from scripts.descargar_info import ejecutar_descarga, obtener_fechas_usuario
from scripts.lectura_proceso import cargar_datos
from scripts.revision_informes import revisiones
from scripts.desviaciones import desviaciones
from scripts.informe_consumo import hacer_informe


# ══════════════════════════════════════════════
# CLASE ORQUESTADORA DEL PIPELINE
# ══════════════════════════════════════════════

class ConsumoPipeline:
    """
    Orquesta la ejecución secuencial de los 5 pasos del pipeline de reportes.

    Pasos:
        1. Descarga de archivos desde SaludIPS.
        2. Carga dinámica de datos con las rutas generadas.
        3. Auditoría de inconsistencias en centros de costo.
        4. Análisis de desviaciones estadísticas.
        5. Generación del informe final de consumos.
    """

    def __init__(self, fecha_inicio: str, fecha_fin: str):
        """
        Inicializa el pipeline con las fechas del período a procesar.

        Args:
            fecha_inicio: Fecha inicio en formato DD/MM/AAAA.
            fecha_fin: Fecha fin en formato DD/MM/AAAA.
        """
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.mes_informe = fecha_inicio[3:5]

        # Resultados intermedios de cada paso
        self.rutas_descargadas: dict = {}
        self.consumos_facturacion = None
        self.facturacion_productos = None
        self.entradas = None
        self.listado_productos = None
        self.inconsistencias = None
        self.datos_desviaciones = None
        self.resultados_informe = None

    # ── Paso 1: Descarga ──
    def paso_1_descarga(self) -> dict:
        """Ejecuta la descarga de archivos desde SaludIPS vía Playwright."""
        print("\n" + "=" * 60)
        print("PASO 1: DESCARGA DE ARCHIVOS")
        print("=" * 60)
        try:
            self.rutas_descargadas = ejecutar_descarga(self.fecha_inicio, self.fecha_fin)
            print(f"✓ Paso 1 completado. Archivos: {list(self.rutas_descargadas.keys())}")
            return self.rutas_descargadas
        except Exception as e:
            print(f"✗ Error en Paso 1 (Descarga): {e}")
            traceback.print_exc()
            raise

    # ── Paso 2: Carga dinámica ──
    def paso_2_carga(self, rutas: dict = None) -> tuple:
        """
        Carga los DataFrames usando las rutas del paso 1 o rutas proporcionadas.

        Args:
            rutas: dict con rutas de archivos. Si es None, usa self.rutas_descargadas.
        """
        print("\n" + "=" * 60)
        print("PASO 2: CARGA DINÁMICA DE DATOS")
        print("=" * 60)
        try:
            rutas_a_usar = rutas or self.rutas_descargadas
            if not rutas_a_usar:
                raise ValueError("No hay rutas disponibles. Ejecute paso_1_descarga() primero o proporcione rutas.")

            (self.consumos_facturacion,
             self.facturacion_productos,
             self.entradas,
             self.listado_productos) = cargar_datos(rutas_a_usar)

            print(f"✓ Paso 2 completado.")
            print(f"  - consumos_facturacion: {self.consumos_facturacion.shape}")
            print(f"  - facturacion_productos: {self.facturacion_productos.shape}")
            print(f"  - entradas: {self.entradas.shape}")
            return (self.consumos_facturacion, self.facturacion_productos, 
                    self.entradas, self.listado_productos)
        except Exception as e:
            print(f"✗ Error en Paso 2 (Carga): {e}")
            traceback.print_exc()
            raise

    # ── Paso 3: Auditoría ──
    def paso_3_auditoria(self, consumos_facturados: pl.DataFrame = None) -> pl.DataFrame:
        """
        Ejecuta revisiones de consistencia sobre los consumos facturados.

        Args:
            consumos_facturados: DataFrame de consumos. Si es None, usa self.consumos_facturacion.
        """
        print("\n" + "=" * 60)
        print("PASO 3: AUDITORÍA DE INCONSISTENCIAS")
        print("=" * 60)
        try:
            datos = consumos_facturados if consumos_facturados is not None else self.consumos_facturacion
            if datos is None:
                raise ValueError("No hay datos de consumos. Ejecute paso_2_carga() primero.")

            self.inconsistencias = revisiones(datos)
            print(f"✓ Paso 3 completado. Inconsistencias encontradas: {self.inconsistencias.shape[0]} registros")
            return self.inconsistencias
        except Exception as e:
            print(f"✗ Error en Paso 3 (Auditoría): {e}")
            traceback.print_exc()
            raise

    # ── Paso 4: Desviaciones ──
    def paso_4_desviaciones(self, consumos: pl.DataFrame = None) -> pl.DataFrame:
        """
        Calcula desviaciones estadísticas (moda, media, std) sobre los consumos.

        Args:
            consumos: DataFrame de consumos. Si es None, usa self.consumos_facturacion.
        """
        print("\n" + "=" * 60)
        print("PASO 4: ANÁLISIS DE DESVIACIONES")
        print("=" * 60)
        try:
            datos = consumos if consumos is not None else self.consumos_facturacion
            if datos is None:
                raise ValueError("No hay datos de consumos. Ejecute paso_2_carga() primero.")

            self.datos_desviaciones = desviaciones(datos)
            print(f"✓ Paso 4 completado. Alertas de desviación: {self.datos_desviaciones.shape[0]} registros")
            return self.datos_desviaciones
        except Exception as e:
            print(f"✗ Error en Paso 4 (Desviaciones): {e}")
            traceback.print_exc()
            raise

    # ── Paso 5: Generación de informe ──
    def paso_5_informe(self, consumos: pl.DataFrame = None, entradas: pl.DataFrame = None) -> tuple:
        """
        Genera el informe final de consumos netos (salidas - entradas).

        Args:
            consumos: DataFrame de salidas. Si es None, usa datos del pipeline.
            entradas: DataFrame de entradas. Si es None, usa datos del pipeline.
        """
        print("\n" + "=" * 60)
        print("PASO 5: GENERACIÓN DE INFORME FINAL")
        print("=" * 60)
        try:
            datos_consumos = consumos if consumos is not None else self.consumos_facturacion
            datos_entradas = entradas if entradas is not None else self.entradas
            
            if datos_consumos is None or datos_entradas is None:
                raise ValueError("Faltan datos de consumos y/o entradas. Ejecute paso_2_carga() primero.")

            self.resultados_informe = hacer_informe(datos_consumos, datos_entradas)
            print(f"✓ Paso 5 completado. Informe generado con {len(self.resultados_informe)} componentes.")
            return self.resultados_informe
        except Exception as e:
            print(f"✗ Error en Paso 5 (Informe): {e}")
            traceback.print_exc()
            raise

    # ── Ejecución completa del pipeline ──
    def ejecutar(self, saltar_descarga: bool = False, rutas_manuales: dict = None) -> dict:
        """
        Ejecuta los 5 pasos del pipeline secuencialmente.

        Args:
            saltar_descarga: Si True, omite el paso 1 y usa rutas_manuales o las del paso anterior.
            rutas_manuales: dict con rutas de archivos para saltar la descarga.

        Returns:
            dict con los resultados de cada paso del pipeline.
        """
        print("\n" + "█" * 60)
        print("  PIPELINE DE REPORTES DE CONSUMO - SaludIPS")
        print(f"  Período: {self.fecha_inicio} → {self.fecha_fin}")
        print("█" * 60)

        resultados = {
            'paso_1_descarga': None,
            'paso_2_carga': None,
            'paso_3_auditoria': None,
            'paso_4_desviaciones': None,
            'paso_5_informe': None,
            'exitoso': False,
        }

        try:
            # Paso 1: Descarga
            if not saltar_descarga:
                resultados['paso_1_descarga'] = self.paso_1_descarga()
            else:
                self.rutas_descargadas = rutas_manuales or {}
                print("\n⏭  Paso 1 omitido (saltar_descarga=True)")

            # Paso 2: Carga
            resultados['paso_2_carga'] = self.paso_2_carga(rutas_manuales)

            # Paso 3: Auditoría
            resultados['paso_3_auditoria'] = self.paso_3_auditoria()

            # Paso 4: Desviaciones
            resultados['paso_4_desviaciones'] = self.paso_4_desviaciones()

            # Paso 5: Informe
            resultados['paso_5_informe'] = self.paso_5_informe()

            resultados['exitoso'] = True
            print("\n" + "█" * 60)
            print("  ✓ PIPELINE COMPLETADO EXITOSAMENTE")
            print("█" * 60)

        except Exception as e:
            print(f"\n✗ PIPELINE INTERRUMPIDO en: {e}")
            traceback.print_exc()

        return resultados


# ══════════════════════════════════════════════
# FUNCIONES UTILITARIAS (preservadas del código original)
# ══════════════════════════════════════════════

def leer_informes_consumos():
    """Lee los archivos de salidas y entradas directamente desde la ruta en D:."""
    fecha_inicio, fecha_fin, mes_Informe = obtener_fechas_usuario()
    dest_dir = Path(r"D:\proyectos\Reportes_saludips\consumos") / mes_Informe
    #TODO: Traer los documentos que tocaron costo segun el otro informe
    salidas = pl.read_excel(str(dest_dir / f"Informe consumos {mes_Informe} Salidas.xlsx"), read_options={"skip_rows":6, "header_row": None})    
    entradas = pl.read_excel(str(dest_dir / f"Informe consumos mes de {mes_Informe} Entradas.xlsx"), read_options={"skip_rows":6, "header_row": None})
    nombres_columnas = ['Comprobante','Numero','Fecha','NoDocumento','Proveedor','CentroCosto','Dependencia','Bodega','CodGrupo','Grupo','CodArticulo','Articulo','Cantidad','ValorUnitario','TotalBruto','ValorIVA','ValorDescuento','ValorTotal','Unidad','LaboratorioMarca','Observacion','Usuario','User','FechaDigitacion']
    
    #colocamos la primera fila como nombre de columnas
    mapeo_columnas_salidas = dict(zip(salidas.columns, nombres_columnas))
    mapeo_columnas_entradas = dict(zip(entradas.columns, nombres_columnas))

    # 3. Procesar usando encadenamiento de métodos (Método idóneo en Polars)
    salidas = (
        salidas
        .slice(1) # Extrae desde la fila 1 en adelante (elimina la fila 0 de forma segura)
        .rename(mapeo_columnas_salidas) # Renombra de manera inmutable
    )
    
    entradas = (
        entradas
        .slice(1) 
        .rename(mapeo_columnas_entradas)
    )
    #print(salidas.head(10))
    #print(entradas.head(10))


    salidas = salidas.filter(
        pl.col("Comprobante").is_in([
            "SALIDAS INTERNAS ALMACEN", 
            "SALIDAS INTERNAS FARMACIA", 
            "SISTEMA DISPENSACION FARMACIA",
            ])
    ).with_columns(
        pl.col("Cantidad").cast(pl.Float64).alias("Cantidad"), 
        pl.col("ValorUnitario").cast(pl.Float64).alias("ValorUnitario"),
        pl.col("ValorTotal").cast(pl.Float64).alias("ValorTotal")
    ).with_columns(
        Municipio = pl.col("CentroCosto").str.slice(0, 3),
            Servicio = pl.col("CentroCosto")
                        .str.slice(3)
                        .str.split("-")
                        .list.get(0)
                        .str.strip_chars(),
            Tipo_servicio = pl.col("CentroCosto")
                        .str.split("-")
                        .list.get(1)
                        .str.strip_chars(), 
            Linea_inventario = pl.when(pl.col('CodGrupo').str.starts_with('1'))
                        .then(pl.lit('Medicamentos'))
                        .when(pl.col('CodGrupo').str.starts_with('2'))
                        .then(pl.lit('Dispositivos'))
                        .otherwise(pl.lit('Suministros'))
    )

    entradas = entradas.filter(
        pl.col("Comprobante").is_in([
            'SISTEMA ANULACION DISPENSACION FARMACIA',
            'SISTEMA DEVOLUCION FARMACIA',
            "ENTRADAS INTERNAS FARMACIA",
            'ENTRADAS INTERNAS SIMA'
            ])
    ).with_columns(
        pl.col("Cantidad").cast(pl.Float64).alias("Cantidad"), 
        pl.col("ValorUnitario").cast(pl.Float64).alias("ValorUnitario"),
        pl.col("ValorTotal").cast(pl.Float64).alias("ValorTotal")
    ).with_columns(
        Municipio = pl.col("CentroCosto").str.slice(0, 3),
            Servicio = pl.col("CentroCosto")
                        .str.slice(3)
                        .str.split("-")
                        .list.get(0)
                        .str.strip_chars(),
            Tipo_servicio = pl.col("CentroCosto")
                        .str.split("-")
                        .list.get(1)
                        .str.strip_chars(), 
            Linea_inventario = pl.when(pl.col('CodGrupo').str.starts_with('1'))
                        .then(pl.lit('Medicamentos'))
                        .when(pl.col('CodGrupo').str.starts_with('2'))
                        .then(pl.lit('Dispositivos'))
                        .otherwise(pl.lit('Suministros'))
    )

    #print(f"Columnas salidas: {salidas.columns}, Columnas entradas: {entradas.columns}")  


    return salidas, entradas

#TODO: Revisar como se anularian las dispensaciones y mirar si se vuelven a facturar o no.
#TODO: Cambiar la estructura del archivo(uno la generacion, otro archivo lectura y alistamiento y otro generacion del informe, otro para sacar inconsistencias y unirlos todos en pipeline)


def alistamiento_para_informes(entradas_para_procesar, salidas_para_procesar):
    try:
        consumos_por_mpios_medicamentos = salidas_para_procesar.filter(
            pl.col("Municipio") != "Pas",
            pl.col("Linea_inventario") == "Medicamentos"
        ).group_by("Municipio").agg(
            pl.col("ValorTotal").sum().cast(pl.Int64).alias("valor_total")
        )

        consumos_por_servicio_medicamentos = salidas_para_procesar.filter(
            pl.col("Municipio") == "Pas",
            pl.col("Linea_inventario") == "Medicamentos"
        ).group_by("Servicio").agg(
            pl.col("ValorTotal").sum().cast(pl.Int64).alias("valor_total")
        )

        entradas_por_mpios_medicamentos = entradas_para_procesar.filter(
            pl.col("Municipio") != "Pas",
            pl.col("Linea_inventario") == "Medicamentos"
            
        ).group_by("Municipio").agg(
            pl.col("ValorTotal").sum().cast(pl.Int64).alias("valor_total")
        )

        entradas_por_servicio_medicamentos = entradas_para_procesar.filter(
            pl.col("Municipio") == "Pas",
            pl.col("Linea_inventario") == "Medicamentos"
        ).group_by("Servicio").agg(
            pl.col("ValorTotal").sum().cast(pl.Int64).alias("valor_total")
        )

        print("*"*50)
        print("CONSUMOS POR MUNICIPIO")
        print("*"*50)
        print(consumos_por_mpios_medicamentos)
        print("*"*50)
        print("CONSUMOS POR SERVICIO")
        print("*"*50)
        print(consumos_por_servicio_medicamentos)
        print("*"*50)
        print("ENTRADAS POR MUNICIPIO")
        print("*"*50)

        print(entradas_por_mpios_medicamentos)
        print("*"*50)
        print("ENTRADAS POR SERVICIO")
        print("*"*50)
        print(entradas_por_servicio_medicamentos)
        print("*"*50)
    except Exception as error:
        print(f"Error general: {error}")


def encontrar_inconsistencias(entradas_para_procesar, salidas_para_procesar):
    try:
        salidas_para_procesar = salidas_para_procesar.filter(
            
        )
        
    except Exception as error:
        print(f"Error general: {error}")


# ══════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════

if __name__ == "__main__":
    # Modo pipeline completo
    if "--pipeline" in sys.argv:
        fecha_inicio, fecha_fin, _ = obtener_fechas_usuario()
        pipeline = ConsumoPipeline(fecha_inicio, fecha_fin)
        
        # Si se pasa --sin-descarga, omite el paso 1
        saltar = "--sin-descarga" in sys.argv
        resultados = pipeline.ejecutar(saltar_descarga=saltar)

    else:
        # Modo legacy: ejecutar solo lectura + alistamiento
        salidas_sin_procesar, entradas_sin_procesar = leer_informes_consumos()
        alistamiento_para_informes(entradas_sin_procesar, salidas_sin_procesar)
