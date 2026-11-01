"""The window is built for real (hidden) when a display is available; otherwise these tests are skipped."""
import tkinter as tk

import pytest

from src.pdf_markdown_converter import app as app_module
from src.pdf_markdown_converter.app import PdfMarkdownConverterApp


@pytest.fixture
def window():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"no display: {exc}")
    root.withdraw()
    win = PdfMarkdownConverterApp(root)
    yield win
    root.destroy()


def test_the_window_builds_with_an_empty_queue(window):
    assert window.root.title() == "PDF to Markdown Converter"
    assert window.queue_count_var.get() == "0 PDFs queued"
    assert str(window.convert_btn["state"]) == "disabled"
    app_module.set_window_icon(window.root)        # the SVG icon may not load in Tk; it must not raise


def test_duplicates_are_skipped_and_the_queue_can_be_cleared(window, tmp_path):
    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    window.add_paths([a, b, a])
    assert window.pdf_paths == [a.resolve(), b.resolve()]
    assert window.queue_count_var.get() == "2 PDFs queued"
    assert str(window.convert_btn["state"]) == "normal"
    window.clear_queue()
    assert window.pdf_paths == [] and str(window.convert_btn["state"]) == "disabled"


def test_log_lines_are_coloured_by_meaning(window):
    assert window.log_tag_for("MISSING: a.pdf -> a.md") == "error"
    assert window.log_tag_for("OK: a.pdf -> a.md") == "success"
    assert window.log_tag_for("Converting 2 PDF(s)") == "info"
    assert window.log_tag_for("plain line") is None


def test_the_worker_reports_each_markdown_file(window, tmp_path, monkeypatch):
    found, lost = tmp_path / "found.pdf", tmp_path / "lost.pdf"
    out = tmp_path / "out"
    out.mkdir()
    (out / "found.md").write_text("# found\n")
    monkeypatch.setattr(app_module, "convert_pdfs", lambda paths, folder, extract_images: None)
    logged = []
    monkeypatch.setattr(window, "log", logged.append)
    window.conversion_worker([found, lost], out, True)
    assert "OK: found.pdf -> found.md" in logged
    assert "MISSING: lost.pdf -> lost.md" in logged
    assert "Done. OK: 1. Missing: 1." in logged


def test_a_failed_conversion_is_logged(window, tmp_path, monkeypatch):
    def fail(paths, folder, extract_images):
        raise app_module.ConversionError("Conversion failed: broken")
    monkeypatch.setattr(app_module, "convert_pdfs", fail)
    logged = []
    monkeypatch.setattr(window, "log", logged.append)
    window.conversion_worker([tmp_path / "x.pdf"], tmp_path, True)
    assert logged == ["ERROR: Conversion failed: broken"]


def test_the_log_loop_does_not_start_extra_ui_loops(window, monkeypatch):
    scheduled = []
    monkeypatch.setattr(window.root, "after", lambda ms, callback: scheduled.append(callback))
    window.process_log_queue()
    window.process_ui_queue()
    assert scheduled == [window.process_log_queue, window.process_ui_queue]
