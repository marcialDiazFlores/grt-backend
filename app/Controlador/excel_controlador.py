from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from app.Modelo.excel_modelo import (
    leer_primera_hoja_desde_path
)
from app.Modelo.Reglas.reglas_post_nuevos_equipos import validar_grt as validar_grt_reglas
import os
import shutil
import uuid
import json
import logging

router = APIRouter()
logger = logging.getLogger("uvicorn")

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

TMP_PATH = os.path.join(BASE_DIR, "tmp")
RESULTS_PATH = os.path.join(BASE_DIR, "results")

os.makedirs(TMP_PATH, exist_ok=True)
os.makedirs(RESULTS_PATH, exist_ok=True)


# ------------------------------
# Background task
# ------------------------------
def procesar_validacion_grt(task_id: str, base_path: str, comp_path: str):
    try:
        logger.info(f"[{task_id}] Procesando GRT")

        df_base = leer_primera_hoja_desde_path(base_path)
        df_comp = leer_primera_hoja_desde_path(comp_path)

        resultado = validar_grt_reglas(df_base, df_comp)

        result_path = os.path.join(RESULTS_PATH, f"{task_id}.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False)

        logger.info(f"[{task_id}] Procesamiento terminado")

    except Exception as e:
        logger.exception(f"[{task_id}] Error")
        error_path = os.path.join(RESULTS_PATH, f"{task_id}.json")
        with open(error_path, "w") as f:
            json.dump({"error": str(e)}, f)


# ------------------------------
# POST: iniciar validación
# ------------------------------
@router.post("/validar-grt")
async def validar_grt(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...)
):
    archivo_base, archivo_comp = files
    task_id = str(uuid.uuid4())

    base_path = os.path.join(TMP_PATH, f"{task_id}_base.xlsx")
    comp_path = os.path.join(TMP_PATH, f"{task_id}_comp.xlsx")

    with open(base_path, "wb") as buffer:
        shutil.copyfileobj(archivo_base.file, buffer)

    with open(comp_path, "wb") as buffer:
        shutil.copyfileobj(archivo_comp.file, buffer)

    background_tasks.add_task(
        procesar_validacion_grt,
        task_id,
        base_path,
        comp_path
    )

    return JSONResponse(
        status_code=202,
        content={
            "task_id": task_id,
            "status": "processing"
        }
    )


# ------------------------------
# GET: consultar resultado
# ------------------------------
@router.get("/validar-grt/{task_id}")
async def obtener_resultado(task_id: str):
    result_path = os.path.join(RESULTS_PATH, f"{task_id}.json")

    if not os.path.exists(result_path):
        return {"status": "processing"}

    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "status": "done",
        "data": data
    }
