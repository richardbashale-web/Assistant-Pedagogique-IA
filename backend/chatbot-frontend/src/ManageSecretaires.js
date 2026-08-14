import { useState, useEffect, useCallback } from "react";
import FacultySelector from "./FacultySelector";
import { useToast } from "./Toast";

function ManageSecretaires({ token }) {
  const [secretaires, setSecretaires] = useState([]);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nom_complet, setNom_complet] = useState("");
  const [faculte, setFaculte] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const { toastContainer, showToast } = useToast();

  const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
  const API_URL = `${API_BASE_URL}/api/secretaire/create/`;
  const LIST_API_URL = `${API_BASE_URL}/api/roles/users/?role_nom=secretaire_facultaire`;

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

  const handleCreateSecretaire = async () => {
    if (!faculte) {
      showToast("Veuillez sélectionner une faculté", "error");
      return;
    }

    if (!username || !email || !password || !nom_complet) {
      showToast("Veuillez remplir tous les champs", "error");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          username, email, password, nom_complet, faculte
        })
      });

      if (res.ok) {
        showToast("Secrétaire créé avec succès!", "success");
        setUsername(""); setEmail(""); setPassword(""); setNom_complet(""); setFaculte("");
        fetchSecretaires();
      } else {
        const error = await res.json();
        const msg = error.error || error.detail || (typeof error === 'object' ? Object.values(error).flat().join(' ') : "Impossible de créer le secrétaire");
        showToast(`Erreur: ${msg}`, "error");
      }
    } catch (error) {
      showToast("Erreur réseau lors de la création du secrétaire", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>Créer un Secrétaire Facultaire 📋</h2>
          <p>Enregistrez un secrétaire pour gérer les professeurs et étudiants d'une faculté spécifique.</p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Nom d'utilisateur
            <input placeholder="Ex: marie_secretaire" value={username} onChange={e => setUsername(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Nom complet
            <input placeholder="Ex: Marie Martin" value={nom_complet} onChange={e => setNom_complet(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Adresse email
            <input placeholder="Ex: marie@univ.edu" type="email" value={email} onChange={e => setEmail(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Mot de passe
            <input placeholder="••••••••" type="password" value={password} onChange={e => setPassword(e.target.value)} disabled={loading} />
          </label>
          <FacultySelector token={token} value={faculte} onChange={e => setFaculte(e.target.value)} label="Sélectionner la faculté" />
          <button className="primary-btn" onClick={handleCreateSecretaire} disabled={loading}>
            {loading ? "Création en cours..." : "Créer le secrétaire"}
          </button>
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
              </tr>
            </thead>
            <tbody>
              {secretaires.map(s => (
                <tr key={s.user__id}>
                  <td style={{ fontWeight: 600 }}>{s.nom_complet || s.user__username}</td>
                  <td>{s.user__username}</td>
                  <td>{s.user__email || '-'}</td>
                  <td>{s.faculte || 'Non spécifiée'}</td>
                  <td>
                    <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 700, background: s.est_actif ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: s.est_actif ? '#10b981' : '#f87171' }}>
                      {s.est_actif ? 'Actif' : 'Inactif'}
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

export default ManageSecretaires;
