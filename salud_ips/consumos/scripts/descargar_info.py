from playwright.sync_api import Playwright, sync_playwright, expect
import polars as pl
from pathlib import Path
from datetime import time
import re
import sys


# ──────────────────────────────────────────────
# Configuración de rutas base
# ──────────────────────────────────────────────
RUTA_BASE_REPORTES = Path(r"D:\proyectos\Reportes_saludips\consumos")


def obtener_fechas_usuario() -> tuple:
    """Solicita o recibe las fechas de inicio y fin del reporte."""
    # Valores por defecto
    fecha_inicio = "01/04/2026"
    fecha_fin = "30/04/2026"
    
    # Si se pasaron por argumentos de línea de comandos (ej: python script.py DD/MM/AAAA DD/MM/AAAA)
    if len(sys.argv) >= 3:
        fecha_inicio = sys.argv[1]
        fecha_fin = sys.argv[2]
        print(f"Usando fechas desde argumentos: Inicio={fecha_inicio}, Fin={fecha_fin}")
    else:
        # Preguntar en consola al usuario
        print("\n=== CONFIGURACIÓN DE FECHAS PARA EL REPORTE ===")
        try:
            val_ini = input(f"Ingrese Fecha Inicio (DD/MM/AAAA) [Presione Enter para {fecha_inicio}]: ").strip()
            if val_ini:
                fecha_inicio = val_ini
            
            val_fin = input(f"Ingrese Fecha Final (DD/MM/AAAA) [Presione Enter para {fecha_fin}]: ").strip()
            if val_fin:
                fecha_fin = val_fin
        
        except Exception:
            # En entornos no interactivos o si falla el input, usar valores por defecto
            pass
        print(f"Fechas seleccionadas: Inicio={fecha_inicio}, Fin={fecha_fin}\n")
    mes_Informe = fecha_inicio[3:5]
    return fecha_inicio, fecha_fin, mes_Informe


def _validar_ruta_destino(ruta_base: Path, mes: str) -> Path:
    """Valida que la ruta base exista y sea escribible, crea subcarpeta del mes."""
    if not ruta_base.parent.exists():
        raise FileNotFoundError(
            f"La ruta padre '{ruta_base.parent}' no existe. "
            f"Verifique que la unidad D: esté montada y la estructura de carpetas sea correcta."
        )
    dest_dir = ruta_base / mes
    dest_dir.mkdir(parents=True, exist_ok=True)
    return dest_dir


