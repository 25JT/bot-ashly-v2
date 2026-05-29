import sys
import time
import uiautomation as auto

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def test_reader(limite=8):
    try:
        whatsapp = None
        for w in auto.GetRootControl().GetChildren():
            if "WhatsApp" in w.Name:
                whatsapp = w
                break
                
        if not whatsapp:
            print("WhatsApp window not found!")
            return
            
        win_rect = whatsapp.BoundingRectangle
        
        text_controls = []
        def find_texts(ctrl):
            if ctrl.ControlType == auto.ControlType.TextControl and ctrl.Name:
                text_controls.append(ctrl)
            for child in ctrl.GetChildren():
                find_texts(child)
                
        find_texts(whatsapp)
        print(f"Found {len(text_controls)} total TextControls.")
        
        right_texts = []
        for txt in text_controls:
            rect = txt.BoundingRectangle
            if rect.left > win_rect.left + 380 and rect.bottom < win_rect.bottom - 80:
                right_texts.append(txt)
                
        if not right_texts:
            print("No right texts found.")
            return
            
        # Ordenamos los textos por su coordenada Y para leerlos de arriba a abajo
        right_texts.sort(key=lambda t: t.BoundingRectangle.top)
        
        # Procesamos y de-duplicamos
        conversacion_lineas = []
        vistos = set()
        
        for txt in right_texts:
            val = txt.Name.strip()
            if not val:
                continue
                
            # Evitar repetir el mismo texto en la misma zona
            rect = txt.BoundingRectangle
            identificador_unico = (val, rect.top // 5) # tolerar 5px de variación vertical
            
            if identificador_unico not in vistos:
                vistos.add(identificador_unico)
                es_saliente = rect.left > win_rect.left + 600
                prefijo = "[Tú]" if es_saliente else "[Contacto]"
                
                # Ignorar sistemas, cifrados y timestamps
                if any(excl in val for excl in ["cifrados de extremo", "encriptados", "Usa WhatsApp en tu"]):
                    continue
                if "p. m." in val or "a. m." in val or val.lower() in ["hoy", "ayer"]:
                    continue
                    
                conversacion_lineas.append(f"{prefijo}: {val}")
                
        print("\n--- FORMATTED CONVERSATION (SEPARATED) ---")
        print("\n".join(conversacion_lineas[-limite:]))
        print("------------------------------------------")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_reader()
