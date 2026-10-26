#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd -P)"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/Desktop"
APPLICATIONS_DIR="$HOME/.local/share/applications"

CURRENT_DIR="$(pwd -P)"
SOURCE_SCRIPT="$CURRENT_DIR/pdf_to_markdown_converter.py"
SOURCE_SRC_DIR="$CURRENT_DIR/src"
SOURCE_DOCS_DIR="$CURRENT_DIR/docs"
SOURCE_REQUIREMENTS="$CURRENT_DIR/requirements.txt"

if [ ! -f "$SOURCE_SCRIPT" ]; then
  echo "ERROR: pdf_to_markdown_converter.py not found in current folder."
  echo "Run this installer from the extracted package folder."
  exit 1
fi

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$APPLICATIONS_DIR"

# If installer is running from the same install folder, do not copy file onto itself.
# If running from another folder, update the installed script.
if [ "$(realpath "$SOURCE_SCRIPT")" != "$(realpath "$APP_DIR/pdf_to_markdown_converter.py" 2>/dev/null || echo "$APP_DIR/pdf_to_markdown_converter.py")" ]; then
  cp "$SOURCE_SCRIPT" "$APP_DIR/pdf_to_markdown_converter.py"
else
  echo "Source and destination are the same file. Keeping current script in place."
fi

chmod +x "$APP_DIR/pdf_to_markdown_converter.py"

SOURCE_PACKAGE="$SOURCE_SRC_DIR/pdf_markdown_converter"
TARGET_PACKAGE="$APP_DIR/src/pdf_markdown_converter"
if [ -d "$SOURCE_PACKAGE" ]; then
  mkdir -p "$APP_DIR/src"
  if [ "$(realpath "$SOURCE_PACKAGE")" != "$(realpath "$TARGET_PACKAGE" 2>/dev/null || echo "$TARGET_PACKAGE")" ]; then
    rm -rf "$TARGET_PACKAGE"
    cp -R "$SOURCE_PACKAGE" "$TARGET_PACKAGE"
  else
    echo "Source and destination package are the same folder. Keeping current package in place."
  fi
fi

if [ -d "$SOURCE_DOCS_DIR" ]; then
  mkdir -p "$APP_DIR/docs"
  if [ "$(realpath "$SOURCE_DOCS_DIR")" != "$(realpath "$APP_DIR/docs" 2>/dev/null || echo "$APP_DIR/docs")" ]; then
    cp -R "$SOURCE_DOCS_DIR/." "$APP_DIR/docs/"
  else
    echo "Source and destination docs are the same folder. Keeping current docs in place."
  fi
fi

if [ -f "$SOURCE_REQUIREMENTS" ]; then
  if [ "$(realpath "$SOURCE_REQUIREMENTS")" != "$(realpath "$APP_DIR/requirements.txt" 2>/dev/null || echo "$APP_DIR/requirements.txt")" ]; then
    cp "$SOURCE_REQUIREMENTS" "$APP_DIR/requirements.txt"
  else
    echo "Source and destination requirements are the same file. Keeping current requirements in place."
  fi
fi

PYTHON_BIN="python3"
for candidate in "$HOME/miniconda3/bin/python3" "$HOME/anaconda3/bin/python3"; do
  if [ -x "$candidate" ] && "$candidate" -c "import tkinter, opendataloader_pdf" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

cat > "$BIN_DIR/pdf-to-markdown-converter" <<LAUNCHER
#!/usr/bin/env bash
"$PYTHON_BIN" "$APP_DIR/pdf_to_markdown_converter.py"
LAUNCHER
chmod +x "$BIN_DIR/pdf-to-markdown-converter"

cat > "$APPLICATIONS_DIR/pdf-to-markdown-converter.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=PDF to Markdown Converter
Comment=Convert PDF files to Markdown with opendataloader-pdf
Exec=$BIN_DIR/pdf-to-markdown-converter
Icon=$APP_DIR/assets/pdf-to-markdown-converter.svg
Terminal=false
Categories=Utility;Office;
DESKTOP

chmod +x "$APPLICATIONS_DIR/pdf-to-markdown-converter.desktop"

SOURCE_ICON="$CURRENT_DIR/assets/pdf-to-markdown-converter.svg"
TARGET_ICON="$APP_DIR/assets/pdf-to-markdown-converter.svg"
if [ -f "$SOURCE_ICON" ]; then
  mkdir -p "$APP_DIR/assets"
  if [ "$(realpath "$SOURCE_ICON")" != "$(realpath "$TARGET_ICON" 2>/dev/null || echo "$TARGET_ICON")" ]; then
    cp "$SOURCE_ICON" "$TARGET_ICON"
  else
    echo "Source and destination icon are the same file. Keeping current icon in place."
  fi
fi

cp "$APPLICATIONS_DIR/pdf-to-markdown-converter.desktop" "$DESKTOP_DIR/PDF to Markdown Converter.desktop"
chmod +x "$DESKTOP_DIR/PDF to Markdown Converter.desktop"
gio set "$DESKTOP_DIR/PDF to Markdown Converter.desktop" metadata::trusted true 2>/dev/null || true

echo ""
echo "Installed / updated successfully with no conflict."
echo ""
echo "Tool path:"
echo "  $APP_DIR"
echo ""
echo "Run from terminal:"
echo "  pdf-to-markdown-converter"
echo ""
echo "Desktop launcher:"
echo "  $DESKTOP_DIR/PDF to Markdown Converter.desktop"
