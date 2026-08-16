import { useState, useEffect, useRef, useCallback } from "react";
import Login from "./login";
import "./App.css";
import ManageProfessors from "./ManageProfessors";
import ManageStudents from "./ManageStudents";
import ManageNotes from "./ManageNotes";
import StudentProgress from "./StudentProgress";
import FacultiesView from "./FacultiesView";
import ManageSecretaires from "./ManageSecretaires";
import ManageGestionnaires from "./ManageGestionnaires";
import ManageRoles from "./ManageRoles";
import ManageCourses from "./ManageCourses";
import Dashboard from "./Dashboard";
import { getRoleAccess } from "./roleAccess";

const API_BASE_URL = process.env.REACT_APP_API_URL;

function App() {
  const [currentView, setCurrentView] = useState("dashboard");
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [isAdmin, setIsAdmin] = useState(false);
  const [isProfessor, setIsProfessor] = useState(false);
  const [loggedUser, setLoggedUser] = useState("");
  const [userRole, setUserRole] = useState(null);
  const [userRoleDisplay, setUserRoleDisplay] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const chatEndRef = useRef(null);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
    setChat([]);
    setConversations([]);
    setActiveConversationId(null);
    setIsAdmin(false);
    setIsProfessor(false);
    setUserRole(null);
    setUserRoleDisplay("");
    setLoggedUser("");
    setCurrentView("dashboard");
  }, []);

  const fetchUserInfo = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/me/`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setIsAdmin(data.is_staff);
        setIsProfessor(data.is_professor);
        setLoggedUser(data.username);
        setUserRole(data.role);
        setUserRoleDisplay(data.role_display);
      }
    } catch (e) {
      console.error(e);
    }
  }, [token]);

  const deleteConversation = async (e, convId) => {
    e.stopPropagation();
    if (!window.confirm("Voulez-vous vraiment supprimer cet historique ?")) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${convId}/`, {
        method: 'DELETE',
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        if (activeConversationId === convId) setActiveConversationId(null);
        fetchConversations();
      }
    } catch (err) {
      console.error("Erreur supression:", err);
    }
  };

  const fetchConversations = useCallback(async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.status === 401) {
        handleLogout();
        return;
      }
      if (response.ok) {
        const data = await response.json();
        setConversations(data);
      }
    } catch (error) {
      console.error("Erreur conversations:", error);
    }
  }, [token, handleLogout]);


  const fetchHistory = useCallback(async (convId) => {
    if (!token || !convId) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/history/?conversation_id=${convId}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.status === 401) {
        handleLogout();
        return;
      }
      if (response.ok) {
        const data = await response.json();
        setChat(data);
      }
    } catch (error) {
      console.error("Erreur historique:", error);
    }
  }, [token, handleLogout]);

  useEffect(() => {
    if (token) {
      fetchUserInfo();
      fetchConversations();
    }
  }, [token, fetchConversations, fetchUserInfo]);
  useEffect(() => {
    if (activeConversationId) {
      fetchHistory(activeConversationId);
    } else {
      setChat([]);
    }
  }, [activeConversationId, fetchHistory]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const sendMessage = async () => {
    if (!message.trim() || isSending) return;

    const questionText = message.trim();
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMessage = {
      sender: "user",
      text: questionText,
      time: currentTime
    };

    setChat(prev => [...prev, userMessage]);
    setMessage("");
    setIsSending(true);

    const typingTimer = setTimeout(() => setIsTyping(true), 1000);
    const controller = new AbortController();
    const clientTimeout = setTimeout(() => controller.abort(), 60000);

    try {
      const questionData = new FormData();
      questionData.append("message", questionText);
      if (activeConversationId) {
        questionData.append("conversation_id", activeConversationId);
      }

      const response = await fetch(`${API_BASE_URL}/api/chatbot/`, {
        method: "POST",
        headers: {
          ...(token && { "Authorization": `Bearer ${token}` })
        },
        body: questionData,
        signal: controller.signal
      });

      clearTimeout(clientTimeout);

      if (response.status === 401) {
        handleLogout();
        return;
      }

      const data = await response.json();
      if (response.ok) {
        // Mettre à jour l'ID de conversation si nouvelle
        if (data.conversation_id && !activeConversationId) {
          setActiveConversationId(data.conversation_id);
          fetchConversations();
        }

        const botMessage = {
          sender: "bot",
          text: data.response || data.answer || "",
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          sources: data.sources || [],
          file: data.file,
          fileName: data.file_name
        };
        setChat(prev => [...prev, botMessage]);
      } else {
        throw new Error(data.error || "Erreur serveur");
      }
    } catch (error) {
      clearTimeout(clientTimeout);
      const isTimeout = error.name === 'AbortError';
      console.error("Erreur:", error);
      setChat(prev => [...prev, {
        sender: "bot",
        text: isTimeout
          ? "⏱️ Le serveur met trop de temps à répondre. Vérifiez que le backend est démarré et réessayez."
          : `Difficulté technique. ${error.message}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      clearTimeout(typingTimer);
      setIsTyping(false);
      setIsSending(false);
    }
  };

  const createNewChat = () => {
    setActiveConversationId(null);
    setChat([]);
  };

  if (!token) {
    return <Login setToken={(t) => {
      localStorage.setItem("token", t);
      setToken(t);
    }} />;
  }

  const access = getRoleAccess({ userRole, isAdmin, isProfessor });

  const showGestionnaires = access.canManageGestionnaires;
  const showSecretaires = access.canManageSecretaires;
  const showProfessors = access.canManageProfessors;
  const showStudents = access.canManageStudents;
  const showFaculties = access.canAccessFaculties;
  const showNotes = access.canManageNotes;
  const showCourses = access.canManageCourses;
  const showProgress = access.canViewProgress;
  const showAdminSystem = access.canAccessAdminSystem;
  const isStudent = access.isStudent;

  const roleTitle = userRoleDisplay || (access.isCentralAdmin ? 'Administrateur Central' : userRole === 'admin_gestionnaire' ? 'Administrateur Gestionnaire' : userRole === 'secretaire_facultaire' ? 'Secrétaire Facultaire' : userRole === 'professeur' ? 'Professeur' : userRole === 'etudiant' ? 'Étudiant' : isAdmin ? 'Administrateur' : isProfessor ? 'Professeur' : 'Utilisateur');

  const welcomeBadge = access.isCentralAdmin
    ? 'Administrateur Central'
    : isStudent
      ? 'Étudiant'
      : access.isProfessor
        ? 'Professeur'
        : (access.canManageStudents || access.canManageProfessors)
          ? 'Gestion académique'
          : 'Administration';

  const welcomeMsg = access.isCentralAdmin
    ? 'Bonjour Administrateur Central ! Bienvenue sur la plateforme de gestion et de supervision pédagogique.'
    : isStudent
      ? 'Bonjour ! Posez vos questions et consultez les ressources pédagogiques mises à votre disposition.'
      : 'Bonjour ! Gérez les responsabilités attribuées à votre profil avec une vue claire sur la plateforme.';

  const roleHint = access.isCentralAdmin
    ? "Vous disposez des privilèges complets pour gérer le système, attribuer les rôles et administrer la plateforme."
    : isStudent
      ? "Vous pouvez consulter les ressources pédagogiques et dialoguer avec l’assistant."
      : access.isProfessor
        ? "Vous pouvez alimenter la plateforme avec des contenus pédagogiques."
        : (access.canManageStudents || access.canManageProfessors)
          ? "Vous gérez les utilisateurs académiques de votre périmètre."
          : "Vous avez un accès de supervision sur la plateforme.";


  return (
    <div className="app-layout">


      {/* ── Historique du Chat (visible uniquement si le chat est ouvert) ── */}
      {currentView === 'chat' && (
        <div className={`sidebar${sidebarCollapsed ? ' sidebar--collapsed' : ''}`}>
          <button
            className="sidebar-toggle-btn"
            onClick={() => setSidebarCollapsed(prev => !prev)}
            title={sidebarCollapsed ? 'Afficher l\'historique' : 'Réduire l\'historique'}
            aria-label={sidebarCollapsed ? 'Ouvrir la sidebar' : 'Fermer la sidebar'}
          >
            {sidebarCollapsed ? '▶' : '◀'}
          </button>

          <div className="sidebar-inner">
            <div className="sidebar-header">
              <button className="new-chat-btn" onClick={createNewChat}>
                <span>+</span> Nouvelle discussion
              </button>
            </div>
            <div className="history-list">
              {conversations.map(conv => (
                <div
                  key={conv.id}
                  className={`history-item ${activeConversationId === conv.id ? 'active' : ''}`}
                  onClick={() => {
                    setActiveConversationId(conv.id);
                  }}
                >
                  <div className="history-title">{conv.title}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="history-date">{conv.updated_at}</span>
                    <button
                      style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                      onClick={(e) => deleteConversation(e, conv.id)}
                      title="Supprimer la discussion"
                    >🗑️</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Contenu Principal ── */}
      <div className="main-content">
        <div className="header">
          <h2 className="title">Assistant Pédagogique IA</h2>

          <div className="navbar">
            <button
              className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentView('dashboard')}
            >📊 Tableau de bord</button>

            {showFaculties && (
              <button
                className={`nav-btn ${currentView === 'faculties' ? 'active' : ''}`}
                onClick={() => setCurrentView('faculties')}
              >🏢 Facultés</button>
            )}

            {showGestionnaires && (
              <button
                className={`nav-btn ${currentView === 'gestionnaires' ? 'active' : ''}`}
                onClick={() => setCurrentView('gestionnaires')}
              >💼 Gestionnaires</button>
            )}

            {showSecretaires && (
              <button
                className={`nav-btn ${currentView === 'secretaires' ? 'active' : ''}`}
                onClick={() => setCurrentView('secretaires')}
              >📋 Secrétaires</button>
            )}

            {showProfessors && (
              <button
                className={`nav-btn ${currentView === 'professors' ? 'active' : ''}`}
                onClick={() => setCurrentView('professors')}
              >👨‍🏫 Professeurs</button>
            )}

            {showCourses && (
              <button
                className={`nav-btn ${currentView === 'courses' ? 'active' : ''}`}
                onClick={() => setCurrentView('courses')}
              >📚 Cours</button>
            )}

            {showStudents && (
              <button
                className={`nav-btn ${currentView === 'students' ? 'active' : ''}`}
                onClick={() => setCurrentView('students')}
              >🎓 Étudiants</button>
            )}

            {showNotes && (
              <button
                className={`nav-btn ${currentView === 'notes' ? 'active' : ''}`}
                onClick={() => setCurrentView('notes')}
              >📝 Notes</button>
            )}

            {showProgress && (
              <button
                className={`nav-btn ${currentView === 'progress' ? 'active' : ''}`}
                onClick={() => setCurrentView('progress')}
              >📊 Suivi</button>
            )}

            {showAdminSystem && (
              <button
                className={`nav-btn ${currentView === 'admin_system' ? 'active' : ''}`}
                onClick={() => setCurrentView('admin_system')}
                style={currentView === 'admin_system' ? {} : { borderColor: 'rgba(239,68,68,0.25)', color: '#fca5a5' }}
              >⚙️ Admin Système</button>
            )}
          </div>

          <div className="user-info">
            {loggedUser && (
              <span style={{ fontWeight: 600, color: '#e2e8f0', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: '13px', textAlign: 'right' }}>
                <span>👤 {loggedUser}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{roleTitle}</span>
              </span>
            )}
            <button onClick={handleLogout} className="logout-btn">Déconnexion</button>
          </div>
        </div>

        <div className="content-area">
          {currentView === 'dashboard' && <Dashboard token={token} />}
          {showStudents && currentView === 'students' && <ManageStudents token={token} />}
          {showProfessors && currentView === 'professors' && <ManageProfessors token={token} />}
          {showSecretaires && currentView === 'secretaires' && <ManageSecretaires token={token} />}
          {showGestionnaires && currentView === 'gestionnaires' && <ManageGestionnaires token={token} />}
          {showFaculties && currentView === 'faculties' && <FacultiesView token={token} />}
          {showCourses && currentView === 'courses' && <ManageCourses token={token} />}
          {showNotes && currentView === 'notes' && <ManageNotes token={token} />}
          {showProgress && currentView === 'progress' && <StudentProgress token={token} />}
          {showAdminSystem && currentView === 'admin_system' && <ManageRoles token={token} />}

          {currentView === 'chat' && (
            <>
              <div className="chat-box">
                {chat.length === 0 && !activeConversationId ? (
                  <div className="welcome-container">
                    <div className="welcome-card">
                      <div className="welcome-badge">{welcomeBadge}</div>
                      <div className="welcome-msg">{welcomeMsg}</div>
                      <div className="welcome-hint">{roleHint}</div>
                    </div>
                  </div>
                ) : (
                  chat.map((msg, index) => (
                    <div
                      key={index}
                      className={`message ${msg.sender === "user" ? "user-message" : "bot-message"}`}
                    >
                      {msg.file && (() => {
                        const fileUrl = msg.file.startsWith('blob:') ? msg.file : (msg.file.startsWith('http') ? msg.file : `${API_BASE_URL}${msg.file}`);
                        const lower = (msg.fileName || fileUrl || '').toLowerCase();
                        if (lower.endsWith('.pdf')) {
                          return (
                            <div className="message-file">
                              <a href={fileUrl} target="_blank" rel="noreferrer" className="attachment-link">📄 Télécharger le PDF</a>
                            </div>
                          );
                        }
                        if (lower.match(/\.(png|jpe?g|gif)$/)) {
                          return (
                            <div className="message-file">
                              <img src={fileUrl} alt="Pièce jointe" className="message-image" />
                            </div>
                          );
                        }
                        return (
                          <div className="message-file">
                            <a href={fileUrl} target="_blank" rel="noreferrer" className="attachment-link">Télécharger la pièce jointe</a>
                          </div>
                        );
                      })()}
                      {msg.text}
                      {msg.sources && msg.sources.length > 0 && (
                        <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
                          Sources : {msg.sources.join(', ')}
                        </div>
                      )}
                      <div className="msg-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                        <span className="time">{msg.time}</span>
                        <button
                          onClick={() => navigator.clipboard.writeText(msg.text)}
                          style={{
                            background: 'transparent', border: 'none', cursor: 'pointer',
                            color: msg.sender === 'user' ? 'rgba(255,255,255,0.7)' : 'var(--text-muted)'
                          }}
                          title="Copier le message"
                        >📋</button>
                      </div>
                    </div>
                  ))
                )}
                {isTyping && (
                  <div className="message bot-message typing-indicator">
                    <span className="typing-dot"></span>
                    <span className="typing-dot"></span>
                    <span className="typing-dot"></span>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="input-area">
                <div className="input-container" style={{ flexDirection: 'column', alignItems: 'stretch' }}>


                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '10px' }}>
                    <input
                      type="text"
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Posez votre question ici..."
                      onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                      disabled={isSending}
                      autoFocus
                      style={{ flex: 1 }}
                    />
                    <button onClick={sendMessage} className="send-btn" disabled={isSending}>
                      {isSending ? "..." : "Envoyer"}
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Bouton Flottant (FAB) Chat IA ── */}
      <button 
        className={`fab-chat ${currentView === 'chat' ? 'active' : ''}`}
        onClick={() => setCurrentView(currentView === 'chat' ? 'dashboard' : 'chat')}
        title="Ouvrir le Chat IA"
      >
        <span className="fab-icon">💬</span>
      </button>
    </div>
  );
}

export default App;