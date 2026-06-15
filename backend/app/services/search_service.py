from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Tuple
from app.models import Ayuda, FragmentoAyuda
from app.services.embeddings import embedding_service
from app.schemas import SearchResponseItem, AtributoSchema, VersionSimplificadaSchema
from app.logging_config import logger

class SearchService:
    def hybrid_search(self, db: Session, query_text: str, k: int = 60, limit: int = 10, usuario_id: int = None) -> List[SearchResponseItem]:
        if not query_text.strip():
            return []

        query_words = query_text.lower().split()
        lexical_filters = []
        for word in query_words:
            if len(word) > 2:
                lexical_filters.append(Ayuda.titulo.ilike(f"%{word}%"))
                lexical_filters.append(Ayuda.descripcion_oficial.ilike(f"%{word}%"))
        
        lexical_results = []
        if lexical_filters:
            lexical_results = db.query(Ayuda).filter(
                Ayuda.es_para_particulares == True,
                Ayuda.es_relevante == True
            ).filter(or_(*lexical_filters)).limit(20).all()
        
        degraded_service = False
        vector_ayudas_map: Dict[int, float] = {}
        ayudas_obj_map: Dict[int, Ayuda] = {}
        sorted_vector_ids = []

        try:
            query_vector = embedding_service.get_embedding(query_text)
            
            vector_chunks = db.query(
                FragmentoAyuda,
                (1 - FragmentoAyuda.vector_embedding.cosine_distance(query_vector)).label("similarity")
            ).join(Ayuda).filter(
                Ayuda.es_para_particulares == True,
                Ayuda.es_relevante == True
            ).order_by(
                FragmentoAyuda.vector_embedding.cosine_distance(query_vector)
            ).limit(20).all()

            for chunk, similarity in vector_chunks:
                ayuda_id = chunk.ayuda_id
                if ayuda_id not in vector_ayudas_map or similarity > vector_ayudas_map[ayuda_id]:
                    vector_ayudas_map[ayuda_id] = similarity
                    ayudas_obj_map[ayuda_id] = chunk.ayuda

            sorted_vector_ids = [aid for aid, _ in sorted(vector_ayudas_map.items(), key=lambda item: item[1], reverse=True)]
        except Exception as embed_err:
            logger.warning(embed_err)
            degraded_service = True

        rrf_scores: Dict[int, float] = {}
        
        all_ayudas: Dict[int, Ayuda] = {}
        for a in lexical_results:
            all_ayudas[a.id] = a
        for aid, a in ayudas_obj_map.items():
            all_ayudas[aid] = a

        for rank, ayuda in enumerate(lexical_results):
            rrf_scores[ayuda.id] = rrf_scores.get(ayuda.id, 0.0) + (1.0 / (k + (rank + 1)))

        for rank, ayuda_id in enumerate(sorted_vector_ids):
            rrf_scores[ayuda_id] = rrf_scores.get(ayuda_id, 0.0) + (1.0 / (k + (rank + 1)))

        sorted_rrf = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)[:limit]

        response_items = []
        if sorted_rrf:
            max_rrf_score = sorted_rrf[0][1]
            for ayuda_id, rrf_score in sorted_rrf:
                ayuda_model = all_ayudas[ayuda_id]
                
                if max_rrf_score > 0:
                    normalized_score = int(60 + (38 * (rrf_score / max_rrf_score)))
                else:
                    normalized_score = 60

                atributos = []
                if ayuda_model.atributos_json:
                    atributos = [
                        AtributoSchema(
                            clave=attr.get("clave", ""),
                            valor=attr.get("valor", ""),
                            icono=attr.get("icono", ""),
                            color=attr.get("color", "blue")
                        ) for attr in ayuda_model.atributos_json
                    ]

                version_simplificada = None
                if ayuda_model.lectura_facil_json:
                    lf = ayuda_model.lectura_facil_json
                    version_simplificada = VersionSimplificadaSchema(
                        queEs=lf.get("queEs", ""),
                        quienPuedePedir=lf.get("quienPuedePedir", ""),
                        cuantoDan=lf.get("cuantoDan", ""),
                        plazoComoPedir=lf.get("plazoComoPedir", "")
                    )

                item = SearchResponseItem(
                    id=ayuda_model.id,
                    codigo_bdns=ayuda_model.codigo_bdns,
                    titulo=ayuda_model.titulo,
                    titulo_simplificado=ayuda_model.titulo_simplificado,
                    organismo=ayuda_model.organismo,
                    categoria=ayuda_model.categoria,
                    cuantia=ayuda_model.cuantia,
                    plazo=ayuda_model.plazo,
                    plazo_abierto=ayuda_model.plazo_abierto,
                    es_para_particulares=ayuda_model.es_para_particulares,
                    es_relevante=ayuda_model.es_relevante,
                    sede_link=ayuda_model.sede_link,
                    boe_link=ayuda_model.boe_link,
                    descripcion_oficial=ayuda_model.descripcion_oficial,
                    atributos_json=atributos,
                    relevanceScore=normalized_score,
                    version_simplificada=version_simplificada,
                    degraded_service=degraded_service
                )
                response_items.append(item)

        try:
            from app.models import HistorialConsulta
            historial = HistorialConsulta(
                usuario_id=usuario_id,
                query_text=query_text,
                results_count=len(response_items)
            )
            db.add(historial)
            db.commit()
        except Exception as hist_err:
            logger.error(hist_err)

        return response_items

search_service = SearchService()
