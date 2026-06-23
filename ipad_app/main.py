import os
import time
import sys
import tempfile

def log_to_file(message):
    error_msgs = []
    dirs_to_try = []
    
    # 1. Sandbox HOME Documents
    home = os.environ.get("HOME")
    if home:
        dirs_to_try.append(os.path.join(home, "Documents"))
    
    # 2. expanduser ~ Documents
    try:
        dirs_to_try.append(os.path.join(os.path.expanduser("~"), "Documents"))
    except Exception as e:
        error_msgs.append(f"expanduser error: {e}")
        
    # 3. Temp dir
    dirs_to_try.append(tempfile.gettempdir())
    
    # 4. Current dir
    dirs_to_try.append(os.getcwd())
    
    for d in dirs_to_try:
        try:
            os.makedirs(d, exist_ok=True)
            log_path = os.path.join(d, "app_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except Exception as e:
            error_msgs.append(f"Failed to write to {d}: {e}")

log_to_file("main.py started.")

import flet as ft

def main(page: ft.Page):
    log_to_file("main() entered.")
    
    page.title = "Math OCR Test"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.colors.BLUE_GREY_900
    
    # Center content
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # Minimal controls
    text_control = ft.Text("Math OCR App Test!", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_ACCENT)
    info_control = ft.Text("Wenn du das siehst, funktioniert Flet! 🎉", size=16, color=ft.colors.WHITE)
    home_control = ft.Text(f"HOME: {os.environ.get('HOME')}", size=10, color=ft.colors.WHITE70)
    
    log_to_file("Adding controls to page...")
    page.add(text_control, info_control, home_control)
    log_to_file("Page updated.")

if __name__ == "__main__":
    ft.app(target=main)
