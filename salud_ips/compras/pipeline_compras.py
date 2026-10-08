"""
Módulo principal de orquestación del pipeline de reportes de compras en SaludIPS.

Contiene:
- ComprasPipeline: Clase orquestadora que ejecuta secuencialmente los 3 pasos:
    1. Consolidación de archivos de movimientos de inventario (lectura_archivos.py).
    2. Procesamiento, clasificación y neteo de comprobantes (procesamiento.py).
    3. Análisis financiero y evaluación de compras/proveedores (compras.py).
"""

from pathlib import Path
import sys
import time
import traceback

# Configurar resolución de rutas en sys.path para ejecución directa (botón 'Play')
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Asegurar codificación utf-8 en consola para caracteres especiales en Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import polars as pl

# ──────────────────────────────────────────────
# Imports de los módulos del pipeline
# ──────────────────────────────────────────────

from scripts.lectura_archivos import lectura_archivos_completa
from scripts.procesamiento import procesamiento
from scripts.compras import Analizando_compras
from scripts.saldos_prestamos import analisis_prestamos


# ══════════════════════════════════════════════
# CLASE ORQUESTADORA DEL PIPELINE
# ══════════════════════════════════════════════


class ComprasPipeline:
    """
    Orquesta la ejecución secuencial de los pasos del pipeline de reportes de compras.

    Pasos:
        1. Consolidación de archivos desde la ruta de red de movimientos.
        2. Procesamiento, limpieza y cálculo de netos por tipo de comprobante.
        3. Análisis financiero de compras, proveedores, productos y comportamiento mensual.
    """

    def __init__(self):
        # Resultados intermedios y finales
        self.df_movimientos: pl.DataFrame | None = None
        self.df_compras_aprovechamientos: pl.DataFrame | None = None
        self.df_neto_compras: pl.DataFrame | None = None
        self.df_neto_mov_iniciales: pl.DataFrame | None = None
        self.df_neto_ajustes: pl.DataFrame | None = None
        self.df_neto_prestamos_realizados: pl.DataFrame | None = None
        self.df_neto_prestamos_recibidos: pl.DataFrame | None = None
        self.df_neto_traslados: pl.DataFrame | None = None
        self.df_neto_consumos: pl.DataFrame | None = None
        self.datos_procesados: dict[str, pl.DataFrame] | None = None
        self.resultados_compras: dict[str, pl.DataFrame] | None = None

    def paso1_consolidacion(self) -> pl.DataFrame:
        """Paso 1: Ejecuta la lectura y consolidación diagonal de todos los archivos."""
        print("\n" + "=" * 60)
        print("PASO 1: CONSOLIDADO DE ARCHIVOS")
        print("=" * 60)
        try:
            self.df_movimientos = lectura_archivos_completa()
            total_filas = len(self.df_movimientos) if self.df_movimientos is not None else 0
            print(f"✓ Paso 1 completado exitosamente: {total_filas:,} filas consolidadas.")
            return self.df_movimientos
        except Exception as e:
            print(f"✗ Error en Paso 1 (Consolidación): {e}")
            traceback.print_exc()
            raise

    def paso2_procesamiento(self) -> dict[str, pl.DataFrame]:
        """Paso 2: Ejecuta la clasificación y neteo reutilizando el dataframe consolidado."""
        try:
            self.datos_procesados = procesamiento(self.df_movimientos)
            self.df_compras_aprovechamientos = self.datos_procesados['compras_aprovechamientos']
            self.df_neto_compras = self.datos_procesados['neto_compras']
            self.df_neto_mov_iniciales = self.datos_procesados['neto_mov_iniciales']
            self.df_neto_ajustes = self.datos_procesados['neto_ajustes']
            self.df_neto_prestamos_realizados = self.datos_procesados['neto_prestamos_realizados']
            self.df_neto_prestamos_recibidos = self.datos_procesados['neto_prestamos_recibidos']
            self.df_neto_traslados = self.datos_procesados['neto_traslados']
            self.df_neto_consumos = self.datos_procesados['neto_consumos']
            total_dfs = len(self.datos_procesados) if self.datos_procesados else 0
            print(f"✓ Paso 2 completado exitosamente: {total_dfs} dataframes neteados y procesados.")
            return self.datos_procesados
        except Exception as e:
            print(f"✗ Error en Paso 2 (Procesamiento): {e}")
            traceback.print_exc()
            raise

    def paso3_analisis_compras(self) -> dict[str, pl.DataFrame]:
        """Paso 3: Ejecuta los cálculos analíticos de compras reutilizando los datos procesados."""
        try:
            self.resultados_compras = Analizando_compras(self.df_compras_aprovechamientos)
            total_entregables = len(self.resultados_compras) if self.resultados_compras else 0
            print(f"✓ Paso 3 completado exitosamente: {total_entregables} entregables de análisis generados.")
            return self.resultados_compras
        except Exception as e:
            print(f"✗ Error en Paso 3 (Análisis de Compras): {e}")
            traceback.print_exc()
            raise

    def paso4_analisis_prestamos(self) -> pl.DataFrame:
        """Paso 4: Ejecuta los cálculos analíticos de compras reutilizando los datos procesados."""
        try:
            self.df_prestamos_netos = analisis_prestamos(self.df_neto_prestamos_realizados, self.df_neto_prestamos_recibidos)
            total_entregables = len(self.df_prestamos_netos) if self.df_prestamos_netos else 0
            print(f"✓ Paso 4 completado exitosamente: {total_entregables} entregables de análisis generados.")
            return self.df_prestamos_netos
        except Exception as e:
            print(f"✗ Error en Paso 4 (Análisis de prestamos): {e}")
            traceback.print_exc()
            raise
        

    def ejecutar(self) -> dict:
        """
        Ejecuta todos los pasos del pipeline de compras de forma secuencial y cronometrada.

        Returns:
            dict con los resultados de cada etapa y estado de ejecución.
        """
        t_inicio = time.time()
        print("\n" + "█" * 60)
        print("  PIPELINE DE REPORTES DE COMPRAS - SaludIPS")
        print("█" * 60)

        resultados = {
            'paso_1_consolidacion': None,
            'paso_2_procesamiento': None,
            'paso_3_analisis_compras': None,
            'paso_4_analisis_prestamos': None,
            'exitoso': False,
        }

        try:
            # Paso 1: Consolidación
            resultados['paso_1_consolidacion'] = self.paso1_consolidacion()

            # Paso 2: Procesamiento y neteos
            resultados['paso_2_procesamiento'] = self.paso2_procesamiento()

            # Paso 3: Análisis de compras y proveedores
            resultados['paso_3_analisis_compras'] = self.paso3_analisis_compras()

            # Paso 4: Análisis de prestamos
            resultados['paso_4_analisis_prestamos'] = self.paso4_analisis_prestamos()

            resultados['exitoso'] = True
            duracion = time.time() - t_inicio
            print("\n" + "█" * 60)
            print(f"  ✓ PIPELINE COMPLETADO EXITOSAMENTE en {duracion:.2f}s")
            print("█" * 60)

        except Exception as e:
            duracion = time.time() - t_inicio
            print(f"\n✗ PIPELINE INTERRUMPIDO en: {e} tras {duracion:.2f}s")
            traceback.print_exc()

        return resultados


if __name__ == "__main__":
    pipeline = ComprasPipeline()
    pipeline.ejecutar()