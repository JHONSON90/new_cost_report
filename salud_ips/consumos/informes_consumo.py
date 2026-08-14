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
import xlsxwriter


import polars as pl
import pandas as pd

# ──────────────────────────────────────────────
# Imports de los módulos del pipeline
# ──────────────────────────────────────────────
from scripts.descargar_info import ejecutar_descarga, obtener_fechas_usuario
from scripts.lectura_proceso import cargar_datos
from scripts.revision_informes import revisiones
from scripts.desviaciones import desviaciones
from scripts.informe_consumo import hacer_informe
from scripts.rentabilidad import realizar_rentabilidad
from scripts.conciliacion import conciliar_informacion
from scripts.analisis_financiero import generar_informe_financiero


# ══════════════════════════════════════════════
# CLASE ORQUESTADORA DEL PIPELINE
# ══════════════════════════════════════════════

class ConsumoPipeline:
    """
    Orquesta la ejecución secuencial de los 8 pasos del pipeline de reportes.

    Pasos:
        1. Descarga de archivos desde SaludIPS.
        2. Carga dinámica de datos con las rutas generadas.
        3. Auditoría de inconsistencias en centros de costo.
        4. Análisis de desviaciones estadísticas.
        5. Generación del informe final de consumos.
        6. Generación del informe de rentabilidad.
        7. Conciliación de totales.
        8. Análisis financiero (varianza proveedor, eficiencia stock, gap facturación).
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
        self.ruta_informes = None
        self.consumos_facturacion = None
        self.anulados_limpieza = None
        self.limpieza_consumos_facturacion = None
        self.salidas_consumo = None
        self.entradas_facturacion = None
        self.entradas_consumo = None
        self.inconsistencias = None
        self.datos_desviaciones = None
        self.resultados_informe = None
        self.rentabilidad = None
        self.analisis_financiero = None

    def _crear_carpeta_informes(self, rutas=None) -> Path:
        """
        Crea la carpeta 'informes' en la misma carpeta donde están los archivos descargados.
        """
        rutas = rutas or self.rutas_descargadas

        if not rutas:
            raise ValueError("No hay rutas disponibles para crear la carpeta de informes.")

        # Si rutas es dict, tomamos sus valores
        valores = rutas.values() if isinstance(rutas, dict) else rutas

        # Tomamos la primera ruta válida
        ruta_referencia = next((Path(r) for r in valores if r), None)

        if ruta_referencia is None:
            raise ValueError("No se encontró ninguna ruta válida.")

        # Si la ruta es un archivo, usamos su carpeta padre
        carpeta_base = ruta_referencia if ruta_referencia.is_dir() else ruta_referencia.parent

        # Creamos carpeta informes
        ruta_informes = carpeta_base / "informes"
        ruta_informes.mkdir(parents=True, exist_ok=True)

        return ruta_informes


    def _texto_archivo_seguro(self, texto: str) -> str:
        """
        Limpia texto para usarlo como nombre de archivo.
        Evita problemas con /, \\, :, *, ?, etc.
        """
        return re.sub(r'[<>:"/\\|?*]+', "-", str(texto))


    def _rango_fechas_archivo(self) -> str:
        """
        Devuelve las fechas en formato seguro para nombre de archivo.
        """
        inicio = self._texto_archivo_seguro(self.fecha_inicio)
        fin = self._texto_archivo_seguro(self.fecha_fin)
        return f"{inicio}_{fin}"

    # ── Paso 1: Descarga ──
    def paso_1_descarga(self) -> dict:
        """Ejecuta la descarga de archivos desde SaludIPS vía Playwright."""
        print("\n" + "=" * 60)
        print("PASO 1: DESCARGA DE ARCHIVOS")
        print("=" * 60)
        try:
            rutas_para_no_descargar = {'facturacion': r'D:/proyectos/Reportes_saludips/consumos/07/Facturacion 07 2026.xlsx', 'salidas': r'D:/proyectos/Reportes_saludips/consumos/07/Informe consumos 07 Salidas.xlsx', 'entradas': r'D:/proyectos/Reportes_saludips/consumos/07/Informe consumos mes de 07 Entradas.xlsx', 'listado': r'D:/proyectos/Reportes_saludips/consumos/07/Listado_Productos 07.xlsx', 'mes_informe': '07', 'dest_dir': r'D:/proyectos/Reportes_saludips/consumos/07'}
            #self.rutas_descargadas = ejecutar_descarga(self.fecha_inicio, self.fecha_fin)
            self.rutas_descargadas = rutas_para_no_descargar
            print(f"✓ Paso 1 completado. Archivos: {list(self.rutas_descargadas.keys())}")
            print(f"rutas para colocar en vez del paso 1: \n{self.rutas_descargadas}")
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
            self.ruta_informes = self._crear_carpeta_informes(rutas_a_usar)

            (self.consumos_de_facturacion,
             self.anulados_limpieza, 
             self.limpieza_consumos_facturacion, 
             self.salidas_consumo,
             self.entradas_facturacion,
             self.entradas_consumo
             ) = cargar_datos(rutas_a_usar)

            print(f"✓ Paso 2 completado.")
            print(f"  - consumos_facturacion: {self.consumos_de_facturacion.shape}")
            print(f"  - Medicos Nullos: {self.anulados_limpieza.shape}")
            print(f"  - limpieza_consumos_facturacion: {self.limpieza_consumos_facturacion.shape}")
            print(f"  - salidas_consumos: {self.salidas_consumo.shape}")
            print(f"  - Entradas Facturacion: {self.entradas_facturacion.shape}")
            print(f"  - Entradas consumo: {self.entradas_consumo.shape}")

            ruta_informes = self.ruta_informes or self._crear_carpeta_informes()
            nombre_archivo = f"Medicos nullos {self._rango_fechas_archivo()}.xlsx"
            ruta_salida = ruta_informes / nombre_archivo

            self.anulados_limpieza.write_excel(str(ruta_salida))
            print(f"✓ Inconsistencias guardadas en: {ruta_salida}")

            return (self.consumos_de_facturacion, self.anulados_limpieza, self.limpieza_consumos_facturacion, self.salidas_consumo, self.entradas_facturacion, self.entradas_consumo)
        except Exception as e:
            print(f"✗ Error en Paso 2 (Carga): {e}")
            traceback.print_exc()
            raise

    # ── Paso 3: Auditoría ──
    def paso_3_auditoria(self, limpieza_consumos_facturacion: pl.DataFrame = None) -> pl.DataFrame:
        """
        Ejecuta revisiones de consistencia sobre los consumos facturados.

        Args:
            limpieza_consumos_facturacion: DataFrame de consumos. Si es None, usa self.limpieza_consumos_facturacion.
        """
        print("\n" + "=" * 60)
        print("PASO 3: AUDITORÍA DE INCONSISTENCIAS")
        print("=" * 60)
        try:
            datos = limpieza_consumos_facturacion if limpieza_consumos_facturacion is not None else self.limpieza_consumos_facturacion
            if datos is None:
                raise ValueError("No hay datos de consumos. Ejecute paso_2_carga() primero.")

            self.inconsistencias = revisiones(datos)
            print(f"✓ Paso 3 completado. Inconsistencias encontradas: {self.inconsistencias.shape[0]} registros")

            ruta_informes = self.ruta_informes or self._crear_carpeta_informes()
            nombre_archivo = f"inconsistencias_{self._rango_fechas_archivo()}.xlsx"
            ruta_salida = ruta_informes / nombre_archivo

            self.inconsistencias.write_excel(str(ruta_salida))
            print(f"✓ Paso 3 completado. Inconsistencias guardadas en: {ruta_salida}")
            return self.inconsistencias
        except Exception as e:
            print(f"✗ Error en Paso 3 (Auditoría): {e}")
            traceback.print_exc()
            raise
        
    # ── Paso 4: Desviaciones ──
    def paso_4_desviaciones(self, limpieza_consumos_facturacion: pl.DataFrame = None) -> pl.DataFrame:
        """
        Calcula desviaciones estadísticas (moda, media, std) sobre los consumos.

        Args:
            consumos: DataFrame de consumos. Si es None, usa self.consumos_facturacion.
        """
        print("\n" + "=" * 60)
        print("PASO 4: ANÁLISIS DE DESVIACIONES")
        print("=" * 60)
        try:
            datos = limpieza_consumos_facturacion if limpieza_consumos_facturacion is not None else self.limpieza_consumos_facturacion
            if datos is None:
                raise ValueError("No hay datos de consumos. Ejecute paso_2_carga() primero.")

            self.datos_desviaciones = desviaciones(datos)
            ruta_informes = self.ruta_informes or self._crear_carpeta_informes()
            nombre_archivo = f"desviaciones_{self._rango_fechas_archivo()}.xlsx"
            ruta_salida = ruta_informes / nombre_archivo

            self.datos_desviaciones.write_excel(str(ruta_salida))
            print(f"✓ Paso 4 completado. Alertas de desviación: {self.datos_desviaciones.shape[0]} registros")
            return self.datos_desviaciones
        except Exception as e:
            print(f"✗ Error en Paso 4 (Desviaciones): {e}")
            traceback.print_exc()
            raise

    # ── Paso 5: Generación de informe ──
    def paso_5_informe(self, consumos_de_facturacion: pl.DataFrame = None, entradas_facturacion: pl.DataFrame = None, salidas_consumo: pl.DataFrame = None, entradas_consumo: pl.DataFrame = None) -> tuple:
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
            datos_consumos_facturacion = consumos_de_facturacion if consumos_de_facturacion is not None else self.consumos_de_facturacion
            datos_entradas_facturacion = entradas_facturacion if entradas_facturacion is not None else self.entradas_facturacion
            datos_salidas_consumo = salidas_consumo if salidas_consumo is not None else self.salidas_consumo
            datos_entradas_consumo = entradas_consumo if entradas_consumo is not None else self.entradas_consumo

            
            if datos_consumos_facturacion is None or datos_entradas_facturacion is None or datos_salidas_consumo is None or datos_entradas_consumo is None:
                raise ValueError("Faltan datos de consumos y/o entradas. Ejecute paso_2_carga() primero.")

            self.resultados_informe = hacer_informe(datos_consumos_facturacion, datos_entradas_facturacion, datos_salidas_consumo, datos_salidas_consumo)
            
            ruta_informes = self.ruta_informes or self._crear_carpeta_informes()
            nombre_archivo = f"informe_{self._rango_fechas_archivo()}.xlsx"
            ruta_salida = ruta_informes / nombre_archivo

            if isinstance(self.resultados_informe, dict):
                with pd.ExcelWriter(str(ruta_salida), engine='xlsxwriter') as writer:
                    for nombre_sheet, df_sheet in self.resultados_informe.items():

                        df_sheet.to_pandas().to_excel(writer, sheet_name=nombre_sheet[:31], index=False)
                        print(f"✓ Paso 5 completado. Guardado en: {ruta_salida}")
                        print(f"  - Hojas: {list(self.resultados_informe.keys())}")
            else:
                self.resultados_informe.to_pandas().to_excel(str(ruta_salida), index=False)
            print(f"✓ Paso 5 completado. Informe generado con {len(self.resultados_informe)} componentes.")
            return self.resultados_informe
        except Exception as e:
            print(f"✗ Error en Paso 5 (Informe): {e}")
            traceback.print_exc()
            raise

    # ── Paso 6: Generación de informe de rentabilidad ──

    def informe_rentabilidad(self, consumos_de_facturacion: pl.DataFrame = None, entradas_facturacion: pl.DataFrame = None) -> pl.DataFrame:
        print("\n" + "=" * 60)
        print("PASO 6: GENERACIÓN DE INFORME DE RENTABILIDAD")
        print("=" * 60)
        try:
            datos_limpios = consumos_de_facturacion if consumos_de_facturacion is not None else self.consumos_de_facturacion
            datos_devoluciones = entradas_facturacion if entradas_facturacion is not None else self.entradas_facturacion
            
            if datos_limpios is None:
                raise ValueError("Faltan datos de medicamentos facturacion. Ejecute paso_5_informe() primero.")

            self.rentabilidad = realizar_rentabilidad(datos_devoluciones, datos_limpios)
            
            ruta_informes = self.ruta_informes or self._crear_carpeta_informes()
            nombre_archivo = f"informe_rentabilidad_{self._rango_fechas_archivo()}.xlsx"
            
            ruta_salida = ruta_informes / nombre_archivo

            self.rentabilidad.write_excel(str(ruta_salida))
            print(f"✓ Paso 6 completado. Informe de rentabilidad guardado en: {ruta_salida}")
            return self.rentabilidad
        except Exception as e:
            print(f"✗ Error en Paso 6 (Informe): {e}")
            traceback.print_exc()
            raise
    
    # ── Paso 7: Conciliación ──
    def conciliacion(self, rutas: dict = None, resultados_informes: dict = None) -> dict:
        """Conciliación de los datos de consumos usando las rutas del paso 1 o rutas proporcionadas."""
        print("\n" + "=" * 60)
        print("PASO 7: CONCILIACIÓN")
        print("=" * 60)
        try:
            rutas_a_usar = rutas or self.rutas_descargadas
            resultados_a_usar = resultados_informes or self.resultados_informe

            if not rutas_a_usar:
                raise ValueError("No hay rutas disponibles. Ejecute paso_1_descarga() primero o proporcione rutas.")
            if not resultados_a_usar:
                raise ValueError("No hay resultados disponibles. Ejecute paso_5_informe() primero o proporcione los resultados del informe.")

            resultado = conciliar_informacion(rutas_a_usar, resultados_a_usar)
            if resultado is None:
                raise RuntimeError("La conciliación no pudo completarse (ver logs anteriores).")

            print(f"✓ Paso 7 completado. Conciliación realizada")
            return resultado
        except Exception as e:
            print(f"✗ Error en Paso 7 (Conciliación): {e}")
            traceback.print_exc()
            raise

    # ── Paso 8: Análisis Financiero ──
    def paso_8_analisis_financiero(
        self,
        consumos: pl.DataFrame = None,
        entradas: pl.DataFrame = None,
        facturacion: pl.DataFrame = None
    ) -> dict:
        """
        Genera análisis financiero avanzado: varianza proveedor, eficiencia stock, gap facturación.
        
        Args:
            consumos: DataFrame combinado de consumos (facturación + salidas). Si None, usa datos del pipeline.
            entradas: DataFrame combinado de entradas (facturación + consumo). Si None, usa datos del pipeline.
            facturacion: DataFrame de facturación con detalle por admisión. Si None, usa consumos_de_facturacion.
        """
        print("\n" + "=" * 60)
        print("PASO 8: ANÁLISIS FINANCIERO")
        print("=" * 60)
        try:
            # Combinar consumos: facturación + salidas internas
            datos_consumos = consumos if consumos is not None else None
            if datos_consumos is None:
                if self.limpieza_consumos_facturacion is not None and self.salidas_consumo is not None:
                    datos_consumos = pl.concat([
                        self.limpieza_consumos_facturacion,
                        self.salidas_consumo
                    ], how="diagonal_relaxed")
                else:
                    raise ValueError("Faltan datos de consumos. Ejecute paso_2_carga() primero.")
            
            # Combinar entradas: facturación + entradas internas
            datos_entradas = entradas if entradas is not None else None
            if datos_entradas is None:
                if self.entradas_facturacion is not None and self.entradas_consumo is not None:
                    datos_entradas = pl.concat([
                        self.entradas_facturacion,
                        self.entradas_consumo
                    ], how="diagonal_relaxed")
                else:
                    raise ValueError("Faltan datos de entradas. Ejecute paso_2_carga() primero.")
            
            # Facturación para gap analysis (usa consumos_de_facturacion que ya tiene join con facturación)
            datos_facturacion = facturacion if facturacion is not None else self.consumos_de_facturacion
            if datos_facturacion is None:
                raise ValueError("Faltan datos de facturación. Ejecute paso_2_carga() primero.")
            
            ruta_informes = self.ruta_informes or self._crear_carpeta_informes()
            nombre_archivo = f"analisis_financiero_{self._rango_fechas_archivo()}.xlsx"
            ruta_salida = ruta_informes / nombre_archivo
            
            self.analisis_financiero = generar_informe_financiero(
                consumos=datos_consumos,
                entradas=datos_entradas,
                facturacion=datos_facturacion,
                ruta_salida=ruta_salida
            )
            
            print(f"✓ Paso 8 completado. Análisis financiero guardado en: {ruta_salida}")
            print(f"  - Hojas: Varianza_Proveedor, Eficiencia_Stock (Detalle/Resumen), Gap_Fact_Consumo (Detalle/Resumen/Alertas)")
            return self.analisis_financiero
            
        except Exception as e:
            print(f"✗ Error en Paso 8 (Análisis Financiero): {e}")
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
            'paso_6_rentabilidad': None,
            'paso_7_conciliacion': None,
            'paso_8_analisis_financiero': None,
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

            # Paso 6: Informe de rentabilidad
            resultados['paso_6_rentabilidad'] = self.informe_rentabilidad()

            # Paso 7: Conciliación
            resultados['paso_7_conciliacion'] = self.conciliacion() 

            # Paso 8: Análisis Financiero
            resultados['paso_8_analisis_financiero'] = self.paso_8_analisis_financiero()

            resultados['exitoso'] = True
            print("\n" + "█" * 60)
            print("  ✓ PIPELINE COMPLETADO EXITOSAMENTE")
            print("█" * 60)

        except Exception as e:
            print(f"\n✗ PIPELINE INTERRUMPIDO en: {e}")
            traceback.print_exc()

        return resultados

# ══════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════

if __name__ == "__main__":
    # Modo pipeline completo
    # if "--pipeline" in sys.argv:
    #     fecha_inicio, fecha_fin, _ = obtener_fechas_usuario()
    #     pipeline = ConsumoPipeline(fecha_inicio, fecha_fin)
        
    #     # Si se pasa --sin-descarga, omite el paso 1
    #     saltar = "--sin-descarga" in sys.argv
    #     resultados = pipeline.ejecutar(saltar_descarga=saltar)

    # else:
    #     # Modo legacy: ejecutar solo lectura + alistamiento
    #     salidas_sin_procesar, entradas_sin_procesar = leer_informes_consumos()
    #     alistamiento_para_informes(entradas_sin_procesar, salidas_sin_procesar)

    if "--legacy" in sys.argv:
        # Modo legacy: ejecutar solo lectura + alistamiento
        salidas_sin_procesar, entradas_sin_procesar = leer_informes_consumos()
        alistamiento_para_informes(entradas_sin_procesar, salidas_sin_procesar)
    else:
        fecha_inicio, fecha_fin, _ = obtener_fechas_usuario()
        pipeline = ConsumoPipeline(fecha_inicio, fecha_fin)
 
        # Si se pasa --sin-descarga, omite el paso 1
        saltar = "--sin-descarga" in sys.argv
        resultados = pipeline.ejecutar(saltar_descarga=saltar)
