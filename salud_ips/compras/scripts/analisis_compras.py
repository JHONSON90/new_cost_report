import polars as pl 
import os 
from pathlib import Path

#traer todos los informes de entradas disponibles
ruta = Path("D:/proyectos/Reportes_saludips/consumos")


dataframes = {
    carpeta.name: pl.read_excel(carpeta/f"Informe consumos mes de {carpeta.name} Entradas.xlsx", read_options={"header_row": 6}, sheet_name="Reporte")
    for carpeta in ruta.iterdir()
    if carpeta.is_dir() and (carpeta/f"Informe consumos mes de {carpeta.name} Entradas.xlsx").exists()
}
#concatenando todos los dataframes

consolidado = pl.concat(dataframes.values())

print(consolidado.shape)