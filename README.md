# PDF to Markdown Converter

<p align="center">
  <strong>A Linux desktop app for converting PDF files to Markdown with opendataloader-pdf.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> |
  <a href="#requirements">Requirements</a> |
  <a href="#installation">Installation</a> |
  <a href="#usage">Usage</a> |
  <a href="#development">Development</a>
</p>

PDF to Markdown Converter is a simple GUI around [`opendataloader-pdf`](https://pypi.org/project/opendataloader-pdf/). It helps researchers and writers batch-convert PDFs into `.md` files while optionally extracting figures as external image files.

The app is designed for local research workflows where you want Markdown output without memorizing command-line options.

## Features

- Add multiple PDF files to a conversion queue.
- Add a folder and queue every non-recursive `*.pdf` file inside it.
- Review queued filenames, remove selected items, or clear the queue.
- Choose an output folder, with a default under `~/Documents`.
- Convert the whole queue in one `opendataloader-pdf` batch call.
- Optional image extraction, enabled by default.
- Background-thread conversion so the Tkinter window stays responsive.
- Indeterminate progress bar for long-running conversions.
- Per-file Markdown output verification after each run.
- Copyable and saveable logs for debugging.
- Desktop launcher, app-menu launcher, and terminal command installer.

## Screenshots

Add screenshots here after publishing the first GitHub release.

```text
assets/screenshots/main-window.png
```

## Requirements

This project currently targets Ubuntu/Debian-style Linux desktops.

Install system packages:

```bash
sudo apt update
sudo apt install python3 python3-tk openjdk-17-jre -y
```

Java 11 or newer is required by `opendataloader-pdf`.

Install Python requirements:

```bash
pip install -r requirements.txt
```

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

Run the installer:

```bash
chmod +x install_pdf_to_markdown_converter.sh
./install_pdf_to_markdown_converter.sh
```

The installer creates:

| Target | Path / Command |
| --- | --- |
| Terminal command | `pdf-to-markdown-converter` |
| Desktop launcher | `~/Desktop/PDF to Markdown Converter.desktop` |
| App menu launcher | `~/.local/share/applications/pdf-to-markdown-converter.desktop` |

## Launch

After installation:

```bash
pdf-to-markdown-converter
```

Run directly from the project folder:

```bash
python3 pdf_to_markdown_converter.py
```

Run as a module:

```bash
python3 -m src.pdf_markdown_converter
```

## Usage

1. Open PDF to Markdown Converter.
2. Click `Add Files` to queue specific PDFs, or `Add Folder` to queue every PDF in a folder.
3. Review the queue and use `Remove Selected` or `Clear` if needed.
4. Choose the output folder.
5. Keep `Extract images` enabled if you want figures written beside the Markdown.
6. Click `Convert`.
7. Use `Open Output Folder`, `Copy Log`, or `Save Log` after completion.

Example output:

```text
paper-title.md
paper-title-images/
```

## Project Structure

```text
.
|-- assets/
|   `-- pdf-to-markdown-converter.svg
|-- docs/
|   `-- ARCHITECTURE.md
|-- src/
|   `-- pdf_markdown_converter/
|       |-- __init__.py
|       |-- __main__.py
|       |-- app.py
|       |-- config.py
|       `-- converter.py
|-- install_pdf_to_markdown_converter.sh
|-- requirements.txt
|-- README.md
`-- pdf_to_markdown_converter.py
```

## Architecture

The app is split into small modules so the conversion logic can be tested independently from the GUI.

| File | Purpose |
| --- | --- |
| `src/pdf_markdown_converter/app.py` | Tkinter GUI, events, progress, queue, logs |
| `src/pdf_markdown_converter/converter.py` | Pure wrapper around `opendataloader_pdf.convert()` |
| `src/pdf_markdown_converter/config.py` | App constants, palettes, defaults |
| `pdf_to_markdown_converter.py` | Simple top-level compatibility launcher |

## About `pdf_to_markdown_converter.py`

This file is intentionally kept as a convenience launcher:

```python
from src.pdf_markdown_converter.app import main
```

It lets users run the app with:

```bash
python3 pdf_to_markdown_converter.py
```

The main application code lives in `src/pdf_markdown_converter/`.

## Troubleshooting

### Java is missing

Install Java 11 or newer. On Ubuntu/Debian:

```bash
sudo apt install openjdk-17-jre -y
```

### Conversion fails for one PDF

Check the log panel for the exact `opendataloader-pdf` error. Try converting the rest of the queue separately if one PDF is damaged or encrypted.

### Markdown files are missing after a run

The app verifies each expected `.md` file after conversion. If a file is reported missing, inspect the saved log and confirm the output folder is writable.

### Images were not extracted

Make sure `Extract images` is checked before conversion. Run into a fresh output folder when comparing image and no-image output.

## Development

Run syntax checks:

```bash
python3 -m py_compile pdf_to_markdown_converter.py src/pdf_markdown_converter/*.py
bash -n install_pdf_to_markdown_converter.sh
```

Recommended local workflow:

```bash
python3 pdf_to_markdown_converter.py
```

Design and architecture notes:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Roadmap

- Save user preferences for output folder and image extraction.
- Add cancellation support if the upstream API exposes a cancellable process hook.
- Add automated tests for queue handling and converter error mapping.
- Add advanced conversion options only when there is a clear research workflow need.
- Add packaged releases for easier installation.

## Contributing

Issues and pull requests are welcome after the repository is published. Please keep changes focused and avoid mixing UI redesigns with conversion behavior changes in the same pull request.

## License

No license has been selected yet. Add a license before publishing publicly. MIT is a good default for a general-purpose open-source utility.
