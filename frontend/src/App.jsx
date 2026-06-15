import React, { useState, useEffect } from 'react';
import { mockSubvenciones } from './data/mockData';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedSubvencion, setSelectedSubvencion] = useState(null);
  const [tfgMockupMode, setTfgMockupMode] = useState(false);
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('subvenciones-user');
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      return null;
    }
  });
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authRole, setAuthRole] = useState('ciudadano');
  const [authIsRegister, setAuthIsRegister] = useState(false);
  const [authError, setAuthError] = useState('');
  const [degradedService, setDegradedService] = useState(false);
  const [showOfficialInEasyRead, setShowOfficialInEasyRead] = useState(false);
  const [adminActiveTab, setAdminActiveTab] = useState('add');
  const [adminHistory, setAdminHistory] = useState([]);
  const [adminSyncStatus, setAdminSyncStatus] = useState('');
  const [adminForm, setAdminForm] = useState({
    codigo_bdns: '',
    titulo: '',
    organismo: '',
    categoria: 'Vivienda',
    cuantia: '',
    descripcion_oficial: '',
    sede_link: '',
    boe_link: '',
    plazo: ''
  });
  const [adminIsSubmitting, setAdminIsSubmitting] = useState(false);
  const [accessibilityMode, setAccessibilityMode] = useState(() => {
    try {
      const savedUser = localStorage.getItem('subvenciones-user');
      if (savedUser) {
        const u = JSON.parse(savedUser);
        if (u.accessibility_profile) return u.accessibility_profile;
      }
      return localStorage.getItem('subvenciones-accessibility-mode') || 'standard';
    } catch (e) {
      console.warn("Storage access denied, falling back to standard profile", e);
      return 'standard';
    }
  });
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [ttsUtterance, setTtsUtterance] = useState(null);

  useEffect(() => {
    const body = document.body;
    body.className = '';
    if (accessibilityMode === 'easy') {
      body.classList.add('accessibility-easy-read');
    } else if (accessibilityMode === 'contrast') {
      body.classList.add('accessibility-high-contrast');
    }
    
    try {
      localStorage.setItem('subvenciones-accessibility-mode', accessibilityMode);
    } catch (e) {
      console.warn("Unable to write accessibility preferences to localStorage", e);
    }

    if (user && user.id) {
      fetch(`http://localhost:8000/api/users/${user.id}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accessibility_profile: accessibilityMode })
      })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error();
      })
      .then(updatedUser => {
        const newUserData = { ...user, accessibility_profile: updatedUser.accessibility_profile };
        setUser(newUserData);
        localStorage.setItem('subvenciones-user', JSON.stringify(newUserData));
      })
      .catch(err => console.warn("Failed to sync accessibility profile to server", err));
    }
    
    stopSpeech();
  }, [accessibilityMode]);

  useEffect(() => {
    if (currentPage === 'admin' && adminActiveTab === 'history') {
      fetch('http://localhost:8000/api/admin/history')
        .then(res => res.json())
        .then(data => setAdminHistory(data))
        .catch(err => console.error("Error fetching audit logs:", err));
    }
  }, [currentPage, adminActiveTab]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.shiftKey && e.altKey && e.key.toLowerCase() === 'm') {
        e.preventDefault();
        setTfgMockupMode(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleAuthSubmit = (e) => {
    e.preventDefault();
    setAuthError('');
    if (!authUsername.trim() || !authPassword.trim()) {
      setAuthError('Por favor, rellene todos los campos.');
      return;
    }

    const endpoint = authIsRegister ? 'register' : 'login';
    const payload = authIsRegister 
      ? { username: authUsername, password: authPassword, role: authRole }
      : { username: authUsername, password: authPassword };

    fetch(`http://localhost:8000/api/auth/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(res => {
      if (!res.ok) {
        return res.json().then(err => { throw new Error(err.detail || 'Fallo de autenticación') });
      }
      return res.json();
    })
    .then(userData => {
      setUser(userData);
      localStorage.setItem('subvenciones-user', JSON.stringify(userData));
      if (userData.accessibility_profile) {
        setAccessibilityMode(userData.accessibility_profile);
      }
      setShowAuthModal(false);
      setAuthUsername('');
      setAuthPassword('');
      setAuthError('');
    })
    .catch(err => {
      setAuthError(err.message || 'Error de conexión con el servidor.');
    });
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('subvenciones-user');
    setAccessibilityMode('standard');
    localStorage.removeItem('subvenciones-accessibility-mode');
    setCurrentPage('search');
    stopSpeech();
  };

  const handleAdminFormSubmit = (e) => {
    e.preventDefault();
    if (!adminForm.codigo_bdns || !adminForm.titulo || !adminForm.descripcion_oficial) {
      alert("Por favor, rellene los campos obligatorios: Código BDNS, Título y Descripción.");
      return;
    }
    setAdminIsSubmitting(true);

    fetch('http://localhost:8000/api/ayudas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(adminForm)
    })
    .then(res => {
      if (!res.ok) return res.json().then(err => { throw new Error(err.detail || 'Fallo al guardar') });
      return res.json();
    })
    .then(() => {
      alert("¡Ayuda guardada y vectorizada correctamente con el LLM!");
      setAdminForm({
        codigo_bdns: '',
        titulo: '',
        organismo: '',
        categoria: 'Vivienda',
        cuantia: '',
        descripcion_oficial: '',
        sede_link: '',
        boe_link: '',
        plazo: ''
      });
      setAdminIsSubmitting(false);
    })
    .catch(err => {
      alert("Error: " + err.message);
      setAdminIsSubmitting(false);
    });
  };

  const handleAdminSync = () => {
    setAdminIsSubmitting(true);
    setAdminSyncStatus('');

    fetch('http://localhost:8000/api/admin/sync', { method: 'POST' })
    .then(res => {
      if (!res.ok) throw new Error('Error al sincronizar');
      return res.json();
    })
    .then(data => {
      setAdminSyncStatus(`Sincronización completada. Se importaron ${data.imported_count} nuevas ayudas del BOE.`);
      setAdminIsSubmitting(false);
    })
    .catch(err => {
      setAdminSyncStatus("Error: " + err.message);
      setAdminIsSubmitting(false);
    });
  };

  const toggleSpeech = (textToRead) => {
    if (isSpeaking) {
      stopSpeech();
      return;
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(textToRead);
      utterance.lang = 'es-ES';
      utterance.rate = accessibilityMode === 'easy' ? 0.85 : 1.0;

      utterance.onend = () => {
        setIsSpeaking(false);
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
      };

      setTtsUtterance(utterance);
      setIsSpeaking(true);
      window.speechSynthesis.speak(utterance);
    } else {
      alert('La lectura por voz no está soportada en este navegador.');
    }
  };

  const stopSpeech = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  useEffect(() => {
    return () => stopSpeech();
  }, [currentPage, selectedSubvencion]);

  const mapBackendToFrontend = (item) => {
    return {
      id: item.id,
      codigoBdns: item.codigo_bdns,
      titulo: item.titulo,
      tituloSimplificado: item.titulo_simplificado,
      organism: item.organismo,
      categoria: item.categoria,
      cuantia: item.cuantia,
      plazo: item.plazo,
      plazoAbierto: item.plazo_abierto,
      sedeLink: item.sede_link,
      boeLink: item.boe_link,
      descripcionOficial: item.descripcion_oficial,
      atributos: item.atributos_json || [],
      degradedService: item.degraded_service || false,
      versionSimplificada: item.version_simplificada ? {
        queEs: item.version_simplificada.queEs,
        quienPuedePedir: item.version_simplificada.quienPuedePedir,
        cuantoDan: item.version_simplificada.cuantoDan,
        plazoComoPedir: item.version_simplificada.plazoComoPedir
      } : null
    };
  };

  const handleSearchSubmit = (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    setDegradedService(false);
    const userParam = user ? `&user_id=${user.id}` : '';
    fetch(`http://localhost:8000/api/search?q=${encodeURIComponent(searchQuery)}${userParam}`)
      .then(res => {
        if (!res.ok) throw new Error("Error en la respuesta del backend");
        return res.json();
      })
      .then(data => {
        const isDegraded = data.some(item => item.degraded_service);
        setDegradedService(isDegraded);
        const mapped = data.map(mapBackendToFrontend);
        setSearchResults(mapped);
        setCurrentPage('results');
      })
      .catch(err => {
        console.warn("Fallo al consultar la API, usando fallback local:", err);
        setDegradedService(true);
        const query = searchQuery.toLowerCase();
        
        const matched = mockSubvenciones.map(sub => {
          let score = 50; 
          
          if (query.includes(sub.categoria.toLowerCase())) score += 20;
          
          const queryWords = query.split(/\s+/);
          let matches = 0;
          queryWords.forEach(word => {
            if (word.length > 3) {
              if (sub.titulo.toLowerCase().includes(word)) matches++;
              if (sub.descripcionOficial.toLowerCase().includes(word)) matches++;
              if (sub.versionSimplificada.queEs.toLowerCase().includes(word)) matches++;
            }
          });
          
          score += Math.min(matches * 8, 30);
          score += Math.floor(Math.random() * 5);
          score = Math.min(score, 99);
          
          return { ...sub, relevanceScore: score };
        })
        .filter(sub => sub.relevanceScore > 55)
        .sort((a, b) => b.relevanceScore - a.relevanceScore);

        setSearchResults(matched);
        setCurrentPage('results');
      });
  };

  const handleSuggestionClick = (suggestionText) => {
    setSearchQuery(suggestionText);
    setDegradedService(false);
    const userParam = user ? `&user_id=${user.id}` : '';
    
    fetch(`http://localhost:8000/api/search?q=${encodeURIComponent(suggestionText)}${userParam}`)
      .then(res => {
        if (!res.ok) throw new Error("Error en la respuesta del backend");
        return res.json();
      })
      .then(data => {
        const isDegraded = data.some(item => item.degraded_service);
        setDegradedService(isDegraded);
        const mapped = data.map(mapBackendToFrontend);
        setSearchResults(mapped);
        setCurrentPage('results');
      })
      .catch(err => {
        console.warn("Fallo al procesar sugerencia, usando fallback local:", err);
        setDegradedService(true);
        const query = suggestionText.toLowerCase();
        const matched = mockSubvenciones.map(sub => {
          let score = 65;
          if (query.includes(sub.categoria.toLowerCase())) score += 15;
          if (sub.titulo.toLowerCase().includes(query.split(' ')[0])) score += 10;
          score += Math.floor(Math.random() * 5);
          return { ...sub, relevanceScore: Math.min(score, 99) };
        })
        .filter(sub => sub.relevanceScore > 55)
        .sort((a, b) => b.relevanceScore - a.relevanceScore);

        setSearchResults(matched);
        setCurrentPage('results');
      });
  };

  const handleViewDetail = (subvencion) => {
    if (typeof subvencion.id === 'string' && subvencion.id.startsWith('sub')) {
      setSelectedSubvencion(subvencion);
      setCurrentPage('detail');
      return;
    }

    fetch(`http://localhost:8000/api/ayudas/${subvencion.id}`)
      .then(res => {
        if (!res.ok) throw new Error("Error obteniendo detalle de la ayuda");
        return res.json();
      })
      .then(data => {
        const mapped = mapBackendToFrontend(data);
        setSelectedSubvencion(mapped);
        setCurrentPage('detail');
      })
      .catch(err => {
        console.warn("Fallo al obtener detalle de la API, usando fallback local:", err);
        setSelectedSubvencion(subvencion);
        setCurrentPage('detail');
      });
  };

  const getSubvencionTtsText = (sub) => {
    if (accessibilityMode === 'easy') {
      return `Ayuda: ${sub.tituloSimplificado || sub.titulo}. 
      ¿Qué es? ${sub.versionSimplificada.queEs} 
      ¿Quién puede pedirla? ${sub.versionSimplificada.quienPuedePedir} 
      ¿Cuánto dinero dan? ${sub.versionSimplificada.cuantoDan} 
      ¿Hasta cuándo hay plazo? ${sub.versionSimplificada.plazoComoPedir}`;
    } else {
      return `Ayuda oficial: ${sub.titulo}. Organismo: ${sub.organismo}. Plazo: ${sub.plazo}. Cuantía: ${sub.cuantia}. Resumen oficial: ${sub.descripcionOficial}`;
    }
  };

  return (
    <div className="app-layout">
      <header className="app-header" role="banner">
        <div className="header-container">
          <a href="#" className="logo-section" onClick={() => { setCurrentPage('search'); stopSpeech(); }} aria-label="Volver al inicio">
            <div className="logo-icon" aria-hidden="true">A</div>
            <div className="logo-title">
              <h1>AyudaFácil</h1>
              <div className="logo-subtitle">Buscador Accesible de Ayudas Públicas</div>
            </div>
          </a>

          <nav className="accessibility-panel" aria-label="Opciones de accesibilidad">
            <span className="panel-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{verticalAlign: 'middle'}} aria-hidden="true">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4M12 8h.01"/>
              </svg>
              {accessibilityMode === 'easy' ? 'Perfil:' : 'Perfil de Accesibilidad:'}
            </span>
            <button 
              className={`accessibility-btn ${accessibilityMode === 'standard' ? 'active' : ''}`}
              onClick={() => setAccessibilityMode('standard')}
              aria-pressed={accessibilityMode === 'standard'}
              title="Perfil Estándar"
            >
              Estándar
            </button>
            <button 
              className={`accessibility-btn ${accessibilityMode === 'easy' ? 'active' : ''}`}
              onClick={() => setAccessibilityMode('easy')}
              aria-pressed={accessibilityMode === 'easy'}
              title="Perfil Adaptado a Lectura Fácil para personas con dificultades de comprensión"
            >
              <span> Lectura Fácil</span>
            </button>
            <button 
              className={`accessibility-btn ${accessibilityMode === 'contrast' ? 'active' : ''}`}
              onClick={() => setAccessibilityMode('contrast')}
              aria-pressed={accessibilityMode === 'contrast'}
              title="Perfil de Alto Contraste para personas con dificultades visuales"
            >
              Alto Contraste
            </button>
          </nav>

          <div className="header-auth-container">
            {user ? (
              <>
                <span className="user-welcome-text">
                  Hola, <strong>{user.username}</strong>
                </span>
                {user.role === 'admin' && (
                  <button 
                    type="button" 
                    className="auth-header-btn"
                    onClick={() => { setCurrentPage(currentPage === 'admin' ? 'search' : 'admin'); stopSpeech(); }}
                  >
                    {currentPage === 'admin' ? 'Buscador' : 'Administración'}
                  </button>
                )}
                <button 
                  type="button" 
                  className="auth-header-btn logout" 
                  onClick={handleLogout}
                >
                  Salir
                </button>
              </>
            ) : (
              <button 
                type="button" 
                className="auth-header-btn" 
                onClick={() => { setShowAuthModal(true); setAuthError(''); }}
              >
                Entrar
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="main-content" role="main" id="main-content">
        
        {degradedService && (
          <div className="degraded-service-banner" role="alert">
            <span aria-hidden="true">⚠️</span>
            <span>
              <strong>Búsqueda en modo de contingencia:</strong> El motor de búsqueda semántica no está disponible temporalmente. Mostrando resultados basados estrictamente en coincidencia de texto.
            </span>
          </div>
        )}

        {currentPage === 'search' && (
          <section className="hero-search-section" style={{ position: 'relative' }}>
            {tfgMockupMode && <span className="tfg-annotation-tag top-right">RF-4 / RNF-3: Buscador Semántico-Léxico</span>}
            <h2 className="hero-title">
              {accessibilityMode === 'easy' 
                ? 'Busca ayudas y subvenciones del Gobierno' 
                : 'Descubre ayudas públicas en lenguaje claro'}
            </h2>
            <p className="hero-subtitle">
              {accessibilityMode === 'easy'
                ? 'Escribe lo que necesitas y te ayudaremos a encontrar un dinero o apoyo oficial.'
                : 'Utiliza nuestro buscador inteligente con tecnología RAG para localizar ayudas de la BDNS explicadas de forma sencilla.'}
            </p>

            <form onSubmit={handleSearchSubmit} className="search-form-container" style={{ position: 'relative' }}>
              {tfgMockupMode && <span className="tfg-annotation-tag top-left" style={{ top: '-1.8rem', left: '0' }}>Entrada en Lenguaje Natural Coloquial</span>}
              <div className="search-box-wrapper">
                <input
                  type="text"
                  className="search-input"
                  placeholder={accessibilityMode === 'easy' 
                    ? "Ejemplo: ayuda para arreglar las ventanas..." 
                    : "Describe lo que necesitas (ej. bono alquiler para jóvenes, ayudas placas solares)..."}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  aria-label="Escribe tu consulta de búsqueda"
                />
                <button type="submit" className="search-submit-btn" aria-label="Buscar ayudas">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                    <circle cx="11" cy="11" r="8"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  <span>{accessibilityMode === 'easy' ? 'Buscar ayuda' : 'Buscar'}</span>
                </button>
              </div>
            </form>

            <div className="search-suggestions" style={{ position: 'relative' }}>
              {tfgMockupMode && <span className="tfg-annotation-tag bottom-left" style={{ bottom: '-1.8rem', left: '0' }}>Ejemplos para mitigar la Brecha de Vocabulario</span>}
              <span className="suggestion-label">
                {accessibilityMode === 'easy' ? 'Ejemplos de búsqueda:' : 'Prueba a buscar:'}
              </span>
              <button 
                type="button" 
                className="suggestion-chip"
                onClick={() => handleSuggestionClick('Bono alquiler joven')}
              >
                Bono alquiler joven
              </button>
              <button 
                type="button" 
                className="suggestion-chip"
                onClick={() => handleSuggestionClick('Reformar ventanas vivienda')}
              >
                Arreglar ventanas de casa
              </button>
              <button 
                type="button" 
                className="suggestion-chip"
                onClick={() => handleSuggestionClick('autoempleo autónomos')}
              >
                Montar un negocio (autónomos)
              </button>
            </div>
          </section>
        )}

        {currentPage === 'results' && (
          <section className="results-section">
            <div className="results-header-section">
              <h2 className="results-title" aria-live="polite">
                {accessibilityMode === 'easy'
                  ? `Hemos encontrado ${searchResults.length} ayudas que te pueden interesar`
                  : `Resultados de búsqueda: "${searchQuery}" (${searchResults.length})`}
              </h2>
              <button 
                type="button" 
                className="results-back-btn" 
                onClick={() => { setCurrentPage('search'); stopSpeech(); }}
                aria-label="Volver al buscador principal"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                  <line x1="19" y1="12" x2="5" y2="12"/>
                  <polyline points="12 19 5 12 12 5"/>
                </svg>
                <span>Volver atrás</span>
              </button>
            </div>

            {searchResults.length === 0 ? (
              <div className="easy-read-card" style={{textAlign: 'center', padding: '3rem'}}>
                <p style={{fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '1rem'}}>
                  {accessibilityMode === 'easy' 
                    ? 'No hemos encontrado ninguna ayuda con estas palabras.' 
                    : 'No se encontraron resultados para tu consulta.'}
                </p>
                <p className="card-section-text">
                  {accessibilityMode === 'easy'
                    ? 'Prueba a escribirlo de otra forma más sencilla o haz clic en "Volver atrás" para elegir uno de los ejemplos.'
                    : 'Intenta utilizar términos alternativos o comprueba que no haya errores de ortografía.'}
                </p>
              </div>
            ) : (
              <div className="subvenciones-list">
                {searchResults.map((sub) => (
                  <article key={sub.id} className="subvencion-card" style={{ position: 'relative' }}>
                    {tfgMockupMode && <span className="tfg-annotation-tag top-left" style={{ top: '-0.75rem', left: '1rem', zIndex: 5 }}>Boceto de Tarjeta de Resultados</span>}
                    <div className="subvencion-main-info" style={{ position: 'relative' }}>
                      {tfgMockupMode && <span className="tfg-annotation-tag top-left" style={{ top: '-1.8rem', left: '0', zIndex: 1 }}>RF-3: Clasificación Inteligente (LLM)</span>}
                      <div className="card-top-tags">
                        <span className="tag-badge category">{sub.categoria}</span>
                        {accessibilityMode !== 'easy' && (
                          <span className="tag-badge relevance">
                            {tfgMockupMode && <span className="tfg-annotation-tag bottom-right" style={{ right: '100%', top: '-0.25rem', whiteSpace: 'nowrap', marginRight: '5px' }}>RRF Fusion Score</span>}
                            Coincidencia: {sub.relevanceScore}%
                          </span>
                        )}
                        <span className={`tag-badge ${sub.plazoAbierto ? 'deadline-open' : 'deadline-closed'}`}>
                          {sub.plazoAbierto ? 'Plazo Abierto' : 'Plazo Cerrado'}
                        </span>
                      </div>
                      <h3 className="card-title">
                        {accessibilityMode === 'easy' && sub.tituloSimplificado 
                          ? sub.tituloSimplificado 
                          : sub.titulo}
                      </h3>
                      <p className="card-organism">{sub.organism}</p>
                      
                      <p className="card-excerpt">
                        {accessibilityMode === 'easy'
                          ? (sub.versionSimplificada?.queEs || sub.descripcionOficial)
                          : sub.descripcionOficial}
                      </p>

                      <div className="card-meta-indicators" style={{ position: 'relative' }}>
                        {tfgMockupMode && <span className="tfg-annotation-tag bottom-left" style={{ bottom: '-1.8rem', left: '0' }}>Atributos Dinámicos (Modelo Híbrido JSONB)</span>}
                        {sub.atributos && sub.atributos.map((attr, index) => (
                          <div key={index} className={`meta-badge attr-${attr.color}`}>
                            <span className="meta-icon" aria-hidden="true">{attr.icono}</span>
                            <span><strong>{attr.clave}:</strong> {attr.valor}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="card-actions">
                      <button 
                        type="button" 
                        className="card-view-btn"
                        onClick={() => handleViewDetail(sub)}
                        aria-label={`Ver información detallada de: ${accessibilityMode === 'easy' && sub.tituloSimplificado ? sub.tituloSimplificado : sub.titulo}`}
                      >
                        <span>{accessibilityMode === 'easy' ? 'Ver información sencilla' : 'Ver detalle'}</span>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                          <polyline points="9 18 15 12 9 6"/>
                        </svg>
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

        {currentPage === 'detail' && selectedSubvencion && (
          <section className="detail-page-wrapper">
            
            <div className="detail-header">
              <button 
                type="button" 
                className="results-back-btn" 
                onClick={() => { setCurrentPage('results'); stopSpeech(); }}
                aria-label="Volver a los resultados de búsqueda"
                style={{alignSelf: 'flex-start', marginBottom: '0.5rem'}}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                  <line x1="19" y1="12" x2="5" y2="12"/>
                  <polyline points="12 19 5 12 12 5"/>
                </svg>
                <span>Volver a la lista</span>
              </button>
              
              <div className="detail-title-section" style={{ position: 'relative' }}>
                <h2 className="detail-title">
                  {accessibilityMode === 'easy' && selectedSubvencion.tituloSimplificado 
                    ? selectedSubvencion.tituloSimplificado 
                    : selectedSubvencion.titulo}
                </h2>
                {tfgMockupMode && <span className="tfg-annotation-tag bottom-left" style={{ bottom: '-1.5rem', left: '0' }}>RF-7 / RNF-1: Lector de Voz (TTS) Adaptativo</span>}
                <button
                  type="button"
                  className={`tts-control-button ${isSpeaking ? 'playing' : ''}`}
                  onClick={() => toggleSpeech(getSubvencionTtsText(selectedSubvencion))}
                  aria-pressed={isSpeaking}
                  aria-label={isSpeaking ? "Detener la lectura de texto por voz" : "Escuchar la información en voz alta"}
                >
                  {isSpeaking ? (
                    <>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                        <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
                      </svg>
                      <span>Detener Voz</span>
                    </>
                  ) : (
                    <>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                      </svg>
                      <span>Escuchar</span>
                    </>
                  )}
                </button>
              </div>
              
              <div className="card-top-tags" style={{ position: 'relative' }}>
                {tfgMockupMode && <span className="tfg-annotation-tag bottom-right" style={{ right: '0', top: '-1.5rem' }}>Metadatos Relacionales</span>}
                <span className="tag-badge category">{selectedSubvencion.categoria}</span>
                <span className="card-organism" style={{marginLeft: '0.5rem'}}>{selectedSubvencion.organismo}</span>
              </div>
              
              <div className="detail-meta-indicators" style={{display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '1rem', position: 'relative'}}>
                {tfgMockupMode && <span className="tfg-annotation-tag bottom-left" style={{ bottom: '-1.8rem', zIndex: 1 }}>Atributos Dinámicos Extraídos</span>}
                {selectedSubvencion.atributos && selectedSubvencion.atributos.map((attr, index) => (
                  <div key={index} className={`meta-badge attr-${attr.color}`}>
                    <span className="meta-icon" aria-hidden="true">{attr.icono}</span>
                    <span><strong>{attr.clave}:</strong> {attr.valor}</span>
                  </div>
                ))}
              </div>
            </div>

            {accessibilityMode === 'easy' && (
              <div className="toggle-official-container">
                <button 
                  type="button" 
                  className="toggle-official-btn"
                  onClick={() => setShowOfficialInEasyRead(!showOfficialInEasyRead)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="16" x2="12" y2="12"/>
                    <line x1="12" y1="8" x2="12.01" y2="8"/>
                  </svg>
                  <span>{showOfficialInEasyRead ? 'Ocultar texto legal oficial' : 'Mostrar texto legal oficial'}</span>
                </button>
              </div>
            )}

            <div className={`dual-view-container ${accessibilityMode === 'easy' && !showOfficialInEasyRead ? 'easy-only' : ''}`}>
              
              <article className="official-view-column" style={{ position: 'relative' }}>
                {tfgMockupMode && <span className="tfg-annotation-tag top-left" style={{ top: '-1rem', left: '1rem' }}>RF-2: Texto Oficial del Boletín (BOE)</span>}
                <div className="official-header">
                  <span className="official-title-tag">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                      <line x1="16" y1="13" x2="8" y2="13"/>
                      <line x1="16" y1="17" x2="8" y2="17"/>
                      <polyline points="10 9 9 9 8 9"/>
                    </svg>
                    Texto Oficial (BOE)
                  </span>
                  {selectedSubvencion.boeLink && (
                    <a 
                      href={selectedSubvencion.boeLink} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="official-external-link"
                      title="Enlace externo. Abre en pestaña nueva"
                    >
                      <span>Ver BOE</span>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        <polyline points="15 3 21 3 21 9"/>
                        <line x1="10" y1="14" x2="21" y2="3"/>
                      </svg>
                    </a>
                  )}
                </div>
                <div className="official-text-content">
                  {selectedSubvencion.descripcionOficial}
                </div>
              </article>

              <div className="easy-read-view-column" style={{ position: 'relative' }}>
                {tfgMockupMode && <span className="tfg-annotation-tag top-right" style={{ top: '-1.5rem', right: '0' }}>RF-5 / RNF-5: Vista Adaptada a Lectura Fácil (IA + RAG)</span>}
                <div className="easy-read-header">
                  <div className="easy-read-header-icon" aria-hidden="true">⭐</div>
                  <span>Vista Adaptada a Lectura Fácil (UNE 153101:2018 EX)</span>
                </div>

                {selectedSubvencion.versionSimplificada ? (
                  <>
                    <section className="easy-read-card" aria-label="¿Qué es esta ayuda?">
                      <h4 className="card-section-title">
                        <span className="card-section-icon" aria-hidden="true">💡</span>
                        ¿Qué es?
                      </h4>
                      <p className="card-section-text">
                        {selectedSubvencion.versionSimplificada.queEs}
                      </p>
                    </section>

                    <section className="easy-read-card" aria-label="¿Quién puede solicitar esta ayuda?">
                      <h4 className="card-section-title">
                        <span className="card-section-icon" aria-hidden="true">👤</span>
                        ¿Quién puede pedirla?
                      </h4>
                      <p className="card-section-text">
                        {selectedSubvencion.versionSimplificada.quienPuedePedir}
                      </p>
                    </section>

                    <section className="easy-read-card" aria-label="¿Cuánto dinero conceden?">
                      <h4 className="card-section-title">
                        <span className="card-section-icon" aria-hidden="true">💶</span>
                        ¿Cuánto dinero dan?
                      </h4>
                      <p className="card-section-text">
                        {selectedSubvencion.versionSimplificada.cuantoDan}
                      </p>
                    </section>

                    <section className="easy-read-card" aria-label="Plazo y cómo realizar la solicitud">
                      <h4 className="card-section-title">
                        <span className="card-section-icon" aria-hidden="true">📅</span>
                        ¿Hasta cuándo hay plazo?
                      </h4>
                      <p className="card-section-text">
                        {selectedSubvencion.versionSimplificada.plazoComoPedir}
                      </p>
                    </section>
                  </>
                ) : (
                  <section className="easy-read-card">
                    <p className="card-section-text">Generando versión simplificada...</p>
                  </section>
                )}

                <div className="easy-read-apply-action" style={{ position: 'relative' }}>
                  {tfgMockupMode && <span className="tfg-annotation-tag bottom-right" style={{ bottom: '100%', right: '0', marginBottom: '5px' }}>Redirección Sede Electrónica (Lenguaje Claro)</span>}
                  {selectedSubvencion.plazoAbierto ? (
                    <a 
                      href={selectedSubvencion.sedeLink || '#'}
                      target="_blank"
                      rel="noopener noreferrer" 
                      className="apply-button-large" 
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                      </svg>
                      <strong>Solicitar esta ayuda</strong>
                    </a>
                  ) : (
                    <button 
                      className="apply-button-large" 
                      disabled 
                      style={{backgroundColor: '#94a3b8', color: '#f1f5f9', cursor: 'not-allowed', boxShadow: 'none'}}
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                      </svg>
                      <strong>Plazo Cerrado</strong>
                    </button>
                  )}
                  <p className="apply-disclaimer">
                    * Esta página es una guía adaptada y simplificada de asistencia. Comprueba siempre los detalles del texto oficial en el enlace del BOE.
                  </p>
                </div>

              </div>

            </div>
          </section>
        )}

        {currentPage === 'admin' && user && user.role === 'admin' && (
          <section className="admin-panel-wrapper">
            <h2 style={{marginBottom: '1rem'}}>Panel de Control de Administración</h2>
            <p style={{color: 'var(--text-muted)', marginBottom: '2rem'}}>
              Desde este panel puedes añadir nuevas subvenciones de forma manual (que serán indexadas semánticamente con IA) o sincronizar manualmente el BOE RSS.
            </p>

            <nav className="admin-tabs" role="tablist">
              <button 
                type="button"
                className={`admin-tab-btn ${adminActiveTab === 'add' ? 'active' : ''}`}
                onClick={() => setAdminActiveTab('add')}
                role="tab"
                aria-selected={adminActiveTab === 'add'}
              >
                Añadir Ayuda
              </button>
              <button 
                type="button"
                className={`admin-tab-btn ${adminActiveTab === 'sync' ? 'active' : ''}`}
                onClick={() => setAdminActiveTab('sync')}
                role="tab"
                aria-selected={adminActiveTab === 'sync'}
              >
                Sincronizar BOE
              </button>
              <button 
                type="button"
                className={`admin-tab-btn ${adminActiveTab === 'history' ? 'active' : ''}`}
                onClick={() => setAdminActiveTab('history')}
                role="tab"
                aria-selected={adminActiveTab === 'history'}
              >
                Historial de Consultas
              </button>
            </nav>

            {adminActiveTab === 'add' && (
              <form onSubmit={handleAdminFormSubmit} className="admin-form">
                <div className="auth-form-group">
                  <label className="auth-form-label">Código BDNS (Obligatorio)</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    placeholder="Ej. 999006" 
                    value={adminForm.codigo_bdns}
                    onChange={(e) => setAdminForm({...adminForm, codigo_bdns: e.target.value})}
                    required
                  />
                </div>
                <div className="auth-form-group">
                  <label className="auth-form-label">Título de la Ayuda (Obligatorio)</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    placeholder="Ej. Ayudas para la compra de ordenadores escolares" 
                    value={adminForm.titulo}
                    onChange={(e) => setAdminForm({...adminForm, titulo: e.target.value})}
                    required
                  />
                </div>
                <div className="auth-form-group">
                  <label className="auth-form-label">Organismo Convocante</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    placeholder="Ej. Consejería de Desarrollo Educativo y Formación Profesional" 
                    value={adminForm.organismo}
                    onChange={(e) => setAdminForm({...adminForm, organismo: e.target.value})}
                  />
                </div>
                <div className="auth-form-group">
                  <label className="auth-form-label">Categoría</label>
                  <select 
                    className="admin-form-select"
                    value={adminForm.categoria}
                    onChange={(e) => setAdminForm({...adminForm, categoria: e.target.value})}
                  >
                    <option value="Vivienda">Vivienda</option>
                    <option value="Educación">Educación</option>
                    <option value="Empleo">Empleo</option>
                    <option value="Energía">Energía</option>
                    <option value="Social">Social</option>
                    <option value="Transporte">Transporte</option>
                    <option value="Otros">Otros</option>
                  </select>
                </div>
                <div className="auth-form-group">
                  <label className="auth-form-label">Cuantía Estimada (ej. 'Hasta 500 €')</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    placeholder="Ej. Hasta 400 € por alumno" 
                    value={adminForm.cuantia}
                    onChange={(e) => setAdminForm({...adminForm, cuantia: e.target.value})}
                  />
                </div>
                <div className="auth-form-group">
                  <label className="auth-form-label">Fecha Límite Plazo (YYYY-MM-DD)</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    placeholder="Ej. 2026-12-31" 
                    value={adminForm.plazo}
                    onChange={(e) => setAdminForm({...adminForm, plazo: e.target.value})}
                  />
                </div>
                <div className="auth-form-group">
                  <label className="auth-form-label">Enlace a Sede Electrónica (Link Solicitud)</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    placeholder="https://..." 
                    value={adminForm.sede_link}
                    onChange={(e) => setAdminForm({...adminForm, sede_link: e.target.value})}
                  />
                </div>
                <div className="auth-form-group">
                  <label className="auth-form-label">Enlace al Boletín Oficial (BOE/BOJA)</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    placeholder="https://..." 
                    value={adminForm.boe_link}
                    onChange={(e) => setAdminForm({...adminForm, boe_link: e.target.value})}
                  />
                </div>
                <div className="auth-form-group admin-form-full">
                  <label className="auth-form-label">Texto Completo de las Bases Reguladoras (Obligatorio)</label>
                  <textarea 
                    className="admin-form-textarea" 
                    placeholder="Pegue aquí el texto oficial de la convocatoria del boletín..."
                    value={adminForm.descripcion_oficial}
                    onChange={(e) => setAdminForm({...adminForm, descripcion_oficial: e.target.value})}
                    required
                  />
                </div>
                <div className="admin-submit-container">
                  {adminIsSubmitting && (
                    <span style={{color: 'var(--text-muted)', fontSize: '0.9rem'}}>
                      <span className="spinner-icon" style={{marginRight: '0.5rem'}}>⏳</span>
                      Procesando e indexando texto con la IA local...
                    </span>
                  )}
                  <button 
                    type="submit" 
                    className="admin-submit-btn" 
                    disabled={adminIsSubmitting}
                  >
                    <span>Guardar y Vectorizar</span>
                  </button>
                </div>
              </form>
            )}

            {adminActiveTab === 'sync' && (
              <div className="rss-sync-box">
                <div style={{fontSize: '3rem'}}>📥</div>
                <h3>Sincronización manual del Boletín Oficial</h3>
                <p style={{maxWidth: '500px', color: 'var(--text-muted)'}}>
                  Al pulsar el botón se consultará en tiempo real el canal RSS oficial de ayudas del BOE para descargar y procesar las últimas convocatorias.
                </p>
                <button 
                  type="button" 
                  className="rss-sync-btn"
                  onClick={handleAdminSync}
                  disabled={adminIsSubmitting}
                >
                  {adminIsSubmitting ? (
                    <>
                      <span className="spinner-icon">⏳</span>
                      <span>Sincronizando...</span>
                    </>
                  ) : (
                    <span>Sincronizar Últimas Convocatorias</span>
                  )}
                </button>
                {adminSyncStatus && (
                  <p className="sync-success-msg">{adminSyncStatus}</p>
                )}
              </div>
            )}

            {adminActiveTab === 'history' && (
              <div className="history-table-container">
                <h3>Registro de Auditoría de Búsquedas (RI-5)</h3>
                <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem'}}>
                  Lista de búsquedas en lenguaje natural ejecutadas por los usuarios en la plataforma.
                </p>
                <div className="history-table-container">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Usuario</th>
                        <th>Consulta</th>
                        <th>Resultados devueltos</th>
                        <th>Fecha y Hora</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminHistory.length === 0 ? (
                        <tr>
                          <td colSpan="4" style={{textAlign: 'center'}}>No hay búsquedas registradas en el historial.</td>
                        </tr>
                      ) : (
                        adminHistory.map((h) => (
                          <tr key={h.id}>
                            <td><strong>{h.usuario_username}</strong></td>
                            <td><em>"{h.query_text}"</em></td>
                            <td>{h.results_count}</td>
                            <td>{new Date(h.timestamp).toLocaleString('es-ES')}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>
        )}

      </main>

      {showAuthModal && (
        <div className="auth-modal-overlay" onClick={() => setShowAuthModal(false)}>
          <div className="auth-modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              type="button" 
              className="auth-modal-close-btn" 
              onClick={() => setShowAuthModal(false)}
              aria-label="Cerrar ventana de acceso"
            >
              ✕
            </button>
            <h2 className="auth-modal-title">
              {authIsRegister ? 'Crear Cuenta' : 'Iniciar Sesión'}
            </h2>
            <form onSubmit={handleAuthSubmit} className="auth-modal-form">
              <div className="auth-form-group">
                <label className="auth-form-label">Nombre de Usuario</label>
                <input 
                  type="text" 
                  className="auth-form-input" 
                  value={authUsername}
                  onChange={(e) => setAuthUsername(e.target.value)}
                  placeholder="Ej. ciudadano123"
                  required
                />
              </div>
              <div className="auth-form-group">
                <label className="auth-form-label">Contraseña</label>
                <input 
                  type="password" 
                  className="auth-form-input" 
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              {authIsRegister && (
                <div className="auth-form-group">
                  <label className="auth-form-label">Tipo de Usuario</label>
                  <select 
                    className="auth-form-select"
                    value={authRole}
                    onChange={(e) => setAuthRole(e.target.value)}
                  >
                    <option value="ciudadano">Ciudadano</option>
                    <option value="admin">Administrador</option>
                  </select>
                </div>
              )}

              {authError && <p className="auth-error-msg">{authError}</p>}

              <button type="submit" className="auth-submit-btn">
                {authIsRegister ? 'Registrarme y Entrar' : 'Acceder'}
              </button>
            </form>
            <p className="auth-modal-toggle-text">
              {authIsRegister ? '¿Ya tienes una cuenta?' : '¿No tienes cuenta aún?'}
              {' '}
              <button 
                type="button" 
                className="auth-modal-toggle-link"
                onClick={() => { setAuthIsRegister(!authIsRegister); setAuthError(''); }}
              >
                {authIsRegister ? 'Inicia sesión aquí' : 'Regístrate aquí'}
              </button>
            </p>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
