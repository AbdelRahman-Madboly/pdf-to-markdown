from __future__ import annotations

import queue
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import tkinter as tk

from . import __version__
from .config import (
    APP_ICON,
    APP_NAME,
    DEFAULT_OUTPUT_PATH,
    LIGHT_PALETTE,
    LOG_FILENAME,
    SUPPORTED_EXTENSION,
)
from .converter import ConversionError, convert_pdfs


class PdfMarkdownConverterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("980x720")
        self.root.minsize(860, 620)

        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.palette = LIGHT_PALETTE

        self.output_var = tk.StringVar(value=str(DEFAULT_OUTPUT_PATH))
        self.extract_images_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready")
        self.queue_count_var = tk.StringVar(value="0 PDFs queued")
        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.ui_queue: "queue.Queue[object]" = queue.Queue()
        self.pdf_paths: list[Path] = []
        self.log_has_real_content = False
        self.is_running = False

        self.build_ui()
        self.apply_theme()
        self.root.after(100, self.process_log_queue)
        self.root.after(100, self.process_ui_queue)

    def build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        header = ttk.Frame(self.root, style="Header.TFrame", padding=(20, 12, 20, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        self.icon_canvas = tk.Canvas(header, width=30, height=30, highlightthickness=0, bd=0)
        self.icon_canvas.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.draw_header_icon()
        ttk.Label(header, text=APP_NAME, style="HeaderTitle.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(header, text=f"v{__version__}", style="Version.TLabel").grid(row=0, column=2, sticky="e")

        queue_panel = ttk.LabelFrame(self.root, text="PDF Queue", padding=14, style="Panel.TLabelframe")
        queue_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 12))
        queue_panel.columnconfigure(0, weight=1)
        queue_panel.rowconfigure(1, weight=1)

        queue_actions = ttk.Frame(queue_panel, style="Surface.TFrame")
        queue_actions.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        queue_actions.columnconfigure(5, weight=1)
        ttk.Button(queue_actions, text="Add Files", command=self.add_files, style="Primary.TButton").grid(row=0, column=0, padx=(0, 8))
        ttk.Button(queue_actions, text="Add Folder", command=self.add_folder).grid(row=0, column=1, padx=(0, 8))
        self.remove_btn = ttk.Button(queue_actions, text="Remove Selected", command=self.remove_selected, state="disabled")
        self.remove_btn.grid(row=0, column=2, padx=(0, 8))
        self.clear_btn = ttk.Button(queue_actions, text="Clear", command=self.clear_queue, state="disabled")
        self.clear_btn.grid(row=0, column=3, padx=(0, 8))
        ttk.Label(queue_actions, textvariable=self.queue_count_var, style="Muted.Surface.TLabel").grid(row=0, column=5, sticky="e")

        self.queue_list = tk.Listbox(queue_panel, height=9, activestyle="none", exportselection=False, selectmode="extended")
        self.queue_list.grid(row=1, column=0, sticky="nsew")
        self.queue_list.bind("<<ListboxSelect>>", lambda _event: self.update_queue_buttons())
        queue_scroll = ttk.Scrollbar(queue_panel, command=self.queue_list.yview)
        queue_scroll.grid(row=1, column=1, sticky="ns")
        self.queue_list.configure(yscrollcommand=queue_scroll.set)

        output_panel = ttk.LabelFrame(self.root, text="Output", padding=14, style="Panel.TLabelframe")
        output_panel.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))
        output_panel.columnconfigure(0, weight=1)

        ttk.Label(output_panel, text="Output folder", style="Field.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(output_panel, textvariable=self.output_var, style="Mono.TEntry").grid(row=1, column=0, sticky="ew", pady=(4, 10))
        ttk.Button(output_panel, text="Browse", command=self.choose_output_folder).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 10))
        ttk.Checkbutton(output_panel, text="Extract images", variable=self.extract_images_var, style="App.TCheckbutton").grid(row=2, column=0, sticky="w")

        actions = ttk.Frame(output_panel, style="Surface.TFrame")
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions.columnconfigure(7, weight=1)
        self.convert_btn = ttk.Button(actions, text="Convert", command=self.start_conversion, style="Primary.TButton")
        self.convert_btn.grid(row=0, column=0, padx=(0, 8))
        self.open_output_btn = ttk.Button(actions, text="Open Output Folder", command=self.open_output_folder, state="disabled")
        self.open_output_btn.grid(row=0, column=1, padx=(0, 8))
        ttk.Button(actions, text="Copy Log", command=self.copy_log).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(actions, text="Save Log", command=self.save_log).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(actions, text="Clear Log", command=self.clear_log).grid(row=0, column=4, padx=(0, 8))
        ttk.Label(actions, textvariable=self.status_var, style="Status.TLabel").grid(row=0, column=7, sticky="e")

        self.progress = ttk.Progressbar(actions, mode="indeterminate", style="App.Horizontal.TProgressbar")
        self.progress.grid(row=1, column=0, columnspan=8, sticky="ew", pady=(10, 0))

        log_panel = ttk.LabelFrame(self.root, text="Output Log", padding=10, style="Panel.TLabelframe")
        log_panel.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        log_panel.columnconfigure(0, weight=1)
        log_panel.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_panel, height=14, wrap="word", relief="flat", borderwidth=0, padx=12, pady=10, state="normal")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_panel, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.bind("<Control-a>", self.select_all_log)
        self.configure_log_tags()
        self.show_log_placeholder()
        self.update_queue_buttons()

    def draw_header_icon(self) -> None:
        self.icon_canvas.delete("all")
        self.icon_canvas.create_rectangle(6, 3, 23, 27, outline="#2563eb", width=2)
        self.icon_canvas.create_polygon(18, 3, 23, 8, 18, 8, fill="#bfdbfe", outline="#2563eb")
        self.icon_canvas.create_line(9, 12, 20, 12, fill="#16a34a", width=2)
        self.icon_canvas.create_line(9, 17, 20, 17, fill="#16a34a", width=2)
        self.icon_canvas.create_line(9, 22, 17, 22, fill="#16a34a", width=2)

    def apply_theme(self) -> None:
        palette = self.palette
        self.root.configure(bg=palette["window"])
        self.style.configure("Header.TFrame", background=palette["window"])
        self.style.configure("Surface.TFrame", background=palette["surface"])
        self.style.configure("Panel.TLabelframe", background=palette["surface"], foreground=palette["text"], bordercolor=palette["border"], relief="solid")
        self.style.configure("Panel.TLabelframe.Label", background=palette["window"], foreground=palette["text"], font=("Arial", 10, "bold"))
        self.style.configure("HeaderTitle.TLabel", background=palette["window"], foreground=palette["text"], font=("Arial", 15, "bold"))
        self.style.configure("Version.TLabel", background=palette["window"], foreground=palette["muted"], font=("Courier", 9), padding=(6, 2))
        self.style.configure("Muted.Surface.TLabel", background=palette["surface"], foreground=palette["muted"], font=("Arial", 9))
        self.style.configure("Field.TLabel", background=palette["surface"], foreground=palette["muted"], font=("Arial", 8, "bold"))
        self.style.configure("Status.TLabel", background=palette["surface"], foreground=palette["muted"], font=("Courier", 10, "bold"))
        self.style.configure("App.TCheckbutton", background=palette["surface"], foreground=palette["text"], font=("Arial", 9))
        self.style.configure("TButton", padding=(10, 6), background=palette["surface_alt"], foreground=palette["text"], bordercolor=palette["border"])
        self.style.configure("Primary.TButton", padding=(14, 7), background=palette["accent"], foreground="#ffffff", bordercolor=palette["accent"], font=("Arial", 10, "bold"))
        self.style.configure("Mono.TEntry", fieldbackground=palette["surface_alt"], foreground=palette["text"], bordercolor=palette["border"], insertcolor=palette["text"], font=("Courier", 10))
        self.style.configure("App.Horizontal.TProgressbar", troughcolor=palette["surface_alt"], background=palette["success"], bordercolor=palette["border"])
        self.queue_list.configure(bg=palette["log_bg"], fg=palette["text"], selectbackground=palette["accent"], selectforeground="#ffffff", font=("Courier", 10), highlightthickness=1, highlightbackground=palette["border"], relief="flat")
        self.log_text.configure(bg=palette["log_bg"], fg=palette["log_fg"], insertbackground=palette["log_fg"], selectbackground=palette["accent"], selectforeground="#ffffff", font=("Courier", 10))
        self.icon_canvas.configure(bg=palette["window"])
        self.draw_header_icon()

    def configure_log_tags(self) -> None:
        self.log_text.tag_configure("error", foreground="#dc2626")
        self.log_text.tag_configure("success", foreground="#16a34a")
        self.log_text.tag_configure("info", foreground="#2563eb")
        self.log_text.tag_configure("warning", foreground="#d97706")
        self.log_text.tag_configure("placeholder", foreground="#6b7280")

    def log_tag_for(self, message: str) -> str | None:
        lower = message.lower()
        if "error" in lower or "missing" in lower or "failed" in lower:
            return "error"
        if "warning" in lower:
            return "warning"
        if "ok:" in lower or "done" in lower or "saved" in lower:
            return "success"
        if "converting" in lower or "output:" in lower or "queued" in lower:
            return "info"
        return None

    def add_files(self) -> None:
        filenames = filedialog.askopenfilenames(
            title="Choose PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        self.add_paths([Path(name) for name in filenames])

    def add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose folder with PDFs")
        if not folder:
            return
        paths = sorted(Path(folder).glob(f"*{SUPPORTED_EXTENSION}"))
        self.add_paths(paths)

    def add_paths(self, paths: list[Path]) -> None:
        existing = {path.resolve(strict=False) for path in self.pdf_paths}
        added = 0
        skipped = 0
        for path in paths:
            normalized = path.expanduser().resolve(strict=False)
            if normalized in existing:
                skipped += 1
                continue
            self.pdf_paths.append(normalized)
            existing.add(normalized)
            added += 1
        self.refresh_queue()
        if added or skipped:
            self.log(f"Queued {added} PDF(s). Skipped {skipped} duplicate(s).")

    def refresh_queue(self) -> None:
        self.queue_list.delete(0, "end")
        for path in self.pdf_paths:
            self.queue_list.insert("end", f"{path.name}    {path.parent}")
        count = len(self.pdf_paths)
        self.queue_count_var.set(f"{count} PDF{'s' if count != 1 else ''} queued")
        self.update_queue_buttons()

    def update_queue_buttons(self) -> None:
        has_items = bool(self.pdf_paths)
        has_selection = bool(self.queue_list.curselection())
        state = "disabled" if self.is_running else "normal"
        self.remove_btn.configure(state=state if has_selection else "disabled")
        self.clear_btn.configure(state=state if has_items else "disabled")
        self.convert_btn.configure(state=state if has_items else "disabled")

    def remove_selected(self) -> None:
        selected = list(self.queue_list.curselection())
        if not selected:
            return
        for index in reversed(selected):
            self.pdf_paths.pop(index)
        self.refresh_queue()
        self.log(f"Removed {len(selected)} queued PDF(s).")

    def clear_queue(self) -> None:
        removed = len(self.pdf_paths)
        self.pdf_paths.clear()
        self.refresh_queue()
        self.log(f"Cleared {removed} queued PDF(s).")

    def choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.output_var.get() or str(DEFAULT_OUTPUT_PATH))
        if folder:
            self.output_var.set(folder)

    def target_folder(self) -> Path:
        return Path(self.output_var.get().strip() or str(DEFAULT_OUTPUT_PATH)).expanduser()

    def start_conversion(self) -> None:
        if not self.pdf_paths:
            messagebox.showerror("No PDFs queued", "Add at least one PDF before converting.")
            return
        target_folder = self.target_folder()
        target_folder.mkdir(parents=True, exist_ok=True)
        self.is_running = True
        self.update_queue_buttons()
        self.progress.start(10)
        self.status_var.set("Converting...")
        self.log("=" * 80)
        self.log(f"Converting {len(self.pdf_paths)} PDF(s)")
        self.log(f"Output: {target_folder}")
        self.log(f"Extract images: {self.extract_images_var.get()}")
        self.log("")
        paths_snapshot = list(self.pdf_paths)
        threading.Thread(target=self.conversion_worker, args=(paths_snapshot, target_folder, self.extract_images_var.get()), daemon=True).start()

    def conversion_worker(self, paths: list[Path], target_folder: Path, extract_images: bool) -> None:
        try:
            convert_pdfs(paths, target_folder, extract_images=extract_images)
            self.log("Conversion command finished. Verifying Markdown outputs...")
            ok_count = 0
            missing_count = 0
            for path in paths:
                markdown_path = target_folder / f"{path.stem}.md"
                if markdown_path.exists() and markdown_path.stat().st_size > 0:
                    ok_count += 1
                    self.log(f"OK: {path.name} -> {markdown_path.name}")
                else:
                    missing_count += 1
                    self.log(f"MISSING: {path.name} -> {markdown_path.name}")
            self.log(f"Done. OK: {ok_count}. Missing: {missing_count}.")
            self.queue_ui(lambda: self.status_var.set("Done" if missing_count == 0 else "Done with missing files"))
            self.queue_ui(lambda: self.open_output_btn.configure(state="normal"))
        except ConversionError as exc:
            self.log(f"ERROR: {exc}")
            message = str(exc)
            self.queue_ui(lambda: self.status_var.set("Error"))
            self.queue_ui(lambda: messagebox.showerror("Conversion failed", message))
        finally:
            self.queue_ui(self.finish_conversion_ui)

    def queue_ui(self, callback) -> None:
        self.ui_queue.put(callback)

    def process_ui_queue(self) -> None:
        try:
            while True:
                callback = self.ui_queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        self.root.after(100, self.process_ui_queue)

    def finish_conversion_ui(self) -> None:
        self.progress.stop()
        self.is_running = False
        self.update_queue_buttons()

    def open_output_folder(self) -> None:
        target_folder = self.target_folder()
        target_folder.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["xdg-open", str(target_folder)])

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}" if message else "")

    def process_log_queue(self) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()
                if not self.log_has_real_content:
                    self.log_text.configure(state="normal")
                    self.log_text.delete("1.0", "end")
                    self.log_has_real_content = True
                    self.log_text.configure(state="disabled")
                self.log_text.configure(state="normal")
                tag = self.log_tag_for(message)
                if tag:
                    self.log_text.insert("end", message + "\n", tag)
                else:
                    self.log_text.insert("end", message + "\n")
                self.log_text.configure(state="disabled")
                self.log_text.see("end")
        except queue.Empty:
            pass
        self.root.after(100, self.process_log_queue)

    def show_log_placeholder(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", "Log output will appear here after conversion.\n", "placeholder")
        self.log_text.configure(state="disabled")

    def clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.log_has_real_content = False
        self.show_log_placeholder()
        self.status_var.set("Log cleared")

    def copy_log(self) -> None:
        text = "" if not self.log_has_real_content else self.log_text.get("1.0", "end").strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("Log copied")

    def save_log(self) -> None:
        target_folder = self.target_folder()
        target_folder.mkdir(parents=True, exist_ok=True)
        log_path = target_folder / LOG_FILENAME
        text = "" if not self.log_has_real_content else self.log_text.get("1.0", "end")
        log_path.write_text(text, encoding="utf-8")
        self.log(f"Log saved: {log_path}")
        self.status_var.set("Log saved")

    def select_all_log(self, _event=None):
        self.log_text.tag_add("sel", "1.0", "end")
        return "break"


def set_window_icon(root: tk.Tk) -> None:
    if APP_ICON.exists():
        try:
            root.iconphoto(True, tk.PhotoImage(file=str(APP_ICON)))
        except tk.TclError:
            pass


def main() -> None:
    root = tk.Tk()
    set_window_icon(root)
    PdfMarkdownConverterApp(root)
    root.mainloop()
