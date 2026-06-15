import os
import sys
import csv
import textstat

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.logging_config import logger

# Configure textstat for Spanish
textstat.set_lang('es')

# Define Fernández-Huerta classification ranges
def get_fernandez_huerta_category(score):
    if score >= 90:
        return "Muy fácil (Primaria - 4º)"
    elif score >= 80:
        return "Fácil (Primaria - 5º)"
    elif score >= 70:
        return "Bastante fácil (Primaria - 6º)"
    elif score >= 60:
        return "Algo difícil (E.S.O. - 7º/8º)"
    elif score >= 50:
        return "Difícil (Bachillerato)"
    elif score >= 30:
        return "Muy difícil (Universidad)"
    else:
        return "Pedante / Científico (Doctorado)"

# Define fallback samples in case the database is empty or inaccessible
FALLBACK_SAMPLES = [
    {
        "titulo": "Bono Alquiler Joven",
        "original": (
            "Resolución de 12 de marzo de 2026, de la Dirección General de Vivienda y Arquitectura, "
            "por la que se convocan subvenciones destinadas al alquiler de vivienda habitual y permanente "
            "para jóvenes de hasta treinta y cinco años inclusive, con escasos recursos económicos, "
            "en régimen de concurrencia competitiva, cofinanciadas por el Plan Estatal de Vivienda."
        ),
        "simplificado": (
            "Ayuda de dinero para pagar el alquiler de tu casa habitual. "
            "Es para jóvenes de hasta 35 años que ganan poco dinero."
        )
    },
    {
        "titulo": "Subvención Placas Solares",
        "original": (
            "Decreto-Ley 4/2026, de 8 de enero, por el que se aprueban las bases reguladoras "
            "para la concesión de subvenciones en materia de transición energética y fomento de las "
            "instalaciones de autoconsumo eléctrico con fuentes de energía renovable en el sector residencial "
            "y pequeños comercios."
        ),
        "simplificado": (
            "Ayuda de dinero para instalar placas solares en tu casa o en tu pequeño negocio."
        )
    },
    {
        "titulo": "Bono Cultural Joven",
        "original": (
            "Orden CUD/345/2026, de 25 de febrero, por la que se establecen las normas de gestión "
            "del programa de fomento del acceso a la cultura mediante el otorgamiento de ayudas "
            "económicas individuales a jóvenes que cumplan la mayoría de edad en el presente ejercicio presupuestario."
        ),
        "simplificado": (
            "Ayuda de dinero para jóvenes de 18 años. "
            "Sirve para comprar libros o para ir al cine, teatro y conciertos."
        )
    },
    {
        "titulo": "Ayuda Digitalización (Kit Digital)",
        "original": (
            "Resolución de la Presidencia de la Entidad Pública Empresarial Red.es, por la que se aprueba "
            "la convocatoria de ayudas destinadas a la digitalización de pequeñas empresas, microempresas "
            "y personas en situación de autoempleo en el marco de la Agenda España Digital 2026 y el Plan de "
            "Digitalización de Pymes."
        ),
        "simplificado": (
            "Dinero para que las pequeñas empresas y autónomos puedan comprar ordenadores o hacer su página web."
        )
    },
    {
        "titulo": "Ayuda Rehabilitación Fachadas",
        "original": (
            "Convocatoria pública de subvenciones en régimen de concurrencia competitiva dirigidas a "
            "comunidades de propietarios de edificios residenciales para la mejora de la eficiencia energética, "
            "aislamiento térmico en fachadas y cubiertas, y accesibilidad universal en el municipio."
        ),
        "simplificado": (
            "Dinero para que los vecinos arreglen las paredes del edificio, gasten menos calefacción y pongan rampas."
        )
    }
]

def load_data_from_db():
    """Attempt to load real data from the database."""
    # Add app directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from app.database import SessionLocal
        from app.models import Ayuda
        
        db = SessionLocal()
        ayudas = db.query(Ayuda).all()
        db.close()
        
        db_samples = []
        for a in ayudas:
            if a.lectura_facil_json and isinstance(a.lectura_facil_json, dict):
                lf = a.lectura_facil_json
                que_es = lf.get("queEs", "")
                quien = lf.get("quienPuedePedir", "")
                cuanto = lf.get("cuantoDan", "")
                plazo = lf.get("plazoComoPedir", "")
                
                # Reconstruct full readable text by combining paragraphs
                parts = []
                if que_es: parts.append(que_es)
                if quien: parts.append(quien)
                if cuanto: parts.append(cuanto)
                if plazo: parts.append(plazo)
                
                combined_lf = " ".join(parts)
                
                if combined_lf and a.descripcion_oficial:
                    db_samples.append({
                        "titulo": a.titulo_simplificado or a.titulo[:30],
                        "original": a.descripcion_oficial,
                        "simplificado": combined_lf
                    })
        return db_samples
    except Exception as e:
        logger.warning(e)
        return []

