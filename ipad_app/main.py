import os
import time
import sys
import tempfile
import traceback

def log_to_file(message):
    home = os.environ.get("HOME")
    dirs_to_try = []
    if home:
        dirs_to_try.append(os.path.join(home, "Documents"))
    try:
        dirs_to_try.append(os.path.join(os.path.expanduser("~"), "Documents"))
    except:
        pass
    dirs_to_try.append(tempfile.gettempdir())
    
    for d in dirs_to_try:
        try:
            os.makedirs(d, exist_ok=True)
            log_path = os.path.join(d, "app_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except:
            pass

log_to_file("main.py started.")

IMPORT_ERROR = None
try:
    log_to_file("Importing flet...")
    import flet as ft
    log_to_file("flet imported successfully!")
    
    log_to_file("Importing standard libraries...")
    import shutil
    import threading
    import urllib.request
    import urllib.parse
    import json
    import uuid
    log_to_file("All imports completed successfully!")
except Exception as e:
    IMPORT_ERROR = traceback.format_exc()
    log_to_file(f"Import failed: {IMPORT_ERROR}")

# Hugging Face Settings
HF_SPACE = "MasterSayn/ocr-app-private"
HF_TOKEN = os.environ.get("HF_TOKEN") or "HF_TOKEN_PLACEHOLDER"

def main(page: ft.Page):
    log_to_file("main() entered.")
    
    if IMPORT_ERROR:
        log_to_file("Displaying import error UI...")
        page.title = "App-Fehler beim Start"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = ft.colors.BLUE_GREY_900
        page.add(
            ft.Column([
                ft.Icon(ft.icons.ERROR_OUTLINE_ROUNDED, color=ft.colors.RED, size=50),
                ft.Text("Fehler beim Starten der App (Import-Fehler):", size=20, color=ft.colors.RED, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(IMPORT_ERROR, size=12, color=ft.colors.WHITE, font_family="monospace"),
                    bgcolor="#1F2833",
                    padding=15,
                    border_radius=10,
                )
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        return

    log_to_file("Setting page configuration...")
    page.title = "Math & Handwritten OCR Central"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    page.bgcolor = ft.colors.BLUE_GREY_900  # Slate gray/blue background to visually verify rendering!
    
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

    log_to_file("Defining File Pickers...")
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
                page.show_snack_bar(ft.SnackBar(ft.Text("Datei erfolgreich gespeichert! 💾"), bgcolor=ft.colors.GREEN))
            except Exception as ex:
                page.show_snack_bar(ft.SnackBar(ft.Text(f"Fehler beim Speichern: {ex}"), bgcolor=ft.colors.RED))

    file_picker = ft.FilePicker(on_result=pick_files_result)
    save_file_picker = ft.FilePicker(on_result=save_file_result)
    page.overlay.extend([file_picker, save_file_picker])

    log_to_file("Building UI components: Header...")
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

    log_to_file("Building UI components: File Card...")
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

    log_to_file("Building UI components: Mode Card...")
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

    log_to_file("Building UI components: Progress container...")
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

    log_to_file("Building UI components: Download / Reset...")
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

    log_to_file("Building UI components: Start button...")
    def run_ocr():
        nonlocal downloaded_result_path
        try:
            log_to_file("run_ocr thread started.")
            progress_status.value = "PDF-Datei wird vorbereitet..."
            progress_bar.value = 0.05
            page.update()
            
            space_url = "https://mastersayn-ocr-app-private.hf.space/gradio_api"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            log_to_file(f"Targeting space: {HF_SPACE} via {space_url}")
            
            # 1. Upload the PDF file
            progress_status.value = "PDF-Datei wird hochgeladen..."
            progress_bar.value = 0.1
            page.update()
            
            log_to_file(f"Uploading file: {selected_file_path}")
            boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
            
            with open(selected_file_path, "rb") as f:
                file_content = f.read()
            
            filename = os.path.basename(selected_file_path)
            
            parts = []
            parts.append(f"--{boundary}".encode('utf-8'))
            parts.append(f'Content-Disposition: form-data; name="files"; filename="{filename}"'.encode('utf-8'))
            parts.append(b"Content-Type: application/pdf")
            parts.append(b"")
            parts.append(file_content)
            parts.append(f"--{boundary}--".encode('utf-8'))
            parts.append(b"")
            
            body = b"\r\n".join(parts)
            
            upload_req = urllib.request.Request(f"{space_url}/upload", data=body)
            for k, v in headers.items():
                upload_req.add_header(k, v)
            upload_req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
            
            with urllib.request.urlopen(upload_req) as r:
                resp = json.loads(r.read().decode('utf-8'))
                log_to_file(f"Upload completed. Response: {resp}")
                remote_file_path = resp[0]
                
            # 2. Join the queue for predictions
            progress_status.value = "Warteschlange beitreten..."
            progress_bar.value = 0.2
            page.update()
            
            session_hash = uuid.uuid4().hex[:10]
            log_to_file(f"Joining queue with session_hash: {session_hash}")
            
            join_data = {
                "data": [
                    {
                        "path": remote_file_path,
                        "orig_name": filename,
                        "meta": {"_type": "gradio.FileData"}
                    },
                    mode_radio.value
                ],
                "fn_index": 0,
                "session_hash": session_hash
            }
            
            join_body = json.dumps(join_data).encode('utf-8')
            join_req = urllib.request.Request(f"{space_url}/queue/join", data=join_body)
            for k, v in headers.items():
                join_req.add_header(k, v)
            join_req.add_header("Content-Type", "application/json")
            
            with urllib.request.urlopen(join_req) as r:
                join_resp = json.loads(r.read().decode('utf-8'))
                log_to_file(f"Join completed. Response: {join_resp}")
                event_id = join_resp["event_id"]
                
            # 3. Listen to SSE queue data stream
            progress_status.value = "Verbindung zum Verarbeitungs-Stream hergestellt..."
            progress_bar.value = 0.3
            page.update()
            
            stream_url = f"{space_url}/queue/data?session_hash={session_hash}"
            log_to_file(f"Listening to stream: {stream_url}")
            
            stream_req = urllib.request.Request(stream_url)
            for k, v in headers.items():
                stream_req.add_header(k, v)
                
            with urllib.request.urlopen(stream_req) as response:
                buffer = ""
                completed = False
                output_file_info = None
                
                while not completed:
                    chunk = response.readline().decode('utf-8')
                    if not chunk:
                        break
                    buffer += chunk
                    if buffer.endswith("\n\n"):
                        lines = buffer.strip().split("\n")
                        buffer = ""
                        for line in lines:
                            if line.startswith("data:"):
                                evt_data = json.loads(line[5:])
                                msg = evt_data.get("msg")
                                log_to_file(f"Queue event: {msg}")
                                
                                if msg == "estimation":
                                    rank = evt_data.get("rank", 0)
                                    queue_size = evt_data.get("queue_size", 1)
                                    progress_status.value = f"In Warteschlange... Position {rank+1} von {queue_size}"
                                    page.update()
                                    
                                elif msg == "process_starts":
                                    progress_status.value = "Verarbeitung gestartet..."
                                    progress_bar.value = 0.4
                                    page.update()
                                    
                                elif msg == "progress":
                                    p_data_list = evt_data.get("progress_data", [])
                                    if p_data_list:
                                        p_item = p_data_list[0]
                                        desc = p_item.get("desc", "Verarbeite...")
                                        prog = p_item.get("progress", None)
                                        if prog is not None:
                                            progress_bar.value = 0.4 + (prog * 0.5)
                                        progress_status.value = desc
                                        page.update()
                                        
                                elif msg == "process_completed":
                                    success = evt_data.get("success", False)
                                    if not success:
                                        raise Exception("Server-seitige Verarbeitung fehlgeschlagen.")
                                    output_file_info = evt_data["output"]["data"][0]
                                    log_to_file(f"Prediction complete. Output file info: {output_file_info}")
                                    completed = True
                                    break
                                    
                                elif msg == "queue_full":
                                    raise Exception("Der Server ist voll ausgelastet. Bitte versuche es später noch einmal.")
                                    
                                elif msg == "close_stream":
                                    completed = True
                                    break
                                    
            if not output_file_info:
                raise Exception("Keine Ergebnisdatei vom Server erhalten.")
                
            # 4. Download the resulting PDF file
            progress_status.value = "Ergebnisdatei wird heruntergeladen..."
            progress_bar.value = 0.9
            page.update()
            
            result_url = output_file_info["url"]
            log_to_file(f"Downloading result from: {result_url}")
            
            download_req = urllib.request.Request(result_url)
            for k, v in headers.items():
                download_req.add_header(k, v)
                
            temp_dir = tempfile.gettempdir()
            local_dest = os.path.join(temp_dir, f"ocr_{uuid.uuid4().hex[:8]}.pdf")
            
            with urllib.request.urlopen(download_req) as dl_resp:
                with open(local_dest, "wb") as f_out:
                    f_out.write(dl_resp.read())
                    
            log_to_file(f"Saved result locally to: {local_dest}")
            downloaded_result_path = local_dest
            
            progress_status.value = "Download abgeschlossen!"
            progress_bar.value = 1.0
            page.update()
            
            time.sleep(1)
            
            progress_container.visible = False
            result_card.visible = True
            page.update()
            
        except Exception as err:
            err_trace = traceback.format_exc()
            log_to_file(f"run_ocr thread encountered error: {err_trace}")
            progress_container.visible = False
            file_card.visible = True
            mode_card.visible = True
            start_button.visible = True
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Verarbeitungsfehler: {err}"), bgcolor=ft.colors.RED))
            page.update()

    def start_ocr_click(e):
        if not selected_file_path:
            return
        start_button.visible = False
        file_card.visible = False
        mode_card.visible = False
        progress_container.visible = True
        page.update()
        threading.Thread(target=run_ocr, daemon=True).start()

    start_button = ft.CupertinoButton(
        content=ft.Text("OCR Starten 🚀", size=18, color=TEXT_COLOR, weight=ft.FontWeight.BOLD),
        on_click=start_ocr_click,
        disabled=True,
        color=PRIMARY_COLOR,
        width=300
    )

    log_to_file("Assembling layout...")
    page.scroll = ft.ScrollMode.AUTO
    
    # We do NOT use expand=True on direct children of page to prevent collapsing!
    page.add(
        header,
        ft.Row([file_card], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([mode_card], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([start_button], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([progress_container], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([result_card], alignment=ft.MainAxisAlignment.CENTER)
    )
    log_to_file("Layout successfully built and added. page.update() next.")
    page.update()
    log_to_file("page.update() completed in main(). App is fully initialized!")

if __name__ == "__main__":
    ft.app(target=main)
