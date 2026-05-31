import mss
import mss.tools
import pygetwindow as gw
import os

class ScreenPerceptionEngine:
    def __init__(self, capture_dir="captures"):
        self.sct = mss.mss()
        self.capture_dir = capture_dir
        if not os.path.exists(self.capture_dir):
            os.makedirs(self.capture_dir)
            
    def get_active_window_info(self):
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                return {
                    "title": active_window.title,
                    "left": active_window.left,
                    "top": active_window.top,
                    "width": active_window.width,
                    "height": active_window.height
                }
            return None
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None

    def capture_screen(self):
        # Capture the primary monitor
        monitor = self.sct.monitors[1]
        output_path = os.path.join(self.capture_dir, "current_screen.png")
        sct_img = self.sct.grab(monitor)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=output_path)
        return output_path
        
    def capture_active_window(self, target_window_info=None):
        window_info = target_window_info or self.get_active_window_info()
        if window_info and window_info["width"] > 0 and window_info["height"] > 0:
            try:
                # Get primary monitor bounds to clamp coordinates
                primary = self.sct.monitors[1]
                p_left = primary["left"]
                p_top = primary["top"]
                p_width = primary["width"]
                p_height = primary["height"]
                
                # Clamp coordinates to prevent negative offsets from maximized windows (e.g. -8, -8)
                left = max(p_left, window_info["left"])
                top = max(p_top, window_info["top"])
                
                # Fit width and height within monitor bounds
                right = min(p_left + p_width, window_info["left"] + window_info["width"])
                bottom = min(p_top + p_height, window_info["top"] + window_info["height"])
                
                width = max(1, right - left)
                height = max(1, bottom - top)
                
                monitor = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }
            except Exception:
                monitor = {
                    "top": max(0, window_info["top"]),
                    "left": max(0, window_info["left"]),
                    "width": window_info["width"],
                    "height": window_info["height"]
                }
                
            output_path = os.path.join(self.capture_dir, "active_window.png")
            try:
                sct_img = self.sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=output_path)
                return output_path
            except Exception:
                # Fallback to full screen if window bounds are outside monitor
                return self.capture_screen()
        return self.capture_screen()
