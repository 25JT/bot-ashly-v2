import pyautogui
import time
import random
import numpy as np
from typing import Tuple


class MouseOperator:
    def __init__(self):
        pyautogui.FAILSAFE = True
        self.width, self.height = pyautogui.size()

    def _generate_path(self, start: Tuple[int, int], end: Tuple[int, int], points: int = 20):
        x_pts = np.linspace(start[0], end[0], points)
        y_pts = np.linspace(start[1], end[1], points)

        dist = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        offset = dist * 0.1

        path = []
        for i in range(len(x_pts)):
            deviation_x = random.uniform(-offset, offset) * (i / points) * (1 - i / points)
            deviation_y = random.uniform(-offset, offset) * (i / points) * (1 - i / points)

            path.append((x_pts[i] + deviation_x, y_pts[i] + deviation_y))

        return path

    def smooth_move(self, target: Tuple[int, int], duration: float = None, speed: float = 1.0):
        start = pyautogui.position()
        path = self._generate_path(start, target)
        
        if duration is not None:
            step_duration = duration / len(path)
        else:
            step_duration = 0.01 * speed

        for point in path:
            pyautogui.moveTo(point[0], point[1], duration=step_duration)
        
        return f"Mouse movido exitosamente a {target}"

    def drag_and_drop(self, origin: Tuple[int, int], target: Tuple[int, int]):
        self.smooth_move(origin)
        time.sleep(random.uniform(0.1, 0.3))

        pyautogui.mouseDown(button='left')
        time.sleep(0.2)

        self.smooth_move(target, speed=0.8)

        time.sleep(random.uniform(0.2, 0.4))
        pyautogui.mouseUp(button='left')
        
        return f"Arrastre completado desde {origin} hasta {target}"

    def left_click(self):
        pyautogui.click(button='left')
        return "Click izquierdo realizado"

    def right_click(self):
        pyautogui.click(button='right')
        return "Click derecho realizado"

    def middle_click(self):
        pyautogui.click(button='middle')
        return "Click central realizado"

    def scroll_mouse(self, cantidad: int):
        """cantidad positiva para arriba, negativa para abajo"""
        pyautogui.scroll(cantidad)
        direccion = "arriba" if cantidad > 0 else "abajo"
        return f"Scroll realizado {direccion} ({abs(cantidad)} clics)"