def run_evaluation():
    print("=" * 70)
    print(" EVALUACIÓN CUANTITATIVA DE LEGIBILIDAD (ÍNDICE FERNÁNDEZ-HUERTA)")
    print("=" * 70)
    
    csv_rows = []
    
    # 1. EVALUATE CURATED BENCHMARK SAMPLES
    print("\n>>> EVALUACIÓN DEL BENCHMARK CONTROLADO (Ejemplos representativos)")
    print("-" * 70)
    print(f"{'Título de la Ayuda':<25} | {'Score BOE':<10} | {'Score LF':<10} | {'Mejora':<8} | {'Resultado'}")
    print("-" * 70)
    
    total_orig_bench = 0.0
    total_simp_bench = 0.0
    total_imp_bench = 0.0
    
    csv_rows.append(["--- BENCHMARK CONTROLADO ---"])
    csv_rows.append(["Título", "Fernández-Huerta BOE", "Categoría BOE", "Fernández-Huerta LF", "Categoría LF", "Mejora"])
    
    for item in FALLBACK_SAMPLES:
        title = item["titulo"]
        if len(title) > 23:
            title = title[:22] + "..."
        orig_text = item["original"]
        simp_text = item["simplificado"]
        
        score_orig = textstat.fernandez_huerta(orig_text)
        score_simp = textstat.fernandez_huerta(simp_text)
        improvement = score_simp - score_orig
        
        total_orig_bench += score_orig
        total_simp_bench += score_simp
        total_imp_bench += improvement
        
        orig_cat = get_fernandez_huerta_category(score_orig)
        simp_cat = get_fernandez_huerta_category(score_simp)
        
        csv_rows.append([
            item["titulo"],
            f"{score_orig:.2f}",
            orig_cat,
            f"{score_simp:.2f}",
            simp_cat,
            f"{improvement:.2f}"
        ])
        
        print(f"{title:<25} | {score_orig:>10.2f} | {score_simp:>10.2f} | {improvement:>+8.2f} | BOE: {orig_cat.split(' (')[0]} -> LF: {simp_cat.split(' (')[0]}")
        
    avg_orig_bench = total_orig_bench / len(FALLBACK_SAMPLES)
    avg_simp_bench = total_simp_bench / len(FALLBACK_SAMPLES)
    avg_imp_bench = total_imp_bench / len(FALLBACK_SAMPLES)
    
    print("-" * 70)
    print(f"{'PROMEDIO BENCHMARK':<25} | {avg_orig_bench:>10.2f} | {avg_simp_bench:>10.2f} | {avg_imp_bench:>+8.2f} | BOE: {get_fernandez_huerta_category(avg_orig_bench).split(' (')[0]} -> LF: {get_fernandez_huerta_category(avg_simp_bench).split(' (')[0]}")
    
    csv_rows.append(["PROMEDIO BENCHMARK", f"{avg_orig_bench:.2f}", get_fernandez_huerta_category(avg_orig_bench), f"{avg_simp_bench:.2f}", get_fernandez_huerta_category(avg_simp_bench), f"{avg_imp_bench:.2f}"])
    csv_rows.append([])
    
    # 2. EVALUATE DATABASE RECORDS
    db_samples = load_data_from_db()
    if db_samples:
        print("\n>>> EVALUACIÓN DE REGISTROS DE LA BASE DE DATOS (Ayudas reales)")
        print("-" * 70)
        print(f"{'Título de la Ayuda':<25} | {'Score BOE':<10} | {'Score LF':<10} | {'Mejora':<8} | {'Resultado'}")
        print("-" * 70)
        
        total_orig_db = 0.0
        total_simp_db = 0.0
        total_imp_db = 0.0
        
        csv_rows.append(["--- BASE DE DATOS (AYUDAS REALES) ---"])
        csv_rows.append(["Título", "Fernández-Huerta BOE", "Categoría BOE", "Fernández-Huerta LF", "Categoría LF", "Mejora"])
        
        for item in db_samples:
            title = item["titulo"]
            if len(title) > 23:
                title = title[:22] + "..."
            orig_text = item["original"]
            simp_text = item["simplificado"]
            
            score_orig = textstat.fernandez_huerta(orig_text)
            score_simp = textstat.fernandez_huerta(simp_text)
            improvement = score_simp - score_orig
            
            total_orig_db += score_orig
            total_simp_db += score_simp
            total_imp_db += improvement
            
            orig_cat = get_fernandez_huerta_category(score_orig)
            simp_cat = get_fernandez_huerta_category(score_simp)
            
            csv_rows.append([
                item["titulo"],
                f"{score_orig:.2f}",
                orig_cat,
                f"{score_simp:.2f}",
                simp_cat,
                f"{improvement:.2f}"
            ])
            
            print(f"{title:<25} | {score_orig:>10.2f} | {score_simp:>10.2f} | {improvement:>+8.2f} | BOE: {orig_cat.split(' (')[0]} -> LF: {simp_cat.split(' (')[0]}")
            
        avg_orig_db = total_orig_db / len(db_samples)
        avg_simp_db = total_simp_db / len(db_samples)
        avg_imp_db = total_imp_db / len(db_samples)
        
        print("-" * 70)
        print(f"{'PROMEDIO BASE DE DATOS':<25} | {avg_orig_db:>10.2f} | {avg_simp_db:>10.2f} | {avg_imp_db:>+8.2f} | BOE: {get_fernandez_huerta_category(avg_orig_db).split(' (')[0]} -> LF: {get_fernandez_huerta_category(avg_simp_db).split(' (')[0]}")
        
        csv_rows.append(["PROMEDIO BASE DE DATOS", f"{avg_orig_db:.2f}", get_fernandez_huerta_category(avg_orig_db), f"{avg_simp_db:.2f}", get_fernandez_huerta_category(avg_simp_db), f"{avg_imp_db:.2f}"])
    else:
        logger.warning("sin registros en db")

    print("=" * 70)
    
    # Save results to CSV
    csv_file = "evaluation_results.csv"
    with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)
        
    logger.info("resultados en %s", csv_file)

if __name__ == "__main__":
    run_evaluation()
