import sys
import uiautomation as auto

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def find_details():
    whatsapp = None
    for w in auto.GetRootControl().GetChildren():
        if "WhatsApp" in w.Name:
            whatsapp = w
            break
            
    if not whatsapp:
        print("WhatsApp window not found!")
        return

    # Find the chat items directly
    chats = []
    def find_chats(ctrl):
        if ctrl.ControlType == auto.ControlType.DataItemControl and ctrl.ClassName == "x10l6tqk xh8yej3 x1g42fcv":
            chats.append(ctrl)
        for child in ctrl.GetChildren():
            find_chats(child)
            
    find_chats(whatsapp)
    print(f"Found {len(chats)} total chats.")
    
    for idx, chat in enumerate(chats[:10]):
        print(f"\n================================ CHAT [{idx}] ================================")
        print(f"Chat Name: {repr(chat.Name)}")
        
        # Recursive print of descendants
        def print_descendants(ctrl, depth=1):
            indent = "  " * depth
            name = ctrl.Name or ""
            class_name = ctrl.ClassName or ""
            type_name = ctrl.ControlTypeName
            
            # Print if it has any relevant info
            print(f"{indent}{type_name} | Name: {repr(name)} | Class: {class_name}")
            
            for child in ctrl.GetChildren():
                print_descendants(child, depth + 1)
                
        print_descendants(chat, 1)

if __name__ == "__main__":
    find_details()
