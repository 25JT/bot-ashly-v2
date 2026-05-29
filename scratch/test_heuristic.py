import sys
import uiautomation as auto

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def test_heuristic():
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
    
    matches_found = 0
    for idx, chat in enumerate(chats):
        chat_rect = chat.BoundingRectangle
        chat_w = chat_rect.width()
        
        # We search descendants of this chat item
        unread_candidates = []
        
        def search_badge(ctrl):
            name = (ctrl.Name or "").strip()
            if name.isdigit() and len(name) <= 3:
                rect = ctrl.BoundingRectangle
                # Check heuristics:
                # 1. Must be on the far right of the chat item
                is_on_right = rect.left > chat_rect.left + 230
                # 2. Must be small and square-ish
                is_small = rect.width() < 30 and rect.height() < 30
                
                if is_on_right and is_small:
                    unread_candidates.append((ctrl, name, rect))
                    
            for child in ctrl.GetChildren():
                search_badge(child)
                
        search_badge(chat)
        
        if unread_candidates:
            matches_found += 1
            print(f"\n[POTENTIAL UNREAD] Chat [{idx}]: {repr(chat.Name)}")
            for ctrl, val, rect in unread_candidates:
                print(f"  Badge Control: {ctrl.ControlTypeName} | Value: {repr(val)} | Rect: {rect} | Relative X: {rect.left - chat_rect.left}")
                
    print(f"\nTotal chats matching heuristic: {matches_found}")

if __name__ == "__main__":
    test_heuristic()
