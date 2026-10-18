#!/bin/bash

# Build the macOS application (PyInstaller viene del grupo dev de uv)
uv run pyinstaller \
    --name "PKG Inspector" \
    --windowed \
    --onefile \
    --icon package.icns \
    --add-binary '/System/Library/Frameworks/Tk.framework/Tk':'tk' \
    --add-binary '/System/Library/Frameworks/Tcl.framework/Tcl':'tcl' \
    --osx-bundle-identifier "com.dumb.pkginspector" \
    pkg_inspector.py

# Clean up build artifacts
rm -rf build
rm -rf __pycache__

echo "Build complete: dist/PKG Inspector.app"