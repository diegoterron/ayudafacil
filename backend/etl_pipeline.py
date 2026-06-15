import os
import sys
import asyncio
import pandas as pd
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, SessionLocal
from app.models import Ayuda, FragmentoAyuda
from app.services.llm_service import llm_service
from app.services.embeddings import embedding_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "convocatorias_2025.csv")
OUTPUT_PDF_FOLDER = os.path.join(BASE_DIR, "data/pdfs")
OUTPUT_TEXT_FOLDER = os.path.join(BASE_DIR, "data/text_extracted")
MAX_ITEMS_TO_PROCESS = 15

async def download_pdf_with_playwright(url: str, output_path: str) -> bool:
    from playwright.async_api import async_playwright
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Descargando PDF: {url}")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            download_button_selector = 'a[title="Descargar"]'
            await page.wait_for_selector(download_button_selector, timeout=15000)
            
            async with page.expect_download() as download_info:
                await page.click(download_button_selector)
            
            download = await download_info.value
            await download.save_as(output_path)
            await browser.close()
            print(f"pdf guardado en {output_path}")
            return True
            
        except Exception as e:
            print(e)
            return False

def extract_text_from_pdf(pdf_path: str) -> str:
    import pdfplumber
    print(f"extrayendo texto de {pdf_path}")
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    return full_text

def chunk_text(text: str) -> list:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len
    )
    return text_splitter.split_text(text)

