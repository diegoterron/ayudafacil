from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional

class AtributoSchema(BaseModel):
    clave: str
    valor: str
    icono: str
    color: str

class AyudaBase(BaseModel):
    codigo_bdns: str
    titulo: str
    titulo_simplificado: Optional[str] = None
    organismo: Optional[str] = None
    categoria: Optional[str] = None
    cuantia: Optional[str] = None
    plazo: Optional[date] = None
    plazo_abierto: bool = True
    es_para_particulares: bool = True
    es_relevante: bool = True
    sede_link: Optional[str] = None
    boe_link: Optional[str] = None
    descripcion_oficial: str
    atributos_json: Optional[List[AtributoSchema]] = None

class AyudaCreate(AyudaBase):
    pass

class AyudaResponse(AyudaBase):
    id: int

    class Config:
        from_attributes = True

class VersionSimplificadaSchema(BaseModel):
    queEs: str = Field(..., description="¿Qué es esta ayuda?")
    quienPuedePedir: str = Field(..., description="¿Quién puede solicitar esta ayuda?")
    cuantoDan: str = Field(..., description="¿Cuánto dinero o apoyo dan?")
    plazoComoPedir: str = Field(..., description="¿Hasta cuándo hay plazo y cómo pedirla?")

class AyudaDetailResponse(AyudaResponse):
    version_simplificada: Optional[VersionSimplificadaSchema] = None

class SearchResponseItem(AyudaResponse):
    relevanceScore: int = Field(..., description="Puntuación de relevancia normalizada de 0 a 100")
    version_simplificada: Optional[VersionSimplificadaSchema] = None
    degraded_service: Optional[bool] = Field(False, description="Indica si el servicio está degradado por fallo del motor semántico")


from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "ciudadano"

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    accessibility_profile: str

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    accessibility_profile: str

class HistorialResponse(BaseModel):
    id: int
    query_text: str
    timestamp: datetime
    results_count: int
    usuario_username: Optional[str] = None

    class Config:
        from_attributes = True

class AyudaCreateInput(BaseModel):
    codigo_bdns: str
    titulo: str
    organismo: str
    categoria: str
    cuantia: str
    descripcion_oficial: str
    sede_link: Optional[str] = None
    boe_link: Optional[str] = None
    plazo: Optional[str] = None
