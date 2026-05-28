# Backend Python + PostgreSQL (Render Ready)

API REST con CRUD de usuarios, ajustada completamente a entorno Python y lista para desplegar en Render.

## Stack

- Python 3.12
- Flask
- PostgreSQL (`psycopg2-binary`)
- Gunicorn para produccion
- `python-dotenv` para variables de entorno

## Estructura

- `api/app.py`: app Flask
- `routes/user_routes.py`: rutas `/api/users`
- `controllers/user_controller.py`: validaciones y respuestas HTTP
- `models/user_model.py`: consultas SQL
- `database/db.py`: conexion a PostgreSQL
- `database/schema.sql`: esquema y datos iniciales
- `database/init_schema.py`: ejecuta el esquema
- `scraper/exito_scraper.py`: scraping con Scrapling y guardado en PostgreSQL (Exito)
- `scraper/adidas_scraper.py`: scraping con Scrapling y guardado en PostgreSQL (Adidas)
- `render.yaml`: blueprint para Render

## Endpoints

- `GET /api/users` -> listar usuarios
- `POST /api/users` -> crear usuario
- `PUT /api/users/:id` -> actualizar usuario
- `DELETE /api/users/:id` -> eliminar usuario

## Ejecutar local

1. Crear y activar entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Crear `.env` desde `.env.example`:

```env
PORT=3000
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DB_NAME
PYTHON_VERSION=3.12.3
```

4. Inicializar esquema:

```bash
python database/init_schema.py
```

5. Levantar API:

```bash
python api/app.py
```

Servidor local: `http://localhost:3000`

## Scrapers (Scrapling)

Estos scripts siguen la guia de Scrapling para extraer productos y guardar los datos en la BD.

Exito:
```bash
python scraper/exito_scraper.py --search "tenis" --max-items 10
```

Adidas:
```bash
python scraper/adidas_scraper.py --search "ultraboost" --max-items 10
```

Periodic scheduler
------------------

You can run a periodic job that scrapes multiple brands and categories and writes JSON outputs (dry-run by default). Install `apscheduler` and run:

```powershell
pip install -r requirements.txt
# dry-run (no DB writes)
python backend/scraper/run_scheduler.py --interval 3600 --brands adidas,nike,puma --max-items 5

# to persist into PostgreSQL, set the env var and run (PowerShell):
$env:DATABASE_URL = 'postgresql://USER:PASS@HOST:5432/DB'
$env:ENABLE_PERSIST = '1'
python backend/scraper/run_scheduler.py --interval 3600 --brands adidas,nike,puma --max-items 5
```

The scheduler writes run outputs to `scrape_runs/` by default.

Notas:
1. Inserta o actualiza registros en `products` y registra precios en `product_prices`.
2. Si `--search` no se envia, la categoria se guarda como `General`.

## Despliegue en Render

### Opcion 1: Blueprint (`render.yaml`) recomendado

1. Sube este repo a GitHub.
2. En Render: `New +` -> `Blueprint`.
3. Selecciona el repositorio.
4. Render creara automaticamente:
   - servicio web `tecnologias-api` (Python)
   - base de datos PostgreSQL `tecnologias-db`
5. Cuando termine el primer deploy, ejecuta una vez en Shell del servicio:

```bash
python database/init_schema.py
```

### Opcion 2: Manual

1. Crear PostgreSQL en Render.
2. Crear Web Service Python conectado al repo.
3. Variables:
   - `DATABASE_URL=<connection string de Postgres en Render>`
4. Build Command:

```bash
pip install -r requirements.txt
```

5. Start Command:

```bash
gunicorn api.app:app
```

6. Ejecutar esquema una vez:

```bash
python database/init_schema.py
```
