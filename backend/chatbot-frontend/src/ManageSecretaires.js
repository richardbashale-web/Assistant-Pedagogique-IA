import { useState, useEffect, useCallback, useRef } from "react";
import FacultySelector from "./FacultySelector";
import { useToast } from "./Toast";

function ManageSecretaires({ token }) {
  const [secretaires, setSecretaires] = useState([]);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nom_complet, setNom_complet] = useState("");
  const [faculte, setFaculte] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [togglingId, setTogglingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const { toastContainer, showToast } = useToast();
  const nomCompletInputRef = useRef(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
  const CREATE_API_URL = `${API_BASE_URL}/api/secretaire/create/`;
  const LIST_API_URL = `${API_BASE_URL}/api/roles/users/?role_nom=secretaire_facultaire`;
  const DETAIL_API_URL = (id) => `${API_BASE_URL}/api/secretaire/${id}`;

  const fetchSecretaires = useCallback(async () => {
    try {
      const res = await fetch(LIST_API_URL, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSecretaires(data);
      }
    } catch (error) {
      console.error("Erreur lors du chargement des secrétaires:", error);
    } finally {
      setFetching(false);
    }
  }, [token, LIST_API_URL]);

  useEffect(() => {
    if (token) fetchSecretaires();
  }, [token, fetchSecretaires]);

  useEffect(() => {
    if (editingId && nomCompletInputRef.current) {
      nomCompletInputRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
      nomCompletInputRef.current.focus();
    }
  }, [editingId]);

  const resetForm = () => {
    setUsername("");
    setEmail("");
    setPassword("");
    setNom_complet("");
    setFaculte("");
    setEditingId(null);
  };

  const handleCreateSecretaire = async () => {
    if (!faculte) {
      showToast("Veuillez sélectionner une faculté", "error");
      return;
    }

    if (!email || !nom_complet || (!editingId && (!username || !password))) {
      showToast(editingId ? "Veuillez remplir le nom complet et l'email" : "Veuillez remplir tous les champs", "error");
      return;
    }

    setLoading(true);

    try {
      const url = editingId ? `${DETAIL_API_URL(editingId)}/update/` : CREATE_API_URL;
      const method = editingId ? "PATCH" : "POST";
      const body = editingId
        ? { nom_complet, email, faculte }
        : { username, email, password, nom_complet, faculte };
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      if (res.ok) {
        showToast(editingId ? "Secrétaire modifié avec succès !" : "Secrétaire créé avec succès!", "success");
        resetForm();
        fetchSecretaires();
      } else {
        const responseText = await res.text();
        let msg = responseText || `Impossible d'enregistrer le secrétaire (HTTP ${res.status}).`;
        try {
          const error = JSON.parse(responseText);
          msg = error.error || error.detail || (typeof error === "object" ? Object.values(error).flat().join(" ") : msg);
        } catch {
          // Keep the response text when the server does not return JSON.
        }
        showToast(`Erreur: ${msg}`, "error");
      }
    } catch (error) {
      console.error("Erreur lors de l'enregistrement du secrétaire:", error);
      showToast("Erreur réseau lors de l'enregistrement du secrétaire", "error");
    } finally {
      setLoading(false);
    }
  };

  const editSecretaire = (secretaire) => {
    setUsername(secretaire.user__username);
    setEmail(secretaire.user__email || "");
    setPassword("");
    setNom_complet(secretaire.nom_complet || "");
    setFaculte(secretaire.faculte_code || "");
    setEditingId(secretaire.user__id);
  };

  const toggleSecretaireActive = async (secretaire) => {
    const action = secretaire.est_actif ? "désactiver" : "activer";
    if (!window.confirm(`Voulez-vous vraiment ${action} "${secretaire.nom_complet || secretaire.user__username}" ?`)) return;
    setTogglingId(secretaire.user__id);
    try {
      const res = await fetch(`${DETAIL_API_URL(secretaire.user__id)}/toggle-active/`, {
        method: "PATCH",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        showToast(data.message, "success");
        setSecretaires((previous) => previous.map((item) =>
          item.user__id === secretaire.user__id ? { ...item, est_actif: data.is_active } : item
        ));
      } else {
        const responseText = await res.text();
        let message = responseText || `Erreur lors du changement d'état (HTTP ${res.status}).`;
        try {
          const error = JSON.parse(responseText);
          message = error.error || error.detail || message;
        } catch {
          // Preserve non-JSON server responses.
        }
        showToast(message, "error");
      }
    } catch (error) {
      console.error("Erreur lors du changement d'état du secrétaire:", error);
      showToast("Erreur réseau lors du changement d'état du secrétaire.", "error");
    } finally {
      setTogglingId(null);
    }
  };

  const deleteSecretaire = async (secretaire) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer "${secretaire.nom_complet || secretaire.user__username}" ?`)) return;
    setDeletingId(secretaire.user__id);
    try {
      const res = await fetch(`${DETAIL_API_URL(secretaire.user__id)}/delete/`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        showToast("Secrétaire supprimé.", "success");
        setSecretaires((previous) => previous.filter((item) => item.user__id !== secretaire.user__id));
        if (editingId === secretaire.user__id) resetForm();
      } else {
        const responseText = await res.text();
        let message = responseText || `Erreur lors de la suppression (HTTP ${res.status}).`;
        try {
          const error = JSON.parse(responseText);
          message = error.error || error.detail || message;
        } catch {
          // Preserve non-JSON server responses.
        }
        showToast(message, "error");
      }
    } catch (error) {
      console.error("Erreur lors de la suppression du secrétaire:", error);
      showToast("Erreur réseau lors de la suppression du secrétaire.", "error");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>{editingId ? "Modifier un Secrétaire Facultaire 📋" : "Créer un Secrétaire Facultaire 📋"}</h2>
          <p>{editingId ? "Modifiez les informations du secrétaire sélectionné." : "Enregistrez un secrétaire pour gérer les enseignants et étudiants d'une faculté spécifique."}</p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Nom d'utilisateur
            <input placeholder="Ex: marie_secretaire" value={username} onChange={e => setUsername(e.target.value)} disabled={loading || !!editingId} />
          </label>
          <label className="field-label">
            Nom complet
            <input ref={nomCompletInputRef} placeholder="Ex: Marie Martin" value={nom_complet} onChange={e => setNom_complet(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Adresse email
            <input placeholder="Ex: marie@univ.edu" type="email" value={email} onChange={e => setEmail(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Mot de passe
            <input placeholder="••••••••" type="password" value={password} onChange={e => setPassword(e.target.value)} disabled={loading || !!editingId} />
          </label>
          <FacultySelector token={token} value={faculte} onChange={e => setFaculte(e.target.value)} label="Sélectionner la faculté" />
          <div className="field-full" style={{ display: "flex", gap: "12px", marginTop: "10px" }}>
            <button className="primary-btn" onClick={handleCreateSecretaire} disabled={loading}>
              {loading ? "Traitement..." : editingId ? "Enregistrer les modifications" : "Créer le secrétaire"}
            </button>
            {editingId && (
              <button className="logout-btn" onClick={resetForm}
                style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#cbd5e1" }}>
                Annuler
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="section-header section-header-tight">
        <h3>Secrétaires existants</h3>
      </div>

      {fetching ? (
        <div className="empty-state">Chargement des secrétaires...</div>
      ) : secretaires.length === 0 ? (
        <div className="empty-state">Aucun secrétaire trouvé</div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Nom complet</th>
                <th>Nom d'utilisateur</th>
                <th>Email</th>
                <th>Faculté</th>
                <th>État</th>
                <th style={{ textAlign: "center" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {secretaires.map(s => (
                <tr key={s.user__id} style={editingId === s.user__id ? { background: "rgba(99,102,241,0.08)" } : {}}>
                  <td style={{ fontWeight: 600 }}>{s.nom_complet || s.user__username}</td>
                  <td>{s.user__username}</td>
                  <td>{s.user__email || '-'}</td>
                  <td>{s.faculte || 'Non spécifiée'}</td>
                  <td>
                    <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 700, background: s.est_actif ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: s.est_actif ? '#10b981' : '#f87171' }}>
                      {s.est_actif ? 'Actif' : 'Inactif'}
                    </span>
                  </td>
                  <td style={{ textAlign: "center", whiteSpace: "nowrap" }}>
                    <button onClick={() => editSecretaire(s)}
                      style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.25)", borderRadius: "8px", padding: "6px 10px", marginRight: "6px", cursor: "pointer", color: "#a5b4fc" }}
                      title="Modifier le secrétaire">✏️ Modifier</button>
                    <button onClick={() => toggleSecretaireActive(s)}
                      disabled={togglingId === s.user__id}
                      style={{
                        background: s.est_actif ? "rgba(245,158,11,0.1)" : "rgba(16,185,129,0.1)",
                        border: `1px solid ${s.est_actif ? "rgba(245,158,11,0.25)" : "rgba(16,185,129,0.25)"}`,
                        borderRadius: "8px", padding: "6px 10px", marginRight: "6px",
                        cursor: togglingId === s.user__id ? "not-allowed" : "pointer",
                        color: s.est_actif ? "#fbbf24" : "#34d399",
                        opacity: togglingId === s.user__id ? 0.5 : 1,
                        fontSize: "12px", fontWeight: 600,
                      }}
                      title={s.est_actif ? "Désactiver le secrétaire" : "Réactiver le secrétaire"}>
                      {togglingId === s.user__id ? "..." : s.est_actif ? "🔒 Désactiver" : "🔓 Activer"}
                    </button>
                    <button onClick={() => deleteSecretaire(s)}
                      disabled={deletingId === s.user__id}
                      style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: "8px", padding: "6px 10px", cursor: deletingId === s.user__id ? "not-allowed" : "pointer", color: "#f87171", opacity: deletingId === s.user__id ? 0.5 : 1 }}
                      title="Supprimer le secrétaire">
                      {deletingId === s.user__id ? "..." : "🗑️"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ManageSecretaires;
