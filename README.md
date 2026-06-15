# AyudaFácil - Buscador de Ayudas Públicas

Buscador de subvenciones y ayudas públicas con soporte de Lectura Fácil mediante LLM y búsqueda semántica (pgvector).

## Requisitos

- Docker y Docker Compose
- Cuenta/API Key en OpenAI o instancia local de Ollama

## Cómo correr el proyecto

### 1. Configurar variables de entorno

Crea el archivo `backend/.env` y define tu proveedor de IA:

```env
PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_LLM_MODEL=llama3
OLLAMA_EMBED_MODEL=nomic-embed-text

# O si usas OpenAI:
# PROVIDER=openai
# OPENAI_API_KEY=tu_api_key
# OPENAI_LLM_MODEL=gpt-4o-mini
# OPENAI_EMBED_MODEL=text-embedding-3-small
```

### 2. Levantar Docker

Levantar los contenedores:

```bash
docker compose up --build -d
```

Servicios:

- **Frontend**: `http://localhost:5173`
- **FastAPI Backend**: `http://localhost:8000` (docs en `/docs`)
- **n8n**: `http://localhost:5678`

### 3. Configurar n8n

1. Entra a `http://localhost:5678`.
2. Crea tu cuenta de administrador.
3. Importa el archivo `n8n_workflow.json` (menú de arriba a la derecha `...` -> "Import from File").
4. Activa el flujo (marcar "Active").

### 4. Inicializar Base de Datos

Crea las tablas de PostgreSQL y el usuario por defecto:

```bash
docker exec -it ayudafacil_backend python reset_db.py
```

### 5. Correr ETL (Ingesta de datos)

Descarga ayudas reales de la BDNS/BOE e indexa en base de datos (también se puede hacer desde la interfaz, usuario admin contraseña admin):

```bash
docker exec -it ayudafacil_backend python etl_pipeline.py
```

---

## Pruebas

Para correr los tests en local:

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/
```
