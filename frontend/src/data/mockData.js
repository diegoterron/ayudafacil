export const mockSubvenciones = [
  {
    id: "subv-001",
    titulo: "Ayudas para la rehabilitación energética de viviendas habituales (Plan Ecovivienda)",
    tituloSimplificado: "Ayudas para arreglar ventanas y aislar viviendas",
    organismo: "Consejería de Fomento, Articulación del Territorio y Vivienda",
    categoria: "Vivienda",
    plazoAbierto: true,
    relevancia: 98,
    boeLink: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-12345",
    sedeLink: "https://www.juntadeandalucia.es/organismos/fomentodearticulaciondelterritorioyvivienda.html",
    descripcionOficial: `RESOLUCIÓN de la Dirección General de Vivienda por la que se convocan subvenciones, en régimen de concurrencia no competitiva, para la rehabilitación energética y mejora de la eficiencia en edificios de tipología residencial colectiva y viviendas unifamiliares. Serán subvencionables las actuaciones que acrediten una reducción de al menos el 30% del consumo de energía primaria no renovable, evaluado mediante certificación de eficiencia energética antes y después de la reforma, y una reducción de la demanda energética anual de calefacción y refrigeración del 7% en zona climática C o superior. Las cuantías oscilarán entre el 40% y el 80% del coste subvencionable de la actuación, con un límite máximo de 18.800 euros por vivienda dependiendo del ahorro energético conseguido. El plazo de presentación de solicitudes expirará el 30 de noviembre de 2026, estando sujeto a disponibilidad presupuestaria.`,
    atributos: [
      { clave: "Cuantía", valor: "Hasta 18.000 € por vivienda", icono: "💰", color: "green" },
      { clave: "Plazo", valor: "Hasta el 30 de noviembre de 2026", icono: "📅", color: "blue" },
      { clave: "Ahorro Exigido", valor: "Reducción mínima de 30% de energía", icono: "⚡", color: "orange" },
      { clave: "Ámbito", valor: "Comunidad Autónoma (Andalucía)", icono: "📍", color: "purple" }
    ],
    versionSimplificada: {
      queEs: "Es un dinero que da el Gobierno para ayudarte a hacer obras en tu casa y que gaste menos energía (por ejemplo, poner ventanas nuevas o aislar las paredes).",
      quienPuedePedir: "Cualquier persona que sea dueña de una casa o piso que sea su vivienda habitual y que haga obras que ahorren al menos un 30% de energía.",
      cuantoDan: "Te pagan una parte de la obra. El máximo de dinero que te pueden dar son 18.000 euros por cada vivienda.",
      plazoComoPedir: "Tienes de plazo para pedirlo hasta el 30 de noviembre de 2026. Se pide por internet en la página web oficial de la Junta de Andalucía."
    }
  },
  {
    id: "subv-002",
    titulo: "Bono Alquiler Joven 2026",
    tituloSimplificado: "Ayuda de alquiler para jóvenes",
    organismo: "Ministerio de Vivienda y Agenda Urbana",
    categoria: "Vivienda",
    plazoAbierto: true,
    relevancia: 95,
    boeLink: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-67890",
    sedeLink: "https://www.mivau.gob.es/el-ministerio/bono-alquiler-joven",
    descripcionOficial: `REAL DECRETO por el que se regula el Bono Alquiler Joven y el Plan Estatal para el Acceso a la Vivienda 2022-2026. El objeto es facilitar la emancipación de los jóvenes mediante una ayuda económica mensual destinada a sufragar el coste del arrendamiento de vivienda habitual. Los beneficiarios deberán poseer entre 18 y 35 años, acreditar una fuente regular de ingresos que no supere 3 veces el IPREM (Indicador Público de Renta de Efectos Múltiples) y disponer de un contrato de arrendamiento válido donde la renta no exceda los 600 euros mensuales (ampliable a 900 euros en zonas tensionadas). La ayuda consiste en una subvención periódica de 250 euros mensuales concedida por un plazo máximo de 24 meses consecutivos.`,
    atributos: [
      { clave: "Ayuda Mensual", valor: "250 € al mes durante 2 años", icono: "💰", color: "green" },
      { clave: "Plazo de Solicitud", valor: "Hasta el 15 de octubre de 2026", icono: "📅", color: "blue" },
      { clave: "Edad Permitida", valor: "Entre 18 y 35 años", icono: "👶", color: "orange" },
      { clave: "Renta Máxima", valor: "Límite de 3 veces el IPREM (~24.300 €/año)", icono: "📈", color: "red" }
    ],
    versionSimplificada: {
      queEs: "Es una ayuda de dinero mensual para que los jóvenes puedan pagar el alquiler de su piso o de su habitación.",
      quienPuedePedir: "Jóvenes de entre 18 y 35 años que tengan un contrato de alquiler, trabajen o tengan ingresos, y no ganen mucho dinero (menos de 24.300 euros al año). El alquiler del piso debe costar menos de 600 euros al mes (o hasta 900 euros en algunas ciudades grandes).",
      cuantoDan: "Te dan 250 euros cada mes durante un máximo de 2 años (24 meses). En total, son hasta 6.000 euros de ayuda.",
      plazoComoPedir: "El plazo para pedirlo termina el 15 de octubre de 2026. Debes presentar tu contrato de alquiler y tus nóminas por internet en la web de vivienda de tu comunidad autónoma."
    }
  },
  {
    id: "subv-003",
    titulo: "Becas de ayuda al estudio para enseñanzas universitarias (Beca MEC)",
    tituloSimplificado: "Beca general de estudios (Becas MEC)",
    organismo: "Ministerio de Educación, Formación Profesional y Deportes",
    categoria: "Educación",
    plazoAbierto: false,
    relevancia: 87,
    boeLink: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-11111",
    sedeLink: "https://www.becaseducacion.gob.es/becas-y-ayudas.html",
    descripcionOficial: `CONVOCATORIA de becas de carácter general para el curso académico 2026-2027, para estudiantes que cursen estudios postobligatorios universitarios y no universitarios. Comprende una cuantía fija ligada a la renta del solicitante (1.700 euros), una cuantía fija ligada a la residencia del estudiante durante el curso (2.500 euros), una cuantía fija por excelencia académica (de 50 a 125 euros) y la beca de matrícula que cubre el importe de los créditos matriculados por primera vez. Asimismo, incluye una cuantía variable que se calcula mediante fórmula polinómica según la renta familiar y el rendimiento académico del alumno en el curso anterior. Las solicitudes deberán formalizarse por vía telemática.`,
    atributos: [
      { clave: "Importe", valor: "Matrícula gratis + cuantías variables", icono: "💰", color: "green" },
      { clave: "Plazo", valor: "Finalizado el 10 de mayo de 2026", icono: "📅", color: "red" },
      { clave: "Estudios", valor: "Grado Universitario, Máster y FP", icono: "🎓", color: "purple" },
      { clave: "Rendimiento", valor: "Aprobar porcentaje mínimo de créditos", icono: "📝", color: "orange" }
    ],
    versionSimplificada: {
      queEs: "Es una beca del Gobierno para ayudar a los estudiantes universitarios a pagar sus estudios y no tener que dejar la universidad por falta de dinero.",
      quienPuedePedir: "Estudiantes matriculados en la universidad que cumplan unos límites de renta familiar (dinero que entra en casa) y aprueben un mínimo de asignaturas cada año.",
      cuantoDan: "La beca te paga la matrícula de las asignaturas que te apuntes por primera vez. Además, te pueden dar dinero para pagar el piso si estudias fuera de tu ciudad (hasta 2.500 euros) o dinero para tus gastos si tu familia tiene pocos recursos (hasta 1.700 euros).",
      plazoComoPedir: "El plazo ya está cerrado. Terminó el 10 de mayo de 2026. Las becas se solicitan siempre a través de la sede electrónica del Ministerio de Educación."
    }
  },
  {
    id: "subv-004",
    titulo: "Ayudas para el fomento del autoempleo y consolidación del trabajo autónomo",
    tituloSimplificado: "Ayuda para nuevos autónomos",
    organismo: "Consejería de Empleo, Empresa y Trabajo Autónomo",
    categoria: "Empleo",
    plazoAbierto: true,
    relevancia: 91,
    boeLink: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-99999",
    sedeLink: "https://www.juntadeandalucia.es/organismos/empleoempresaytrabajoautonomo.html",
    descripcionOficial: `ORDEN de la Consejería de Empleo por la que se aprueban las bases reguladoras para la concesión de subvenciones destinadas a fomentar la inserción laboral de personas desempleadas mediante el autoempleo. La línea de subvenciones sufraga el inicio de la actividad económica de personas trabajadoras autónomas inscritas como demandantes de empleo no ocupadas. Las cuantías de la subvención oscilarán entre 3.000 euros para hombres menores de 30 años o mayores de 45 años, 4.500 euros para mujeres autónomas en general, y hasta 5.500 euros para colectivos vulnerables o personas con discapacidad. Se requiere el mantenimiento de la condición de autónomo y el alta en el RETA de forma ininterrumpida por un período mínimo de 12 meses.`,
    atributos: [
      { clave: "Pago Único", valor: "De 3.000 € a 5.500 € según perfil", icono: "💰", color: "green" },
      { clave: "Plazo", valor: "Hasta el 30 de septiembre de 2026", icono: "📅", color: "blue" },
      { clave: "Compromiso", valor: "Mantener alta RETA mínimo 12 meses", icono: "🤝", color: "orange" },
      { clave: "Destinatarios", valor: "Desempleados inscritos en SAE", icono: "👤", color: "purple" }
    ],
    versionSimplificada: {
      queEs: "Es una ayuda económica de un solo pago para personas sin trabajo que deciden darse de alta como autónomos y montar su propio negocio.",
      quienPuedePedir: "Personas desempleadas inscritas en el paro que inicien una actividad por cuenta propia. Deben comprometerse a estar dados de alta de autónomos durante al menos 1 año seguido.",
      cuantoDan: "Te dan un pago único de dinero que varía según tu edad y género: 3.000 euros para hombres menores de 30 o mayores de 45 años; 4.500 euros para mujeres autónomas; y hasta 5.500 euros si tienes alguna discapacidad o perteneces a un colectivo vulnerable.",
      plazoComoPedir: "Tienes de plazo para solicitarla hasta el 30 de septiembre de 2026. La solicitud se realiza a través de la oficina virtual de la Consejería de Empleo."
    }
  },
  {
    id: "subv-005",
    titulo: "Subvenciones para la adquisición de vehículos eléctricos e infraestructura de recarga (Plan MOVES III)",
    tituloSimplificado: "Descuento para comprar coche o moto eléctrica",
    organismo: "Instituto para la Diversificación y Ahorro de la Energía (IDAE)",
    categoria: "Transporte",
    plazoAbierto: true,
    relevancia: 83,
    boeLink: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2021-5678",
    sedeLink: "https://www.idae.es/ayudas-y-financiacion/para-movilidad-y-vehiculos/programa-moves-iii",
    descripcionOficial: `RESOLUCIÓN por la que se convoca el programa de incentivos a la movilidad eficiente y sostenible (MOVES III). Son objeto de ayuda la adquisición directa o por medio de operaciones de leasing financiero de vehículos nuevos eléctricos puros (BEV), eléctricos de autonomía extendida (REEV), híbridos enchufables (PHEV) y de pila de combustible (FCV). El importe de la ayuda será de 4.500 euros para turismos, incrementándose hasta los 7.000 euros si el comprador acredita la baja definitiva en el registro de vehículos de un turismo de más de 7 años de antigüedad para su achatarramiento. Asimismo, se subvenciona hasta el 70% del coste de instalación de puntos de recarga de baterías.`,
    atributos: [
      { clave: "Descuento", valor: "Hasta 7.000 € por vehículo", icono: "💰", color: "green" },
      { clave: "Plazo", valor: "Hasta el 31 de diciembre de 2026", icono: "📅", color: "blue" },
      { clave: "Requisito Coche", valor: "Eléctrico o híbrido enchufable", icono: "🚗", color: "orange" },
      { clave: "Achatarramiento", valor: "Opcional (aporta 2.500 € más)", icono: "♻️", color: "purple" }
    ],
    versionSimplificada: {
      queEs: "Es una ayuda económica para comprar un coche o moto eléctrica, o para instalar un enchufe de carga rápida en tu garaje.",
      quienPuedePedir: "Cualquier persona, empresa o autónomo que compre un vehicle eléctrico nuevo o instale un cargador.",
      cuantoDan: "Para coches, te dan 4.500 euros de descuento. Si además entregas tu coche viejo (de más de 7 años) para destruirlo en el desguace, la ayuda sube hasta los 7.000 euros.",
      plazoComoPedir: "Puedes pedirla hasta el 31 de diciembre de 2026. Normalmente, el propio concesionario donde compras el coche te ayuda a tramitar la solicitud en el portal de energía de tu comunidad autónoma."
    }
  }
];
