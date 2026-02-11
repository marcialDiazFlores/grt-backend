from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from app.Modelo.excel_modelo import procesar_excel, leer_primera_hoja_desde_path
from app.Modelo.Reglas.reglas_post_nuevos_equipos import validar_grt as validar_grt_reglas
from app.Vista.excel_vista import construir_payload
import json
import time
import os
import shutil
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

router = APIRouter()
logger = logging.getLogger("uvicorn")

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

TMP_PATH = os.path.join(BASE_DIR, "tmp")
os.makedirs(TMP_PATH, exist_ok=True)


# ------------------------------
# Upload normal
# ------------------------------
@router.post("/upload-excel")
async def upload_excel(files: list[UploadFile] = File(...)):
    response = []
    for file in files:
        sheets = procesar_excel(file.file)
        response.append(construir_payload(file.filename, sheets))
    return response


# ------------------------------
# Upload streaming
# ------------------------------
@router.post("/upload-excel-stream")
async def upload_excel_stream(files: list[UploadFile] = File(...)):

    async def event_generator():
        for file in files:
            sheets = procesar_excel(file.file)
            payload = construir_payload(file.filename, sheets)
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(0.1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# ------------------------------
# Validar GRT
# ------------------------------
@router.post("/validar-grt")
async def validar_grt(files: list[UploadFile] = File(...)):
    """
    Endpoint para validar GRT.
    Valida las siguientes reglas: 
    
    # Regla 0:

    # Precio_base * 1.19 = Precio_comparación, donde el precio base es el precio de la columna Full Price de la primera planilla, y precio comparación es el precio de la columna valor full de la segunda planilla

    # Regla 1:

    # Si el valor en la columna Make no es Apple y el valor de Full Price con IVA es menor o igual a 250000, el valor de Equipment Rank Value debe ser 1.

    # Regla 2:

    # Si el valor en la columna Make no es Apple y el valor de Full Price con IVA es mayor a 250000, el valor de Equipment Rank Value debe ser 3.

    # Regla 3: 

    # Si el valor en la columna Make es Apple, entonces Equipment Rank Value debe ser 2.

    # Regla 4:

    # Si el valor en la columna Equipment Rank Value es 4, entonces Equipment Classification debe ser "MDM".

    # Regla 5:

    # Si el valor en la columna Equipment Classification es "MDM", entonces Use Category debe ser "DATOS"

    # Regla 6:

    # El nombre, color y modelo del equipo debe ser menor o igual a 30 caracteres.

    # Regla 7:

    # Los nombres, colores y modelos no deben contener caracteres no válidos, donde los caracteres inválidos son / * - # , . ( ) y otros símbolos especiales, se permiten: letras (incluyendo acentos), números y espacios.
    """
    archivo_base, archivo_comp = files

    # Guardar archivos temporalmente
    base_path = os.path.join(TMP_PATH, archivo_base.filename)
    comp_path = os.path.join(TMP_PATH, archivo_comp.filename)

    with open(base_path, "wb") as buffer:
        shutil.copyfileobj(archivo_base.file, buffer)

    with open(comp_path, "wb") as buffer:
        shutil.copyfileobj(archivo_comp.file, buffer)

    # Leer dataframes
    df_base = leer_primera_hoja_desde_path(base_path)
    df_comp = leer_primera_hoja_desde_path(comp_path)

    # Ejecutar lógica de negocio
    resultado = validar_grt_reglas(df_base, df_comp)

    logger.info(f"Resultado comparar-grt: {resultado}")
    return resultado