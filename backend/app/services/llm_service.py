from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.schemas import VersionSimplificadaSchema
from app.logging_config import logger

class ExtractedAttribute(BaseModel):
    clave: str = Field(..., description="Nombre extremadamente corto de 1 palabra para el atributo (ej: 'Quién', 'Ayuda', 'Límite', 'Requisito')")
    valor: str = Field(..., description="Valor ultra resumido de 1 a 2 palabras útil para el ciudadano (ej: 'Solo jóvenes', 'Sin empleo', 'Placas solares', 'No particulares'). NUNCA pongas presupuestos totales ni textos largos.")
    icono: str = Field(..., description="Un único emoji relacionado con el atributo (ej: 👤, 💰, 📅, 🏠)")
    color: str = Field(..., description="Color temático para la tarjeta. Debe ser uno de: 'green', 'blue', 'orange', 'red', 'purple'")

class AyudaMetadataExtraction(BaseModel):
    titulo_simplificado: str = Field(..., description="Título de la ayuda ultra-simplificado y muy corto para el ciudadano (máximo 4 palabras, ej: 'Ayuda para placas solares' o 'Subvención a Club Ponce')")
    categoria: str = Field(..., description="Categoría temática general en una palabra (ej. Vivienda, Educación, Empleo, Digitalización, Energía, Social)")
    cuantia: str = Field(..., description="Texto muy corto de la cuantía individual (ej. 'Hasta 250 €', 'Sin dinero directo' o 'No para ti')")
    plazo: Optional[str] = Field(None, description="Fecha límite de presentación en formato YYYY-MM-DD. Si no hay plazo fijo o es indefinido, poner null")
    sede_link: Optional[str] = Field(None, description="URL del trámite oficial en la Sede Electrónica (si se menciona en el texto)")
    atributos: List[ExtractedAttribute] = Field(..., description="Lista de exactamente 3 atributos clave ultra-cortos para mostrar en la interfaz en formato de fichas")
    es_para_particulares: bool = Field(..., description="Indica si la ayuda va dirigida a personas físicas individuales (ciudadanos, familias, estudiantes, autónomos). Pon False si va dirigida únicamente a corporaciones locales, ayuntamientos, empresas, clubes deportivos u organizaciones.")
    es_relevante: bool = Field(..., description="Indica si la ayuda ofrece un beneficio o servicio relevante al que el ciudadano puede acceder. Pon False si es un gasto interno de la administración, un convenio puramente administrativo o contable, o una transferencia de fondos ya cerrada y liquidada sin impacto directo.")


def parse_ayuda_metadata(text: str) -> AyudaMetadataExtraction:
    import json
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON block found")
    json_str = text[start:end+1]
    data = json.loads(json_str)
        
    if "properties" in data and isinstance(data["properties"], dict):
        data = data["properties"]
        
    def extract_field(d, key, default=""):
        if key not in d:
            for k in d.keys():
                if k.lower() == key.lower():
                    key = k
                    break
        if key not in d:
            return default
        val = d[key]
        if isinstance(val, dict):
            for sub_key in ["value", "val", "default", "description"]:
                if sub_key in val and isinstance(val[sub_key], str):
                    return val[sub_key]
            for sub_val in val.values():
                if isinstance(sub_val, str):
                    return sub_val
        if isinstance(val, str):
            return val
        if val is None:
            return None
        return str(val)

    titulo_simplificado = extract_field(data, "titulo_simplificado") or extract_field(data, "tituloSimplificado")
    categoria = extract_field(data, "categoria")
    cuantia = extract_field(data, "cuantia")
    plazo = extract_field(data, "plazo")
    sede_link = extract_field(data, "sede_link") or extract_field(data, "sedeLink")
    
    es_para_particulares_str = extract_field(data, "es_para_particulares") or extract_field(data, "esParaParticulares")
    es_para_particulares = True
    if str(es_para_particulares_str).lower() in ["false", "0", "no"]:
        es_para_particulares = False

    es_relevante_str = extract_field(data, "es_relevante") or extract_field(data, "esRelevante")
    es_relevante = True
    if str(es_relevante_str).lower() in ["false", "0", "no"]:
        es_relevante = False

    atributos_raw = data.get("atributos", [])
    if isinstance(atributos_raw, dict) and "properties" in atributos_raw:
        atributos_raw = atributos_raw.get("value", []) or atributos_raw.get("default", [])
    
    atributos_list = []
    if isinstance(atributos_raw, list):
        for attr in atributos_raw:
            if isinstance(attr, dict):
                clave = extract_field(attr, "clave", "Dato")
                valor = extract_field(attr, "valor", "Consultar")
                
                icono = extract_field(attr, "icono", "📋")
                if not icono or not icono.strip():
                    icono = "📋"
                    
                color = extract_field(attr, "color", "blue")
                if not color or not color.strip() or color not in ["green", "blue", "orange", "red", "purple"]:
                    color = "blue"
                atributos_list.append(ExtractedAttribute(clave=clave, valor=valor, icono=icono, color=color))
                
    while len(atributos_list) < 3:
        if len(atributos_list) == 0:
            atributos_list.append(ExtractedAttribute(clave="Ámbito", valor="Ciudadanos", icono="👥", color="green"))
        elif len(atributos_list) == 1:
            atributos_list.append(ExtractedAttribute(clave="Ayuda", valor="Pública", icono="💰", color="blue"))
        else:
            atributos_list.append(ExtractedAttribute(clave="Plazo", valor="Abierto", icono="📅", color="orange"))
            
    atributos_list = atributos_list[:3]

    return AyudaMetadataExtraction(
        titulo_simplificado=titulo_simplificado or "Ayuda pública",
        categoria=categoria or "General",
        cuantia=cuantia or "Consultar",
        plazo=plazo,
        sede_link=sede_link,
        atributos=atributos_list,
        es_para_particulares=es_para_particulares,
        es_relevante=es_relevante
    )


