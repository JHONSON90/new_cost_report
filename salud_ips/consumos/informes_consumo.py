from datetime import time
import re
import os 
import sys
from playwright.sync_api import Playwright, sync_playwright, expect
import polars as pl 



# def obtener_fechas_usuario() -> tuple:
#     # Valores por defecto
#     fecha_inicio = "01/04/2026"
#     fecha_fin = "30/04/2026"
    
#     # Si se pasaron por argumentos de línea de comandos (ej: python script.py DD/MM/AAAA DD/MM/AAAA)
#     if len(sys.argv) >= 3:
#         fecha_inicio = sys.argv[1]
#         fecha_fin = sys.argv[2]
#         print(f"Usando fechas desde argumentos: Inicio={fecha_inicio}, Fin={fecha_fin}")
#     else:
#         # Preguntar en consola al usuario
#         print("\n=== CONFIGURACIÓN DE FECHAS PARA EL REPORTE ===")
#         try:
#             val_ini = input(f"Ingrese Fecha Inicio (DD/MM/AAAA) [Presione Enter para {fecha_inicio}]: ").strip()
#             if val_ini:
#                 fecha_inicio = val_ini
            
#             val_fin = input(f"Ingrese Fecha Final (DD/MM/AAAA) [Presione Enter para {fecha_fin}]: ").strip()
#             if val_fin:
#                 fecha_fin = val_fin
        
#         except Exception:
#             # En entornos no interactivos o si falla el input, usar valores por defecto
#             pass
#         print(f"Fechas seleccionadas: Inicio={fecha_inicio}, Fin={fecha_fin}\n")
#     mes_Informe = fecha_inicio[3:5]
#     return fecha_inicio, fecha_fin, mes_Informe


# def ejecutar_navegacion_consumos(playwright: Playwright) -> None:
#     fecha_inicio, fecha_fin, mes_Informe = obtener_fechas_usuario()

#     browser = playwright.chromium.launch(headless=False, slow_mo=500)
#     context = browser.new_context()
#     page = context.new_page()

#     try:
#         page.goto("http://192.168.4.214/SaludIPS/Account/Login")
#         page.get_by_role("textbox", name="Usuario").click()
#         page.get_by_role("textbox", name="Usuario").fill("1085917679")
#         page.get_by_role("textbox", name="Usuario").press("Tab")
#         page.get_by_role("textbox", name="Password").fill("1087049780")
#         page.get_by_role("button", name="Iniciar sesión").click()
#         page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Reportes ").click()
#         page.locator("#ifrLeft").content_frame.get_by_role("link", name=" Reportes Almacén ").click()
#         with page.expect_popup() as page1_info:
#             page.locator("#ifrLeft").content_frame.get_by_role("link", name="Movimientos Inventario Detallado por Articulo").click()
#         page1 = page1_info.value
#         page1.wait_for_load_state("load")
        
#         # Esperar a que el selector esté listo y seleccionar la opción "2" (SALIDA)
#         page1.wait_for_selector("[id=\"Tipo Movimiento-TipoEntradaSalida\"]")
#         page1.locator("[id=\"Tipo Movimiento-TipoEntradaSalida\"]").select_option("2")
#         # Forzar el evento de cambio por si select2 requiere actualización
#         page1.evaluate('try { jQuery("[id=\'Tipo Movimiento-TipoEntradaSalida\']").trigger("change"); } catch(e) {}')
        
#         # Establecer las fechas mediante Vanilla JS para evitar que el Datepicker las borre/sobreescriba
#         page1.evaluate(f'document.getElementById("Fecha Inicio-Fecha").value = "{fecha_inicio}"')
#         page1.evaluate(f'document.getElementById("Fecha Final-Fecha").value = "{fecha_fin}"')
        
#         # Disparar eventos para actualizar cualquier widget o validación de formulario
#         page1.evaluate('document.getElementById("Fecha Inicio-Fecha").dispatchEvent(new Event("change"))')
#         page1.evaluate('document.getElementById("Fecha Final-Fecha").dispatchEvent(new Event("change"))')
#         page1.evaluate('try { jQuery("[id=\'Fecha Inicio-Fecha\']").trigger("change"); } catch(e) {}')
#         page1.evaluate('try { jQuery("[id=\'Fecha Final-Fecha\']").trigger("change"); } catch(e) {}')
        
