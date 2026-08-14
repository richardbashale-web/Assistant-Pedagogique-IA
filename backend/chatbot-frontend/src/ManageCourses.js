import { useState, useEffect, useCallback } from "react";
import { useToast } from "./Toast";

function ManageCourses({ token }) {
  const [titre, setTitre] = useState("");
  const [description, setDescription] = useState("");
  const [professeurId, setProfesseurId] = useState("");
  const [promotions, setPromotions] = useState([]);
  const [list, setList] = useState([]);
  const [professors, setProfessors] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [search, setSearch] = useState("");
  const { toastContainer, showToast } = useToast();

  const PROMOTION_OPTIONS = ["L1", "L2", "L3", "M1", "M2"];

  const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
  const API_COURSES = `${API_BASE_URL}/api/courses/`;
  const API_PROFESSORS = `${API_BASE_URL}/api/professors/`;

  const fetchCourses = useCallback(async () => {
    try {
      const res = await fetch(API_COURSES, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) setList(await res.json());
    } catch (e) {
      console.error("Erreur lors du chargement des cours:", e);
    } finally {
      setFetching(false);
    }
  }, [token, API_COURSES]);

  const fetchProfessors = useCallback(async () => {
    try {
      // Pour permettre à un professeur d'avoir un cours dans n'importe quelle faculté,
      // on récupère tous les professeurs disponibles.
      const res = await fetch(API_PROFESSORS, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) setProfessors(await res.json());
    } catch (e) {
      console.error("Erreur professeurs:", e);
    }
  }, [token, API_PROFESSORS]);

  useEffect(() => {
    if (token) {
      fetchCourses();
      fetchProfessors();
    }
  }, [token, fetchCourses, fetchProfessors]);

  const resetForm = () => {
    setTitre(""); setDescription(""); setProfesseurId(""); setPromotions([]);
    setEditingId(null);
  };

  const handlePromotionToggle = (promo) => {
    setPromotions(prev => 
      prev.includes(promo) ? prev.filter(p => p !== promo) : [...prev, promo]
    );
  };

  const handleSubmit = async () => {
    if (!titre || !description || !professeurId || promotions.length === 0) { 
      showToast("Titre, description, professeur et au moins une promotion sont obligatoires.", "error"); 
      return; 
    }
    setLoading(true);
    const method = editingId ? "PUT" : "POST";
    const url = editingId ? `${API_COURSES}${editingId}/` : API_COURSES;
    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ 
          titre, 
          description, 
          professeur: professeurId,
          promotions 
        })
      });
      if (res.ok) {
        showToast(editingId ? "Cours modifié avec succès !" : "Cours créé avec succès !", "success");
        resetForm();
        fetchCourses();
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

  const editCourse = (c) => {
    setTitre(c.titre); 
    setDescription(c.description); 
    setProfesseurId(c.professeur);
    setPromotions(c.promotions || []);
    setEditingId(c.id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteCourse = async (id) => {
    if (!window.confirm("Supprimer ce cours ? (Toutes les notes de cours associées seront également supprimées)")) return;
    try {
      const res = await fetch(`${API_COURSES}${id}/`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) { 
        showToast("Cours supprimé.", "success"); 
        fetchCourses(); 
      }
      else showToast("Erreur lors de la suppression.", "error");
    } catch { showToast("Erreur réseau.", "error"); }
  };

  const filtered = list.filter(c =>
    `${c.titre} ${c.description} ${c.professeur_nom} ${(c.promotions || []).join(" ")}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>Gestion des Cours 📚</h2>
          <p>{editingId ? "Modifiez les informations du cours sélectionné." : "Créez de nouveaux cours et associez-les à des professeurs."}</p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Titre du cours *
            <input placeholder="Ex: Introduction à l'Intelligence Artificielle" value={titre} onChange={e => setTitre(e.target.value)} disabled={loading} />
          </label>
          <label className="field-label">
            Professeur *
            <select value={professeurId} onChange={e => setProfesseurId(e.target.value)} disabled={loading} style={{ backgroundColor: "#1e293b", padding: "10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.1)", color: "#f8fafc" }}>
              <option value="">-- Sélectionner un professeur --</option>
              {professors.map(p => (
                <option key={p.id} value={p.id}>{p.nom} ({p.faculte})</option>
              ))}
            </select>
          </label>
          <label className="field-label field-full">
            Promotions ciblées
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginTop: "8px" }}>
              {PROMOTION_OPTIONS.map(promo => (
                <label key={promo} style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer", background: promotions.includes(promo) ? "rgba(99,102,241,0.2)" : "rgba(30,41,59,0.8)", padding: "6px 12px", borderRadius: "20px", border: `1px solid ${promotions.includes(promo) ? "#818cf8" : "rgba(255,255,255,0.1)"}`, fontSize: "13px" }}>
                  <input type="checkbox" checked={promotions.includes(promo)} onChange={() => handlePromotionToggle(promo)} disabled={loading} style={{ margin: 0 }} />
                  {promo}
                </label>
              ))}
            </div>
          </label>
          <label className="field-label field-full">
            Description *
            <textarea placeholder="Description du cours..." value={description} onChange={e => setDescription(e.target.value)} disabled={loading} rows={3} />
          </label>
          
          <div className="field-full" style={{ display: "flex", gap: "12px", marginTop: "10px" }}>
            <button className="primary-btn" onClick={handleSubmit} disabled={loading}>
              {loading ? "Traitement..." : editingId ? "Enregistrer les modifications" : "Créer le cours"}
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
        <h3>Cours existants</h3>
        <input
          placeholder="🔍 Rechercher..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ background: "rgba(30,41,59,0.8)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: "12px", color: "#f8fafc", padding: "8px 14px", fontSize: "13px", outline: "none", width: "220px" }}
        />
      </div>

      {fetching ? (
        <div className="empty-state">Chargement des cours...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">{search ? "Aucun résultat pour votre recherche." : "Aucun cours enregistré pour le moment."}</div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Titre</th><th>Professeur</th><th>Faculté</th><th>Promotions</th><th style={{ textAlign: "center" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} style={editingId === c.id ? { background: "rgba(99,102,241,0.08)" } : {}}>
                  <td style={{ fontWeight: 600 }}>{c.titre}</td>
                  <td>{c.professeur_nom}</td>
                  <td>
                    <span style={{ padding: "4px 10px", borderRadius: "12px", fontSize: "11px", fontWeight: 700, background: "rgba(99,102,241,0.15)", color: "#a5b4fc" }}>
                      {c.faculte_nom || "-"}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                      {(c.promotions || []).length > 0 ? c.promotions.map(p => (
                        <span key={p} style={{ padding: "2px 6px", borderRadius: "6px", fontSize: "10px", fontWeight: 600, background: "rgba(255,255,255,0.1)", color: "#cbd5e1" }}>
                          {p}
                        </span>
                      )) : <span style={{ color: "#64748b", fontSize: "11px" }}>-</span>}
                    </div>
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <button onClick={() => editCourse(c)}
                      style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.25)", borderRadius: "8px", padding: "6px 10px", marginRight: "8px", cursor: "pointer", color: "#a5b4fc" }}
                      title="Modifier">✏️ Modifier</button>
                    <button onClick={() => deleteCourse(c.id)}
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

export default ManageCourses;
