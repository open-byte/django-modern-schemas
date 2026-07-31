# Django test app

Este proyecto Django está aislado dentro de `tests/testapp`. No modifica ni
carga las pruebas heredadas de `tests`.

## Contenido

- `library_testapp`: aplicación Django con los modelos `Author` y `Book`.
- `library_testapp/migrations`: migración inicial de los modelos de ejemplo.
- `config/settings.py`: configuración mínima con SQLite en memoria.

La aplicación no incluye pruebas; puede usarse como base para añadirlas más
adelante.
