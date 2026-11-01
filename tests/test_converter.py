import shutil
import subprocess
from pathlib import Path

import pytest

from src.pdf_markdown_converter import converter
from src.pdf_markdown_converter.converter import ConversionError, convert_pdfs, normalize_input_paths


def test_an_empty_queue_is_refused():
    with pytest.raises(ConversionError, match="at least one PDF"):
        normalize_input_paths([])


def test_paths_are_expanded(tmp_path):
    paths = normalize_input_paths(["~/a.pdf", tmp_path / "b.pdf"])
    assert paths[0] == Path.home() / "a.pdf" and paths[1] == tmp_path / "b.pdf"


def test_the_whole_queue_goes_in_one_call_with_images(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(converter.opendataloader_pdf, "convert", lambda **kw: calls.append(kw))
    out = tmp_path / "new" / "out"
    result = convert_pdfs([tmp_path / "a.pdf", tmp_path / "b.pdf"], out)
    assert len(calls) == 1
    assert calls[0]["input_path"] == [str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf")]
    assert calls[0]["output_dir"] == str(out) and calls[0]["format"] == ["markdown"]
    assert calls[0]["image_output"] == "external" and result.image_output == "external"
    assert out.is_dir()


def test_images_can_be_turned_off(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(converter.opendataloader_pdf, "convert", lambda **kw: calls.append(kw))
    assert convert_pdfs([tmp_path / "a.pdf"], tmp_path, extract_images=False).image_output == "off"
    assert calls[0]["image_output"] == "off"


@pytest.mark.parametrize("error, shown", [
    (subprocess.CalledProcessError(1, ["java"], output="", stderr="  bad xref table \n"), "bad xref table"),
    (subprocess.CalledProcessError(2, ["java"], output="only stdout", stderr=None), "only stdout"),
    (FileNotFoundError("java"), "java"),
    (ValueError("odd"), "odd"),
])
def test_engine_errors_become_one_readable_error(monkeypatch, tmp_path, error, shown):
    def fail(**kw):
        raise error
    monkeypatch.setattr(converter.opendataloader_pdf, "convert", fail)
    with pytest.raises(ConversionError) as caught:
        convert_pdfs([tmp_path / "a.pdf"], tmp_path)
    assert str(caught.value) == f"Conversion failed: {shown}"


@pytest.mark.skipif(shutil.which("java") is None, reason="opendataloader-pdf needs Java")
def test_a_real_pdf_becomes_markdown(tiny_pdf, tmp_path):
    out = tmp_path / "out"
    convert_pdfs([tiny_pdf], out, extract_images=False)
    markdown = out / "tiny paper.md"
    assert markdown.exists()
    text = markdown.read_text(encoding="utf-8")
    assert "Hello Markdown" in text and "Second line of text" in text
