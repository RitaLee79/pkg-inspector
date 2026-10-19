# CLAUDE.md

PKG Inspector: aplicación de escritorio (Tkinter) para mirar por dentro un instalador `.pkg` de
macOS sin instalarlo. Lo abre con `pkgutil --expand`, saca el `Payload` con `cpio` en una carpeta
temporal y enseña el árbol de ficheros que instalaría y sus guiones (preinstall, postinstall…).
Solo funciona en macOS.

## Qué hay en cada sitio

```
pkg_inspector.py   todo el programa (una clase, PKGInspector)
build_mac_app.sh   empaqueta la aplicación con PyInstaller (grupo dev de uv)
package.icns       el icono de la aplicación
dist/              la aplicación compilada; fuera de git
README.md          la lista de cosas pendientes
```

## Cómo se arranca y se comprueba

- `uv run pkg_inspector.py` — abre la ventana; menú File → Open PKG.
- `./build_mac_app.sh` — deja `dist/PKG Inspector.app` y borra `build/` y `__pycache__/`.

**No hay pruebas.** Se prueba a mano: abrir un `.pkg` real y ver que salen el árbol de ficheros y los
guiones, que «mostrar en Finder» y abrir un guion funcionan, y que al cerrar se borra la carpeta
temporal. Pendiente (README): paquetes sin `Payload` y guiones en subcarpetas.

## Qué no se toca

- El `--add-binary` de Tk y Tcl de `build_mac_app.sh` apunta a los del sistema
  (`/System/Library/Frameworks/…`): es ruta de macOS, no de usuario, y se deja.
- El identificador `com.dumb.pkginspector` no se cambia: macOS lo usa para reconocer la aplicación.
