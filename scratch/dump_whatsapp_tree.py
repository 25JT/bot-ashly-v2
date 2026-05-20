import uiautomation as auto
import time

def dump_whatsapp_tree():
    print("Buscando ventana de WhatsApp...")
    whatsapp = None
    for w in auto.GetRootControl().GetChildren():
        if "WhatsApp" in w.Name:
            whatsapp = w
            break
            
    if not whatsapp:
        print("WhatsApp no encontrado.")
        return

    print(f"Ventana encontrada: {whatsapp.Name}. Volcando árbol (parcial)...")
    
    with open("whatsapp_tree_dump.txt", "w", encoding="utf-8") as f:
        def walk(control, depth=0):
            if depth > 10: return
            indent = "  " * depth
            try:
                line = f"{indent}{control.ControlTypeName} | Name: {control.Name} | Class: {control.ClassName}\n"
                f.write(line)
                print(line.strip())
            except:
                pass
            
            for child in control.GetChildren():
                walk(child, depth + 1)

        walk(whatsapp)

if __name__ == "__main__":
    dump_whatsapp_tree()
