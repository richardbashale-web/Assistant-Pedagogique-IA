import { useState, useEffect, useCallback } from "react";
import FacultySelector from "./FacultySelector";

function ManageRoles({ token }) {
  const [roles, setRoles] = useState([]);
  const [assignUsername, setAssignUsername] = useState("");
  const [assignRoleNom, setAssignRoleNom] = useState("");
  const [users, setUsers] = useState([]);
  const [selectedRoleFilter, setSelectedRoleFilter] = useState("admin_gestionnaire");
  const [createRoleNom, setCreateRoleNom] = useState("admin_gestionnaire");
  const [createUsername, setCreateUsername] = useState("");
  const [createEmail, setCreateEmail] = useState("");
  const [createPassword, setCreatePassword] = useState("");
  const [createNomComplet, setCreateNomComplet] = useState("");
  const [createFaculte, setCreateFaculte] = useState("");
  const [createSpecialite, setCreateSpecialite] = useState("");
  const [createTelephone, setCreateTelephone] = useState("");
  const [createNiveau, setCreateNiveau] = useState("");
  const [createMatricule, setCreateMatricule] = useState("");
  const [loading, setLoading] = useState(false);
  const [initLoading, setInitLoading] = useState(false);
  const [fetchingUsers, setFetchingUsers] = useState(false);
  const [message, setMessage] = useState(null); // { type: 'success'|'error', text: string }

  const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const fetchRoles = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/roles/`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) setRoles(await res.json());
    } catch (e) {
      console.error("Erreur chargement rôles:", e);
    }
  }, [token, API_BASE_URL]);

  const fetchUsersByRole = useCallback(async (roleNom) => {
    if (!roleNom) return;
    setFetchingUsers(true);
    try {
      let endpoint = `${API_BASE_URL}/api/roles/users/?role_nom=${roleNom}`;
      if (roleNom === "professeur") endpoint = `${API_BASE_URL}/api/professors/`;
      if (roleNom === "etudiant") endpoint = `${API_BASE_URL}/api/students/`;
      const res = await fetch(endpoint, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (roleNom === "professeur") {
          setUsers(data.map(u => ({
            user__id: u.id,
            user__username: u.nom,
            user__email: u.email,
            faculte: u.faculte,
            specialite: u.specialite,
            telephone: u.telephone,
            est_actif: true
          })));
        } else if (roleNom === "etudiant") {
          setUsers(data.map(u => ({
            user__id: u.id,
            user__username: u.nom,
            user__email: u.email,
            faculte: u.faculte,
            niveau: u.niveau,
            matricule: u.matricule,
            est_actif: true
          })));
        } else {
          setUsers(data);
        }
      } else {
        setUsers([]);
      }
    } catch (e) {
      console.error("Erreur chargement utilisateurs:", e);
      setUsers([]);
    } finally {
      setFetchingUsers(false);
    }
  }, [token, API_BASE_URL]);

  useEffect(() => {
    if (token) {
      fetchRoles();
      fetchUsersByRole(selectedRoleFilter);
    }
  }, [token, fetchRoles, fetchUsersByRole, selectedRoleFilter]);

  const handleInitRoles = async () => {
    if (!window.confirm("Initialiser tous les rôles du système ? Cette action est idempotente et sans danger.")) return;
    setInitLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/roles/initialize/`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        showMessage("success", "✅ " + (data.success || "Rôles initialisés avec succès !"));
        fetchRoles();
      } else {
        showMessage("error", "❌ " + (data.error || "Erreur lors de l'initialisation."));
      }
    } catch (e) {
      showMessage("error", "❌ Erreur réseau.");
    } finally {
      setInitLoading(false);
    }
  };

  const handleAssignRole = async () => {
    if (!assignUsername.trim() || !assignRoleNom) {
      showMessage("error", "❌ Veuillez entrer un nom d'utilisateur et sélectionner un rôle.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/roles/assign/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ username: assignUsername.trim(), role_nom: assignRoleNom })
      });
      const data = await res.json();
      if (res.ok) {
        showMessage("success", "✅ " + (data.success || "Rôle assigné avec succès !"));
        setAssignUsername("");
        setAssignRoleNom("");
        fetchUsersByRole(selectedRoleFilter);
      } else {
        showMessage("error", "❌ " + (data.error || "Impossible d'assigner le rôle."));
      }
    } catch (e) {
      showMessage("error", "❌ Erreur réseau.");
    } finally {
      setLoading(false);
    }
  };

  const resetCreateForm = () => {
    setCreateUsername("");
    setCreateEmail("");
    setCreatePassword("");
    setCreateNomComplet("");
    setCreateFaculte("");
    setCreateSpecialite("");
    setCreateTelephone("");
    setCreateNiveau("");
    setCreateMatricule("");
  };

  const handleCreateAccount = async () => {
    if (!createRoleNom) {
      showMessage("error", "❌ Veuillez sélectionner un rôle à créer.");
      return;
    }

    if (!createUsername.trim() || !createEmail.trim() || !createPassword.trim() || !createNomComplet.trim()) {
      showMessage("error", "❌ Veuillez remplir tous les champs de base.");
      return;
    }

    if (createRoleNom === "secretaire_facultaire" && !createFaculte) {
      showMessage("error", "❌ La faculté est requise pour un secrétaire facultaire.");
      return;
    }

    if (createRoleNom === "professeur" && (!createSpecialite.trim() || !createFaculte)) {
      showMessage("error", "❌ Spécialité et faculté sont requises pour un professeur.");
      return;
    }

    if (createRoleNom === "etudiant" && (!createNiveau.trim() || !createFaculte)) {
      showMessage("error", "❌ Niveau et faculté sont requis pour un étudiant.");
      return;
    }

    if (createRoleNom === "admin_central") {
      showMessage("error", "❌ La création d'un administrateur central se fait via le Django admin.");
      return;
    }

    setLoading(true);
    try {
      let url = null;
      let body = {
        username: createUsername.trim(),
        email: createEmail.trim(),
        password: createPassword.trim(),
        nom_complet: createNomComplet.trim(),
      };

      if (createRoleNom === "admin_gestionnaire") {
        url = `${API_BASE_URL}/api/admin-gestionnaire/create/`;
      } else if (createRoleNom === "secretaire_facultaire") {
        url = `${API_BASE_URL}/api/secretaire/create/`;
        body.faculte = createFaculte;
      } else if (createRoleNom === "professeur") {
        url = `${API_BASE_URL}/api/professors/`;
        body = {
          username: createUsername.trim(),
          password: createPassword.trim(),
          nom: createNomComplet.trim(),
          email: createEmail.trim(),
          specialite: createSpecialite.trim(),
          faculte: createFaculte,
          telephone: createTelephone.trim(),
        };
      } else if (createRoleNom === "etudiant") {
        url = `${API_BASE_URL}/api/students/`;
        body = {
          nom: createNomComplet.trim(),
          email: createEmail.trim(),
          niveau: createNiveau.trim(),
          faculte: createFaculte,
          matricule: createMatricule.trim(),
        };
      }

      if (!url) {
        showMessage("error", "❌ Ce rôle ne peut pas être créé depuis cette interface.");
        return;
      }

      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (res.ok) {
        showMessage("success", `✅ Compte ${roleLabels[createRoleNom]} créé avec succès !`);
        resetCreateForm();
        setSelectedRoleFilter(createRoleNom);
        fetchUsersByRole(createRoleNom);
      } else {
        showMessage("error", "❌ " + (data.error || data.detail || JSON.stringify(data)));
      }
    } catch (e) {
      console.error("Erreur création compte:", e);
      showMessage("error", "❌ Erreur réseau lors de la création du compte.");
    } finally {
      setLoading(false);
    }
  };

  const roleLabels = {
    admin_central: "Administrateur Central",
    admin_gestionnaire: "Administrateur Gestionnaire",
    secretaire_facultaire: "Secrétaire Facultaire",
    professeur: "Professeur",
    etudiant: "Étudiant",
  };

  const roleColors = {
    admin_central: { bg: "rgba(239,68,68,0.12)", color: "#f87171" },
    admin_gestionnaire: { bg: "rgba(245,158,11,0.12)", color: "#fbbf24" },
    secretaire_facultaire: { bg: "rgba(16,185,129,0.12)", color: "#34d399" },
    professeur: { bg: "rgba(99,102,241,0.12)", color: "#a5b4fc" },
    etudiant: { bg: "rgba(14,165,233,0.12)", color: "#38bdf8" },
  };

  return (
    <div className="page-section">
      <div className="section-header">
        <div>
          <h2>Administration du Système ⚙️</h2>
          <p>Initialisez les rôles, assignez des rôles aux utilisateurs, et supervisez la structure de permissions.</p>
        </div>
      </div>

      {/* Message de feedback */}
      {message && (
        <div style={{
          padding: "14px 20px",
          borderRadius: "16px",
          background: message.type === "success" ? "rgba(16,185,129,0.12)" : "rgba(239,68,68,0.12)",
          border: `1px solid ${message.type === "success" ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`,
          color: message.type === "success" ? "#34d399" : "#f87171",
          fontWeight: 600,
          fontSize: "14px",
          animation: "messageSlide 0.3s ease",
        }}>
          {message.text}
        </div>
      )}

      {/* Section 1 — Initialisation des rôles */}
      <div className="card notes-card">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "20px", flexWrap: "wrap" }}>
          <div>
            <h3 style={{ margin: "0 0 6px", color: "#f8fafc", fontSize: "1.1rem" }}>🔧 Initialisation des rôles</h3>
            <p style={{ margin: 0, color: "#94a3b8", fontSize: "13px" }}>
              Crée ou met à jour les rôles standards du système (idempotent — sans danger si déjà fait).
            </p>
          </div>
          <button
            className="primary-btn"
            style={{ gridColumn: "auto", marginTop: 0 }}
            onClick={handleInitRoles}
            disabled={initLoading}
          >
            {initLoading ? "Initialisation..." : "⚡ Initialiser les rôles"}
          </button>
        </div>

        {/* Rôles disponibles */}
        {roles.length > 0 && (
          <div style={{ marginTop: "20px", display: "flex", flexWrap: "wrap", gap: "10px" }}>
            {roles.map(role => {
              const colors = roleColors[role.nom] || { bg: "rgba(255,255,255,0.06)", color: "#cbd5e1" };
              return (
                <span key={role.id} style={{
                  padding: "6px 14px",
                  borderRadius: "999px",
                  fontSize: "12px",
                  fontWeight: 700,
                  background: colors.bg,
                  color: colors.color,
                  border: `1px solid ${colors.color}30`,
                }}>
                  {roleLabels[role.nom] || role.nom}
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* Section 2 — Assigner un rôle */}
      <div className="card notes-card">
        <h3 style={{ margin: "0 0 16px", color: "#f8fafc", fontSize: "1.1rem" }}>🎭 Assigner un rôle à un utilisateur</h3>
        <div className="form-grid">
          <label className="field-label">
            Nom d'utilisateur
            <input
              placeholder="Ex: jean_dupont"
              value={assignUsername}
              onChange={e => setAssignUsername(e.target.value)}
              disabled={loading}
            />
          </label>

          <label className="field-label">
            Rôle à assigner
            <select
              value={assignRoleNom}
              onChange={e => setAssignRoleNom(e.target.value)}
              disabled={loading}
              style={{ backgroundColor: "#1e293b" }}
            >
              <option value="">-- Sélectionner un rôle --</option>
              {Object.entries(roleLabels).map(([nom, label]) => (
                <option key={nom} value={nom} style={{ backgroundColor: "#1e293b" }}>{label}</option>
              ))}
            </select>
          </label>

          <button
            className="primary-btn"
            onClick={handleAssignRole}
            disabled={loading}
          >
            {loading ? "Attribution..." : "✅ Assigner le rôle"}
          </button>
        </div>
      </div>

      {/* Section 3 — Créer un compte (rôles recommandés) */}
      <div className="card notes-card">
        <h3 style={{ margin: "0 0 16px", color: "#f8fafc", fontSize: "1.1rem" }}>➕ Créer un compte</h3>
        <p style={{ margin: "0 0 20px", color: "#94a3b8", fontSize: "13px" }}>
          Créez un compte pour un rôle recommandé. Les comptes administrateurs centraux doivent être créés via l'admin Django.
        </p>
        <div className="form-grid">
          <label className="field-label">
            Rôle à créer
            <select value={createRoleNom} onChange={e => setCreateRoleNom(e.target.value)} disabled={loading} style={{ backgroundColor: "#1e293b" }}>
              {Object.entries(roleLabels).map(([nom, label]) => (
                <option key={nom} value={nom} style={{ backgroundColor: "#1e293b" }}>{label}</option>
              ))}
            </select>
          </label>
          <label className="field-label">
            Nom d'utilisateur *
            <input placeholder="Ex: alice_etudiant" value={createUsername} onChange={e => setCreateUsername(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Adresse email *
            <input placeholder="Ex: alice@univ.edu" type="email" value={createEmail} onChange={e => setCreateEmail(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Mot de passe *
            <input placeholder="••••••••" type="password" value={createPassword} onChange={e => setCreatePassword(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Nom complet *
            <input placeholder="Ex: Alice Dupont" value={createNomComplet} onChange={e => setCreateNomComplet(e.target.value)} disabled={loading} />
          </label>
          {(createRoleNom === "secretaire_facultaire" || createRoleNom === "professeur" || createRoleNom === "etudiant") && (
            <FacultySelector token={token} value={createFaculte} onChange={e => setCreateFaculte(e.target.value)} label="Sélectionner la faculté *" />
          )}
          {createRoleNom === "professeur" && (
            <>
              <label className="field-label">
                Spécialité *
                <input placeholder="Ex: Data Science" value={createSpecialite} onChange={e => setCreateSpecialite(e.target.value)} disabled={loading} />
              </label>
              <label className="field-label">
                Téléphone
                <input placeholder="Ex: +243..." value={createTelephone} onChange={e => setCreateTelephone(e.target.value)} disabled={loading} />
              </label>
            </>
          )}
          {createRoleNom === "etudiant" && (
            <>
              <label className="field-label">
                Niveau *
                <input placeholder="Ex: L1, L2, Master 1" value={createNiveau} onChange={e => setCreateNiveau(e.target.value)} disabled={loading} />
              </label>
              <label className="field-label">
                Matricule
                <input placeholder="Ex: MAT-2026-123" value={createMatricule} onChange={e => setCreateMatricule(e.target.value)} disabled={loading} />
              </label>
            </>
          )}
          <div className="field-full" style={{ display: "flex", gap: "12px", marginTop: "10px", flexWrap: "wrap" }}>
            <button className="primary-btn" onClick={handleCreateAccount} disabled={loading}>
              {loading ? "Création en cours..." : "Créer le compte"}
            </button>
            <button className="logout-btn" onClick={resetCreateForm} style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#cbd5e1" }}>Réinitialiser</button>
          </div>
        </div>
      </div>

      {/* Section 4 — Voir les utilisateurs par rôle */}
      <div className="section-header section-header-tight">
        <h3>Utilisateurs par rôle</h3>
        <select
          value={selectedRoleFilter}
          onChange={e => setSelectedRoleFilter(e.target.value)}
          style={{
            background: "rgba(30,41,59,0.8)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "12px",
            color: "#f8fafc",
            padding: "8px 14px",
            fontSize: "13px",
            cursor: "pointer",
          }}
        >
          {Object.entries(roleLabels).map(([nom, label]) => (
            <option key={nom} value={nom} style={{ backgroundColor: "#1e293b" }}>{label}</option>
          ))}
        </select>
      </div>

      {fetchingUsers ? (
        <div className="empty-state">Chargement des utilisateurs...</div>
      ) : users.length === 0 ? (
        <div className="empty-state">Aucun utilisateur avec le rôle « {roleLabels[selectedRoleFilter] || selectedRoleFilter} ».</div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Nom complet</th>
                <th>Nom d'utilisateur</th>
                <th>Email</th>
                {selectedRoleFilter === "secretaire_facultaire" && <th>Faculté</th>}
                <th>État</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => {
                return (
                  <tr key={u.user__id}>
                    <td style={{ fontWeight: 600 }}>{u.nom_complet || u.user__username}</td>
                    <td>{u.user__username}</td>
                    <td>{u.user__email || "—"}</td>
                    {selectedRoleFilter === "secretaire_facultaire" && (
                      <td>
                        <span style={{
                          padding: "4px 10px", borderRadius: "12px",
                          fontSize: "11px", fontWeight: 700,
                          background: "rgba(99,102,241,0.15)", color: "#a5b4fc"
                        }}>
                          {u.faculte || "Non spécifiée"}
                        </span>
                      </td>
                    )}
                    <td>
                      <span style={{
                        padding: "4px 10px", borderRadius: "12px",
                        fontSize: "11px", fontWeight: 700,
                        background: u.est_actif ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.15)",
                        color: u.est_actif ? "#10b981" : "#f87171"
                      }}>
                        {u.est_actif ? "Actif" : "Inactif"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ManageRoles;
