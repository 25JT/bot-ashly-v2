import win32com.client

def _get_active_sheet():
    try:
        excel = win32com.client.GetActiveObject("Excel.Application")
        return excel.ActiveSheet
    except Exception as e:
        raise Exception("No se pudo conectar a Excel. Asegúrate de que Excel esté abierto y el documento activo.")

def escribir_celda(celda: str, valor: str) -> str:
    """Escribe un valor en una celda específica de Excel (ej. A1)."""
    try:
        sheet = _get_active_sheet()
        sheet.Range(celda).Value = valor
        return f"Valor '{valor}' escrito correctamente en la celda {celda} de Excel."
    except Exception as e:
        return f"Error al escribir en la celda {celda}: {str(e)}"

def escribir_interseccion(fila_texto: str, columna_texto: str, valor: str) -> str:
    """
    Busca una fila que contenga fila_texto y una columna que contenga columna_texto.
    Escribe el valor en la intersección de ambas.
    """
    try:
        sheet = _get_active_sheet()
        
        # Obtener rango usado para limitar la búsqueda y hacerla rápida
        used_range = sheet.UsedRange
        max_row = used_range.Row + used_range.Rows.Count + 50
        max_col = used_range.Column + used_range.Columns.Count + 50
        
        # Buscar la fila
        found_row = None
        for row in range(1, max_row):
            for col in range(1, 10): # Buscar en las primeras 9 columnas (A-I)
                cell_val = sheet.Cells(row, col).Value
                if cell_val is not None:
                    if str(cell_val).strip().lower() == fila_texto.lower():
                        found_row = row
                        break
            if found_row:
                break
                
        if not found_row:
            return f"Error: No se encontró ninguna fila con el texto exacto '{fila_texto}'."
            
        # Buscar la columna
        found_col = None
        for col in range(1, max_col):
            for row in range(1, 15): # Buscar en las primeras 14 filas para los encabezados
                cell_val = sheet.Cells(row, col).Value
                if cell_val is not None:
                    # Excel devuelve los números como floats (ej. 10.0)
                    val_str = str(int(cell_val)) if isinstance(cell_val, float) and cell_val.is_integer() else str(cell_val)
                    if val_str.strip().lower() == columna_texto.lower():
                        found_col = col
                        break
            if found_col:
                break
                
        if not found_col:
            return f"Error: No se encontró ningún encabezado de columna con el texto '{columna_texto}'."
            
        # Escribir en la intersección
        sheet.Cells(found_row, found_col).Value = valor
        
        # Obtener la letra de la columna para un mensaje bonito
        col_letter = sheet.Cells(1, found_col).Address.split('$')[1]
        
        return f"Valor '{valor}' escrito exitosamente en la intersección de '{fila_texto}' y '{columna_texto}' (Celda {col_letter}{found_row})."
        
    except Exception as e:
        return f"Error crítico de Excel: {str(e)}"
