import os
import time

# Simple log
try:
    doc_dir = os.path.join(os.path.expanduser("~"), "Documents")
    os.makedirs(doc_dir, exist_ok=True)
    with open(os.path.join(doc_dir, "app_log.txt"), "a") as f:
        f.write("Hello World main.py started\n")
except Exception as e:
    pass

import flet as ft

def main(page: ft.Page):
    try:
        doc_dir = os.path.join(os.path.expanduser("~"), "Documents")
        with open(os.path.join(doc_dir, "app_log.txt"), "a") as f:
            f.write("main() started\n")
    except:
        pass

    page.title = "Math OCR Test"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B0C10"
    
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=ft.colors.GREEN, size=80),
                ft.Text("Math OCR App Test!", size=30, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
                ft.Text("Wenn du das siehst, funktioniert die App grundsätzlich! 🎉", size=16, color=ft.colors.WHITE),
                ft.Text(f"Dateipfad: {os.path.expanduser('~')}", size=12, color=ft.colors.GREY_400)
            ], spacing=20, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
