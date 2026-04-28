import uiautomation as auto

def test_taskbar():
    print("Buscando barra de tareas...")
    taskbar = auto.WindowControl(ClassName='Shell_TrayWnd')
    if not taskbar.Exists(0):
        print("No se encontró la barra de tareas.")
        return
    
    print(f"Barra de tareas encontrada: {taskbar.Name}")
    
    # Buscar el área de aplicaciones (AppList o Running Applications)
    # En Windows 10/11 suele ser un control de tipo 'ToolBar' o similar
    apps = taskbar.Control(Name='Aplicaciones en ejecución', ControlType=auto.ControlType.ToolBarControl)
    if not apps.Exists(0):
        # Intentar otro nombre común
        apps = taskbar.Control(Name='Running applications', ControlType=auto.ControlType.ToolBarControl)
    
    if apps.Exists(0):
        print(f"Lista de aplicaciones encontrada: {apps.Name}")
        for btn in apps.GetChildren():
            rect = btn.BoundingRectangle
            print(f" - [{btn.Name}] en ({rect.left}, {rect.top}, {rect.right}, {rect.bottom})")
    else:
        print("No se encontró la lista de aplicaciones directamente. Listando todos los hijos...")
        for child in taskbar.GetChildren():
            print(f" - Hijo: {child.Name} ({child.ControlTypeName})")
            # Profundizar un poco
            for sub in child.GetChildren():
                print(f"   - Sub: {sub.Name} ({sub.ControlTypeName})")

if __name__ == "__main__":
    test_taskbar()
