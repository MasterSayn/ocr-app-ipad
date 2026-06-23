import os
import time
import sys
import tempfile
import traceback
import asyncio

def log_to_file(message):
    """Write log to all accessible directories for debugging."""
    home = os.environ.get("HOME")
    dirs_to_try = []
    if home:
        dirs_to_try.append(os.path.join(home, "Documents"))
    try:
        dirs_to_try.append(os.path.join(os.path.expanduser("~"), "Documents"))
    except Exception:
        pass
    dirs_to_try.append(tempfile.gettempdir())

    for d in dirs_to_try:
        try:
            os.makedirs(d, exist_ok=True)
            log_path = os.path.join(d, "app_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except Exception:
            pass

log_to_file("main.py started.")

# ---- Safe imports with error capture ----
IMPORT_ERROR = None
try:
    log_to_file("Importing flet...")
    import flet as ft
    log_to_file(f"flet imported successfully! Version: {getattr(ft, 'version', 'unknown')}")

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

def border_all(width, color):
    return ft.Border(
        ft.BorderSide(width, color),
        ft.BorderSide(width, color),
        ft.BorderSide(width, color),
        ft.BorderSide(width, color)
    )

def show_error_on_page(page, title, error_text):
    """Helper: display an error message on the page so it's visible on the iPad."""
    try:
        page.clean()
        page.bgcolor = "#1B2631"
        page.add(
            ft.Column(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=50),
                    ft.Text(title, size=20, color=ft.Colors.RED, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(
                            str(error_text),
                            size=11,
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor="#1F2833",
                        padding=15,
                        border_radius=10,
                        width=700,
                    ),
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            )
        )
        page.update()
    except Exception as inner_err:
        log_to_file(f"CRITICAL: Could not even display error on page: {inner_err}")


async def main(page: ft.Page):
    log_to_file("main() entered.")

    # ---- Handle import errors ----
    if IMPORT_ERROR:
        log_to_file("Displaying import error UI...")
        page.title = "App-Fehler"
        page.theme_mode = ft.ThemeMode.DARK
        show_error_on_page(page, "Fehler beim Starten (Import-Fehler):", IMPORT_ERROR)
        return

    # ---- Wrap EVERYTHING in try/except so any crash is visible ----
    try:
        log_to_file("Setting page configuration...")
        page.title = "Math & Handwritten OCR Central"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 30
        page.bgcolor = "#1B2631"

        # State variables
        selected_file_path = None
        selected_file_name = ""
        downloaded_result_path = None

        # Style constants
        PRIMARY_COLOR = "#007AFF"
        CARD_BG = "#1F2833"
        TEXT_COLOR = "#FFFFFF"
        MUTED_TEXT = "#C5C6C7"
        ACCENT_COLOR = "#66FCF1"

        # ---- Snack bar for status messages ----
        status_snack = ft.SnackBar(content=ft.Text(""), bgcolor=ft.Colors.GREEN)
        page.overlay.append(status_snack)

        log_to_file("Building UI components: Header...")
        header = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.AUTO_AWESOME, color=ACCENT_COLOR, size=40),
                            ft.Text("Math & Handwritten OCR", size=28, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        "Konvertiere deine gescannten PDFs in durchsuchbare Dokumente.",
                        size=15,
                        color=MUTED_TEXT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            margin=ft.Margin(0, 0, 0, 30),
        )

        log_to_file("Building UI components: File Card...")
        file_name_text = ft.Text("Tippe, um eine PDF-Datei auszuwaehlen", size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_500)
        file_size_text = ft.Text("", size=14, color=MUTED_TEXT)

        async def pick_files_click(e):
            nonlocal selected_file_path, selected_file_name
            try:
                log_to_file("Opening file picker...")
                picker = ft.FilePicker()
                # pick_files is async and returns selected files directly
                result = await picker.pick_files(allowed_extensions=["pdf"])
                
                if result and result[0].path:
                    selected_file_path = result[0].path
                    selected_file_name = result[0].name
                    file_name_text.value = selected_file_name
                    file_size_text.value = f"Groesse: {round(result[0].size / 1024 / 1024, 2)} MB"
                    start_button.disabled = False
                    file_card.border = border_all(2, ACCENT_COLOR)
                    log_to_file(f"File selected: {selected_file_name}")
                else:
                    file_name_text.value = "Tippe, um eine PDF-Datei auszuwaehlen"
                    file_size_text.value = ""
                    start_button.disabled = True
                    file_card.border = border_all(1, "#555555")
                    log_to_file("File picking cancelled.")
                page.update()
            except Exception as ex:
                log_to_file(f"pick_files error: {traceback.format_exc()}")

        file_card = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.UPLOAD_FILE, color=PRIMARY_COLOR, size=60),
                    file_name_text,
                    file_size_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=550,
            height=180,
            bgcolor=CARD_BG,
            border_radius=18,
            border=border_all(1, "#555555"),
            alignment=ft.Alignment(0, 0),
            on_click=pick_files_click,
        )

        log_to_file("Building UI components: Mode Card...")
        mode_radio = ft.RadioGroup(
            value="Schnell (Gemini Full-Page)",
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Radio(value="Schnell (Gemini Full-Page)", label="Schnell (Gemini Full-Page)", fill_color=PRIMARY_COLOR),
                            ]
                        ),
                        padding=10,
                        bgcolor="#2C3539",
                        border_radius=10,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Radio(value="Praezise (Hybrid: PaddleOCR + Gemini)", label="Praezise (Hybrid)", fill_color=PRIMARY_COLOR),
                            ]
                        ),
                        padding=10,
                        bgcolor="#2C3539",
                        border_radius=10,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Radio(value="Lokal Deep (PaddleOCR + TrOCR)", label="Lokal Deep (Offline)", fill_color=PRIMARY_COLOR),
                            ]
                        ),
                        padding=10,
                        bgcolor="#2C3539",
                        border_radius=10,
                    ),
                ],
                spacing=12,
            ),
        )

        mode_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("OCR Modus Auswaehlen", size=18, color=TEXT_COLOR, weight=ft.FontWeight.BOLD),
                    ft.Divider(color="#555555"),
                    mode_radio,
                ]
            ),
            width=550,
            padding=20,
            bgcolor=CARD_BG,
            border_radius=18,
            border=border_all(1, "#555555"),
        )

        log_to_file("Building UI components: Progress container...")
        progress_bar = ft.ProgressBar(width=450, color=ACCENT_COLOR, bgcolor="#2C3539")
        progress_status = ft.Text("Bereite Verarbeitung vor...", size=16, color=TEXT_COLOR)
        progress_spinner = ft.ProgressRing(color=PRIMARY_COLOR)

        progress_container = ft.Container(
            content=ft.Column(
                [progress_spinner, progress_status, progress_bar],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            visible=False,
        )

        log_to_file("Building UI components: Result card...")

        async def download_click(e):
            nonlocal downloaded_result_path
            if downloaded_result_path:
                try:
                    log_to_file("Opening save file dialog...")
                    picker = ft.FilePicker()
                    # save_file is async and returns the selected path directly on mobile/web
                    # On mobile/web, we MUST pass src_bytes as it doesn't give us direct filesystem write access
                    with open(downloaded_result_path, "rb") as f:
                        file_bytes = f.read()
                    
                    save_path = await picker.save_file(
                        file_name=f"ocr_{selected_file_name}",
                        file_type=ft.FilePickerFileType.CUSTOM,
                        allowed_extensions=["pdf"],
                        src_bytes=file_bytes
                    )
                    
                    if save_path:
                        log_to_file(f"Saved file to: {save_path}")
                        status_snack.content = ft.Text("Datei erfolgreich gespeichert!")
                        status_snack.bgcolor = ft.Colors.GREEN
                        status_snack.open = True
                        page.update()
                except Exception as ex:
                    log_to_file(f"save_file_result error: {traceback.format_exc()}")

        async def reset_click(e):
            nonlocal selected_file_path, selected_file_name, downloaded_result_path
            selected_file_path = None
            selected_file_name = ""
            downloaded_result_path = None
            file_name_text.value = "Tippe, um eine PDF-Datei auszuwaehlen"
            file_size_text.value = ""
            file_card.border = border_all(1, "#555555")
            start_button.visible = True
            file_card.visible = True
            mode_card.visible = True
            progress_container.visible = False
            result_card.visible = False
            page.update()

        result_card = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.GREEN, size=70),
                    ft.Text("Erfolgreich verarbeitet!", size=22, color=TEXT_COLOR, weight=ft.FontWeight.BOLD),
                    ft.Text("Dein durchsuchbares PDF wurde erstellt.", size=15, color=MUTED_TEXT),
                    ft.Row(
                        [
                            ft.Button(
                                content="In Dateien speichern",
                                icon=ft.Icons.SAVE,
                                on_click=download_click,
                                color=TEXT_COLOR,
                                bgcolor=PRIMARY_COLOR,
                            ),
                            ft.Button(
                                content="Neues PDF",
                                icon=ft.Icons.REFRESH,
                                on_click=reset_click,
                                color=TEXT_COLOR,
                                bgcolor="#555555",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
            ),
            visible=False,
        )

        log_to_file("Building UI components: Start button and OCR logic...")

        async def run_ocr():
            nonlocal downloaded_result_path
            try:
                log_to_file("run_ocr async task started.")
                progress_status.value = "PDF-Datei wird vorbereitet..."
                progress_bar.value = 0.05
                page.update()

                loop = asyncio.get_event_loop()
                space_url = "https://mastersayn-ocr-app-private.hf.space/gradio_api"
                auth_headers = {"Authorization": f"Bearer {HF_TOKEN}"}
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
                parts.append(f"--{boundary}".encode("utf-8"))
                parts.append(f'Content-Disposition: form-data; name="files"; filename="{filename}"'.encode("utf-8"))
                parts.append(b"Content-Type: application/pdf")
                parts.append(b"")
                parts.append(file_content)
                parts.append(f"--{boundary}--".encode("utf-8"))
                parts.append(b"")

                body = b"\r\n".join(parts)

                upload_req = urllib.request.Request(f"{space_url}/upload", data=body)
                for k, v in auth_headers.items():
                    upload_req.add_header(k, v)
                upload_req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

                # Run blocking upload request in thread pool
                def perform_upload():
                    with urllib.request.urlopen(upload_req, timeout=120) as r:
                        return json.loads(r.read().decode("utf-8"))

                resp = await loop.run_in_executor(None, perform_upload)
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
                            "meta": {"_type": "gradio.FileData"},
                        },
                        mode_radio.value,
                    ],
                    "fn_index": 0,
                    "session_hash": session_hash,
                }

                join_body = json.dumps(join_data).encode("utf-8")
                join_req = urllib.request.Request(f"{space_url}/queue/join", data=join_body)
                for k, v in auth_headers.items():
                    join_req.add_header(k, v)
                join_req.add_header("Content-Type", "application/json")

                # Run blocking join request in thread pool
                def perform_join():
                    with urllib.request.urlopen(join_req, timeout=30) as r:
                        return json.loads(r.read().decode("utf-8"))

                join_resp = await loop.run_in_executor(None, perform_join)
                log_to_file(f"Join completed. Response: {join_resp}")
                event_id = join_resp.get("event_id", "unknown")

                # 3. Listen to SSE queue data stream
                progress_status.value = "Verbindung zum Server hergestellt..."
                progress_bar.value = 0.3
                page.update()

                stream_url = f"{space_url}/queue/data?session_hash={session_hash}"
                log_to_file(f"Listening to stream: {stream_url}")

                stream_req = urllib.request.Request(stream_url)
                for k, v in auth_headers.items():
                    stream_req.add_header(k, v)

                # Queue to transfer events from reading thread to event loop
                event_queue = asyncio.Queue()

                def run_stream_reader():
                    try:
                        with urllib.request.urlopen(stream_req, timeout=600) as response:
                            buffer = ""
                            completed = False
                            while not completed:
                                chunk = response.readline().decode("utf-8")
                                if not chunk:
                                    break
                                buffer += chunk
                                if buffer.endswith("\n\n"):
                                    lines = buffer.strip().split("\n")
                                    buffer = ""
                                    for line in lines:
                                        if line.startswith("data:"):
                                            try:
                                                evt_data = json.loads(line[5:])
                                            except json.JSONDecodeError:
                                                continue
                                            
                                            # Put event in queue thread-safely
                                            loop.call_soon_threadsafe(event_queue.put_nowait, evt_data)
                                            
                                            msg = evt_data.get("msg")
                                            if msg in ["process_completed", "queue_full", "close_stream"]:
                                                completed = True
                                                break
                    except Exception as stream_err:
                        loop.call_soon_threadsafe(event_queue.put_nowait, {"msg": "error", "error": str(stream_err)})

                # Start background thread for stream reading
                threading.Thread(target=run_stream_reader, daemon=True).start()

                # Process events in the main event loop (non-blocking)
                completed = False
                output_file_info = None

                while not completed:
                    evt_data = await event_queue.get()
                    msg = evt_data.get("msg")
                    log_to_file(f"Queue event received in event loop: {msg}")

                    if msg == "error":
                        raise Exception(evt_data.get("error", "Stream error"))

                    elif msg == "estimation":
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
                        log_to_file(f"Prediction complete. Output: {output_file_info}")
                        completed = True

                    elif msg == "queue_full":
                        raise Exception("Server voll ausgelastet. Bitte spaeter versuchen.")

                    elif msg == "close_stream":
                        completed = True

                if not output_file_info:
                    raise Exception("Keine Ergebnisdatei vom Server erhalten.")

                # 4. Download the resulting PDF file
                progress_status.value = "Ergebnisdatei wird heruntergeladen..."
                progress_bar.value = 0.9
                page.update()

                result_url = output_file_info["url"]
                log_to_file(f"Downloading result from: {result_url}")

                download_req = urllib.request.Request(result_url)
                for k, v in auth_headers.items():
                    download_req.add_header(k, v)

                temp_dir = tempfile.gettempdir()
                local_dest = os.path.join(temp_dir, f"ocr_{uuid.uuid4().hex[:8]}.pdf")

                def perform_download():
                    with urllib.request.urlopen(download_req, timeout=120) as dl_resp:
                        with open(local_dest, "wb") as f_out:
                            f_out.write(dl_resp.read())

                await loop.run_in_executor(None, perform_download)
                log_to_file(f"Saved result locally to: {local_dest}")
                downloaded_result_path = local_dest

                progress_status.value = "Download abgeschlossen!"
                progress_bar.value = 1.0
                page.update()

                await asyncio.sleep(1)

                progress_container.visible = False
                result_card.visible = True
                page.update()

            except Exception as err:
                err_trace = traceback.format_exc()
                log_to_file(f"run_ocr error: {err_trace}")
                progress_container.visible = False
                file_card.visible = True
                mode_card.visible = True
                start_button.visible = True
                show_error_on_page(page, "Verarbeitungsfehler:", err_trace)

        async def start_ocr_click(e):
            if not selected_file_path:
                return
            start_button.visible = False
            file_card.visible = False
            mode_card.visible = False
            progress_container.visible = True
            page.update()
            page.run_task(run_ocr)

        start_button = ft.Button(
            content="OCR Starten",
            icon=ft.Icons.PLAY_ARROW,
            on_click=start_ocr_click,
            disabled=True,
            color=TEXT_COLOR,
            bgcolor=PRIMARY_COLOR,
            width=280,
            height=50,
        )

        log_to_file("Assembling page layout...")
        page.scroll = ft.ScrollMode.AUTO

        # Use ft.Column as root container to avoid layout collapse
        root_column = ft.Column(
            [
                header,
                ft.Row([file_card], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([mode_card], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=15),
                ft.Row([start_button], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([progress_container], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([result_card], alignment=ft.MainAxisAlignment.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        page.add(root_column)
        log_to_file("Layout added to page. Calling page.update()...")
        page.update()
        log_to_file("page.update() completed. App fully initialized!")

    except Exception as build_err:
        err_trace = traceback.format_exc()
        log_to_file(f"FATAL UI BUILD ERROR: {err_trace}")
        show_error_on_page(page, "FATAL: UI konnte nicht aufgebaut werden:", err_trace)


if __name__ == "__main__":
    ft.run(main)
