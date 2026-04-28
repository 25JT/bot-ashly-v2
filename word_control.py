import win32com.client
import os

def _get_word_app():
    try:
        # Intentar obtener la instancia activa
        word = win32com.client.GetActiveObject("Word.Application")
        return word
    except Exception:
        # Si no hay instancia activa, crear una nueva
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = True
        return word

def word_crear_documento() -> str:
    """Crea un nuevo documento de Word en blanco."""
    try:
        word = _get_word_app()
        word.Documents.Add()
        return "Nuevo documento de Word creado correctamente."
    except Exception as e:
        return f"Error al crear documento: {str(e)}"

def word_escribir_texto(texto: str, estilo: str = "Normal", nueva_linea: bool = True) -> str:
    """
    Escribe texto en el documento activo de Word.
    estilo: 'Normal', 'Título 1', 'Título 2', etc.
    """
    try:
        word = _get_word_app()
        if word.Documents.Count == 0:
            word.Documents.Add()
        
        selection = word.Selection
        selection.TypeText(texto)
        if nueva_linea:
            selection.TypeParagraph()
            
        return f"Texto escrito en Word correctamente con estilo {estilo}."
    except Exception as e:
        return f"Error al escribir en Word: {str(e)}"

def word_aplicar_formato(negrita: bool = False, cursiva: bool = False, subrayado: bool = False, tamaño: int = None) -> str:
    """Aplica formato a la selección actual o al texto que se escribirá a continuación."""
    try:
        word = _get_word_app()
        selection = word.Selection
        
        if negrita: selection.Font.Bold = True
        if cursiva: selection.Font.Italic = True
        if subrayado: selection.Font.Underline = 1 # wdUnderlineSingle
        if tamaño: selection.Font.Size = tamaño
        
        return "Formato aplicado correctamente a la selección de Word."
    except Exception as e:
        return f"Error al aplicar formato: {str(e)}"

def word_insertar_tabla(filas: int, columnas: int) -> str:
    """Inserta una tabla en la posición actual del cursor."""
    try:
        word = _get_word_app()
        doc = word.ActiveDocument
        range_pos = word.Selection.Range
        doc.Tables.Add(Range=range_pos, NumRows=filas, NumColumns=columnas)
        return f"Tabla de {filas}x{columnas} insertada correctamente."
    except Exception as e:
        return f"Error al insertar tabla: {str(e)}"

def word_guardar_como(ruta: str) -> str:
    """Guarda el documento activo en la ruta especificada. Debe ser ruta absoluta."""
    try:
        word = _get_word_app()
        if word.Documents.Count == 0:
            return "No hay documentos abiertos para guardar."
            
        # Asegurar ruta absoluta
        if not os.path.isabs(ruta):
            ruta = os.path.abspath(ruta)
            
        word.ActiveDocument.SaveAs(ruta)
        return f"Documento guardado exitosamente en: {ruta}"
    except Exception as e:
        return f"Error al guardar documento: {str(e)}"

if __name__ == "__main__":
    # Prueba rápida
    print(word_crear_documento())
    print(word_escribir_texto("Hola, soy Ashly trabajando en Word.", nueva_linea=True))
    print(word_aplicar_formate(negrita=True, tamaño=20))
    print(word_escribir_texto("Esto es un título importante."))
