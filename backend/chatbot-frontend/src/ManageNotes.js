import { useState, useEffect, useCallback } from "react";
import { useToast } from "./Toast";

function ManageNotes({ token }) {
  const [courses, setCourses] = useState([]);
  const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
  const API_COURSES = `${API_BASE_URL}/api/courses/`;
  const API_COURSE_NOTES = `${API_BASE_URL}/api/course-notes/`;
  const [notes, setNotes] = useState([]);
  const [courseId, setCourseId] = useState("");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const { toastContainer, showToast } = useToast();

  const fetchCourses = useCallback(async () => {
    const res = await fetch(API_COURSES, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (res.ok) setCourses(await res.json());
  }, [API_COURSES, token]);

  const fetchNotes = useCallback(async () => {
    const res = await fetch(
      `${API_COURSE_NOTES}${courseId ? `?course_id=${courseId}` : ""}`,
      { headers: { "Authorization": `Bearer ${token}` } }
    );
    if (res.ok) setNotes(await res.json());
  }, [API_COURSE_NOTES, courseId, token]);

  useEffect(() => { fetchCourses(); }, [fetchCourses]);
  useEffect(() => { fetchNotes(); }, [fetchNotes]);

  const resetForm = () => {
    setTitle(""); setContent(""); setAttachment(null); setEditingId(null);
  };

  const handleSubmit = async () => {
    if (!courseId || !title.trim() || (!content.trim() && !attachment && !editingId)) {
      showToast("Veuillez remplir le cours, le titre et le contenu (ou joindre un PDF).", "error");
      return;
    }
    setLoading(true);
    try {
      if (editingId) {
        // PUT pour modifier
        const res = await fetch(`${API_COURSE_NOTES}${editingId}/`, {
          method: "PUT",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
          body: JSON.stringify({ course: courseId, title, content })
        });
        if (res.ok) {
          showToast("Note modifiée avec succès !", "success");
          resetForm();
          fetchNotes();
        } else {
          showToast("Erreur lors de la modification.", "error");
        }
      } else {
        // POST pour créer
        const formData = new FormData();
        formData.append("course", courseId);
        formData.append("title", title);
        formData.append("content", content);
        if (attachment) formData.append("attachment", attachment);
        const res = await fetch(API_COURSE_NOTES, {
          method: "POST",
          headers: { "Authorization": `Bearer ${token}` },
          body: formData
        });
        if (res.ok) {
          showToast("Note ajoutée avec succès !", "success");
          resetForm();
          fetchNotes();
        } else {
          showToast("Erreur : impossible d'ajouter la note.", "error");
        }
      }
    } catch { showToast("Erreur réseau.", "error"); }
    finally { setLoading(false); }
  };

  const editNote = (note) => {
    setEditingId(note.id);
    setCourseId(note.course);
    setTitle(note.title);
    setContent(note.content || "");
    setAttachment(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteNote = async (id) => {
    if (!window.confirm("Supprimer cette note de cours ?")) return;
    try {
      const res = await fetch(`${API_COURSE_NOTES}${id}/`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) { showToast("Note supprimée.", "success"); fetchNotes(); }
      else showToast("Erreur lors de la suppression.", "error");
    } catch { showToast("Erreur réseau.", "error"); }
  };

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>Ajout de notes de cours 📝</h2>
          <p>{editingId ? "Modifiez le contenu de la note sélectionnée." : "Publie des ressources de cours que tes étudiants peuvent consulter directement."}</p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Cours
            <select value={courseId} onChange={e => setCourseId(e.target.value)} style={{ backgroundColor: "#1e293b" }}>
              <option value="">Sélectionner un cours</option>
              {courses.map(course => (
                <option key={course.id} value={course.id}>{course.titre}</option>
              ))}
            </select>
          </label>

          <label className="field-label">
            Titre de la note
            <input type="text" placeholder="Titre de la note" value={title} onChange={e => setTitle(e.target.value)} />
          </label>

          <label className="field-label field-full">
            Contenu de la note
            <textarea placeholder="Contenu de la note (optionnel si PDF)" value={content} onChange={e => setContent(e.target.value)} rows={6} />
          </label>

          {!editingId && (
            <label className="field-label field-full file-input-label">
              <span>📎 Joindre un fichier de note</span>
              <input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,image/*" onChange={e => setAttachment(e.target.files[0])} />
            </label>
          )}

          {attachment && (
            <div className="file-chip">
              {attachment.name}
              <button type="button" className="file-chip-close" onClick={() => setAttachment(null)}>✕</button>
            </div>
          )}

          <div className="field-full" style={{ display: "flex", gap: "12px", marginTop: "10px" }}>
            <button className="primary-btn" onClick={handleSubmit} disabled={loading}>
              {loading ? "Traitement..." : editingId ? "Enregistrer les modifications" : "Enregistrer la note"}
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
        <h3>Notes existantes</h3>
      </div>

      {notes.length === 0 ? (
        <div className="empty-state">Aucune note trouvée pour ce cours.</div>
      ) : (
        <div className="notes-list">
          {notes.map(note => (
            <div key={note.id} className="note-card" style={editingId === note.id ? { border: "1px solid rgba(99,102,241,0.4)", background: "rgba(99,102,241,0.06)" } : {}}>
              <div className="note-card-header">
                <strong>{note.title}</strong>
                <span className="note-meta">Cours: {note.course_title}</span>
              </div>
              <div className="note-submeta">Par: {note.professor_name || "Enseignant"}</div>
              {note.content && <p className="note-content">{note.content}</p>}
              {note.attachment_url && (
                <a href={note.attachment_url} target="_blank" rel="noreferrer" className="attachment-link">
                  📄 Télécharger la pièce jointe
                </a>
              )}
              <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
                <button onClick={() => editNote(note)}
                  style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.25)", borderRadius: "8px", padding: "6px 12px", cursor: "pointer", color: "#a5b4fc", fontSize: "13px", fontWeight: 600 }}>
                  ✏️ Modifier
                </button>
                <button onClick={() => deleteNote(note.id)}
                  style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: "8px", padding: "6px 12px", cursor: "pointer", color: "#f87171", fontSize: "13px", fontWeight: 600 }}>
                  🗑️ Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ManageNotes;
