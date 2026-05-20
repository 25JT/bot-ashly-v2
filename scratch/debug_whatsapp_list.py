import uiautomation as auto
import time

def debug_whatsapp():
    print("Buscando ventana de WhatsApp...")
    whatsapp = None
    for w in auto.GetRootControl().GetChildren():
        if "WhatsApp" in w.Name:
            whatsapp = w
            break
            
    if not whatsapp:
        print("WhatsApp no encontrado.")
        return

    print("--- Buscando cualquier control que contenga 'mensaje' o 'message' ---")
    def find_and_print(control, depth=0):
        if depth > 5: return
        for child in control.GetChildren():
            if "mensaje" in child.Name.lower() or "message" in child.Name.lower() or child.ControlTypeName in ["ListControl", "GroupControl"]:
                print(f"{'  '*depth}Encontrado: {child.ControlTypeName} - Name: {child.Name} - Hijos: {len(child.GetChildren())}")
                if len(child.GetChildren()) > 3:
                    print(f"{'  '*(depth+1)}Items:")
                    for i, item in enumerate(child.GetChildren()[:5]):
                        print(f"{'  '*(depth+2)}[{i}] {item.Name[:100]}...")
            find_and_print(child, depth + 1)

    find_and_print(whatsapp)

if __name__ == "__main__":
    debug_whatsapp()
