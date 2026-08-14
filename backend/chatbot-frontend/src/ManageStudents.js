import { useState, useEffect, useCallback } from "react";
import FacultySelector from "./FacultySelector";
import { useToast } from "./Toast";

function ManageStudents({ token }) {
  const [students, setStudents] = useState([]);
  const [nom, setNom] = useState("");
  const [email, setEmail] = useState("");
  const [niveau, setNiveau] = useState("");
  const [faculte, setFaculte] = useState("");
  const [matricule, setMatricule] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [search, setSearch] = useState("");
  const { toastContainer, showToast } = useToast();

  const API_URL = "http://127.0.0.1:8000/api/students/";

  const fetchStudents = useCallback(async () => {
    try {
      const res = await fetch(API_URL, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) setStudents(await res.json());
    } catch (e) {
      console.error("Erreur lors de la récupération des étudiants:", e);
    } finally {
      setFetching(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) fetchStudents();
  }, [token, fetchStudents]);

  const resetForm = () => {
    setNom(""); setEmail(""); setNiveau(""); setFaculte(""); setMatricule(""); setEditingId(null);
  };

  const handleSubmit = async () => {
    if (!faculte) { showToast("Veuillez sélectionner une faculté.", "error"); return; }
    if (!nom || !email || !niveau) { showToast("Nom, email et niveau sont obligatoires.", "error"); return; }
    setLoading(true);
    const method = editingId ? "PUT" : "POST";
    const url = editingId ? `${API_URL}${editingId}/` : API_URL;
    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ nom, email, niveau, faculte, matricule })
      });
      if (res.ok) {
        showToast(editingId ? "Étudiant modifié avec succès !" : "Étudiant ajouté avec succès !", "success");
        resetForm();
        fetchStudents();
      } else {
        const error = await res.json();
        showToast(`Erreur : ${error.detail || "Opération impossible."}`, "error");
      }
    } catch { showToast("Erreur réseau.", "error"); }
    finally { setLoading(false); }
  };

  const editStudent = (s) => {
    setNom(s.nom); setEmail(s.email); setNiveau(s.niveau);
    setFaculte(s.faculte); setMatricule(s.matricule || "");
    setEditingId(s.id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteStudent = async (id) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer cet étudiant ?")) return;
    try {
      const res = await fetch(`${API_URL}${id}/`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) { showToast("Étudiant supprimé.", "success"); fetchStudents(); }
      else showToast("Erreur lors de la suppression.", "error");
    } catch { showToast("Erreur réseau.", "error"); }
  };

  const filtered = students.filter(s =>
    `${s.nom} ${s.email} ${s.matricule} ${s.niveau}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>Gestion des Étudiants 🎓</h2>
          <p>{editingId ? "Modifiez les informations de l'étudiant sélectionné." : "Enregistrez et gérez les comptes des étudiants de votre faculté."}</p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Nom complet *
            <input placeholder="Ex: Alice Smith" value={nom} onChange={e => setNom(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Adresse email *
            <input placeholder="Ex: alice@student.univ.edu" type="email" value={email} onChange={e => setEmail(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Niveau d'études *
            <input placeholder="Ex: L1, L2, Master 1..." value={niveau} onChange={e => setNiveau(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Numéro de Matricule
            <input
              placeholder={editingId ? "Ex: ETU-2026-1234" : "Généré automatiquement (ETU-2026-XXXX)"}
              value={matricule}
              onChange={e => setMatricule(e.target.value)}
              disabled={loading || !editingId}
              style={!editingId ? { opacity: 0.55, cursor: 'not-allowed', fontStyle: 'italic' } : {}}
              title={!editingId ? "Le matricule sera généré automatiquement lors de la création" : "Modifier le matricule"}
            />
          </label>

          <FacultySelector token={token} value={faculte} onChange={e => setFaculte(e.target.value)} label="Sélectionner la faculté *" />
          <div className="field-full" style={{ display: "flex", gap: "12px", marginTop: "10px" }}>
            <button className="primary-btn" onClick={handleSubmit} disabled={loading}>
              {loading ? "Traitement..." : editingId ? "Enregistrer les modifications" : "Ajouter l'étudiant"}
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
        <h3>Étudiants existants ({filtered.length})</h3>
        <input
          placeholder="🔍 Rechercher par nom, email, matricule..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ background: "rgba(30,41,59,0.8)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: "12px", color: "#f8fafc", padding: "8px 14px", fontSize: "13px", outline: "none", width: "260px" }}
        />
      </div>

      {fetching ? (
        <div className="empty-state">Chargement des étudiants...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">{search ? "Aucun résultat pour votre recherche." : "Aucun étudiant enregistré pour le moment."}</div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Nom complet</th><th>Matricule</th><th>Niveau</th><th>Email</th><th>Faculté</th><th style={{ textAlign: "center" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(s => (
                <tr key={s.id} style={editingId === s.id ? { background: "rgba(99,102,241,0.08)" } : {}}>
                  <td style={{ fontWeight: 600 }}>{s.nom}</td>
                  <td>{s.matricule || "-"}</td>
                  <td>{s.niveau}</td>
                  <td>{s.email}</td>
                  <td>
                    <span style={{ padding: "4px 10px", borderRadius: "12px", fontSize: "11px", fontWeight: 700, background: "rgba(99,102,241,0.15)", color: "#a5b4fc" }}>
                      {s.faculte}
                    </span>
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <button onClick={() => editStudent(s)}
                      style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.25)", borderRadius: "8px", padding: "6px 10px", marginRight: "8px", cursor: "pointer", color: "#a5b4fc" }}
                      title="Modifier l'étudiant">✏️ Modifier</button>
                    <button onClick={() => deleteStudent(s.id)}
                      style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: "8px", padding: "6px 10px", cursor: "pointer", color: "#f87171" }}
                      title="Supprimer l'étudiant">🗑️</button>
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

export default ManageStudents;
