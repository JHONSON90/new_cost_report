# pyrefly: ignore [missing-import]
import polars as pl 


def revisiones(consumos_facturados: pl.DataFrame) -> pl.DataFrame:

    revision_centros_costos = consumos_facturados.select(['CentroCosto', 'Municipio','Servicio','Tipo_servicio', 'Especialidad', 'MedicoRealiza', 'MedicoOrdena'])

    #Medicina General y odontologia
    revision_cg = revision_centros_costos.filter(
        (pl.col("Servicio") == "consultas generales") & 
        (~pl.col("Especialidad").is_in(["MEDICINA GENERAL", "ODONTOLOGIA"]))
    ).group_by(["CentroCosto", "Especialidad", "MedicoRealiza", "MedicoOrdena"]).agg(
        pl.col("CentroCosto").count().alias("Cantidad Registros")
    )

    # print(f"\n\nrevision_cg: \n{revision_cg}")

    #especializada

    revision_ce = revision_centros_costos.filter(
        (pl.col("Servicio") == "consultas especializadas") & pl.col("Especialidad").is_in(["MEDICINA GENERAL", "ODONTOLOGIA", 'HIGIENE ORAL'])
    ).group_by(["CentroCosto", "Especialidad", "MedicoRealiza", "MedicoOrdena"]).agg(
        pl.col("CentroCosto").count().alias("Cantidad Registros")
    )

    # print(f"\n\nrevision_ce: \n{revision_ce}")

    revision_pym = revision_centros_costos.filter(
        (pl.col("Servicio") == 'pym') & (~pl.col('Especialidad').is_in(['MEDICINA GENERAL', 'ODONTOLOGIA', 'HIGIENE ORAL', 'ENFERMERIA', "GINECOLOGIA", 'EXPERTO EN VIH']))
    ).group_by(["CentroCosto", "Especialidad", "MedicoRealiza", "MedicoOrdena"]).agg(
        pl.col("CentroCosto").count().alias("Cantidad Registros")
    )

    # print(f"\n\nrevision_pym: \n{revision_pym}")

    #cronicos
    revision_cro = revision_centros_costos.filter(
        (pl.col("Servicio") == 'cronicos') & (~pl.col('Especialidad').is_in(['MEDICINA INTERNA', 'MEDICINA GENERAL', 'ENDOCRINOLOGIA', 'MEDICINA FAMILIAR', 'CARDIOLOGIA', 'NEFROLOGIA', 'ENFERMERIA']))
    ).group_by(["CentroCosto", "Especialidad", "MedicoRealiza", "MedicoOrdena"]).agg(
        pl.col("CentroCosto").count().alias("Cantidad Registros")
    )

    # print(f"\n\nrevision_cro: \n{revision_cro}")


    ENTIDADES  = ['CEDIT  DEL SUR SAS ', 'CENTRO  DE CUIDADOS CARDIOVASCULARES PABON SAS ', 'CENTRO  DE ESPECIALISTAS NUTRICION DIABETES OBESIDAD Y OSTEOPOROSIS SAS', 'CENTRO  HOSPITAL SAN JUAN BAUSTISTA ', 'CHRISTUS  SINERGIA SALUD. SA PASTO ', 'CLINCA  NORTE ESPECIALIDADES SAS ', 'CLINICA  DE OJOS (CLINOJOS) SA ', 'CLINICA  DE ORTOPEDIA Y FRACTURAS TRAUMEDICAL ', 'CLINICA  FUNDONAR ', 'CLINICA  IMBANACO SAS ', 'CLINICA  LAS LAJAS SAS ', 'CLINICA  NUESTRA SEÑORA DE FATIMA SA ', 'CLINICA  OFTALMOLOGICA CALI ', 'CLINICA  OFTALMOLOGICA PAREDES SAS ', 'CLINICA  OFTALMOLOGICA UNIGARRO LTDA ', 'CLINICA  ONCOLOGICA AURORA PASTO SAS ', 'CLINICA  PUENTE DEL MEDIO SAS ', 'CLINICA  SOL DE LOS ANDES SAS ', 'COMPLEMEDICA  SAS ', 'E.S.E  CEHANI ', 'E.S.E  CENTO DE SALUD NUESTRA SEÑORA DEL PILAS DE ALDANA ', 'E.S.E  CENTRO DE SALUD ANCUYA ', 'E.S.E  CENTRO DE SALUD BELEN ', 'E.S.E  CENTRO DE SALUD CONSACA ', 'E.S.E  CENTRO DE SALUD DE SAN BARTOLOME DE CORDOBA ', 'E.S.E  CENTRO DE SALUD EL ROSARIO ', 'E.S.E  CENTRO DE SALUD GUACHAVES ', 'E.S.E  CENTRO DE SALUD ILES ', 'E.S.E  CENTRO DE SALUD LA BUENA ESPERANZA ', 'E.S.E  CENTRO DE SALUD SAN BERNARDO ', 'E.S.E  CENTRO DE SALUD SAN FRANCISCO ', 'E.S.E  CENTRO DE SALUD SAN JUAN BAUTISTA DE PUPIALES ', 'E.S.E  CENTRO DE SALUD SAN LORENZO ', 'E.S.E  CENTRO DE SALUD SAN MIGUEL ', 'E.S.E  CENTRO DE SALUD SEÑOR DEL MAR ', 'E.S.E  CENTRO DE SALUD TABLON DE GOMEZ ', 'E.S.E  CENTRO HOSPITAL DIVINO NIÑO ', 'E.S.E  CENTRO HOSPITAL GUAITARILLA ', 'E.S.E  CENTRO HOSPITAL LUIS ANTONIO MONTERO ', 'E.S.E  CENTRO HOSPITAL NUESTRO SEÑOR  DE LA DIVINA MISERICORDIA PUERRES', 'E.S.E  HOSPITAL CIVIL DE IPIALES ', 'E.S.E  HOSPITAL CLARITA SANTOS DE SANDONA ', 'E.S.E  HOSPITAL CUMBAL ', 'E.S.E  HOSPITAL EDUARDO SANTOS ', 'E.S.E  HOSPITAL GUACHUCAL ', 'E.S.E  HOSPITAL SAN ANDRES ', 'E.S.E  HOSPITAL SAN CARLOS ', 'E.S.E  HOSPITAL UNIVERSITARIO DEL VALLE EVARISTO GARCIA ', 'E.S.E  JUAN PABLO SEGUNDO DE LINARES ', 'E.S.E  SAN PEDRO DE CUMBITARA ', 'E.S.E  VIRGEN DE LOURDES BUESACO ', 'ECOGRAFIAS  OBSTETRICAS ', 'ELECTROS  TUQUERRES ', 'FUNDACION  HOSPITAL INFANTIL LOS ANGELES ', 'FUNDACION  HOSPITAL SAN PEDRO ', 'FUNDACION  SANTA FE DE BOGOTA ', 'FUNDACION  VALLE DE LILI ', 'HOSPITAL  DEPARTAMENTAL DE NARIÑO SAS ', 'HOSPITAL  LORENCITA VILLEGAS DE SANTOS ', 'HOSPITAL  MENTAL PERPETUO SOCORRO ', 'HOSPITAL  SAN RAFAEL DE PASTO ', 'INSTITUTO  NEUROCIENCIAS DE NARIÑO IPS SAS ', 'INSTITUTO  PARA NIÑOS CIEGOS Y SORDOS DEL VALLE DEL CAUCA ', 'IPS  MEDICALFISIO ', 'IPS  SALUD DE LOS ANDES SAS ', 'IPS  UNIMEDIC SAS ', 'IPS  UNION SALUD SAS ', 'MEDINUCLEAR  SAS ', 'NEURO  CENTRO COLOMBIA SAS ', 'NEURO  CLINICA SAS ', 'PASTO  FUNDACION CONEXION SALUD ', 'PRAXIS  CENTRO DE REHABILITACION FUNCIONAL ', 'RED  MEDICROM IPS HOSPITAL SAN JOSE ', 'SERVICIO  INTEGRAL DE REUMATOLOGIA E INMUNOLOGIA SAS ', 'UNIDAD  CARDIOQUIRURGICA DE NARIÑO SAS ', 'UNIDAD  DE FISIATRIA Y ORTHOINTEGRAL SAS ', 'UNIDAD  MEDICA UROLOGICA DE NARIÑO UROLAN SAS ', 'UNIDAD  PEDIATRICA DEL SUR ', 'UNIDAD  RENAL NEFRODIAL ', 'VIDA  EN CASA SAS ']

    revision_sf = revision_centros_costos.filter(
        (pl.col('Servicio') == "servicio farmaceutico") & (~pl.col('MedicoRealiza').is_in(ENTIDADES))
    ).group_by(["CentroCosto", "Especialidad", "MedicoRealiza", "MedicoOrdena"]).agg(
        pl.col("CentroCosto").count().alias("Cantidad Registros")
    )

    # print(f"\n\nrevision_sf: \n{revision_sf}")

    inconsistencias = pl.concat([
        revision_cg,
        revision_ce,
        revision_pym,
        revision_cro,
        revision_sf
    ])


    return inconsistencias