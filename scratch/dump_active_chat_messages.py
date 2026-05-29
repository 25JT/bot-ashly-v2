import sys
import uiautomation as auto

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def dump_messages():
    whatsapp = None
    for w in auto.GetRootControl().GetChildren():
        if "WhatsApp" in w.Name:
            whatsapp = w
            break
            
    if not whatsapp:
        print("WhatsApp window not found!")
        return

    # Let's search all elements in the WhatsApp window and look for controls that contain chat messages.
    # Usually in WhatsApp Web:
    # - Messages are in elements with ClassName containing 'message-in' or 'message-out' or under a specific Group/List.
    # Let's print any element that has a ClassName or Name representing a message.
    print("Searching for message-like elements...")
    
    found_messages = []
    
    def search_messages(ctrl):
        name = ctrl.Name or ""
        class_name = ctrl.ClassName or ""
        
        # Check if the class name or name indicates a message
        is_msg = False
        if "message" in class_name.lower():
            is_msg = True
        elif "msg" in class_name.lower():
            is_msg = True
        elif "message-in" in class_name or "message-out" in class_name:
            is_msg = True
        elif "copyable-text" in class_name:
            is_msg = True
        elif "selectable-text" in class_name:
            is_msg = True
            
        if is_msg:
            found_messages.append(ctrl)
            
        for child in ctrl.GetChildren():
            search_messages(child)
            
    search_messages(whatsapp)
    print(f"Found {len(found_messages)} message-like controls.")
    
    # If we didn't find any by class name, let's dump the children of any PaneControl or GroupControl on the right side
    if not found_messages:
        print("\nNo message-like controls found by class. Let's dump all text/group controls in the right-hand panel...")
        # Get the right-hand area. The chat history container is usually a large Group or Pane control.
        # Let's search all TextControls and list them.
        text_controls = []
        def find_texts(ctrl):
            if ctrl.ControlType == auto.ControlType.TextControl and ctrl.Name:
                text_controls.append(ctrl)
            for child in ctrl.GetChildren():
                find_texts(child)
        find_texts(whatsapp)
        print(f"Found {len(text_controls)} total TextControls.")
        # Filter texts that look like messages (longer texts, or near the right/center)
        # We can just print the last 30 text controls
        for idx, txt in enumerate(text_controls[-30:]):
            print(f"Text [{idx}]: {repr(txt.Name)} | Rect: {txt.BoundingRectangle}")

if __name__ == "__main__":
    dump_messages()
