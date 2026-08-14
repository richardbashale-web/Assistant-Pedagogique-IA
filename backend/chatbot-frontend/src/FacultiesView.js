import { useState, useEffect, useCallback } from "react";
import { useToast } from "./Toast";

function FacultiesView({ token }) {
  const [faculties, setFaculties] = useState([]);
  const [selectedFaculty, setSelectedFaculty] = useState(null);
  const [professors, setProfessors] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [activeTab, setActiveTab] = useState("professors");

  // Mode édition
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);

  const { toastContainer, showToast } = useToast();

  const facultyIcons = {
    droit: "⚖️", sciences_economiques: "📈", sciences_informatique_ia: "🤖",
    sciences_info_comm: "📡", theologie: "✝️", medecine: "🏥", istm: "🔬",
  };

  const fetchFaculties = useCallback(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/faculties/", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) setFaculties(await res.json());
    } catch (error) { console.error("Erreur:", error); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => {
    if (token) fetchFaculties();
  }, [token, fetchFaculties]);

  const handleSelectFaculty = async (faculty) => {
    setSelectedFaculty(faculty);
    setIsEditing(false);
    setEditData({
      nom: faculty.nom, description: faculty.description,
      doyen: faculty.doyen, email: faculty.email, telephone: faculty.telephone
    });
    setLoadingDetails(true);
    setProfessors([]); setStudents([]); setActiveTab("professors");

    try {
      const [profsRes, studentsRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/api/faculties/${faculty.code}/professors/`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`http://127.0.0.1:8000/api/faculties/${faculty.code}/students/`, { headers: { "Authorization": `Bearer ${token}` } })
      ]);
      if (profsRes.ok) setProfessors((await profsRes.json()).professeurs || []);
      if (studentsRes.ok) setStudents((await studentsRes.json()).etudiants || []);
    } catch (error) { console.error("Erreur:", error); }
    finally { setLoadingDetails(false); }
  };

  const handleSaveFaculty = async () => {
    setSaving(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/faculties/${selectedFaculty.code}/update/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(editData)
      });
      if (res.ok) {
        const updated = await res.json();
        setSelectedFaculty(updated);
        setFaculties(prev => prev.map(f => f.code === updated.code ? updated : f));
        setIsEditing(false);
        showToast("Informations de la faculté mises à jour.", "success");
      } else {
        showToast("Erreur lors de la mise à jour (permission refusée ?).", "error");
      }
    } catch (error) { showToast("Erreur réseau.", "error"); }
    finally { setSaving(false); }
  };

  if (loading) return <div className="page-section"><div className="empty-state">Chargement des facultés...</div></div>;

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header">
        <div>
          <h2>Gestion des Facultés 🏫</h2>
          <p>Explorez les facultés, modifiez leurs informations, consultez les professeurs et étudiants affiliés.</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px", alignItems: "start" }}>
        <div className="card" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <h3 style={{ margin: "0 0 12px", fontSize: "14px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Facultés disponibles
          </h3>
          {faculties.map(faculty => (
            <button key={faculty.code} onClick={() => handleSelectFaculty(faculty)}
              style={{
                display: "flex", alignItems: "center", gap: "12px", padding: "14px 16px", borderRadius: "16px",
                border: selectedFaculty?.code === faculty.code ? "1px solid rgba(99,102,241,0.45)" : "1px solid rgba(255,255,255,0.06)",
                background: selectedFaculty?.code === faculty.code ? "rgba(99,102,241,0.16)" : "rgba(255,255,255,0.03)",
                color: selectedFaculty?.code === faculty.code ? "#e0e7ff" : "#cbd5e1",
                cursor: "pointer", textAlign: "left", fontSize: "13px",
                fontWeight: selectedFaculty?.code === faculty.code ? 700 : 500, transition: "all 0.2s ease", width: "100%"
              }}>
              <span style={{ fontSize: "20px", flexShrink: 0 }}>{facultyIcons[faculty.code] || "🏫"}</span>
              <span style={{ lineHeight: 1.4 }}>{faculty.nom}</span>
            </button>
          ))}
        </div>

        {selectedFaculty ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div className="card" style={{ padding: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                  <span style={{ fontSize: "40px" }}>{facultyIcons[selectedFaculty.code] || "🏫"}</span>
                  <div>
                    {isEditing ? (
                      <input value={editData.nom || ""} onChange={e => setEditData({...editData, nom: e.target.value})}
                             style={{ background: "rgba(30,41,59,0.8)", border: "1px solid rgba(99,102,241,0.5)", borderRadius: "8px", color: "#f8fafc", padding: "4px 8px", fontSize: "1.2rem", fontWeight: "bold", width: "100%" }} />
                    ) : (
                      <h3 style={{ margin: 0, fontSize: "1.3rem", color: "#f8fafc" }}>{selectedFaculty.nom}</h3>
                    )}
                    <span style={{ display: "inline-block", marginTop: "4px", padding: "3px 12px", borderRadius: "999px", fontSize: "11px", fontWeight: 700, background: "rgba(99,102,241,0.15)", color: "#a5b4fc", border: "1px solid rgba(99,102,241,0.25)" }}>
                      {selectedFaculty.code}
                    </span>
                  </div>
                </div>
                <button onClick={() => isEditing ? handleSaveFaculty() : setIsEditing(true)} disabled={saving}
                  style={{ background: isEditing ? "rgba(16,185,129,0.15)" : "rgba(255,255,255,0.05)", border: `1px solid ${isEditing ? "rgba(16,185,129,0.4)" : "rgba(255,255,255,0.1)"}`, borderRadius: "8px", padding: "6px 12px", color: isEditing ? "#34d399" : "#cbd5e1", cursor: "pointer", fontWeight: 600 }}>
                  {saving ? "..." : isEditing ? "✅ Enregistrer" : "✏️ Modifier"}
                </button>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px" }}>
                <div style={{ gridColumn: "1 / -1", display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Description</span>
                  {isEditing ? (
                    <textarea value={editData.description || ""} onChange={e => setEditData({...editData, description: e.target.value})} rows={3}
                              style={{ background: "rgba(30,41,59,0.8)", border: "1px solid rgba(99,102,241,0.5)", borderRadius: "8px", color: "#f8fafc", padding: "8px", fontSize: "13px", width: "100%" }} />
                  ) : (
                    <div style={{ color: "#94a3b8", fontSize: "13px", lineHeight: 1.6 }}>{selectedFaculty.description || "Aucune description"}</div>
                  )}
                </div>
                
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Doyen</span>
                  {isEditing ? <input value={editData.doyen || ""} onChange={e => setEditData({...editData, doyen: e.target.value})} style={{ background: "rgba(30,41,59,0.8)", border: "1px solid rgba(99,102,241,0.5)", borderRadius: "8px", color: "#f8fafc", padding: "4px 8px", fontSize: "13px" }} /> : <span style={{ color: "#e2e8f0", fontSize: "13px" }}>{selectedFaculty.doyen || "—"}</span>}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Email</span>
                  {isEditing ? <input value={editData.email || ""} onChange={e => setEditData({...editData, email: e.target.value})} style={{ background: "rgba(30,41,59,0.8)", border: "1px solid rgba(99,102,241,0.5)", borderRadius: "8px", color: "#f8fafc", padding: "4px 8px", fontSize: "13px" }} /> : <span style={{ color: "#e2e8f0", fontSize: "13px" }}>{selectedFaculty.email || "—"}</span>}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Téléphone</span>
                  {isEditing ? <input value={editData.telephone || ""} onChange={e => setEditData({...editData, telephone: e.target.value})} style={{ background: "rgba(30,41,59,0.8)", border: "1px solid rgba(99,102,241,0.5)", borderRadius: "8px", color: "#f8fafc", padding: "4px 8px", fontSize: "13px" }} /> : <span style={{ color: "#e2e8f0", fontSize: "13px" }}>{selectedFaculty.telephone || "—"}</span>}
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              {[
                { label: "Professeurs", count: professors.length, icon: "👨‍🏫", color: "#6366f1" },
                { label: "Étudiants", count: students.length, icon: "🎓", color: "#10b981" },
              ].map(stat => (
                <div key={stat.label} className="card" style={{ padding: "20px", display: "flex", alignItems: "center", gap: "16px" }}>
                  <span style={{ fontSize: "28px", width: "52px", height: "52px", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "16px", background: `${stat.color}20` }}>{stat.icon}</span>
                  <div>
                    <div style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", lineHeight: 1 }}>{loadingDetails ? "..." : stat.count}</div>
                    <div style={{ fontSize: "13px", color: "#94a3b8", marginTop: "4px" }}>{stat.label}</div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", gap: "8px" }}>
              {["professors", "students"].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)} className={`nav-btn ${activeTab === tab ? "active" : ""}`}>
                  {tab === "professors" ? `👨‍🏫 Professeurs (${professors.length})` : `🎓 Étudiants (${students.length})`}
                </button>
              ))}
            </div>

            {loadingDetails ? (
              <div className="empty-state">Chargement des données...</div>
            ) : activeTab === "professors" ? (
              professors.length === 0 ? <div className="empty-state">Aucun professeur affilié.</div> : (
                <div className="progress-table-wrapper"><table className="progress-table">
                  <thead><tr><th>Nom</th><th>Spécialité</th><th>Email</th><th>Téléphone</th></tr></thead>
                  <tbody>{professors.map(prof => <tr key={prof.id}><td style={{ fontWeight: 600 }}>👨‍🏫 {prof.nom}</td><td><span style={{ padding: "4px 10px", borderRadius: "12px", fontSize: "11px", fontWeight: 700, background: "rgba(99,102,241,0.15)", color: "#a5b4fc" }}>{prof.specialite}</span></td><td style={{ color: "#94a3b8" }}>{prof.email || "—"}</td><td style={{ color: "#94a3b8" }}>{prof.telephone || "—"}</td></tr>)}</tbody>
                </table></div>
              )
            ) : (
              students.length === 0 ? <div className="empty-state">Aucun étudiant affilié.</div> : (
                <div className="progress-table-wrapper"><table className="progress-table">
                  <thead><tr><th>Nom</th><th>Matricule</th><th>Niveau</th><th>Email</th></tr></thead>
                  <tbody>{students.map(student => <tr key={student.id}><td style={{ fontWeight: 600 }}>🎓 {student.nom}</td><td style={{ color: "#94a3b8", fontFamily: "monospace" }}>{student.matricule || "—"}</td><td><span style={{ padding: "4px 10px", borderRadius: "12px", fontSize: "11px", fontWeight: 700, background: "rgba(16,185,129,0.15)", color: "#34d399" }}>{student.niveau}</span></td><td style={{ color: "#94a3b8" }}>{student.email || "—"}</td></tr>)}</tbody>
                </table></div>
              )
            )}
          </div>
        ) : (
          <div className="card" style={{ padding: "48px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "12px" }}>
            <span style={{ fontSize: "48px", opacity: 0.4 }}>🏫</span>
            <p style={{ color: "#64748b", textAlign: "center", fontSize: "15px", margin: 0 }}>Sélectionnez une faculté pour voir et modifier ses informations.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default FacultiesView;
