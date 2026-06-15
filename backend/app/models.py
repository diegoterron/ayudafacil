from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.config import settings

EMBEDDING_DIM = 768 if settings.PROVIDER == "ollama" else 1536

class Ayuda(Base):
    __tablename__ = "ayudas"

    id = Column(Integer, primary_key=True, index=True)
    codigo_bdns = Column(String(50), unique=True, index=True, nullable=False)
    titulo = Column(String(500), nullable=False)
    titulo_simplificado = Column(String(500), nullable=True)
    organismo = Column(String(250), nullable=True)
    categoria = Column(String(100), nullable=True)
    cuantia = Column(String(250), nullable=True)
    plazo = Column(Date, nullable=True)
    plazo_abierto = Column(Boolean, default=True)
    es_para_particulares = Column(Boolean, default=True, nullable=False)
    es_relevante = Column(Boolean, default=True, nullable=False)
    sede_link = Column(String(1000), nullable=True)
    boe_link = Column(String(1000), nullable=True)
    descripcion_oficial = Column(Text, nullable=False)
    
    atributos_json = Column(JSON, nullable=True)
    
    lectura_facil_json = Column(JSON, nullable=True)

    fragmentos = relationship(
        "FragmentoAyuda", 
        back_populates="ayuda", 
        cascade="all, delete-orphan"
    )


class FragmentoAyuda(Base):
    __tablename__ = "fragmentos_ayudas"

    id = Column(Integer, primary_key=True, index=True)
    ayuda_id = Column(Integer, ForeignKey("ayudas.id"), nullable=False)
    texto_fragmento = Column(Text, nullable=False)
    
    vector_embedding = Column(Vector(EMBEDDING_DIM), nullable=False)

    ayuda = relationship("Ayuda", back_populates="fragmentos")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(250), nullable=False)
    role = Column(String(50), default="ciudadano", nullable=False)
    accessibility_profile = Column(String(50), default="standard", nullable=False)

    consultas = relationship("HistorialConsulta", back_populates="usuario", cascade="all, delete-orphan")


class HistorialConsulta(Base):
    __tablename__ = "historial_consultas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    query_text = Column(String(500), nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    results_count = Column(Integer, default=0, nullable=False)

    usuario = relationship("Usuario", back_populates="consultas")
