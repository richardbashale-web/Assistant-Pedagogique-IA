import { useState, useEffect, useCallback } from "react";
import FacultySelector from "./FacultySelector";
import { useToast } from "./Toast";

function ManageProfessors({ token }) {
  const [nom, setNom] = useState("");
  const [email, setEmail] = useState("");
  const [specialite, setSpecialite] = useState("");
  const [faculte, setFaculte] = useState("");
  const [telephone, setTelephone] = useState("");
  const [list, setList] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [search, setSearch] = useState("");
  const { toastContainer, showToast } = useToast();

  const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
  const API_URL = `${API_BASE_URL}/api/professors/`;

  const fetchProfessors = useCallback(async () => {
    try {
      const res = await fetch(API_URL, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) setList(await res.json());
    } catch (e) {
      console.error("Erreur lors du chargement des professeurs:", e);
    } finally {
      setFetching(false);
    }
  }, [token, API_URL]);

  useEffect(() => {
    if (token) fetchProfessors();
  }, [token, fetchProfessors]);

  const resetForm = () => {
    setNom(""); setEmail(""); setSpecialite(""); setFaculte(""); setTelephone("");
    setEditingId(null);
  };

  const handleSubmit = async () => {
    if (!faculte) { showToast("Veuillez sélectionner une faculté.", "error"); return; }
    if (!nom || !email || !specialite) { showToast("Nom, email et spécialité sont obligatoires.", "error"); return; }
    setLoading(true);
    const method = editingId ? "PUT" : "POST";
    const url = editingId ? `${API_URL}${editingId}/` : API_URL;
    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ nom, email, specialite, faculte, telephone })
      });
      if (res.ok) {
        showToast(editingId ? "Professeur modifié avec succès !" : "Professeur ajouté avec succès !", "success");
        resetForm();
        fetchProfessors();
      } else {
        const err = await res.json();
        const msg = err.error || err.detail || (typeof err === 'object' ? Object.values(err).flat().join(' ') : "Opération impossible.");
        showToast(`Erreur : ${msg}`, "error");
      }
    } catch {
      showToast("Erreur réseau.", "error");
    } finally {
      setLoading(false);
    }
  };

  const editProfessor = (p) => {
    setNom(p.nom); setEmail(p.email); setSpecialite(p.specialite);
    setFaculte(p.faculte); setTelephone(p.telephone || "");
    setEditingId(p.id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteProfessor = async (id) => {
    if (!window.confirm("Supprimer ce professeur ?")) return;
    try {
      const res = await fetch(`${API_URL}${id}/`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) { showToast("Professeur supprimé.", "success"); fetchProfessors(); }
      else showToast("Erreur lors de la suppression.", "error");
    } catch { showToast("Erreur réseau.", "error"); }
  };

  const filtered = list.filter(p =>
    `${p.nom} ${p.specialite} ${p.email}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>Gestion des Professeurs 👨‍🏫</h2>
          <p>{editingId ? "Modifiez les informations du professeur sélectionné." : "Enregistrez et gérez les comptes des professeurs de votre faculté."}</p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Nom complet *
            <input placeholder="Ex: Pr. Jean Dupont" value={nom} onChange={e => setNom(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Adresse email *
            <input placeholder="Ex: j.dupont@univ.edu" type="email" value={email} onChange={e => setEmail(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Spécialité *
            <input placeholder="Ex: Intelligence Artificielle" value={specialite} onChange={e => setSpecialite(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Téléphone
            <input placeholder="Ex: +243..." value={telephone} onChange={e => setTelephone(e.target.value)} disabled={loading} />
          </label>
          <FacultySelector token={token} value={faculte} onChange={e => setFaculte(e.target.value)} label="Sélectionner la faculté *" />
          <div className="field-full" style={{ display: "flex", gap: "12px", marginTop: "10px" }}>
            <button className="primary-btn" onClick={handleSubmit} disabled={loading}>
              {loading ? "Traitement..." : editingId ? "Enregistrer les modifications" : "Ajouter le professeur"}
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
        <h3>Professeurs existants</h3>
        <input
          placeholder="🔍 Rechercher..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ background: "rgba(30,41,59,0.8)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: "12px", color: "#f8fafc", padding: "8px 14px", fontSize: "13px", outline: "none", width: "220px" }}
        />
      </div>

      {fetching ? (
        <div className="empty-state">Chargement des professeurs...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">{search ? "Aucun résultat pour votre recherche." : "Aucun professeur enregistré pour le moment."}</div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Nom complet</th><th>Spécialité</th><th>Email</th><th>Téléphone</th><th>Faculté</th><th style={{ textAlign: "center" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(p => (
                <tr key={p.id} style={editingId === p.id ? { background: "rgba(99,102,241,0.08)" } : {}}>
                  <td style={{ fontWeight: 600 }}>{p.nom}</td>
                  <td>{p.specialite}</td>
                  <td>{p.email}</td>
                  <td>{p.telephone || "-"}</td>
                  <td>
                    <span style={{ padding: "4px 10px", borderRadius: "12px", fontSize: "11px", fontWeight: 700, background: "rgba(99,102,241,0.15)", color: "#a5b4fc" }}>
                      {p.faculte}
                    </span>
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <button onClick={() => editProfessor(p)}
                      style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.25)", borderRadius: "8px", padding: "6px 10px", marginRight: "8px", cursor: "pointer", color: "#a5b4fc" }}
                      title="Modifier">✏️ Modifier</button>
                    <button onClick={() => deleteProfessor(p.id)}
                      style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: "8px", padding: "6px 10px", cursor: "pointer", color: "#f87171" }}
                      title="Supprimer">🗑️</button>
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

export default ManageProfessors;
