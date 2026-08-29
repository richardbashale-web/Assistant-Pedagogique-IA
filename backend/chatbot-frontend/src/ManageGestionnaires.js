import { useState, useEffect, useCallback } from "react";
import { useToast } from "./Toast";

function ManageGestionnaires({ token }) {
  const [gestionnaires, setGestionnaires] = useState([]);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nom_complet, setNom_complet] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [togglingId, setTogglingId] = useState(null);
  const { toastContainer, showToast } = useToast();

  const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
  const CREATE_API_URL = `${API_BASE_URL}/api/admin-gestionnaire/create/`;
  const LIST_API_URL = `${API_BASE_URL}/api/roles/users/?role_nom=admin_gestionnaire`;
  const DETAIL_API_URL = (id) => `${API_BASE_URL}/api/admin-gestionnaire/${id}`;

  const fetchGestionnaires = useCallback(async () => {
    try {
      const res = await fetch(LIST_API_URL, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) setGestionnaires(await res.json());
    } catch (error) {
      console.error("Erreur lors de la récupération:", error);
    } finally {
      setFetching(false);
    }
  }, [token, LIST_API_URL]);

  useEffect(() => {
    if (token) fetchGestionnaires();
  }, [token, fetchGestionnaires]);

  const resetForm = () => {
    setUsername(""); setEmail(""); setPassword(""); setNom_complet(""); setEditingId(null);
  };

  const handleCreateGestionnaire = async () => {
    if (editingId) {
      if (!email || !nom_complet) {
        showToast("Veuillez remplir le nom complet et l'email", "error");
        return;
      }
    } else if (!username || !email || !password || !nom_complet) {
      showToast("Veuillez remplir tous les champs", "error");
      return;
    }

    setLoading(true);

    try {
      const url = editingId ? `${DETAIL_API_URL(editingId)}/update/` : CREATE_API_URL;
      const method = editingId ? "PATCH" : "POST";
      const body = editingId ? { nom_complet, email } : { username, email, password, nom_complet };

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      if (res.ok) {
        showToast(editingId ? "Gestionnaire modifié avec succès !" : "Administrateur gestionnaire créé avec succès!", "success");
        resetForm();
        fetchGestionnaires();
      } else {
        let errorMessage = "Impossible d'enregistrer le gestionnaire";
        try {
          const error = await res.json();
          errorMessage = error.error || error.detail || JSON.stringify(error);
        } catch (e) {
          const text = await res.text();
          errorMessage = text || errorMessage;
        }
        console.error("Gestionnaire save failed", res.status, errorMessage);
        showToast(`Erreur: ${errorMessage}`, "error");
      }
    } catch (error) {
      console.error("Gestionnaire save exception", error);
      showToast("Erreur lors de l'enregistrement du gestionnaire", "error");
    } finally {
      setLoading(false);
    }
  };

  const editGestionnaire = (g) => {
    setUsername(g.user__username);
    setEmail(g.user__email || "");
    setNom_complet(g.nom_complet || "");
    setPassword("");
    setEditingId(g.user__id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteGestionnaire = async (g) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer "${g.nom_complet || g.user__username}" ?`)) return;
    try {
      const res = await fetch(`${DETAIL_API_URL(g.user__id)}/delete/`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) { showToast("Gestionnaire supprimé.", "success"); fetchGestionnaires(); }
      else {
        const err = await res.json();
        showToast(err.error || "Erreur lors de la suppression.", "error");
      }
    } catch { showToast("Erreur réseau.", "error"); }
  };

  const toggleGestionnaireActive = async (g) => {
    const action = g.est_actif ? "désactiver" : "activer";
    if (!window.confirm(`Voulez-vous vraiment ${action} "${g.nom_complet || g.user__username}" ?`)) return;
    setTogglingId(g.user__id);
    try {
      const res = await fetch(`${DETAIL_API_URL(g.user__id)}/toggle-active/`, {
        method: "PATCH",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        showToast(data.message, "success");
        setGestionnaires((prev) =>
          prev.map((item) => item.user__id === g.user__id ? { ...item, est_actif: data.is_active } : item)
        );
      } else {
        const err = await res.json();
        showToast(err.error || "Erreur lors du changement d'état.", "error");
      }
    } catch { showToast("Erreur réseau.", "error"); }
    finally { setTogglingId(null); }
  };

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>Gestion des Administrateurs Gestionnaires </h2>
          <p>{editingId ? "Modifiez les informations du gestionnaire sélectionné." : "Créez et supervisez les profils des gestionnaires de facultés du système."}</p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Nom d'utilisateur
            <input placeholder="Ex: jean_gestionnaire" value={username} onChange={e => setUsername(e.target.value)} disabled={loading || !!editingId} />
          </label>
          <label className="field-label">
            Nom complet
            <input placeholder="Ex: Richard Bashale" value={nom_complet} onChange={e => setNom_complet(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Adresse email
            <input placeholder="Ex: jean@univ.edu" type="email" value={email} onChange={e => setEmail(e.target.value)} disabled={loading} />
          </label>
          {!editingId && (
            <label className="field-label">
              Mot de passe
              <input placeholder="••••••••" type="password" value={password} onChange={e => setPassword(e.target.value)} disabled={loading} />
            </label>
          )}
          <div className="field-full" style={{ display: "flex", gap: "12px", marginTop: "10px" }}>
            <button className="primary-btn" onClick={handleCreateGestionnaire} disabled={loading}>
              {loading ? "Traitement..." : editingId ? "Enregistrer les modifications" : "Créer le gestionnaire"}
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
        <h3>Gestionnaires existants</h3>
      </div>

      {fetching ? (
        <div className="empty-state">Chargement des gestionnaires...</div>
      ) : gestionnaires.length === 0 ? (
        <div className="empty-state">Aucun gestionnaire facultaire créé pour le moment.</div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Nom complet</th>
                <th>Nom d'utilisateur</th>
                <th>Email</th>
                <th>État</th>
                <th style={{ textAlign: "center" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {gestionnaires.map(g => (
                <tr key={g.user__id} style={editingId === g.user__id ? { background: "rgba(99,102,241,0.08)" } : {}}>
                  <td style={{ fontWeight: 600 }}>{g.nom_complet || g.user__username}</td>
                  <td>{g.user__username}</td>
                  <td>{g.user__email || '-'}</td>
                  <td>
                    <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 700, background: g.est_actif ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: g.est_actif ? '#10b981' : '#f87171' }}>
                      {g.est_actif ? 'Actif' : 'Inactif'}
                    </span>
                  </td>
                  <td style={{ textAlign: "center", whiteSpace: "nowrap" }}>
                    <button onClick={() => editGestionnaire(g)}
                      style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.25)", borderRadius: "8px", padding: "6px 10px", marginRight: "6px", cursor: "pointer", color: "#a5b4fc" }}
                      title="Modifier le gestionnaire">✏️ Modifier</button>

                    <button
                      onClick={() => toggleGestionnaireActive(g)}
                      disabled={togglingId === g.user__id}
                      style={{
                        background: g.est_actif ? "rgba(245,158,11,0.1)" : "rgba(16,185,129,0.1)",
                        border: `1px solid ${g.est_actif ? "rgba(245,158,11,0.25)" : "rgba(16,185,129,0.25)"}`,
                        borderRadius: "8px", padding: "6px 10px", marginRight: "6px",
                        cursor: togglingId === g.user__id ? "not-allowed" : "pointer",
                        color: g.est_actif ? "#fbbf24" : "#34d399",
                        opacity: togglingId === g.user__id ? 0.5 : 1,
                        fontSize: "12px", fontWeight: 600,
                      }}
                      title={g.est_actif ? "Désactiver le gestionnaire" : "Réactiver le gestionnaire"}
                    >
                      {togglingId === g.user__id ? "..." : g.est_actif ? "🔒 Désactiver" : "🔓 Activer"}
                    </button>

                    <button onClick={() => deleteGestionnaire(g)}
                      style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: "8px", padding: "6px 10px", cursor: "pointer", color: "#f87171" }}
                      title="Supprimer le gestionnaire">🗑️</button>
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

export default ManageGestionnaires;