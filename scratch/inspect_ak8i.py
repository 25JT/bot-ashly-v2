import sys
import uiautomation as auto

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def inspect_ak8i():
    whatsapp = None
    for w in auto.GetRootControl().GetChildren():
        if "WhatsApp" in w.Name:
            whatsapp = w
            break
            
    if not whatsapp:
        print("WhatsApp window not found!")
        return

    chats = []
    def find_chats(ctrl):
        if ctrl.ControlType == auto.ControlType.DataItemControl and ctrl.ClassName == "x10l6tqk xh8yej3 x1g42fcv":
            chats.append(ctrl)
        for child in ctrl.GetChildren():
            find_chats(child)
            
    find_chats(whatsapp)
    print(f"Found {len(chats)} total chats.")
    
    for idx, chat in enumerate(chats):
        # Find all controls with Class containing '_ak8i'
        ak8i_controls = []
        def find_ak8i(ctrl):
            if "_ak8i" in (ctrl.ClassName or ""):
                ak8i_controls.append(ctrl)
            for child in ctrl.GetChildren():
                find_ak8i(child)
                
        find_ak8i(chat)
        for ak in ak8i_controls:
            # Let's see if this control has children or text
            children = ak.GetChildren()
            if children or ak.Name:
                print(f"\nChat [{idx}]: {repr(chat.Name)}")
                print(f"  _ak8i name: {repr(ak.Name)}")
                for c_idx, child in enumerate(children):
                    print(f"    Child [{c_idx}]: {child.ControlTypeName} | Name: {repr(child.Name)} | Class: {child.ClassName}")
                    # Grandchildren
                    for gc_idx, gc in enumerate(child.GetChildren()):
                        print(f"      Grandchild [{gc_idx}]: {gc.ControlTypeName} | Name: {repr(gc.Name)} | Class: {gc.ClassName}")

if __name__ == "__main__":
    inspect_ak8i()
