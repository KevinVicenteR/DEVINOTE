# DEVINOTE

Requiere Python 3.14 y Poetry.

```sh
poetry env use python3.14
POETRY_REQUESTS_TIMEOUT=120 poetry install --no-root
poetry run fastapi dev main.py
```

La aplicación está en `main.py`, en la raíz del proyecto. La documentación
interactiva estará en <http://127.0.0.1:8000/docs>.

El entorno virtual se guarda en `.venv/`. El rango de Python está limitado a
3.14 para evitar seleccionar versiones incompatibles con las dependencias
nativas. Poetry reintenta hasta tres veces las solicitudes fallidas.
