import os
import time
import traceback
import sys

def log_to_file(message):
    try:
        doc_dir = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.exists(doc_dir):
            os.makedirs(doc_dir, exist_ok=True)
        log_path = os.path.join(doc_dir, "app_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass

log_to_file("main.py execution started.")

IMPORT_ERROR = None
try:
    log_to_file("Importing flet...")
    import flet as ft
    log_to_file("flet imported successfully!")
    
    log_to_file("Importing standard libraries...")
    import shutil
    import threading
    
    log_to_file("Attempting to import gradio_client...")
    from gradio_client import Client
    log_to_file("gradio_client imported successfully!")
except Exception as e:
    IMPORT_ERROR = traceback.format_exc()
    log_to_file(f"Import failed: {IMPORT_ERROR}")

# Hugging Face Settings
HF_SPACE = "MasterSayn/ocr-app-private"
HF_TOKEN = os.environ.get("HF_TOKEN") or "HF_TOKEN_PLACEHOLDER"


def main(page: ft.Page):
    log_to_file("main() entry point reached.")
    if IMPORT_ERROR:
        log_to_file("Displaying import error UI...")
        page.title = "App-Fehler beim Start"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#0B0C10"
        page.add(
            ft.Column([
                ft.Icon(ft.icons.ERROR_OUTLINE_ROUNDED, color=ft.colors.RED, size=50),
                ft.Text("Fehler beim Starten der App (Import-Fehler):", size=20, color=ft.colors.RED, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(IMPORT_ERROR, size=12, color=ft.colors.WHITE, font_family="monospace"),
                    bgcolor="#1F2833",
                    padding=15,
                    border_radius=10,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                ),
                ft.Text(
                    "Dies bedeutet, dass eine Python-Bibliothek (z.B. gradio_client oder eine ihrer Abhängigkeiten wie cryptography) "
                    "nicht mit iOS/iPadOS kompatibel ist, da sie kompilierte C- bzw. Rust-Erweiterungen enthält. "
                    "Falls dies der Fall ist, werde ich die App so umschreiben, dass sie rein über Standard-Web-Anfragen (urllib) mit dem Server kommuniziert.",
                    size=14,
                    color="#C5C6C7"
                )
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        return

    page.title = "Math & Handwritten OCR Central"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    
    # Custom iOS-like styling
    page.bgcolor = "#0B0C10"
    
    # State variables
    selected_file_path = None
    selected_file_name = ""
    downloaded_result_path = None
    
    # Cupertino styles
    PRIMARY_COLOR = "#007AFF" # iOS Blue
    CARD_BG = "#1F2833" # Dark slate card bg
    TEXT_COLOR = "#FFFFFF"
    MUTED_TEXT = "#C5C6C7"
    ACCENT_COLOR = "#66FCF1" # Neon cyan accent

    # File Picker initialization
    def pick_files_result(e: ft.FilePickerResultEvent):
        nonlocal selected_file_path, selected_file_name
        if e.files:
            selected_file_path = e.files[0].path
            selected_file_name = e.files[0].name
            file_name_text.value = selected_file_name
            file_size_text.value = f"Größe: {round(e.files[0].size / 1024 / 1024, 2)} MB"
            start_button.disabled = False
            file_card.border = ft.border.all(2, ACCENT_COLOR)
        else:
            file_name_text.value = "Keine Datei ausgewählt"
            file_size_text.value = ""
            start_button.disabled = True
            file_card.border = ft.border.all(1, ft.colors.OUTLINE)
        page.update()

    def save_file_result(e: ft.FilePickerResultEvent):
        if e.path and downloaded_result_path:
            try:
                shutil.copy(downloaded_result_path, e.path)
                # Show success banner
                page.show_snack_bar(ft.SnackBar(ft.Text("Datei erfolgreich gespeichert! 💾"), bgcolor=ft.colors.GREEN))
            except Exception as ex:
                page.show_snack_bar(ft.SnackBar(ft.Text(f"Fehler beim Speichern: {ex}"), bgcolor=ft.colors.RED))

    file_picker = ft.FilePicker(on_result=pick_files_result)
    save_file_picker = ft.FilePicker(on_result=save_file_result)
    page.overlay.extend([file_picker, save_file_picker])

    # Header Section
    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.AUTO_AWESOME_ROUNDED, color=ACCENT_COLOR, size=40),
                ft.Text("Math & Handwritten OCR", size=32, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text(
                "Konvertiere deine gescannten PDFs in durchsuchbare Dokumente mit mathematischer Formelerkennung.",
                size=16,
                color=MUTED_TEXT,
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=40)
    )

    # File Upload Card
    file_name_text = ft.Text("Tippe, um eine PDF-Datei auszuwählen", size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_500)
    file_size_text = ft.Text("", size=14, color=MUTED_TEXT)
    
    file_card = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.UPLOAD_FILE_ROUNDED, color=PRIMARY_COLOR, size=64),
            file_name_text,
            file_size_text
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=600,
        height=200,
        bgcolor=CARD_BG,
        border_radius=20,
        border=ft.border.all(1, ft.colors.OUTLINE),
        alignment=ft.alignment.center,
        on_click=lambda _: file_picker.pick_files(allowed_extensions=["pdf"]),
        animate=ft.Animation(300, ft.AnimationCurve.DECELERATE)
    )

    # OCR Mode Selection
    mode_radio = ft.RadioGroup(
        value="Schnell (Gemini Full-Page)",
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Radio(value="Schnell (Gemini Full-Page)", label="Schnell (Gemini Full-Page)", fill_color=PRIMARY_COLOR),
                    ft.Column([
                        ft.Text("Extrahiert die ganze Seite auf einmal. Schnellste Verarbeitung.", size=12, color=MUTED_TEXT)
                    ], spacing=1)
                ]),
                padding=10, bgcolor="#2C3539", border_radius=10
            ),
            ft.Container(
                content=ft.Row([
                    ft.Radio(value="Präzise (Hybrid: PaddleOCR + Gemini)", label="Präzise (Hybrid: PaddleOCR + Gemini)", fill_color=PRIMARY_COLOR),
                    ft.Column([
                        ft.Text("Kombiniert lokale Geometrie mit Gemini. Perfekt bei schrägen Texten.", size=12, color=MUTED_TEXT)
                    ], spacing=1)
                ]),
                padding=10, bgcolor="#2C3539", border_radius=10
            ),
            ft.Container(
                content=ft.Row([
                    ft.Radio(value="Lokal Deep (PaddleOCR + TrOCR)", label="Lokal Deep (PaddleOCR + TrOCR)", fill_color=PRIMARY_COLOR),
                    ft.Column([
                        ft.Text("Verarbeitet komplett offline (ohne Gemini) auf dem Hugging Face Space.", size=12, color=MUTED_TEXT)
                    ], spacing=1)
                ]),
                padding=10, bgcolor="#2C3539", border_radius=10
            )
        ], spacing=15)
    )

    mode_card = ft.Container(
        content=ft.Column([
            ft.Text("OCR Modus Auswählen", size=18, color=TEXT_COLOR, weight=ft.FontWeight.BOLD),
            ft.Divider(color=ft.colors.OUTLINE),
            mode_radio
        ]),
        width=600,
        padding=20,
        bgcolor=CARD_BG,
        border_radius=20,
        border=ft.border.all(1, ft.colors.OUTLINE)
    )

    # Processing/Progress Screen
    progress_bar = ft.ProgressBar(width=500, color=ACCENT_COLOR, bgcolor="#2C3539")
    progress_status = ft.Text("Bereite Verarbeitung vor...", size=16, color=TEXT_COLOR)
    progress_spinner = ft.ProgressRing(color=PRIMARY_COLOR)
    
    progress_container = ft.Container(
        content=ft.Column([
            progress_spinner,
            progress_status,
            progress_bar
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
        visible=False
    )

    # Success/Download Card
    def download_click(e):
        if downloaded_result_path:
            save_file_picker.save_file(file_name=f"ocr_{selected_file_name}")

    def reset_click(e):
        nonlocal selected_file_path, selected_file_name, downloaded_result_path
        selected_file_path = None
        selected_file_name = ""
        downloaded_result_path = None
        
        file_name_text.value = "Tippe, um eine PDF-Datei auszuwählen"
        file_size_text.value = ""
        file_card.border = ft.border.all(1, ft.colors.OUTLINE)
        
        start_button.visible = True
        file_card.visible = True
        mode_card.visible = True
        progress_container.visible = False
        result_card.visible = False
        page.update()

    result_card = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=ft.colors.GREEN, size=80),
            ft.Text("Erfolgreich verarbeitet!", size=24, color=TEXT_COLOR, weight=ft.FontWeight.BOLD),
            ft.Text("Dein durchsuchbares PDF wurde erstellt und steht bereit.", size=16, color=MUTED_TEXT),
            ft.Row([
                ft.CupertinoButton(
                    content=ft.Row([
                        ft.Icon(ft.icons.SAVE_ROUNDED, size=20, color=TEXT_COLOR),
                        ft.Text(" In Dateien speichern", color=TEXT_COLOR)
                    ]),
                    on_click=download_click,
                    color=PRIMARY_COLOR
                ),
                ft.CupertinoButton(
                    content=ft.Row([
                        ft.Icon(ft.icons.REFRESH_ROUNDED, size=20, color=TEXT_COLOR),
                        ft.Text(" Neues PDF", color=TEXT_COLOR)
                    ]),
                    on_click=reset_click,
                    color=ft.colors.OUTLINE
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
        visible=False
    )

    # Background Thread for Processing
    def run_ocr():
        nonlocal downloaded_result_path
        try:
            progress_status.value = "Verbindung zum Hugging Face Server wird hergestellt..."
            progress_bar.value = 0.1
            page.update()
            
            client = Client(HF_SPACE, hf_token=HF_TOKEN)
            
            progress_status.value = "PDF wird hochgeladen und verarbeitet (dies kann je nach Modus und Seitenzahl mehrere Minuten dauern)..."
            progress_bar.value = 0.4
            page.update()
            
            result = client.predict(
                selected_file_path,
                mode_radio.value,
                api_name="/process_pdf"
            )
            
            downloaded_result_path = result
            progress_status.value = "Download abgeschlossen!"
            progress_bar.value = 1.0
            page.update()
            
            time.sleep(1)
            
            # Switch to result screen
            progress_container.visible = False
            result_card.visible = True
            page.update()
            
        except Exception as err:
            progress_container.visible = False
            file_card.visible = True
            mode_card.visible = True
            start_button.visible = True
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Verarbeitungsfehler: {err}"), bgcolor=ft.colors.RED))
            page.update()

    def start_ocr_click(e):
        if not selected_file_path:
            return
            
        # Hide selection UI, show loading screen
        start_button.visible = False
        file_card.visible = False
        mode_card.visible = False
        progress_container.visible = True
        page.update()
        
        # Start background thread
        threading.Thread(target=run_ocr, daemon=True).start()

    start_button = ft.CupertinoButton(
        content=ft.Text("OCR Starten 🚀", size=18, color=TEXT_COLOR, weight=ft.FontWeight.BOLD),
        on_click=start_ocr_click,
        disabled=True,
        color=PRIMARY_COLOR,
        width=300
    )

    # Layout compilation
    # Layout compilation
    log_to_file("Assembling layout...")
    page.scroll = ft.ScrollMode.AUTO
    page.add(
        header,
        ft.Row([file_card], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([mode_card], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([start_button], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([progress_container], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([result_card], alignment=ft.MainAxisAlignment.CENTER)
    )
    log_to_file("Layout successfully built and added.")

if __name__ == "__main__":
    ft.app(target=main)
