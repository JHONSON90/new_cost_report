from datetime import time
import re
import os 
import sys
from playwright.sync_api import Playwright, sync_playwright, expect


def obtener_fechas_usuario() -> tuple:
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
        
    return fecha_inicio, fecha_fin


def ejecutar_navegacion_nomina(playwright: Playwright) -> None:
    fecha_inicio, fecha_fin = obtener_fechas_usuario()

    browser = playwright.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context()
    page = context.new_page()

    try:
        page.goto("http://192.168.4.214/SaludIPS/Account/Login")
        page.get_by_role("textbox", name="Usuario").click()
        page.get_by_role("textbox", name="Usuario").fill("1085917679")
        page.get_by_role("textbox", name="Usuario").press("Tab")
        page.get_by_role("textbox", name="Password").fill("1087049780")
        page.get_by_role("button", name="Iniciar sesión").click()
        page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Reportes ").click()
        page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Reportes Almacén ").click()
        with page.expect_popup() as page1_info:
            page.locator("#ifrLeft").content_frame.get_by_role("link", name="Movimientos Inventario Detallado por Articulo").click()
        page1 = page1_info.value
        page1.wait_for_load_state("load")
        
        # Esperar a que el selector esté listo y seleccionar la opción "2" (SALIDA)
        page1.wait_for_selector("[id=\"Tipo Movimiento-TipoEntradaSalida\"]")
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
        
        # Ruta de descarga dinámica
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dest_dir = os.path.join(script_dir, "reportes_nomina")
        os.makedirs(dest_dir, exist_ok=True)

        with page1.expect_download() as download_info:
            page1.get_by_role("button", name="Imprimir").click()
        download1 = download_info.value
        nombre_archivo1 = download1.suggested_filename
        download1.save_as(os.path.join(dest_dir, nombre_archivo1))

        # Seleccionar la opción "1" (ENTRADA)
        page1.locator("[id=\"Tipo Movimiento-TipoEntradaSalida\"]").select_option("1")
        page1.evaluate('try { jQuery("[id=\'Tipo Movimiento-TipoEntradaSalida\']").trigger("change"); } catch(e) {}')
        
        with page1.expect_download() as download_info2:
            page1.get_by_role("button", name="Imprimir").click()
        download2 = download_info2.value
        nombre_archivo2 = download2.suggested_filename
        download2.save_as(os.path.join(dest_dir, nombre_archivo2))

        # ---------------------
        context.close()
        browser.close()

    except Exception as error:
        print(f"Error general: {error}")


with sync_playwright() as playwright:
    ejecutar_navegacion_nomina(playwright)



# import re
# from playwright.sync_api import Playwright, sync_playwright, expect


# def run(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#     page.goto("http://192.168.4.214/SaludIPS/Account/Login")
#     page.get_by_role("textbox", name="Usuario").click()
#     page.get_by_role("textbox", name="Usuario").fill("1085917679")
#     page.get_by_role("textbox", name="Usuario").press("Tab")
#     page.get_by_role("textbox", name="Password").fill("1087049780")
#     page.get_by_role("button", name="Iniciar sesión").click()
#     page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Reportes ").click()
#     page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Reportes Almacén ").click()
#     with page.expect_popup() as page1_info:
#         page.locator("#ifrLeft").content_frame.get_by_role("link", name="Movimientos Inventario Detallado por Articulo").click()
#     page1 = page1_info.value
#     page1.locator("[id=\"Tipo Movimiento-TipoEntradaSalida\"]").click()
#     page1.goto("http://192.168.4.214/SaludIPS/Areas/Reportes/?CodReporte=almacenMovimientosInventarioDetalladoArticulo&vigencia=2026")
#     page1.locator("[id=\"Tipo Movimiento-TipoEntradaSalida\"]").select_option("2")
#     with page1.expect_download() as download_info:
#         page1.get_by_role("button", name="Imprimir").click()
#     download = download_info.value
#     page1.get_by_title("SALIDA").click()
#     page1.get_by_role("treeitem", name="ENTRADA").click()
#     page1.locator("#ctl01 div").filter(has_text="Tipo Movimiento: --Todos--").click()
#     with page1.expect_download() as download1_info:
#         page1.get_by_role("button", name="Imprimir").click()
#     download1 = download1_info.value
#     page1.locator("[id=\"Fecha Inicio-Fecha\"]").click()
#     page1.get_by_role("columnheader", name="«").click()
#     page1.get_by_role("cell", name="1").nth(3).click()
#     page1.locator("[id=\"Fecha Final-Fecha\"]").click()
#     page1.get_by_role("columnheader", name="»").click()
#     page1.get_by_role("columnheader", name="«").dblclick()
#     page1.get_by_role("columnheader", name="»").click()
#     page1.get_by_role("cell", name="30").nth(1).click()
#     with page1.expect_download() as download2_info:
#         page1.get_by_role("button", name="Imprimir").click()
#     download2 = download2_info.value
#     page1.locator("[id=\"Fecha Final-Fecha\"]").click()
#     page1.locator("[id=\"Fecha Final-Fecha\"]").press("ArrowLeft")
#     page1.locator("[id=\"Fecha Final-Fecha\"]").press("ArrowLeft")
#     page1.locator("[id=\"Fecha Final-Fecha\"]").press("ArrowLeft")
#     page1.locator("[id=\"Fecha Final-Fecha\"]").press("ArrowLeft")
#     page1.locator("[id=\"Fecha Final-Fecha\"]").fill("30/05/2026")
#     page1.locator("[id=\"Fecha Final-Fecha\"]").press("Enter")
#     page1.locator("[id=\"Fecha Final-Fecha\"]").click()
#     page1.locator("[id=\"Fecha Final-Fecha\"]").click()
#     page1.locator("[id=\"Fecha Final-Fecha\"]").click()

#     # ---------------------
#     context.close()
#     browser.close()


# with sync_playwright() as playwright:
#     run(playwright)
