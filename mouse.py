import time
import urllib.parse
import webbrowser
import cv2
import mediapipe as mp
import util


class Button:
    """Represents an on-screen keyboard button."""
    def __init__(self, pos, size, text, btn_type="key"):
        self.pos = pos        # (x, y)
        self.size = size      # (w, h)
        self.text = text
        self.btn_type = btn_type  # "key", "space", "action", "search"

    def is_hovered(self, cursor_pos):
        if cursor_pos is None:
            return False
        cx, cy = cursor_pos
        x, y = self.pos
        w, h = self.size
        return x <= cx <= (x + w) and y <= cy <= (y + h)


def build_keyboard_layout(frame_w, frame_h):
    """Constructs keyboard button layout scaled to the camera resolution."""
    gap = max(10, int(frame_w * 0.01))
    kw = max(45, int((frame_w * 0.78 - 9 * gap) / 10))
    kh = max(45, int(kw * 0.95))

    buttons = []
    sb_w = int(frame_w * 0.78)
    sb_h = max(50, int(kh * 1.0))
    sb_x = (frame_w - sb_w) // 2
    sb_y = max(20, int(frame_h * 0.04))
    search_bar_rect = (sb_x, sb_y, sb_w, sb_h)

    start_y = sb_y + sb_h + int(gap * 1.8)

    # Row 0: Q to P (10 keys)
    row0 = ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"]
    total_w0 = len(row0) * kw + (len(row0) - 1) * gap
    start_x0 = (frame_w - total_w0) // 2
    for i, char in enumerate(row0):
        buttons.append(Button((start_x0 + i * (kw + gap), start_y), (kw, kh), char))

    # Row 1: A to L (9 keys)
    start_y += kh + gap
    row1 = ["A", "S", "D", "F", "G", "H", "J", "K", "L"]
    total_w1 = len(row1) * kw + (len(row1) - 1) * gap
    start_x1 = (frame_w - total_w1) // 2
    for i, char in enumerate(row1):
        buttons.append(Button((start_x1 + i * (kw + gap), start_y), (kw, kh), char))

    # Row 2: Z to M (7 keys) + Backspace (<)
    start_y += kh + gap
    row2 = ["Z", "X", "C", "V", "B", "N", "M"]
    bksp_w = int(kw * 1.5)
    total_w2 = len(row2) * kw + bksp_w + len(row2) * gap
    start_x2 = (frame_w - total_w2) // 2
    for i, char in enumerate(row2):
        buttons.append(Button((start_x2 + i * (kw + gap), start_y), (kw, kh), char))
    # Backspace button
    bksp_x = start_x2 + len(row2) * (kw + gap)
    buttons.append(Button((bksp_x, start_y), (bksp_w, kh), "<", btn_type="action"))

    # Row 3: SPACE, CLR, SEARCH
    start_y += kh + gap
    space_w = int(kw * 4.2)
    clr_w = int(kw * 1.5)
    search_w = int(kw * 2.5)
    total_w3 = space_w + clr_w + search_w + 2 * gap
    start_x3 = (frame_w - total_w3) // 2

    buttons.append(Button((start_x3, start_y), (space_w, kh), "SPACE", btn_type="space"))
    buttons.append(Button((start_x3 + space_w + gap, start_y), (clr_w, kh), "CLR", btn_type="action"))
    buttons.append(Button((start_x3 + space_w + gap + clr_w + gap, start_y), (search_w, kh), "SEARCH", btn_type="search"))

    return search_bar_rect, buttons


