import { useState, useEffect, useCallback } from "react";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

function StudentProgress({ token }) {
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchProgress = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/progress/students/`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        setProgress(await res.json());
      }
    } catch (e) {
      console.error("Erreur suivi:", e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) fetchProgress();
  }, [token, fetchProgress]);

  return (
    <div className="page-section">
      <div className="section-header">
        <div>
          <h2>Suivi des étudiants 📊</h2>
          <p>Consultez rapidement l'activité des étudiants de votre périmètre et repérez ceux qui ont besoin d'attention.</p>
        </div>
      </div>

      {loading ? (
        <div className="empty-state">Chargement du suivi...</div>
      ) : progress.length === 0 ? (
        <div className="empty-state">Aucun suivi disponible pour le moment.</div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Étudiant</th>
                <th>Matricule</th>
                <th>Niveau</th>
                <th>Faculté</th>
                <th>Conversations</th>
                <th>Dernière conversation</th>
                <th>Dernier message</th>
              </tr>
            </thead>
            <tbody>
              {progress.map(student => (
                <tr key={student.student_id}>
                  <td style={{ fontWeight: 600 }}>{student.nom}</td>
                  <td>
                    <span style={{ padding: "3px 8px", borderRadius: "8px", fontSize: "11px", fontWeight: 700, background: "rgba(99,102,241,0.15)", color: "#a5b4fc" }}>
                      {student.matricule}
                    </span>
                  </td>
                  <td>{student.niveau}</td>
                  <td>
                    <span style={{ padding: "3px 8px", borderRadius: "8px", fontSize: "11px", fontWeight: 700, background: "rgba(16,185,129,0.12)", color: "#6ee7b7" }}>
                      {student.faculte}
                    </span>
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <span style={{ padding: "4px 10px", borderRadius: "999px", fontSize: "12px", fontWeight: 700, background: student.conversations_count > 0 ? "rgba(99,102,241,0.15)" : "rgba(255,255,255,0.05)", color: student.conversations_count > 0 ? "#a5b4fc" : "#94a3b8" }}>
                      {student.conversations_count}
                    </span>
                  </td>
                  <td>{student.last_conversation_title || <span style={{ color: "#64748b" }}>-</span>}</td>
                  <td style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {student.last_message || <span style={{ color: "#64748b" }}>-</span>}
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

export default StudentProgress;