async def process_row(row, db):
    codigo_bdns = str(row["Código BDNS"]).strip()
    titulo_oficial = str(row["Título"]).strip()
    organismo = str(row["Órgano"]).strip() if pd.notna(row["Órgano"]) else str(row["Administración"]).strip()
    link_convocatoria = str(row["Link convocatoria"]).strip()
    db_ayuda = db.query(Ayuda).filter(Ayuda.codigo_bdns == codigo_bdns).first()
    if db_ayuda:
        return
        
    print(f"Procesando {codigo_bdns}")
    
    pdf_filename = f"{codigo_bdns}_bases.pdf"
    pdf_path = os.path.join(OUTPUT_PDF_FOLDER, pdf_filename)
    

    MOCK_DESCRIPTIONS = {
        "999001": """CONVOCATORIA DE AYUDAS PARA LA REHABILITACIÓN ENERGÉTICA DE VIVIENDAS HABITUALES (PLAN ECOVIVIENDA) EN ANDALUCÍA.
La Consejería de Fomento, Articulación del Territorio y Vivienda de la Junta de Andalucía convoca subvenciones para la rehabilitación energética y mejora de la eficiencia en viviendas.
Cuantía: Las ayudas oscilarán entre el 40% y el 80% del coste subvencionable, con un límite máximo de 18.800 euros por vivienda dependiendo del ahorro conseguido.
Requisitos de los beneficiarios:
- Cualquier persona física que sea dueña de una casa o piso que constituya su vivienda habitual y permanente.
- Realizar obras que acrediten una reducción de al menos el 30% del consumo de energía primaria no renovable.
Plazo de solicitud: El plazo de presentación de solicitudes estará abierto hasta el 30 de noviembre de 2026. La solicitud se presentará por internet en la página web de la Junta de Andalucía.""",
        "999002": """CONVOCATORIA DEL BONO ALQUILER JOVEN 2026.
El Ministerio de Vivienda y Agenda Urbana regula el Bono Alquiler Joven para facilitar la emancipación de los jóvenes.
Cuantía: La ayuda consiste en una subvención de 250 euros mensuales concedida por un plazo máximo de 24 meses (total 6.000 euros).
Requisitos de los beneficiarios:
- Jóvenes de entre 18 y 35 años que posean un contrato de alquiler o de habitación.
- Acreditar una fuente regular de ingresos que no supere 3 veces el IPREM (unos 24.300 euros anuales).
- Disponer de un alquiler mensual que no exceda de 600 euros (hasta 900 euros en zonas tensionadas).
Plazo de solicitud: El plazo de solicitud finaliza el 15 de octubre de 2026. Se solicita en la web de vivienda de la comunidad autónoma.""",
        "999003": """CONVOCATORIA DE BECAS DE AYUDA AL ESTUDIO PARA ENSEÑANZAS UNIVERSITARIAS (BECA MEC).
El Ministerio de Educación, Formación Profesional y Deportes convoca las becas de carácter general para estudiantes de grado o máster.
Cuantía: Cubre el 100% de la matrícula por primera vez. Incluye cuantía fija por renta (1.700 euros), por residencia (2.500 euros) y variable por rendimiento.
Requisitos de los beneficiarios:
- Estudiantes matriculados en enseñanzas universitarias o postobligatorias.
- No superar los umbrales de renta y patrimonio familiar establecidos.
- Cumplir con el rendimiento académico de aprobado de créditos exigido en el curso anterior.
Plazo de solicitud: Las solicitudes se presentarán de forma telemática desde el 15 de marzo de 2025 hasta el 10 de mayo de 2025.""",
        "999004": """CONVOCATORIA DE AYUDAS PARA EL FOMENTO DEL AUTOEMPLEO Y CONSOLIDACIÓN DEL TRABAJO AUTÓNOMO EN ANDALUCÍA.
La Consejería de Empleo, Empresa y Trabajo Autónomo de la Junta de Andalucía otorga subvenciones destinadas a fomentar la inserción laboral de desempleados mediante el autoempleo.
Cuantía: Pago único que varía entre 3.000 y 5.500 euros según la edad, género y situación de vulnerabilidad del solicitante (4.500 euros para mujeres autónomas).
Requisitos de los beneficiarios:
- Personas desempleadas inscritas como demandantes de empleo que se den de alta en el Régimen Especial de Trabajadores Autónomos (RETA).
- Mantener la condición de autónomo y de alta en el RETA de forma ininterrumpida por un período mínimo de 12 meses.
Plazo de solicitud: El plazo finaliza el 30 de septiembre de 2026. Se solicita por internet en la oficina virtual de la Consejería de Empleo.""",
        "999005": """CONVOCATORIA DE SUBVENCIONES PARA LA ADQUISICIÓN DE VEHÍCULOS ELÉCTRICOS E INFRAESTRUCTURA DE RECARGA (PLAN MOVES III).
El IDAE convoca ayudas para la movilidad sostenible a través de la compra de vehículos eléctricos.
Cuantía: Hasta 4.500 euros para turismos (7.000 euros si se entrega coche viejo para chatarra) y subvención de hasta el 70% para instalación de puntos de recarga.
Requisitos de los beneficiarios:
- Personas físicas, autónomos o empresas que compren un vehículo eléctrico nuevo o híbrido enchufable.
Plazo de solicitud: El plazo de presentación está abierto hasta el 31 de diciembre de 2026. Se tramita en el portal oficial de energía."""
    }

    if codigo_bdns in MOCK_DESCRIPTIONS:
        extracted_text = MOCK_DESCRIPTIONS[codigo_bdns]
    elif row.get("Text_BOE"):
        extracted_text = row["Text_BOE"]
    else:
        success = await download_pdf_with_playwright(link_convocatoria, pdf_path)
        if success and os.path.exists(pdf_path):
            extracted_text = extract_text_from_pdf(pdf_path)
    
    if not extracted_text:
        print(f"sin texto para {codigo_bdns}, usando mock")
        extracted_text = (
            f"Convocatoria de ayuda pública regulada por el órgano {organismo}.\n"
            f"El título oficial del proyecto es: {titulo_oficial}.\n"
            f"Esta ayuda persigue incentivar las actividades relacionadas con el fomento del bienestar social "
            f"y la modernización de los sectores involucrados en el ámbito geográfico correspondiente.\n"
            f"Las personas solicitantes deben cumplir con los requisitos establecidos en las bases publicadas "
            f"en la Sede Electrónica oficial.\n"
            f"Para más detalles o presentar la solicitud de forma telemática, visite la Sede Electrónica "
            f"referenciada en el portal oficial utilizando el código de convocatoria {codigo_bdns}."
        )
    
    metadata = llm_service.extract_metadata(extracted_text)
    
    lectura_facil = llm_service.generate_easy_read(extracted_text, titulo_oficial)
    plazo_date = None
    if metadata.plazo:
        try:
            plazo_date = datetime.strptime(metadata.plazo, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    if plazo_date and plazo_date < datetime.now().date():
        plazo_date = plazo_date.replace(year=datetime.now().year + 1)
    elif not plazo_date:
        from datetime import timedelta
        plazo_date = (datetime.now() + timedelta(days=180)).date()
        
    plazo_abierto = True
        
    es_para_particulares = metadata.es_para_particulares
    es_relevante = metadata.es_relevante
    if codigo_bdns.startswith("999"):
        es_para_particulares = True
        es_relevante = True


    atributos_db = [attr.model_dump() for attr in metadata.atributos]
    
    nueva_ayuda = Ayuda(
        codigo_bdns=codigo_bdns,
        titulo=titulo_oficial,
        titulo_simplificado=metadata.titulo_simplificado,
        organismo=organismo,
        categoria=metadata.categoria,
        cuantia=metadata.cuantia,
        plazo=plazo_date,
        plazo_abierto=plazo_abierto,
        es_para_particulares=es_para_particulares,
        es_relevante=es_relevante,
        sede_link=metadata.sede_link or link_convocatoria,
        boe_link=link_convocatoria,
        descripcion_oficial=extracted_text,
        atributos_json=atributos_db,
        lectura_facil_json=lectura_facil.model_dump()
    )
    
    db.add(nueva_ayuda)
    db.commit()
    db.refresh(nueva_ayuda)
    
    chunks = chunk_text(extracted_text)
    
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

def fetch_boe_items(limit=10):
    url = "https://www.boe.es/rss/canal.php?c=ayudas"
    boe_items = []
    try:
        print("Buscando RSS BOE...")
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
            root = ET.fromstring(content)
            channel = root.find('channel')
            items = channel.findall('item')
            print(f"RSS BOE: {len(items)} items")
            
            for item in items[:limit]:
                title = item.find('title').text
                link = item.find('link').text
                
                extracted_text = ""
                try:
                    req_doc = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_doc, timeout=10) as res_doc:
                        html = res_doc.read().decode('utf-8')
                        match = re.search(r'<div\s+id="DOdocText"[^>]*>(.*?)</div>', html, re.DOTALL)
                        if match:
                            text_clean = re.sub(r'<[^>]+>', ' ', match.group(1))
                            extracted_text = re.sub(r'\s+', ' ', text_clean).strip()
                except Exception as e:
                    print(e)
                    
                codigo_bdns = link.split('id=')[-1] if 'id=' in link else f"BOE-{len(boe_items)}"
                
                boe_items.append({
                    "Código BDNS": codigo_bdns,
                    "Título": title,
                    "Órgano": "Boletín Oficial del Estado",
                    "Administración": "Administración General del Estado",
                    "Link convocatoria": link,
                    "Text_BOE": extracted_text,
                    "priority": 1
                })
    except Exception as e:
        print(e)
    return boe_items

async def run_pipeline():
    print("INICIANDO ETL")
    
    init_db()
    
    if not os.path.exists(CSV_FILE):
        print("error: falta csv")
        df_csv = pd.DataFrame()
    else:
        try:
            df_csv = pd.read_csv(CSV_FILE, sep=";")
        except Exception:
            df_csv = pd.read_csv(CSV_FILE)

    df_mocks = pd.DataFrame()
    if not df_csv.empty:
        df_csv['Código BDNS'] = df_csv['Código BDNS'].astype(str)
        df_mocks = df_csv[df_csv['Código BDNS'].str.startswith("999")].copy()
        df_mocks['priority'] = -1

    boe_items = fetch_boe_items(limit=10)
    df_boe = pd.DataFrame(boe_items)
    
    if not df_boe.empty:
        df_final = pd.concat([df_mocks, df_boe], ignore_index=True)
    else:
        df_final = df_mocks
        
    db = SessionLocal()
    try:
        count = 0
        for index, row in df_final.iterrows():
            if count >= MAX_ITEMS_TO_PROCESS:
                break
            
            await process_row(row, db)
            count += 1
            
    finally:
        db.close()
        
    print("ETL TERMINADO")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
