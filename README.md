# PDF to Markdown Converter

<img src="docs/readme-icon.png" width="96" align="right" alt="PDF to Markdown Converter icon">

A small Linux desktop app that turns PDF files into Markdown. It is a Tkinter window around
[`opendataloader-pdf`](https://pypi.org/project/opendataloader-pdf/): queue PDFs, pick an output folder,
press Convert, and get one `.md` file per PDF, with figures saved as image files if you want them.

## Status

1.0.0. Used daily on Ubuntu, no known bugs. The tests run in CI on every push.

## What it does

- Queue single PDFs or every `*.pdf` in a folder (not recursive); duplicates are skipped.
- Convert the whole queue in one `opendataloader-pdf` call (one Java start for the batch).
- Extract images next to the Markdown (on by default) or leave them out.
- Check after the run that every PDF produced a non-empty `.md` file and list any that did not.
- Keep a log you can copy or save into the output folder.

Output for `paper.pdf`:

```text
paper.md             plus a folder of extracted images when Extract images is on and the PDF has figures
```

## What it does not do

- No OCR: a scanned PDF with no text layer gives little or no text.
- No per-file progress or cancel button: the upstream call runs the batch as one job.
- No password prompt for encrypted PDFs, and no settings are remembered between runs.
- Linux only (tested on Ubuntu); it uses `xdg-open` to open the output folder.

## Install

```bash
sudo apt install python3 python3-tk openjdk-17-jre    # Java 11 or newer is needed
pip install -r requirements.txt
./install_pdf_to_markdown_converter.sh
```

The installer writes the `pdf-to-markdown-converter` command to `~/.local/bin`, a menu entry in
`~/.local/share/applications` and a launcher on the Desktop. It picks a Python that has both Tkinter
and `opendataloader-pdf` (a Miniconda or Anaconda one first, if present). Run it again after moving the
folder.

## Run

```bash
pdf-to-markdown-converter            # after installing
python3 pdf_to_markdown_converter.py # straight from the folder
python3 -m src.pdf_markdown_converter
```

## Develop

```bash
pip install -r requirements.txt pytest
python3 -m pytest -q
```

The tests build a one-page PDF by hand and convert it for real; that test is skipped when Java is not
installed. The window tests build the real window hidden and are skipped when there is no display
(CI runs them under `xvfb-run`).

| File | Purpose |
|---|---|
| `src/pdf_markdown_converter/converter.py` | The conversion call and its error messages, no GUI code |
| `src/pdf_markdown_converter/app.py` | Tkinter window, queue, background thread, log |
| `src/pdf_markdown_converter/config.py` | Names, default output folder, colours |
| `docs/ARCHITECTURE.md` | Module layout and design rules |

## License

MIT, see [LICENSE](LICENSE).

## Author

Designed and built by Abdel Rahman Mohamad EL-Sayed ([AbdelRahman-Madboly](https://github.com/AbdelRahman-Madboly) on GitHub).
