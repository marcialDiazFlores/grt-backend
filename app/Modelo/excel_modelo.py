import pandas as pd
import logging
import os
import time

logger = logging.getLogger("uvicorn")

# -------------------------------------------------
# Lee la primera hoja de un archivo Excel desde path
# -------------------------------------------------
def leer_primera_hoja_desde_path(excel_path: str):
    start = time.time()
    logger.info(f"📥 [EXCEL] Intentando abrir archivo: {excel_path}")

    if not os.path.exists(excel_path):
        logger.error(f"❌ [EXCEL] Archivo no existe: {excel_path}")
        raise FileNotFoundError(excel_path)

    try:
        logger.info("📥 [EXCEL] Llamando a pd.read_excel (sheet_name=0)")

        df = pd.read_excel(
            excel_path,
            sheet_name=0,
            engine="openpyxl",  # fuerza engine estable
            dtype=str           # evita inferencias lentas
        )

        elapsed = round(time.time() - start, 2)
        logger.info(
            f"📊 [EXCEL] Lectura OK | filas={len(df)} "
            f"cols={len(df.columns)} | tiempo={elapsed}s"
        )

        return df

    except Exception as e:
        logger.exception("❌ [EXCEL] Error durante pd.read_excel")
        raise


# -------------------------------------------------
# Convierte datos no serializables a JSON
# -------------------------------------------------
def convert_to_serializable(obj):
    try:
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, pd.Timedelta):
            return str(obj)
        if pd.isna(obj):
            return None
        return obj
    except Exception:
        logger.warning(f"⚠️ [SERIALIZE] Error convirtiendo valor: {obj}")
        return None


# -------------------------------------------------
# Procesa un archivo Excel completo (todas las hojas)
# -------------------------------------------------
def procesar_excel(file):
    start = time.time()
    logger.info("📘 [EXCEL] Abriendo ExcelFile")

    try:
        excel = pd.ExcelFile(file, engine="openpyxl")
        logger.info(
            f"📑 [EXCEL] Archivo cargado | hojas={excel.sheet_names}"
        )

        sheets_data = []

        for sheet_name in excel.sheet_names:
            sheet_start = time.time()
            logger.info(f"📄 [EXCEL] Procesando hoja: {sheet_name}")

            df = excel.parse(sheet_name, dtype=str)
            logger.info(
                f"📄 [EXCEL] Hoja leída | filas={len(df)} cols={len(df.columns)}"
            )

            df = df.map(convert_to_serializable)

            sheets_data.append({
                "sheetName": sheet_name,
                "data": df.fillna("").to_dict(orient="records")
            })

            logger.info(
                f"✅ [EXCEL] Hoja lista: {sheet_name} "
                f"({round(time.time() - sheet_start, 2)}s)"
            )

        logger.info(
            f"🏁 [EXCEL] Procesamiento completo "
            f"({round(time.time() - start, 2)}s)"
        )

        return sheets_data

    except Exception:
        logger.exception("❌ [EXCEL] Error procesando archivo completo")
        raise