def ejecutar_descarga(fecha_inicio: str, fecha_fin: str) -> dict:
    """
    Ejecuta la descarga de reportes desde SaludIPS.
    
    Args:
        fecha_inicio: Fecha de inicio en formato DD/MM/AAAA.
        fecha_fin: Fecha final en formato DD/MM/AAAA.
    
    Returns:
        dict con las rutas de los archivos descargados:
            - 'facturacion': Path al archivo de facturación.
            - 'salidas': Path al archivo de salidas de consumo.
            - 'entradas': Path al archivo de entradas de consumo.
            - 'mes_informe': Mes del informe (str).
            - 'dest_dir': Path del directorio destino.
    """
    mes_informe = fecha_inicio[3:5]
    
    # Validar ruta destino antes de iniciar el browser
    dest_dir = _validar_ruta_destino(RUTA_BASE_REPORTES, mes_informe)
    print(f"Directorio destino validado: {dest_dir}")

    rutas_generadas = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        context.set_default_timeout(600000)
        context.set_default_navigation_timeout(600000)
        page = context.new_page()
        try:
            # ── Login ──
            page.goto("http://192.168.4.214/SaludIPS/Account/Login")
            page.get_by_role("textbox", name="Usuario").click()
            page.get_by_role("textbox", name="Usuario").fill("1085917679")
            page.get_by_role("textbox", name="Usuario").press("Tab")
            page.get_by_role("textbox", name="Password").fill("1087049780")
            page.get_by_role("textbox", name="Password").press("Tab")
            page.get_by_title("Proinsalud S.A - Sede Cumbal").click()
            page.get_by_role("treeitem", name="Proinsalud S.A - Sede Pasto").click()
            page.get_by_role("button", name="Iniciar sesión").click()

            # ── Descarga 1: Facturación ──
            page.goto("http://192.168.4.214/SaludIPS/Areas/Reportes/?CodReporte=SIPS_102-2")
            page.evaluate(f'document.getElementById("Fecha Inicio-Fecha").value = "{fecha_inicio}"')
            page.evaluate(f'document.getElementById("Fecha Final-Fecha").value = "{fecha_fin}"')
            page.evaluate('document.getElementById("Fecha Inicio-Fecha").dispatchEvent(new Event("change"))')
            page.evaluate('document.getElementById("Fecha Final-Fecha").dispatchEvent(new Event("change"))')
            page.evaluate('try { jQuery("[id=\'Fecha Inicio-Fecha\']").trigger("change"); } catch(e) {}')         
            page.evaluate('try { jQuery("[id=\'Fecha Final-Fecha\']").trigger("change"); } catch(e) {}')

            with page.expect_download(timeout=600000) as download_info:
                page.get_by_role("button", name="Imprimir").click()
            download1 = download_info.value
            nombre_archivo1 = download1.suggested_filename
            extension = Path(nombre_archivo1).suffix
            nuevo_nombre1 = f"Facturacion {mes_informe} 2026{extension}"
            ruta_facturacion = dest_dir / nuevo_nombre1
            download1.save_as(str(ruta_facturacion))
            rutas_generadas['facturacion'] = ruta_facturacion
            print(f"  ✓ Facturación descargada: {ruta_facturacion.name}")

            # ── Navegación a Almacén → Reportes ──
            page.goto("http://192.168.4.214/SaludIPS/Home/HC")
            page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Almacén ").click()
            page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Almacén ").click()
            page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Reportes ").click()
            page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Reportes Almacén ").click()
            with page.expect_popup() as page1_info:
                page.locator("#ifrLeft").content_frame.get_by_role("link", name="Movimientos Inventario Detallado por Articulo").click()
            page1 = page1_info.value
            page1.wait_for_load_state("load")
            page1.locator("[id=\"Tipo Movimiento-TipoEntradaSalida\"]").select_option("2")

            # Forzar el evento de cambio por si select2 requiere actualización
            page1.evaluate('try { jQuery("[id=\'Tipo Movimiento-TipoEntradaSalida\']").trigger("change"); } catch(e) {}')
 
            # Establecer las fechas mediante Vanilla JS para evitar que el Datepicker las borre/sobreescriba
            page1.evaluate(f'document.getElementById("Fecha Inicio-Fecha").value = "{fecha_inicio}"')
            page1.evaluate(f'document.getElementById("Fecha Final-Fecha").value = "{fecha_fin}"')
 
            # Disparar eventos para actualizar cualquier widget o validación de formulario
            page1.evaluate('document.getElementById("Fecha Inicio-Fecha").dispatchEvent(new Event("change"))')
            page1.evaluate('document.getElementById("Fecha Final-Fecha").dispatchEvent(new Event("change"))')
            page1.evaluate('try { jQuery("[id=\'Fecha Inicio-Fecha\']").trigger("change"); } catch(e) {}')
            page1.evaluate('try { jQuery("[id=\'Fecha Final-Fecha\']").trigger("change"); } catch(e) {}')

            # ── Descarga 2: Salidas de consumo ──
            with page1.expect_download(timeout=600000) as download_info:
                page1.get_by_role("button", name="Imprimir").click()
            download2 = download_info.value
            nombre_archivo2 = download2.suggested_filename
            extension = Path(nombre_archivo2).suffix
            nuevo_nombre2 = f"Informe consumos {mes_informe} Salidas{extension}"
            ruta_salidas = dest_dir / nuevo_nombre2
            download2.save_as(str(ruta_salidas))
            rutas_generadas['salidas'] = ruta_salidas
            print(f"  ✓ Salidas descargadas: {ruta_salidas.name}")

            # ── Descarga 3: Entradas de consumo ──
            page1.get_by_title("SALIDA").click()
            page1.get_by_role("treeitem", name="ENTRADA").click()

            with page1.expect_download(timeout=600000) as download_info:
                page1.get_by_role("button", name="Imprimir").click()
            download3 = download_info.value
            nombre_archivo3 = download3.suggested_filename
            extension = Path(nombre_archivo3).suffix
            nuevo_nombre3 = f"Informe consumos mes de {mes_informe} Entradas{extension}"
            ruta_entradas = dest_dir / nuevo_nombre3
            download3.save_as(str(ruta_entradas))
            rutas_generadas['entradas'] = ruta_entradas
            print(f"  ✓ Entradas descargadas: {ruta_entradas.name}")

            #listado de inventario
            page.goto('http://192.168.4.214/SaludIPS/Areas/Reportes/?CodReporte=almacenListadoInventario')
            page.wait_for_load_state("load")
            with page.expect_download(timeout=600000) as download_info:
                page.get_by_role("button", name="Imprimir").click()
            download4 = download_info.value
            nombre_archivo4 = download4.suggested_filename
            extension = Path(nombre_archivo4).suffix
            nuevo_nombre4 = f"Listado_Productos {mes_informe}{extension}"
            ruta_salidas = dest_dir / nuevo_nombre4
            download4.save_as(str(ruta_salidas))
            rutas_generadas['listado'] = ruta_salidas
            print(f"  ✓ Listado Productos: {ruta_salidas.name}")

        except Exception as error:
            print(f"Error durante la descarga: {error}")
            raise
        finally:
            # Cierre seguro del browser siempre, con o sin error
            context.close()
            browser.close()

    rutas_generadas['mes_informe'] = mes_informe
    rutas_generadas['dest_dir'] = dest_dir
    print(f"\n✓ Descarga completada. {len(rutas_generadas) - 2} archivos guardados en: {dest_dir}")
    return rutas_generadas


# def run(playwright: Playwright) -> dict:
#     """Función legacy para compatibilidad. Usa obtener_fechas_usuario() para las fechas."""
#     fecha_inicio, fecha_fin, _ = obtener_fechas_usuario()
#     return ejecutar_descarga(fecha_inicio, fecha_fin)


# if __name__ == "__main__":
#     fecha_inicio, fecha_fin, _ = obtener_fechas_usuario()
#     rutas = ejecutar_descarga(fecha_inicio, fecha_fin)
#     print(f"\nRutas generadas: {rutas}")