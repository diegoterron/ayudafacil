from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List

import hashlib
from app.database import init_db, get_db
from app.logging_config import logger
from app.models import Ayuda, Usuario, HistorialConsulta, FragmentoAyuda
from app.schemas import (
    SearchResponseItem,
    AyudaDetailResponse,
    VersionSimplificadaSchema,
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileUpdate,
    HistorialResponse,
    AyudaCreateInput
)
from app.services.search_service import search_service
from app.services.llm_service import llm_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("db init")
    init_db()
    yield

app = FastAPI(
    title="AyudaFácil API",
    description="AyudaFácil Backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "AyudaFácil Backend"}

@app.get("/api/search", response_model=List[SearchResponseItem])
def search_ayudas(
    q: str = Query(..., description="Texto de búsqueda en lenguaje natural"),
    user_id: int = Query(None, description="ID del usuario logueado"),
    db: Session = Depends(get_db)
):
    """busqueda hibrida de ayudas"""
    try:
        results = search_service.hybrid_search(db=db, query_text=q, usuario_id=user_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda híbrida: {str(e)}")

@app.get("/api/ayudas/{id}", response_model=AyudaDetailResponse)
def get_ayuda_detail(
    id: int,
    db: Session = Depends(get_db)
):
    """detalle de una ayuda"""
    ayuda = db.query(Ayuda).filter(Ayuda.id == id).first()
    if not ayuda:
        raise HTTPException(status_code=404, detail="Ayuda no encontrada")

    atributos = []
    if ayuda.atributos_json:
        atributos = ayuda.atributos_json

    version_simplificada = None
    if ayuda.lectura_facil_json:
        lf_data = ayuda.lectura_facil_json
        version_simplificada = VersionSimplificadaSchema(
            queEs=lf_data.get("queEs", ""),
            quienPuedePedir=lf_data.get("quienPuedePedir", ""),
            cuantoDan=lf_data.get("cuantoDan", ""),
            plazoComoPedir=lf_data.get("plazoComoPedir", "")
        )
    else:
        logger.info("generando lf ayuda %s", ayuda.id)
        try:
            lf_obj = llm_service.generate_easy_read(
                official_text=ayuda.descripcion_oficial,
                title=ayuda.titulo
            )
            version_simplificada = lf_obj
            
            ayuda.lectura_facil_json = lf_obj.model_dump()
            db.commit()
            db.refresh(ayuda)
        except Exception as e:
            logger.warning(e)
            version_simplificada = VersionSimplificadaSchema(
                queEs="Información no simplificada. Por favor, consulte la sección oficial.",
                quienPuedePedir="Consulte el BOE adjunto.",
                cuantoDan="Consulte el BOE adjunto.",
                plazoComoPedir="Consulte el BOE adjunto."
            )

    return AyudaDetailResponse(
        id=ayuda.id,
        codigo_bdns=ayuda.codigo_bdns,
        titulo=ayuda.titulo,
        titulo_simplificado=ayuda.titulo_simplificado,
        organismo=ayuda.organismo,
        categoria=ayuda.categoria,
        cuantia=ayuda.cuantia,
        plazo=ayuda.plazo,
        plazo_abierto=ayuda.plazo_abierto,
        es_para_particulares=ayuda.es_para_particulares,
        es_relevante=ayuda.es_relevante,
        sede_link=ayuda.sede_link,
        boe_link=ayuda.boe_link,
        descripcion_oficial=ayuda.descripcion_oficial,
        atributos_json=atributos,
        version_simplificada=version_simplificada
    )

@app.post("/api/auth/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    exist = db.query(Usuario).filter(Usuario.username == user_in.username).first()
    if exist:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
    
    pwd_hash = hashlib.sha256(user_in.password.encode("utf-8")).hexdigest()
    new_user = Usuario(
        username=user_in.username,
        password_hash=pwd_hash,
        role=user_in.role or "ciudadano",
        accessibility_profile="standard"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login", response_model=UserResponse)
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):
    pwd_hash = hashlib.sha256(user_in.password.encode("utf-8")).hexdigest()
    user = db.query(Usuario).filter(
        Usuario.username == user_in.username,
        Usuario.password_hash == pwd_hash
    ).first()
    if not user:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    return user

@app.put("/api/users/{user_id}/profile", response_model=UserResponse)
def update_user_profile(user_id: int, profile_in: UserProfileUpdate, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user.accessibility_profile = profile_in.accessibility_profile
    db.commit()
    db.refresh(user)
    return user

@app.post("/api/ayudas")
def create_ayuda_manual(ayuda_in: AyudaCreateInput, db: Session = Depends(get_db)):
    """crea ayuda manual"""
    exist = db.query(Ayuda).filter(Ayuda.codigo_bdns == ayuda_in.codigo_bdns).first()
    if exist:
        raise HTTPException(status_code=400, detail="Ya existe una ayuda con este código BDNS")
    
    logger.info("generando lf manual %s", ayuda_in.codigo_bdns)
    try:
        lectura_facil = llm_service.generate_easy_read(ayuda_in.descripcion_oficial, ayuda_in.titulo)
        lectura_facil_json = lectura_facil.model_dump()
        
        metadata = llm_service.extract_metadata(ayuda_in.descripcion_oficial)
        titulo_simplificado = metadata.titulo_simplificado
        categoria = metadata.categoria or ayuda_in.categoria
        atributos = [attr.model_dump() for attr in metadata.atributos]
    except Exception as e:
        logger.error(e)
        titulo_simplificado = ayuda_in.titulo[:50]
        categoria = ayuda_in.categoria or "Otros"
        lectura_facil_json = {
            "queEs": ayuda_in.descripcion_oficial[:200] + "...",
            "quienPuedePedir": "Consulte las bases.",
            "cuantoDan": ayuda_in.cuantia or "Ver bases.",
            "plazoComoPedir": "Consulte las bases."
        }
        atributos = [
            {"clave": "Quién", "valor": "Ciudadanos", "icono": "👤", "color": "blue"},
            {"clave": "Ayuda", "valor": ayuda_in.cuantia or "Económica", "icono": "💰", "color": "green"},
            {"clave": "Plazo", "valor": ayuda_in.plazo or "Abierto", "icono": "📅", "color": "orange"}
        ]
        
    import datetime
    plazo_date = None
    if ayuda_in.plazo:
        try:
            plazo_date = datetime.datetime.strptime(ayuda_in.plazo, "%Y-%m-%d").date()
        except ValueError:
            pass

    nueva_ayuda = Ayuda(
        codigo_bdns=ayuda_in.codigo_bdns,
        titulo=ayuda_in.titulo,
        titulo_simplificado=titulo_simplificado,
        organismo=ayuda_in.organismo,
        categoria=categoria,
        cuantia=ayuda_in.cuantia,
        plazo=plazo_date,
        plazo_abierto=True,
        es_para_particulares=True,
        es_relevante=True,
        sede_link=ayuda_in.sede_link,
        boe_link=ayuda_in.boe_link,
        descripcion_oficial=ayuda_in.descripcion_oficial,
        atributos_json=atributos,
        lectura_facil_json=lectura_facil_json
    )
    db.add(nueva_ayuda)
    db.commit()
    db.refresh(nueva_ayuda)
    

    try:
        from etl_pipeline import chunk_text
        from app.services.embeddings import embedding_service
        
        chunks = chunk_text(ayuda_in.descripcion_oficial)
        if chunks:
            chunk_embeddings = embedding_service.get_embeddings(chunks)
            for text_chunk, vector in zip(chunks, chunk_embeddings):
                nuevo_fragmento = FragmentoAyuda(
                    ayuda_id=nueva_ayuda.id,
                    texto_fragmento=text_chunk,
                    vector_embedding=vector
                )
                db.add(nuevo_fragmento)
            db.commit()
    except Exception as v_err:
        logger.error(v_err)

    return {"status": "success", "ayuda_id": nueva_ayuda.id}

@app.post("/api/admin/sync")
async def sync_boe_rss(db: Session = Depends(get_db)):
    """sincroniza con el boe"""
    try:
        from etl_pipeline import fetch_boe_items, process_row
        
        boe_items = fetch_boe_items(limit=10)
        
        imported_count = 0
        for item in boe_items:
            codigo_bdns = str(item["Código BDNS"]).strip()
            
            db_ayuda = db.query(Ayuda).filter(Ayuda.codigo_bdns == codigo_bdns).first()
            if not db_ayuda:
                logger.info("sincronizando %s", codigo_bdns)
                await process_row(item, db)
                imported_count += 1
                
        return {"status": "success", "imported_count": imported_count}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error durante la sincronización: {str(e)}")

@app.get("/api/admin/history", response_model=List[HistorialResponse])
def get_search_history(db: Session = Depends(get_db)):
    """historial de busquedas"""
    history = db.query(HistorialConsulta).order_by(HistorialConsulta.timestamp.desc()).limit(100).all()
    results = []
    for h in history:
        username = h.usuario.username if h.usuario else "Anónimo"
        results.append(HistorialResponse(
            id=h.id,
            query_text=h.query_text,
            timestamp=h.timestamp,
            results_count=h.results_count,
            usuario_username=username
        ))
    return results
