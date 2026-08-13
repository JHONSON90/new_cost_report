from importlib import _bootstrap_external
import polars as pl
from pathlib import Path


def cargar_datos(rutas: dict = None):
    """
    Carga y procesa los datos de consumo desde los archivos descargados.
    
    Args:
        rutas: dict con las rutas dinámicas de los archivos. Claves esperadas:
            - 'facturacion': Path al archivo de facturación.
            - 'salidas': Path al archivo de salidas (consumos).
            - 'entradas': Path al archivo de entradas.
            Si es None, usa rutas hardcodeadas legacy (Downloads).
    
    Returns:
        tuple: (consumos_facturacion, facturacion_productos, entradas, listado_productos)
    """
    try:
        if rutas is not None:
            ruta_facturacion = Path(rutas['facturacion'])
            ruta_consumos = Path(rutas['salidas'])
            ruta_entradas = Path(rutas['entradas'])
            # El listado de productos se mantiene como ruta fija por ahora
            ruta_listado_productos = Path(r"C:\Users\COSTOS\Downloads\LISTADO_INVENTARIO-20260618_082554.xlsx")
            print("Nuevas rutas")
        else:
            # Rutas legacy hardcodeadas (fallback)
            ruta_facturacion = Path(r"C:\Users\COSTOS\Downloads\RELACION__DE_FACTURAS_POR_USUARIO_DETALLADO-20260624_023844.xlsx")
            ruta_consumos = Path(r"C:\Users\COSTOS\Downloads\MOVIMIENTOS_INVENTARIO_DETALLADO_POR_ARTICULO-20260618_080915.xlsx")
            ruta_listado_productos = Path(r"C:\Users\COSTOS\Downloads\LISTADO_INVENTARIO-20260618_082554.xlsx")
            ruta_entradas = Path(r"C:\Users\COSTOS\Downloads\MOVIMIENTOS_INVENTARIO_DETALLADO_POR_ARTICULO-20260703_095603.xlsx")
            print("Rutas legacy")

        # Validar existencia de archivos
        for nombre, ruta in [("Facturación", ruta_facturacion), ("Consumos/Salidas", ruta_consumos), 
                             ("Entradas", ruta_entradas), ("Listado Productos", ruta_listado_productos)]:
            if not ruta.exists():
                raise FileNotFoundError(f"Archivo de {nombre} no encontrado: {ruta}")

        #Lectura de archivos
        facturacion = pl.read_excel(str(ruta_facturacion), read_options={"header_row": 6})
        consumos = pl.read_excel(str(ruta_consumos), read_options={"header_row": 6})
        listado_productos = pl.read_excel(str(ruta_listado_productos), read_options={"header_row": 5})
        entradas = pl.read_excel(str(ruta_entradas), read_options={"header_row": 6})

        #Imprimir los df para verificar que se leyeron correctamente
        # print("facturacion: ", facturacion)
        # print("consumos: ", consumos)
        # print("listado_productos: ", listado_productos)
        
    except Exception as e:
        print(f"Error en cargar_datos: {e}")
        raise

    consumos_lectura = consumos.clone()

    #def procesar_datos():
    #TODO: UNIFICAR POR CODIGO DE PRODUCTO LA CANTIDAD DEL CONSUMO O -"Cantidad"

    #region LISTADO DE PRODUCTOS
    listado_productos = listado_productos.select(["Codigo",'Nombre','CodigoGenerico','EstadoArticulo'])

    #region FACTURACION
    facturacion_productos = facturacion.select(["idadmision", 'nofactura', 'idusuario', 'nomtiposervicio','codigo','nombre','cantidad','CantidadSolicitada','vrunitario','vrtotal','Especialidad','MedicoRealiza','MedicoOrdena'])

    facturacion_productos = facturacion_productos.filter(
        pl.col('nomtiposervicio') == "FARMACIA"
    )

    facturacion_productos = facturacion_productos.with_columns(
        pl.col('idusuario').str.slice(2,20).alias('# Identificacion'),
        pl.col('idadmision').cast(pl.Int64)
    )

    #hasta aqui ok

    #region REVISION FACTURACION
    consumos_facturacion = consumos.filter(
        pl.col("Comprobante") == 'SISTEMA DISPENSACION FARMACIA'
    )

    consumos_facturacion = consumos_facturacion.with_columns(
        pl.col('NoDocumento').str.splitn("ADM: ", 2)
        .struct.field('field_1')
        .str.strip_chars()
        .cast(pl.Int32, strict=False)
        .fill_null(0)
    ).with_columns(
        pl.when(pl.col('CodArticulo').str.starts_with("1") == True).then(pl.lit("Medicamentos"))
        .when(pl.col('CodArticulo').str.starts_with("2") == True).then(pl.lit("Dispositivos Medicos"))
        .when(pl.col('CodArticulo').str.starts_with("3") == True).then(pl.lit("Suministros"))
        .otherwise(pl.lit("OTRO"))
        .alias("Clasificacion_consumo")
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
                    .str.strip_chars()
    )