#         # Ruta de descarga dinámica
#         script_dir = os.path.dirname(os.path.abspath(__file__))
#         dest_dir = os.path.join(script_dir, "reportes_consumos")
#         os.makedirs(dest_dir, exist_ok=True)

#         with page1.expect_download() as download_info:
#             page1.get_by_role("button", name="Imprimir").click()
#         download1 = download_info.value
#         nombre_archivo1 = download1.suggested_filename
#         _, extension = os.path.splitext(nombre_archivo1)
#         nuevo_nombre1 = f"Informe consumos {mes_Informe} Salidas{extension}"
#         download1.save_as(os.path.join(dest_dir, nuevo_nombre1))

#         # Seleccionar la opción "1" (ENTRADA)
#         page1.locator("[id=\"Tipo Movimiento-TipoEntradaSalida\"]").select_option("1")
#         page1.evaluate('try { jQuery("[id=\'Tipo Movimiento-TipoEntradaSalida\']").trigger("change"); } catch(e) {}')
        
#         with page1.expect_download() as download_info2:
#             page1.get_by_role("button", name="Imprimir").click()
#         download2 = download_info2.value
#         nombre_archivo2 = download2.suggested_filename
#         _, extension = os.path.splitext(nombre_archivo2)
#         nuevo_nombre2 = f"Informe consumos {mes_Informe} Entradas{extension}"
#         download2.save_as(os.path.join(dest_dir, nuevo_nombre2))

        # page.locator("#ifrLeft").content_frame.get_by_role("link", name="Reportes General").click()
        # page.locator("#ifrLeft").content_frame.locator("#select2-Modulo-container").click()
        # page.locator("#ifrLeft").content_frame.get_by_role("treeitem", name="CONTABILIDAD").click()
        # page.locator("#ifrLeft").content_frame.get_by_role("button", name="Ver Reportes").click()
        # page.locator("#ifrLeft").content_frame.get_by_role("cell", name="AUDITORIACONTABLE").click()
        # with page.expect_popup() as page1_info:
        #     page.locator("#ifrLeft").content_frame.get_by_role("link", description="Generar Reporte", exact=True).click()
        # page1 = page1_info.value
        # TODO: COLOCAR FECHAS COMO EN LA AUTOMATIZACION ANTERIOR
        # page1.locator("[id=\"Fecha Inicio-Fecha\"]").click()
        # page1.locator("input[type=\"search\"]").fill("6135")
        # page1.get_by_role("treeitem", name="6135 - UNIDAD FUNCIONAL DE").click()
        # with page1.expect_download() as download_info:
        #     page1.get_by_role("button", name="Imprimir").click()
        #TODO: HACER FUNCIONAL EL GUARDAR COMO REPORTE SEGUN EL SIGUIENTE CODIGO
        #with page1.expect_download() as download_info:
#             page1.get_by_role("button", name="Imprimir").click()
#         download1 = download_info.value
#         nombre_archivo1 = download1.suggested_filename
#         _, extension = os.path.splitext(nombre_archivo1)
#         nuevo_nombre1 = f"Informe consumos {mes_Informe} Salidas{extension}"
#         download1.save_as(os.path.join(dest_dir, nuevo_nombre1))

#         # ---------------------
#         context.close()
#         browser.close()



#     except Exception as error:
#         print(f"Error general: {error}")


# with sync_playwright() as playwright:
#     ejecutar_navegacion_consumos(playwright)

def leer_informes_consumos():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dest_dir = os.path.join(script_dir, "reportes_consumos")
    #TODO: hacer que el informe sea mas dinamico cambiando el 04 por el mes que el usuario da al inicio
    #TODO: Traer los documentos que tocaron costo segun el otro informe
    salidas = pl.read_excel(os.path.join(dest_dir, "Informe consumos 04 Salidas.xlsx"), read_options={"skip_rows":6, "header_row": None})    
    entradas = pl.read_excel(os.path.join(dest_dir, "Informe consumos mes de 04 Entradas.xlsx"), read_options={"skip_rows":6, "header_row": None}
    )
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

salidas_sin_procesar, entradas_sin_procesar = leer_informes_consumos()
alistamiento_para_informes(entradas_sin_procesar, salidas_sin_procesar)

def encontrar_inconsistencias(entradas_para_procesar, salidas_para_procesar):
    try:
        salidas_para_procesar = salidas_para_procesar.filter(
            
        )
        
    except Exception as error:
        print(f"Error general: {error}")
