import { useState, useEffect, useCallback } from "react";
import { useToast } from "./Toast";

function ManageGestionnaires({ token }) {
  const [gestionnaires, setGestionnaires] = useState([]);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nom_complet, setNom_complet] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const { toastContainer, showToast } = useToast();

  const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
  const CREATE_API_URL = `${API_BASE_URL}/api/admin-gestionnaire/create/`;
  const LIST_API_URL = `${API_BASE_URL}/api/roles/users/?role_nom=admin_gestionnaire`;

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

  const handleCreateGestionnaire = async () => {
    if (!username || !email || !password || !nom_complet) {
      showToast("Veuillez remplir tous les champs", "error");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(CREATE_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ username, email, password, nom_complet })
      });

      if (res.ok) {
        showToast("Administrateur gestionnaire créé avec succès!", "success");
        setUsername(""); setEmail(""); setPassword(""); setNom_complet("");
        fetchGestionnaires();
      } else {
        let errorMessage = "Impossible de créer le gestionnaire";
        try {
          const error = await res.json();
          errorMessage = error.error || error.detail || JSON.stringify(error);
        } catch (e) {
          const text = await res.text();
          errorMessage = text || errorMessage;
        }
        console.error("Gestionnaire creation failed", res.status, errorMessage);
        showToast(`Erreur: ${errorMessage}`, "error");
      }
    } catch (error) {
      console.error("Gestionnaire creation exception", error);
      showToast("Erreur lors de la création du gestionnaire", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>Gestion des Administrateurs Gestionnaires 💼</h2>
          <p>Créez et supervisez les profils des gestionnaires de facultés du système.</p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Nom d'utilisateur
            <input placeholder="Ex: jean_gestionnaire" value={username} onChange={e => setUsername(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Nom complet
            <input placeholder="Ex: Jean Dupont" value={nom_complet} onChange={e => setNom_complet(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Adresse email
            <input placeholder="Ex: jean@univ.edu" type="email" value={email} onChange={e => setEmail(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Mot de passe
            <input placeholder="••••••••" type="password" value={password} onChange={e => setPassword(e.target.value)} disabled={loading} />
          </label>
          <button className="primary-btn" onClick={handleCreateGestionnaire} disabled={loading}>
            {loading ? "Création en cours..." : "Créer le gestionnaire"}
          </button>
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
              </tr>
            </thead>
            <tbody>
              {gestionnaires.map(g => (
                <tr key={g.user__id}>
                  <td style={{ fontWeight: 600 }}>{g.nom_complet || g.user__username}</td>
                  <td>{g.user__username}</td>
                  <td>{g.user__email || '-'}</td>
                  <td>
                    <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 700, background: g.est_actif ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: g.est_actif ? '#10b981' : '#f87171' }}>
                      {g.est_actif ? 'Actif' : 'Inactif'}
                    </span>
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