<<<<<<< Updated upstream
    #region Procesamiento y entregables
    #def procesamiento_datos():
    consumos_facturacion = consumos_facturacion.join(listado_productos, left_on="CodArticulo", right_on="Codigo", how="left").with_columns(
=======
def cargar_datos(rutas: dict = None):
    """
    Carga y procesa los datos de consumo desde los archivos descargados.
    
    Args:
        rutas: dict con las rutas dinámicas de los archivos. Claves esperadas:
            - 'facturacion': Path al archivo de facturación.
            - 'salidas': Path al archivo de salidas (consumos).
            - 'entradas': Path al archivo de entradas.
            Si es None, usa rutas hardcodeadas legacy (Downloads).
    
    Returns:
        tuple: (consumos_facturacion, facturacion_productos, entradas, listado_productos)
    """
    try:
        if rutas is not None:
            ruta_facturacion = Path(rutas['facturacion'])
            ruta_consumos = Path(rutas['salidas'])
            ruta_entradas = Path(rutas['entradas'])
            # El listado de productos se mantiene como ruta fija por ahora
            ruta_listado_productos = Path(rutas['listado'])
            print("Nuevas rutas")
        else:
            # Rutas legacy hardcodeadas (fallback)
            ruta_facturacion = Path(r"C:\Users\COSTOS\Downloads\RELACION__DE_FACTURAS_POR_USUARIO_DETALLADO-20260624_023844.xlsx")
            ruta_consumos = Path(r"C:\Users\COSTOS\Downloads\MOVIMIENTOS_INVENTARIO_DETALLADO_POR_ARTICULO-20260618_080915.xlsx")
            ruta_listado_productos = Path(r"C:\Users\COSTOS\Downloads\LISTADO_INVENTARIO-20260618_082554.xlsx")
            ruta_entradas = Path(r"C:\Users\COSTOS\Downloads\MOVIMIENTOS_INVENTARIO_DETALLADO_POR_ARTICULO-20260703_095603.xlsx")
            print("Rutas legacy")

        # Validar existencia de archivos
        for nombre, ruta in [("Facturación", ruta_facturacion), ("Consumos/Salidas", ruta_consumos), 
                             ("Entradas", ruta_entradas), ("Listado Productos", ruta_listado_productos)]:
            if not ruta.exists():
                raise FileNotFoundError(f"Archivo de {nombre} no encontrado: {ruta}")

        #Lectura de archivos
        facturacion = pl.read_excel(str(ruta_facturacion), read_options={"header_row": 6})
        consumos = pl.read_excel(str(ruta_consumos), read_options={"header_row": 6})
        listado_productos = pl.read_excel(str(ruta_listado_productos), read_options={"header_row": 5})
        entradas = pl.read_excel(str(ruta_entradas), read_options={"header_row": 6})
        
    except Exception as e:
        print(f"Error en cargar_datos: {e}")
        raise

    consumos_lectura = consumos.clone()
    #dIvidimos el centro de costo por mpio, servicio y tipo ss
    consumos_lectura_1 = dividir_cc(consumos_lectura)
    entradas_1 = dividir_cc(entradas)

    #TODO: UNIFICAR POR CODIGO DE PRODUCTO LA CANTIDAD DEL CONSUMO O -"Cantidad"

    #region LISTADO DE PRODUCTOS
    listado_productos = listado_productos.select(["Codigo",'Nombre','CodigoGenerico','EstadoArticulo'])

    #region FACTURACION
    facturacion_productos = facturacion.select(["idadmision", 'nofactura', 'idusuario', 'nomtiposervicio','codigo','nombre','cantidad','CantidadSolicitada','vrunitario','vrtotal','Especialidad','MedicoRealiza']).filter(
        pl.col('nomtiposervicio') == "FARMACIA"
    )
    facturacion_productos = facturacion_productos.with_columns(
        pl.col('cantidad').cast(pl.Int64, strict=False),
        pl.col('CantidadSolicitada').cast(pl.Int64, strict=False),
        pl.col('vrunitario').cast(pl.Float64, strict=False),
        pl.col('vrtotal').cast(pl.Float64, strict=False)
    )

    facturacion_productos = facturacion_productos.group_by(["idadmision", 'nofactura', 'idusuario', 'nomtiposervicio','codigo','nombre','Especialidad','MedicoRealiza']).agg(
        pl.col('cantidad').sum().alias('cantidad'),
        pl.col('CantidadSolicitada').sum().alias('CantidadSolicitada'),
        pl.col('vrunitario').mean().alias('vrunitario'),
        pl.col('vrtotal').sum().alias('vrtotal'),
    )

    #sacamos el numero de id del paciente
    facturacion_productos = facturacion_productos.with_columns(
        pl.col('idusuario').str.slice(2,20).alias('# Identificacion'),
        pl.col('idadmision').cast(pl.Int64)
    )

    #region REVISION FACTURACION
    #Sacamos los consumos que son de facturacion
    consumos_facturacion = consumos_lectura_1.filter(
        pl.col("Comprobante") == 'SISTEMA DISPENSACION FARMACIA'
    )

    entradas_de_facturacion = entradas_1.filter(
        pl.col('Comprobante') == "SISTEMA ANULACION DISPENSACION FARMACIA"
    )

    #unimos con codigo del listado de productos
    consumos_facturacion = consumos_facturacion.join(listado_productos, left_on="CodArticulo", right_on="Codigo", how="left")
    #TODO unificar por codigo y eliminar el codarticulo
    consumos_facturacion = consumos_facturacion.group_by(['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'tipo de insumo', 'Unidad', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Clasificacion_consumo', 'Municipio', 'Servicio', 'Tipo_servicio', 'Nombre', 'CodGrupo', 'Grupo', 'CodigoGenerico', 'EstadoArticulo']).agg(
        pl.col('Cantidad').sum().alias('Cantidad'),
        pl.col('ValorUnitario').mean().alias('ValorUnitario'),
        pl.col('TotalBruto').sum().alias('TotalBruto'),
        pl.col('ValorIVA').sum().alias('ValorIVA'),
        pl.col('ValorDescuento').sum().alias('ValorDescuento'),
        pl.col('ValorTotal').sum().alias('ValorTotal'),
    )
    # print("-0"*60)
    # print(f"columnas de consumos_facturacion \n {consumos_facturacion.columns}")
    # print("-0"*60)

    
    consumos_facturacion = consumos_facturacion.with_columns(
        pl.col("CodigoGenerico").cast(pl.Int64)
    )

    entradas_de_facturacion = entradas_de_facturacion.join(listado_productos, left_on="CodArticulo", right_on="Codigo", how="left")

    entradas_de_facturacion = entradas_de_facturacion.group_by(['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'tipo insumo', 'Unidad', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Clasificacion_consumo', 'Municipio', 'Servicio', 'Tipo_servicio', 'Nombre', 'CodGrupo', 'Grupo', 'CodigoGenerico', 'EstadoArticulo']).agg(
        pl.col('Cantidad').sum().alias('Cantidad'),
        pl.col('ValorUnitario').mean().alias('ValorUnitario'),
        pl.col('TotalBruto').sum().alias('TotalBruto'),
        pl.col('ValorIVA').sum().alias('ValorIVA'),
        pl.col('ValorDescuento').sum().alias('ValorDescuento'),
        pl.col('ValorTotal').sum().alias('ValorTotal'),
    )

    entradas_de_facturacion = entradas_de_facturacion.with_columns(
>>>>>>> Stashed changes
        pl.col("CodigoGenerico").cast(pl.Int64)
    )
    consumos_facturacion = consumos_facturacion.with_columns(
        pl.concat_str(['field_1', "CodigoGenerico"], separator="-").alias("ADM-CodGen")
    )

    # print(consumos_facturacion.columns)
    # print(consumos_facturacion.head(5))
    #['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'CodGrupo', 'Grupo', 'CodArticulo', 'Articulo', 'Cantidad', 'ValorUnitario', 'TotalBruto', 'ValorIVA', 'ValorDescuento', 'ValorTotal', 'Unidad', 'LaboratorioMarca', 'Observacion', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Nombre', 'CodigoGenerico', 'EstadoArticulo', 'ADM-CodGen']

    facturacion_productos = facturacion_productos.with_columns(
        pl.concat_str(['idadmision', 'codigo'], separator="-").alias("ADM-CodGen")
    )
    para_entradas_facturacion = facturacion_productos.select(['idadmision', 'Especialidad', 'MedicoRealiza']).unique()

    # print(f"Columnas de facturacion\n {facturacion_productos.columns}")
    # print(f"Columnas de entradas_de_facturacion\n {entradas_de_facturacion.columns}")

    consumos_with_fact = consumos_facturacion.join(facturacion_productos, left_on="ADM-CodGen", right_on="ADM-CodGen", how="left").sort('idadmision')
    consumos_with_fact.write_csv("Revisiondeconsumos_facturacion.csv")

<<<<<<< Updated upstream
=======

    entradas_de_facturacion = entradas_de_facturacion.join(para_entradas_facturacion, left_on="field_1", right_on="idadmision", how="left").with_columns(
        pl.when((pl.col('Servicio') == 'servicio farmaceutico') & (pl.col('MedicoRealiza').is_in(ENTIDADES)))
        .then(pl.lit("servicio farmaceutico"))
        .when((pl.col('Servicio') == "consultas generales") & (~pl.col("Especialidad").is_in(["MEDICINA GENERAL", 'ODONTOLOGIA'])) & (~pl.col('MedicoRealiza').is_in(ENTIDADES)))
        .then(pl.lit("consultas especializadas"))
        .when((pl.col('Servicio') == "consultas especializadas") & (pl.col("Especialidad").is_in(["MEDICINA GENERAL", 'ODONTOLOGIA'])) & (~pl.col('MedicoRealiza').is_in(ENTIDADES)))
        .then(pl.lit("consultas generales"))
        .when((pl.col('Servicio').is_in(["consultas especializadas", 'consultas generales']) & (pl.col("Especialidad") == 'ENFERMERIA') & (~pl.col('MedicoRealiza').is_in(ENTIDADES))))
        .then(pl.lit("pym"))
        .when((pl.col("Especialidad").is_in(["ONCOLOGIA", 'TERAPIAS ONCOLOGICAS'])) & (~pl.col('MedicoRealiza').is_in(ENTIDADES)))
        .then(pl.lit("terapias oncologicas"))
        .otherwise(pl.col('Servicio'))
        .alias("Servicio_Corregido")
    )

>>>>>>> Stashed changes
    consumos_with_fact = consumos_with_fact.with_columns(
        pl.col("vrtotal").cast(pl.Float64),
        pl.col("ValorTotal").cast(pl.Float64),
        pl.col("cantidad").cast(pl.Int64),
        pl.col("CantidadSolicitada").cast(pl.Int64)
    )
    print("✓ Lectura de archivos completada con exito!!")

    #region Limpieza
    #['Comprobante', 'Numero', 'Fecha', 'NoDocumento', 'Proveedor', 'CentroCosto', 'Dependencia', 'Bodega', 'CodGrupo', 'Grupo', 'CodArticulo', 'Articulo', 'Cantidad', 'ValorUnitario', 'TotalBruto', 'ValorIVA', 'ValorDescuento', 'ValorTotal', 'Unidad', 'LaboratorioMarca', 'Observacion', 'Usuario', 'User', 'FechaDigitacion', 'field_1', 'Nombre', 'CodigoGenerico', 'EstadoArticulo', 'ADM-CodGen', 'idadmision', 'nofactura', 'idusuario', 'nomtiposervicio', 'codigo', 'nombre', 'cantidad', 'CantidadSolicitada', 'vrunitario', 'vrtotal', 'Especialidad', 'MedicoRealiza', 'MedicoOrdena', '# Identificacion']

    # print(consumos_facturados.columns)
    # print(consumos_facturados.head(5))

    ENTIDADES  = ['CEDIT  DEL SUR SAS ', 'CENTRO  DE CUIDADOS CARDIOVASCULARES PABON SAS ', 'CENTRO  DE ESPECIALISTAS NUTRICION DIABETES OBESIDAD Y OSTEOPOROSIS SAS', 'CENTRO  HOSPITAL SAN JUAN BAUSTISTA ', 'CHRISTUS  SINERGIA SALUD. SA PASTO ', 'CLINCA  NORTE ESPECIALIDADES SAS ', 'CLINICA  DE OJOS (CLINOJOS) SA ', 'CLINICA  DE ORTOPEDIA Y FRACTURAS TRAUMEDICAL ', 'CLINICA  FUNDONAR ', 'CLINICA  IMBANACO SAS ', 'CLINICA  LAS LAJAS SAS ', 'CLINICA  NUESTRA SEÑORA DE FATIMA SA ', 'CLINICA  OFTALMOLOGICA CALI ', 'CLINICA  OFTALMOLOGICA PAREDES SAS ', 'CLINICA  OFTALMOLOGICA UNIGARRO LTDA ', 'CLINICA  ONCOLOGICA AURORA PASTO SAS ', 'CLINICA  PUENTE DEL MEDIO SAS ', 'CLINICA  SOL DE LOS ANDES SAS ', 'COMPLEMEDICA  SAS ', 'E.S.E  CEHANI ', 'E.S.E  CENTO DE SALUD NUESTRA SEÑORA DEL PILAS DE ALDANA ', 'E.S.E  CENTRO DE SALUD ANCUYA ', 'E.S.E  CENTRO DE SALUD BELEN ', 'E.S.E  CENTRO DE SALUD CONSACA ', 'E.S.E  CENTRO DE SALUD DE SAN BARTOLOME DE CORDOBA ', 'E.S.E  CENTRO DE SALUD EL ROSARIO ', 'E.S.E  CENTRO DE SALUD GUACHAVES ', 'E.S.E  CENTRO DE SALUD ILES ', 'E.S.E  CENTRO DE SALUD LA BUENA ESPERANZA ', 'E.S.E  CENTRO DE SALUD SAN BERNARDO ', 'E.S.E  CENTRO DE SALUD SAN FRANCISCO ', 'E.S.E  CENTRO DE SALUD SAN JUAN BAUTISTA DE PUPIALES ', 'E.S.E  CENTRO DE SALUD SAN LORENZO ', 'E.S.E  CENTRO DE SALUD SAN MIGUEL ', 'E.S.E  CENTRO DE SALUD SEÑOR DEL MAR ', 'E.S.E  CENTRO DE SALUD TABLON DE GOMEZ ', 'E.S.E  CENTRO HOSPITAL DIVINO NIÑO ', 'E.S.E  CENTRO HOSPITAL GUAITARILLA ', 'E.S.E  CENTRO HOSPITAL LUIS ANTONIO MONTERO ', 'E.S.E  CENTRO HOSPITAL NUESTRO SEÑOR  DE LA DIVINA MISERICORDIA PUERRES', 'E.S.E  HOSPITAL CIVIL DE IPIALES ', 'E.S.E  HOSPITAL CLARITA SANTOS DE SANDONA ', 'E.S.E  HOSPITAL CUMBAL ', 'E.S.E  HOSPITAL EDUARDO SANTOS ', 'E.S.E  HOSPITAL GUACHUCAL ', 'E.S.E  HOSPITAL SAN ANDRES ', 'E.S.E  HOSPITAL SAN CARLOS ', 'E.S.E  HOSPITAL UNIVERSITARIO DEL VALLE EVARISTO GARCIA ', 'E.S.E  JUAN PABLO SEGUNDO DE LINARES ', 'E.S.E  SAN PEDRO DE CUMBITARA ', 'E.S.E  VIRGEN DE LOURDES BUESACO ', 'ECOGRAFIAS  OBSTETRICAS ', 'ELECTROS  TUQUERRES ', 'FUNDACION  HOSPITAL INFANTIL LOS ANGELES ', 'FUNDACION  HOSPITAL SAN PEDRO ', 'FUNDACION  SANTA FE DE BOGOTA ', 'FUNDACION  VALLE DE LILI ', 'HOSPITAL  DEPARTAMENTAL DE NARIÑO SAS ', 'HOSPITAL  LORENCITA VILLEGAS DE SANTOS ', 'HOSPITAL  MENTAL PERPETUO SOCORRO ', 'HOSPITAL  SAN RAFAEL DE PASTO ', 'INSTITUTO  NEUROCIENCIAS DE NARIÑO IPS SAS ', 'INSTITUTO  PARA NIÑOS CIEGOS Y SORDOS DEL VALLE DEL CAUCA ', 'IPS  MEDICALFISIO ', 'IPS  SALUD DE LOS ANDES SAS ', 'IPS  UNIMEDIC SAS ', 'IPS  UNION SALUD SAS ', 'MEDINUCLEAR  SAS ', 'NEURO  CENTRO COLOMBIA SAS ', 'NEURO  CLINICA SAS ', 'PASTO  FUNDACION CONEXION SALUD ', 'PRAXIS  CENTRO DE REHABILITACION FUNCIONAL ', 'RED  MEDICROM IPS HOSPITAL SAN JOSE ', 'SERVICIO  INTEGRAL DE REUMATOLOGIA E INMUNOLOGIA SAS ', 'UNIDAD  CARDIOQUIRURGICA DE NARIÑO SAS ', 'UNIDAD  DE FISIATRIA Y ORTHOINTEGRAL SAS ', 'UNIDAD  MEDICA UROLOGICA DE NARIÑO UROLAN SAS ', 'UNIDAD  PEDIATRICA DEL SUR ', 'UNIDAD  RENAL NEFRODIAL ', 'VIDA  EN CASA SAS ']


    limpieza_consumos_facturacion = consumos_with_fact.with_columns(
        pl.when((pl.col('Servicio') == 'servicio farmaceutico') & (pl.col('MedicoRealiza').is_in(ENTIDADES)))
        .then(pl.lit("servicio farmaceutico"))
        .when((pl.col('Servicio') == "consultas generales") & (~pl.col("Especialidad").is_in(["MEDICINA GENERAL", 'ODONTOLOGIA'])) & (~pl.col('MedicoRealiza').is_in(ENTIDADES)))
        .then(pl.lit("consultas especializadas"))
        .when((pl.col('Servicio') == "consultas especializadas") & (pl.col("Especialidad").is_in(["MEDICINA GENERAL", 'ODONTOLOGIA'])) & (~pl.col('MedicoRealiza').is_in(ENTIDADES)))
        .then(pl.lit("consultas generales"))
        .when((pl.col('Servicio').is_in(["consultas especializadas", 'consultas generales']) & (pl.col("Especialidad") == 'ENFERMERIA') & (~pl.col('MedicoRealiza').is_in(ENTIDADES))))
        .then(pl.lit("pym"))
        .when((pl.col("Especialidad").is_in(["ONCOLOGIA", 'TERAPIAS ONCOLOGICAS'])) & (~pl.col('MedicoRealiza').is_in(ENTIDADES)))
        .then(pl.lit("terapias oncologicas"))
        .otherwise(pl.col('Servicio'))
        .alias("Servicio_Corregido")
    )
    anulados_limpieza = limpieza_consumos_facturacion.filter(pl.col('MedicoRealiza').is_null()).select(
        ['Comprobante','Numero','Fecha','CentroCosto','Dependencia','Bodega','CodGrupo','Grupo','codigo', 'Nombre','Cantidad','ValorUnitario','TotalBruto','ValorIVA','ValorDescuento','ValorTotal','ADM-CodGen','idadmision','nofactura','idusuario','nomtiposervicio']
    )
    #print(f"\n\nAnulados: \n{anulados_limpieza}")
    #para pasar a facturacion y solicitar cerrar esas facturas
    # anulados_limpieza.write_excel("anulados_limpieza_24-06-2026.xlsx")
    #print(limpieza_consumos_facturacion.filter(pl.col('MedicoRealiza').is_not_null()))
    #print(limpieza_consumos_facturacion.shape)

<<<<<<< Updated upstream
    consumos_de_facturacion = limpieza_consumos_facturacion.group_by(["CentroCosto","Municipio","Servicio_Corregido", "Especialidad"]).agg(
        pl.col('ValorTotal').sum().cast(pl.Int64)
=======
    consumos_de_facturacion = limpieza_consumos_facturacion.with_columns(
        pl.when(pl.col("Servicio_Corregido").is_in(["consultas generales", "consultas especializadas"]))
        .then(pl.col('Especialidad'))
        .otherwise(pl.col('Servicio_Corregido'))
        .alias('Especialidad')
    )
    # .group_by(["CentroCosto","Municipio","Servicio_Corregido", "Especialidad"]).agg(
    #     pl.col('ValorTotal').sum().cast(pl.Int64)
    # )

    salidas_consumo = consumos_lectura_1.filter(
        pl.col("Comprobante").is_in(['SALIDAS INTERNAS ALMACEN', 'SALIDAS INTERNAS FARMACIA'])
    )

    entradas_consumo = entradas_1.filter(
        pl.col('Comprobante').is_in(['ENTRADAS INTERNAS FARMACIA', 'ENTRADAS INTERNAS SIMA', 'ENTRADAS INTERNAS ALMACEN'])
>>>>>>> Stashed changes
    )

    print("✓ Limpieza de archivos completada con exito!!")
    #print(f"\n\nConsumos de facturación:\n{consumos_de_facturacion}")

<<<<<<< Updated upstream
    return consumos_de_facturacion, facturacion_productos, entradas, listado_productos, anulados_limpieza, limpieza_consumos_facturacion, consumos_lectura
=======
    return consumos_de_facturacion, anulados_limpieza, limpieza_consumos_facturacion, salidas_consumo, entradas_de_facturacion, entradas_consumo
>>>>>>> Stashed changes
