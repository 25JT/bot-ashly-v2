import sys
import time
import uiautomation as auto
import pyautogui

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def dump_active_chat():
    whatsapp = None
    for w in auto.GetRootControl().GetChildren():
        if "WhatsApp" in w.Name:
            whatsapp = w
            break
            
    if not whatsapp:
        print("WhatsApp window not found!")
        return

    # Focus WhatsApp window
    whatsapp.SetFocus()
    time.sleep(0.5)

    chats = []
    def find_chats(ctrl):
        if ctrl.ControlType == auto.ControlType.DataItemControl and ctrl.ClassName == "x10l6tqk xh8yej3 x1g42fcv":
            chats.append(ctrl)
        for child in ctrl.GetChildren():
            find_chats(child)
            
    find_chats(whatsapp)
    if not chats:
        print("No chats found")
        return
        
    chat = chats[1] # Let's click the second chat to avoid any "Ver estado" ring if the first has one
    print(f"Clicking on chat: {repr(chat.Name)}")
    
    # Click using pyautogui
    rect = chat.BoundingRectangle
    cx = rect.left + 150 # click a bit to the right of the avatar to avoid clicking avatar/status
    cy = rect.top + rect.height() // 2
    
    pyautogui.click(cx, cy)
    print(f"Clicked at coordinates: ({cx}, {cy})")
    time.sleep(3) # Wait for it to open and load
    
    # Now let's list all TextControls again
    win_rect = whatsapp.BoundingRectangle
    
    text_controls = []
    def find_texts(ctrl):
        if ctrl.ControlType == auto.ControlType.TextControl and ctrl.Name:
            text_controls.append(ctrl)
        for child in ctrl.GetChildren():
            find_texts(child)
            
    find_texts(whatsapp)
    print(f"Found {len(text_controls)} total TextControls after opening chat.")
    
    print("\nTextControls in the conversation pane (potential chat messages):")
    messages_found = 0
    for idx, txt in enumerate(text_controls):
        rect = txt.BoundingRectangle
        # Left column ends at around win_rect.left + 350
        # Right column conversation messages are usually at X > win_rect.left + 380
        # We also want to exclude the chat list items which might be in the same list or pane
        # Let's filter out any text control that belongs to the left list
        # A good heuristic is that the chat history pane has X > win_rect.left + 380
        if rect.left > win_rect.left + 380 and rect.bottom < win_rect.bottom - 80:
            print(f"Msg [{messages_found}] (X={rect.left}, Y={rect.top}, W={rect.width()}, H={rect.height()}): {repr(txt.Name)} | Class: {txt.ClassName}")
            messages_found += 1
            
    print(f"\nTotal conversation messages found: {messages_found}")

if __name__ == "__main__":
    dump_active_chat()
