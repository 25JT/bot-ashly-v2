import os

#Lista archivos

def list_files( directorio="."):

    """Lista los archivos en el directorio dado."""
    try:
        archivos = os.listdir(directorio)
        return f"Archivos encontrados: {archivos}"
    except Exception as e:
        return f"Error al listar archivos en '{directorio}': {e}"

#Leer archivos
def read_file( file_path):
    """Lee el contenido de un archivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error al leer el archivo '{file_path}': {e}"

#Editar archivos
def edit_file( file_path, content="", prev_text="", new_text=""):
    try:
        exist = os.path.exists(file_path)
        
        # Si el archivo existe y queremos reemplazar un texto específico
        if exist and prev_text:
            archivo_actual = read_file(file_path)
            if prev_text not in archivo_actual:
                return f"Error: El texto '{prev_text}' no existe en el archivo."
            # Reemplazamos y preparamos el nuevo 'content'
            content = archivo_actual.replace(prev_text, new_text)

        # GUARDAR SIEMPRE: Esto fuera de cualquier IF/ELSE para que funcione para todos los casos
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        action = "editado" if (exist and prev_text) else "creado/sobreescrito"
        return f"Archivo '{file_path}' {action} exitosamente."
        
    except Exception as e:
        return f"Error al procesar el archivo '{file_path}': {e}"