import pandas as pd

# Lee la primera hoja de un archivo excel desde su path
def leer_primera_hoja_desde_path(excel_path: str):
    df = pd.read_excel(excel_path, sheet_name=0)
    return df

# Convierte datos no serializables a JSON (fechas, timedeltas, NaN)
def convert_to_serializable(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, pd.Timedelta):
        return str(obj)
    if pd.isna(obj):
        return None
    return obj

# Procesa un archivo Excel y retorna sus hojas en formato dict para el frontend
def procesar_excel(file):
    excel = pd.ExcelFile(file)
    sheets_data = []

    for sheet_name in excel.sheet_names:
        df = excel.parse(sheet_name)
        df = df.map(convert_to_serializable)

        sheets_data.append({
            "sheetName": sheet_name,
            "data": df.fillna("").to_dict(orient="records")
        })

    return sheets_data