def draw_ui(frame, search_bar_rect, buttons, search_text, hovered_btn, active_flash_btn):
    """Draws sleek semi-transparent keyboard and search bar onto the frame."""
    overlay = frame.copy()
    sb_x, sb_y, sb_w, sb_h = search_bar_rect

    # 1. Search Bar Background
    cv2.rectangle(overlay, (sb_x, sb_y), (sb_x + sb_w, sb_y + sb_h), (30, 30, 30), cv2.FILLED)

    # 2. Keyboard Buttons Background
    for btn in buttons:
        x, y = btn.pos
        w, h = btn.size

        # Choose background color based on state
        if btn == active_flash_btn:
            bg_color = (0, 255, 120)       # Flash green on click
        elif btn == hovered_btn:
            bg_color = (0, 200, 255)       # Amber/Cyan glow on hover
        elif btn.btn_type == "search":
            bg_color = (180, 100, 20)      # Rich blue
        elif btn.btn_type == "action":
            bg_color = (50, 50, 140)       # Dark crimson/red
        elif btn.btn_type == "space":
            bg_color = (60, 60, 60)        # Neutral grey
        else:
            bg_color = (45, 45, 45)        # Dark grey for standard keys

        cv2.rectangle(overlay, (x, y), (x + w, y + h), bg_color, cv2.FILLED)

    # Blend overlay with camera frame for glassy transparency
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # 3. Draw Search Bar Borders and Text
    cv2.rectangle(frame, (sb_x, sb_y), (sb_x + sb_w, sb_y + sb_h), (200, 200, 200), 2)
    # Animated cursor
    cursor = "_" if int(time.time() * 2) % 2 == 0 else " "
    display_str = f"Search: {search_text}{cursor}"
    cv2.putText(frame, display_str, (sb_x + 15, sb_y + int(sb_h * 0.65)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

    # 4. Draw Button Borders and Labels
    for btn in buttons:
        x, y = btn.pos
        w, h = btn.size

        border_color = (255, 255, 255) if btn == hovered_btn else (140, 140, 140)
        border_thick = 2 if btn == hovered_btn else 1
        cv2.rectangle(frame, (x, y), (x + w, y + h), border_color, border_thick)

        # Center the text within button
        font_scale = 0.55 if len(btn.text) > 2 else 0.75
        thickness = 2
        (tw, th), _ = cv2.getTextSize(btn.text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        tx = x + (w - tw) // 2
        ty = y + (h + th) // 2

        text_color = (0, 0, 0) if (btn == hovered_btn or btn == active_flash_btn) else (255, 255, 255)
        cv2.putText(frame, btn.text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness, cv2.LINE_AA)

    # 5. Instructions overlay at the bottom
    instruction = "Pinch Index & Thumb to Type | 'SEARCH' opens Google | Press 'q' to Quit"
    cv2.putText(frame, instruction, (20, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        max_num_hands=1
    )
    draw_utils = mp.solutions.drawing_utils

    search_text = ""
    last_click_time = 0.0
    click_cooldown = 0.38  # seconds between registered clicks
    active_flash_btn = None
    flash_start_time = 0.0

    buttons_cached = None
    search_bar_rect = None

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Mirror the frame horizontally for natural intuitive interaction
            frame = cv2.flip(frame, 1)
            frame_h, frame_w = frame.shape[:2]

            # Initialize keyboard on first frame or if resolution changes
            if buttons_cached is None:
                search_bar_rect, buttons_cached = build_keyboard_layout(frame_w, frame_h)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = hands.process(frame_rgb)

            cursor_pos = None
            is_pinching = False
            pinch_dist = 999

            if processed.multi_hand_landmarks:
                hand_landmarks = processed.multi_hand_landmarks[0]
                draw_utils.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Index fingertip (landmark 8) and Thumb tip (landmark 4)
                idx_lm = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_lm = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

                ix, iy = int(idx_lm.x * frame_w), int(idx_lm.y * frame_h)
                tx, ty = int(thumb_lm.x * frame_w), int(thumb_lm.y * frame_h)
                cursor_pos = (ix, iy)

                # Measure pinch distance in pixels
                pinch_dist = util.get_pixel_distance((ix, iy), (tx, ty))
                pinch_threshold = max(28, int(frame_w * 0.028))
                is_pinching = pinch_dist < pinch_threshold

                # Visual pinch feedback on hand
                line_color = (0, 255, 0) if is_pinching else (0, 165, 255)
                cv2.line(frame, (ix, iy), (tx, ty), line_color, 2)
                cv2.circle(frame, (ix, iy), 8, line_color, cv2.FILLED)
                cv2.circle(frame, (tx, ty), 6, line_color, cv2.FILLED)

            # Check which button is hovered
            hovered_btn = None
            if cursor_pos is not None:
                for btn in buttons_cached:
                    if btn.is_hovered(cursor_pos):
                        hovered_btn = btn
                        break

            # Handle click if pinching over a button
            now = time.time()
            if is_pinching and hovered_btn is not None:
                if (now - last_click_time) > click_cooldown:
                    last_click_time = now
                    active_flash_btn = hovered_btn
                    flash_start_time = now

                    # Process button action
                    action = hovered_btn.text
                    if action == "SPACE":
                        search_text += " "
                        util.speak_async("space")
                    elif action == "<":
                        if len(search_text) > 0:
                            search_text = search_text[:-1]
                            util.speak_async("delete")
                    elif action == "CLR":
                        search_text = ""
                        util.speak_async("clear")
                    elif action == "SEARCH":
                        query = search_text.strip()
                        if query:
                            util.speak_async(f"Searching Google for {query}")
                            encoded_query = urllib.parse.quote_plus(query)
                            webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
                        else:
                            util.speak_async("Search is empty")
                    else:
                        search_text += action
                        util.speak_async(action)

            # Reset flash effect after 150ms
            if active_flash_btn and (now - flash_start_time) > 0.15:
                active_flash_btn = None

            # Render keyboard and interface
            draw_ui(frame, search_bar_rect, buttons_cached, search_text, hovered_btn, active_flash_btn)

            cv2.imshow('Gesture Virtual Keyboard', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()