def parse_version_simplificada(text: str) -> VersionSimplificadaSchema:
    import json
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON block found")
    json_str = text[start:end+1]
    data = json.loads(json_str)
    
    if "properties" in data and isinstance(data["properties"], dict):
        data = data["properties"]
        
    def extract_field(d, key, default=""):
        if key not in d:
            for k in d.keys():
                if k.lower() == key.lower():
                    key = k
                    break
        if key not in d:
            return default
        val = d[key]
        if isinstance(val, dict):
            for sub_key in ["value", "val", "default", "description"]:
                if sub_key in val and isinstance(val[sub_key], str):
                    return val[sub_key]
            for sub_val in val.values():
                if isinstance(sub_val, str):
                    return sub_val
        if isinstance(val, str):
            return val
        return str(val)

    queEs = extract_field(data, "queEs")
    quienPuedePedir = extract_field(data, "quienPuedePedir")
    cuantoDan = extract_field(data, "cuantoDan")
    plazoComoPedir = extract_field(data, "plazoComoPedir")
    
    return VersionSimplificadaSchema(
        queEs=queEs,
        quienPuedePedir=quienPuedePedir,
        cuantoDan=cuantoDan,
        plazoComoPedir=plazoComoPedir
    )


class LlmService:
    def __init__(self):
        self.provider = settings.PROVIDER.lower()
        
        if self.provider == "openai":
            from langchain_openai import ChatOpenAI
            if not settings.OPENAI_API_KEY:
                raise ValueError("Se seleccionó el proveedor OpenAI pero la API Key no está configurada.")
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_LLM_MODEL,
                temperature=0
            )
        else:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_LLM_MODEL,
                )

    def _call_n8n_gateway(self, payload: dict) -> Optional[dict]:
        import httpx
        n8n_base = settings.N8N_BASE_URL.rstrip('/')
        urls = [
            f"{n8n_base}/webhook/llm-gateway",
            f"{n8n_base}/webhook-test/llm-gateway"
        ]
        for url in urls:
            try:
                response = httpx.post(url, json=payload, timeout=120.0)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
                    elif isinstance(data, dict):
                        return data
                elif response.status_code == 404:
                    continue
                else:
                    logger.error("error n8n %s: %s", response.status_code, response.text)
            except Exception as e:
                logger.error(e)
        return None

    def extract_metadata(self, pdf_text: str) -> AyudaMetadataExtraction:
        n8n_payload = {
            "task": "extract_metadata",
            "text": pdf_text[:8000]
        }
        n8n_res = self._call_n8n_gateway(n8n_payload)
        if n8n_res:
            try:
                import json
                if "titulo_simplificado" in n8n_res:
                    return parse_ayuda_metadata(json.dumps(n8n_res))
                elif "raw_response" in n8n_res:
                    return parse_ayuda_metadata(n8n_res["raw_response"])
                else:
                    logger.warning("n8n sin estructura metadata")
            except Exception as parse_err:
                logger.warning(parse_err)
 
        logger.info("langchain local metadata")
        parser = PydanticOutputParser(pydantic_object=AyudaMetadataExtraction)
        
        prompt = PromptTemplate(
            template=(
                "Eres un asistente de IA especializado en analizar convocatorias oficiales de subvenciones públicas.\n"
                "A partir del extracto de las bases reguladoras, debes extraer los campos estructurados en formato JSON.\n\n"
                "INSTRUCCIONES CRÍTICAS DE SIMPLIFICACIÓN:\n"
                "- Título Simplificado: Crea un título ultra-corto de MÁXIMO 4 PALABRAS. Debe ser claro para cualquier ciudadano. NUNCA uses términos burocráticos como 'Resolución', 'Decreto', 'Subvención nominativa', 'Convenio' o artículos de leyes.\n"
                "- Categoría: Clasifica en una sola palabra (ej: Vivienda, Empleo, Educación, Energía, Social).\n"
                "- Cuantía: Indica cuánto dinero recibe un ciudadano individual (ej: 'Hasta 3.000 €', '100% del coste'). NUNCA pongas el presupuesto global de la administración. Si el dinero es solo para una organización (y no para particulares), pon 'No para particulares' o 'Dinero para el club'.\n"
                "- Plazo: Fecha YYYY-MM-DD o null si no se especifica o es indefinido.\n"
                "- Atributos: Genera exactamente 3 atributos. Cada clave debe ser de exactamente 1 palabra (ej: 'Quién', 'Ayuda', 'Requisito', 'Límite'). Cada valor debe ser de MÁXIMO 2 palabras (ej: 'Solo jóvenes', 'No particulares', 'Instalar placas'). NUNCA incluyas presupuestos totales o textos administrativos.\n\n"
                "EJEMPLOS DE EXTRACCIÓN CORRECTA:\n"
                "---------------------------------\n"
                "Ejemplo 1 (Ayuda para una entidad/asociación y NO para ciudadanos individuales):\n"
                "Texto: 'Decreto de la Presidencia nº 3680 por el que se aprueba el convenio con el Club Deportivo Ponce Valladolid para la realización de su programa de actividades deportivas, año 2025. El presupuesto total de la subvención asciende a 45.000 €...'\n"
                "Extracción Correcta:\n"
                "  - Título Simplificado: 'Ayuda a Club Ponce'\n"
                "  - Categoría: 'Social'\n"
                "  - Cuantía: 'No para particulares'\n"
                "  - Atributos:\n"
                "      * Clave: 'Quién', Valor: 'Solo Club Ponce', Icono: '⚽', Color: 'blue'\n"
                "      * Clave: 'Destino', Valor: 'Actividades deportivas', Icono: '📅', Color: 'orange'\n"
                "      * Clave: 'Ayuda', Valor: 'No para particulares', Icono: '🚫', Color: 'red'\n\n"
                "Ejemplo 2 (Ayuda individual para ciudadanos):\n"
                "Texto: 'Convocatoria de subvenciones destinadas al alquiler de vivienda en el medio rural de la provincia de Valladolid, año 2025. Cuantía de hasta 250 € al mes por beneficiario...'\n"
                "Extracción Correcta:\n"
                "  - Título Simplificado: 'Ayuda para el alquiler'\n"
                "  - Categoría: 'Vivienda'\n"
                "  - Cuantía: 'Hasta 250 €/mes'\n"
                "  - Atributos:\n"
                "      * Clave: 'Quién', Valor: 'Inquilinos rurales', Icono: '👤', Color: 'blue'\n"
                "      * Clave: 'Ayuda', Valor: 'Pagar alquiler', Icono: '🏠', Color: 'green'\n"
                "      * Clave: 'Público', Valor: 'Para ciudadanos', Icono: '✅', Color: 'green'\n\n"
                "Ejemplo 3 (Ayuda para ayuntamientos y NO para particulares):\n"
                "Texto: 'Acuerdo de Pleno por el que se aprueba Convocatoria de subvenciones a Ayuntamientos de menos de 20.000 habitantes y ELM para la eliminación de barreras arquitectónicas en edificios municipales. Presupuesto asignado 200.000 €.'\n"
                "Extracción Correcta:\n"
                "  - Título Simplificado: 'Accesibilidad en ayuntamientos'\n"
                "  - Categoría: 'Social'\n"
                "  - Cuantía: 'Para obras municipales'\n"
                "  - Atributos:\n"
                "      * Clave: 'Quién', Valor: 'Solo ayuntamientos', Icono: '🏢', Color: 'blue'\n"
                "      * Clave: 'Ayuda', Valor: 'Quitar barreras', Icono: '♿', Color: 'green'\n"
                "      * Clave: 'Público', Valor: 'No particulares', Icono: '🚫', Color: 'red'\n"
                "---------------------------------\n\n"
                "{format_instructions}\n\n"
                "TEXTO DE LAS BASES REGULADORAS:\n"
                "---------------------------------\n"
                "{text}\n"
                "---------------------------------\n\n"
                "RESPUESTA JSON VÁLIDA:"
            ),
            input_variables=["text"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        truncated_text = pdf_text[:8000]
        chain = prompt | self.llm
        try:
            response = chain.invoke({"text": truncated_text})
            raw_text = response.content
            try:
                result = parser.parse(raw_text)
                return result
            except Exception as parse_error:
                logger.warning(parse_error)
                robust_result = parse_ayuda_metadata(raw_text)
                return robust_result
        except Exception as e:
            logger.exception(e)
            return AyudaMetadataExtraction(
                titulo_simplificado="Ayuda sin título",
                categoria="Otros",
                cuantia="Ver bases reguladoras",
                plazo=None,
                sede_link=None,
                atributos=[
                    ExtractedAttribute(clave="Atención", valor="Revisar texto oficial", icono="⚠️", color="orange")
                ],
                es_para_particulares=True,
                es_relevante=True
            )

    def generate_easy_read(self, official_text: str, title: str, es_para_particulares: bool = True) -> VersionSimplificadaSchema:
        n8n_payload = {
            "task": "generate_easy_read",
            "text": official_text[:6000],
            "title": title,
            "es_para_particulares": es_para_particulares
        }
        n8n_res = self._call_n8n_gateway(n8n_payload)
        if n8n_res:
            try:
                import json
                if "queEs" in n8n_res:
                    return parse_version_simplificada(json.dumps(n8n_res))
                elif "raw_response" in n8n_res:
                    return parse_version_simplificada(n8n_res["raw_response"])
                else:
                    logger.warning("n8n sin estructura lf")
            except Exception as parse_err:
                logger.warning(parse_err)
 
        logger.info("langchain local lf")
        parser = PydanticOutputParser(pydantic_object=VersionSimplificadaSchema)

        prompt_instruction = (
            "Esta ayuda SÍ es para ciudadanos particulares (personas físicas, autónomos, estudiantes, familias).\n"
            "Por tanto:\n"
            "- En 'quienPuedePedir' explica de forma sencilla qué personas físicas específicas pueden pedirla (ej: 'Jóvenes estudiantes' o 'Personas desempleadas'). NUNCA digas que no es para particulares.\n"
            "- En 'cuantoDan' indica claramente qué cuantía o beneficio recibe el ciudadano individual. NUNCA digas 'Cero euros para ti' ni digas que no es para particulares."
        ) if es_para_particulares else (
            "Esta ayuda NO es para ciudadanos particulares (es para un ayuntamiento, club deportivo, empresa o asociación).\n"
            "Por tanto:\n"
            "- En 'quienPuedePedir' debes escribir obligatoriamente: 'Esta ayuda no es para particulares. Solo para [tipo de entidad]'.\n"
            "- En 'cuantoDan' debes escribir obligatoriamente: 'Cero euros para ti. El dinero va a la organización'."
        )

        prompt = PromptTemplate(
            template=(
                "Eres un experto en accesibilidad cognitiva y normas de 'Lectura Fácil' (conforme a la norma UNE 153101:2018 EX).\n"
                "Tu objetivo es transformar el texto de la subvención '{title}' en una versión extremadamente simplificada.\n\n"
                "REGLAS CRÍTICAS DE LECTURA FÁCIL (SÉ ULTRA-CONCISO):\n"
                "1. Escribe de forma ultra-corta. Máximo 1 frase por sección y máximo 10 palabras por frase. Sé directo y ve al grano de forma extrema. Omitir explicaciones largas o de contexto.\n"
                "2. {prompt_instruction}\n"
                "3. En 'queEs': Explica qué financia la ayuda en pocas palabras sencillas (ej: 'Dinero para pagar las actividades del club este año' o 'Dinero para pagar tu piso').\n"
                "4. En 'plazoComoPedir': Explica de forma directa el plazo y la forma (ej: 'Hasta el 31 de diciembre. Se pide por internet.').\n"
                "5. Utiliza verbos activos y dirígete directamente al usuario en segunda persona (tú).\n\n"
                "EJEMPLOS DE RESPUESTA EN LECTURA FÁCIL:\n"
                "-------------------------\n"
                "Ejemplo 1 (Convenio con club deportivo - NO para particulares):\n"
                "Título Oficial: 'Decreto por el que se aprueba el convenio con el Club Deportivo Ponce Valladolid para la realización de su programa de actividades deportivas'\n"
                "Respuesta JSON:\n"
                "{{\n"
                "  \"queEs\": \"Dinero para pagar las actividades del club este año.\",\n"
                "  \"quienPuedePedir\": \"Esta ayuda no es para particulares. Solo para el Club Ponce.\",\n"
                "  \"cuantoDan\": \"Cero euros para ti. El dinero va al club.\",\n"
                "  \"plazoComoPedir\": \"No tienes que pedirla. El club ya la gestionó.\"\n"
                "}}\n\n"
                "Ejemplo 2 (Ayuda de alquiler para ciudadanos - SÍ para particulares):\n"
                "Título Oficial: 'Convocatoria de subvenciones destinadas al alquiler de vivienda en el medio rural de la provincia de Valladolid'\n"
                "Respuesta JSON:\n"
                "{{\n"
                "  \"queEs\": \"Dinero para ayudarte a pagar el alquiler de tu casa.\",\n"
                "  \"quienPuedePedir\": \"Jóvenes que alquilan una casa en un pueblo de Valladolid.\",\n"
                "  \"cuantoDan\": \"Te dan hasta 250 euros cada mes.\",\n"
                "  \"plazoComoPedir\": \"Hasta el 31 de diciembre. Se pide por internet.\"\n"
                "}}\n\n"
                "Ejemplo 3 (Ayuda para ayuntamientos - NO para particulares):\n"
                "Título Oficial: 'Convocatoria de subvenciones a Ayuntamientos de menos de 20.000 habitantes para la eliminación de barreras arquitectónicas en edificios de titularidad municipal'\n"
                "Respuesta JSON:\n"
                "{{\n"
                "  \"queEs\": \"Dinero para que los pueblos quiten escaleras y rampas rotas.\",\n"
                "  \"quienPuedePedir\": \"Esta ayuda no es para particulares. Solo para ayuntamientos pequeños.\",\n"
                "  \"cuantoDan\": \"Cero euros para ti. El dinero se usa en obras municipales.\",\n"
                "  \"plazoComoPedir\": \"El plazo lo gestiona tu ayuntamiento directamente.\"\n"
                "}}\n"
                "-------------------------\n\n"
                "{format_instructions}\n\n"
                "TEXTO OFICIAL A ADAPTAR:\n"
                "-------------------------\n"
                "{text}\n"
                "-------------------------\n\n"
                "RESPUESTA JSON VÁLIDA:"
            ),
            input_variables=["text", "title", "prompt_instruction"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        truncated_text = official_text[:6000]
        chain = prompt | self.llm
        try:
            response = chain.invoke({"text": truncated_text, "title": title, "prompt_instruction": prompt_instruction})
            raw_text = response.content
            try:
                result = parser.parse(raw_text)
                return result
            except Exception as parse_error:
                logger.warning(parse_error)
                robust_result = parse_version_simplificada(raw_text)
                return robust_result
        except Exception as e:
            logger.exception(e)
            return VersionSimplificadaSchema(
                queEs=f"Ayuda pública para {title}. Para ver los detalles completos, por favor abre el enlace del BOE.",
                quienPuedePedir="Personas interesadas que cumplan las condiciones del texto oficial.",
                cuantoDan="La cuantía depende de cada caso. Consulta la convocatoria oficial.",
                plazoComoPedir="El plazo está indicado en el texto regulador. Se solicita telemáticamente."
            )

llm_service = LlmService()
