import { useState, useEffect, useRef } from "react";

const PROMOTIONS = ["L1", "L2", "L3", "M1", "M2", "Doctorat"];

function generateAcademicYears() {
  const current = new Date().getFullYear();
  const years = [];
  for (let y = current - 1; y <= current + 2; y++) {
    years.push(`${y}-${y + 1}`);
  }
  return years;
}

function ImportStudentsModal({ token, onClose, onImportDone }) {
  const [faculties, setFaculties] = useState([]);
  const [facultyId, setFacultyId] = useState("");
  const [promotion, setPromotion] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null); // rapport d'import
  const [errorMsg, setErrorMsg] = useState("");
  const fileInputRef = useRef();

  const ACADEMIC_YEARS = generateAcademicYears();

  // Charger les facult\u00e9s
  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/faculties/", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => {
        setFaculties(Array.isArray(data) ? data : []);
        if (Array.isArray(data) && data.length > 0) {
          // pr\u00e9-s\u00e9lectionner la premi\u00e8re facult\u00e9
        }
      })
      .catch(() => {});
  }, [token]);

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) validateAndSetFile(dropped);
  };

  const validateAndSetFile = (f) => {
    const ext = f.name.split(".").pop().toLowerCase();
    if (!["xlsx", "csv", "pdf", "txt"].includes(ext)) {
      setErrorMsg("Seuls les fichiers .txt, .pdf,  .xlsx et .csv sont acceptés.");
      return;
    }
    setErrorMsg("");
    setFile(f);
    setReport(null);
  };

  const handleSubmit = async () => {
    setErrorMsg("");
    if (!facultyId) { setErrorMsg("Veuillez sélectionner une faculté."); return; }
    if (!promotion) { setErrorMsg("Veuillez sélectionner une promotion."); return; }
    if (!academicYear) { setErrorMsg("Veuillez sélectionner une année académique."); return; }
    if (!file) { setErrorMsg("Veuillez sélectionner un fichier .txt, .pdf, .xlsx ou .csv."); return; }

    setLoading(true);
    setReport(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("faculty_id", facultyId);
    formData.append("promotion", promotion);
    formData.append("academic_year", academicYear);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/students/import/", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setReport(data);
        if (data.created > 0 && onImportDone) onImportDone();
      } else {
        setErrorMsg(data.error || "Erreur lors de l'import.");
      }
    } catch {
      setErrorMsg("Erreur réseau. Vérifiez votre connexion.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={styles.modal}>
        {/* En-t\u00eate */}
        <div style={styles.header}>
          <div>
            <h2 style={styles.title}>📥 Importer des étudiants</h2>
            <p style={styles.subtitle}>Importez une liste depuis un fichier Excel ou CSV</p>
          </div>
          <button onClick={onClose} style={styles.closeBtn} title="Fermer">✕</button>
        </div>

        {/* Corps */}
        <div style={styles.body}>
          {/* Étape 1 : Contexte */}
          <div style={styles.stepCard}>
            <div style={styles.stepLabel}>
              <span style={styles.stepBadge}>1</span>
              Sélectionnez le contexte d'import
            </div>
            <div className="import-modal-form-grid" style={styles.formGrid}>
              <label style={styles.fieldLabel}>
                Faculté *
                <select
                  style={styles.select}
                  value={facultyId}
                  onChange={(e) => setFacultyId(e.target.value)}
                  disabled={loading}
                >
                  <option value="">-- Choisir une faculté --</option>
                  {faculties.map((f) => (
                    <option key={f.code} value={f.code}>{f.nom}</option>
                  ))}
                </select>
              </label>

              <label style={styles.fieldLabel}>
                Promotion *
                <select
                  style={styles.select}
                  value={promotion}
                  onChange={(e) => setPromotion(e.target.value)}
                  disabled={loading}
                >
                  <option value="">-- Choisir une promotion --</option>
                  {PROMOTIONS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </label>

              <label style={styles.fieldLabel}>
                Année académique *
                <select
                  style={styles.select}
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  disabled={loading}
                >
                  <option value="">-- Choisir une année --</option>
                  {ACADEMIC_YEARS.map((y) => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          {/* Étape 2 : Fichier */}
          <div style={styles.stepCard}>
            <div style={styles.stepLabel}>
              <span style={styles.stepBadge}>2</span>
              Choisissez votre fichier
            </div>

            {/* Format attendu */}
            <div style={styles.formatInfo}>
              <span style={styles.formatTitle}>📋 Format attendu des colonnes :</span>
              <div style={styles.columnBadges}>
                {["matricule", "nom", "post-nom", "prenom", "sexe"].map((col) => (
                  <span key={col} style={styles.colBadge}>{col}</span>
                ))}
              </div>
            </div>

            {/* Zone de d\u00e9p\u00f4t */}
            <div
              style={{
                ...styles.dropZone,
                ...(dragging ? styles.dropZoneActive : {}),
                ...(file ? styles.dropZoneHasFile : {}),
              }}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.csv"
                style={{ display: "none" }}
                onChange={(e) => { if (e.target.files[0]) validateAndSetFile(e.target.files[0]); }}
              />
              {file ? (
                <div style={styles.fileInfo}>
                  <span style={styles.fileIcon}>📄</span>
                  <div>
                    <div style={styles.fileName}>{file.name}</div>
                    <div style={styles.fileSize}>{(file.size / 1024).toFixed(1)} Ko</div>
                  </div>
                  <button
                    style={styles.removeFileBtn}
                    onClick={(e) => { e.stopPropagation(); setFile(null); setReport(null); }}
                  >✕</button>
                </div>
              ) : (
                <div style={styles.dropContent}>
                  <span style={styles.dropIcon}>📂</span>
                  <span style={styles.dropText}>Glissez-déposez votre fichier ici</span>
                  <span style={styles.dropSubText}>ou cliquez pour parcourir (.xlsx, .csv)</span>
                </div>
              )}
            </div>
          </div>

          {/* Message d'erreur */}
          {errorMsg && (
            <div style={styles.errorBox}>⚠️ {errorMsg}</div>
          )}

          {/* Bouton Importer */}
          <button
            style={{ ...styles.importBtn, ...(loading ? styles.importBtnDisabled : {}) }}
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <><span style={styles.spinner}></span> Importation en cours...</>
            ) : (
              "📥 Lancer l'import"
            )}
          </button>

          {/* Rapport d'import */}
          {report && (
            <div style={styles.reportCard}>
              <div style={styles.reportHeader}>📊 Rapport d'import</div>

              <div style={styles.reportStats}>
                <div style={{ ...styles.reportStat, background: "rgba(16,185,129,0.12)", borderColor: "rgba(16,185,129,0.3)" }}>
                  <span style={{ ...styles.reportStatNum, color: "#34d399" }}>{report.created}</span>
                  <span style={styles.reportStatLabel}>Créés avec succès</span>
                </div>
                <div style={{ ...styles.reportStat, background: "rgba(239,68,68,0.1)", borderColor: "rgba(239,68,68,0.25)" }}>
                  <span style={{ ...styles.reportStatNum, color: "#f87171" }}>{report.errors_count}</span>
                  <span style={styles.reportStatLabel}>Erreurs</span>
                </div>
                <div style={{ ...styles.reportStat, background: "rgba(99,102,241,0.1)", borderColor: "rgba(99,102,241,0.25)" }}>
                  <span style={{ ...styles.reportStatNum, color: "#a5b4fc" }}>{report.total_lines}</span>
                  <span style={styles.reportStatLabel}>Lignes traitées</span>
                </div>
              </div>

              {report.errors && report.errors.length > 0 && (
                <div>
                  <div style={styles.errorListTitle}>Détail des erreurs :</div>
                  <div style={styles.errorList}>
                    {report.errors.map((err, idx) => (
                      <div key={idx} style={styles.errorItem}>
                        <span style={styles.errorLine}>Ligne {err.line}</span>
                        <span style={styles.errorReason}>{err.reason}</span>
                        {err.data?.matricule && (
                          <span style={styles.errorMat}>Matricule: {err.data.matricule}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {report.created > 0 && report.errors_count === 0 && (
                <div style={styles.successMsg}>
                  ✅ Import terminé avec succès ! Tous les étudiants ont été créés.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────── Styles ──────────────────────────── */
const styles = {
  overlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)", backdropFilter: "blur(6px)",
    display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999, padding: "20px",
  },
  modal: {
    background: "linear-gradient(135deg, rgba(15,23,42,0.98) 0%, rgba(30,41,59,0.98) 100%)",
    border: "1px solid rgba(255,255,255,0.1)", borderRadius: "20px",
    width: "100%", maxWidth: "680px", maxHeight: "90vh", overflow: "hidden",
    display: "flex", flexDirection: "column",
    boxShadow: "0 25px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.15)",
  },
  header: {
    padding: "24px 28px 20px", borderBottom: "1px solid rgba(255,255,255,0.08)",
    display: "flex", alignItems: "flex-start", justifyContent: "space-between",
    background: "linear-gradient(135deg, rgba(99,102,241,0.08), transparent)",
  },
  title: { margin: 0, fontSize: "20px", fontWeight: 700, color: "#f8fafc" },
  subtitle: { margin: "4px 0 0", fontSize: "13px", color: "#94a3b8" },
  closeBtn: {
    background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: "8px", color: "#94a3b8", cursor: "pointer", fontSize: "16px",
    width: "34px", height: "34px", display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0, transition: "all 0.2s",
  },
  body: { padding: "24px 28px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "18px" },
  stepCard: {
    background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: "14px", padding: "18px 20px",
  },
  stepLabel: {
    display: "flex", alignItems: "center", gap: "10px",
    fontSize: "14px", fontWeight: 600, color: "#cbd5e1", marginBottom: "14px",
  },
  stepBadge: {
    background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff",
    borderRadius: "50%", width: "24px", height: "24px", display: "inline-flex",
    alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: 700, flexShrink: 0,
  },
  formGrid: { display: "grid", gap: "14px" },
  fieldLabel: { display: "flex", flexDirection: "column", gap: "6px", fontSize: "12px", color: "#94a3b8", fontWeight: 600 },
  select: {
    background: "rgba(15,23,42,0.8)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px",
    color: "#f1f5f9", padding: "9px 12px", fontSize: "13px", outline: "none", cursor: "pointer",
    appearance: "none",
  },
  formatInfo: {
    background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.15)",
    borderRadius: "10px", padding: "12px 14px", marginBottom: "14px",
  },
  formatTitle: { fontSize: "12px", color: "#a5b4fc", fontWeight: 600, display: "block", marginBottom: "8px" },
  columnBadges: { display: "flex", gap: "8px", flexWrap: "wrap" },
  colBadge: {
    background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.3)",
    borderRadius: "6px", padding: "3px 10px", fontSize: "11px", color: "#c4b5fd", fontWeight: 600, fontFamily: "monospace",
  },
  dropZone: {
    border: "2px dashed rgba(255,255,255,0.12)", borderRadius: "12px", padding: "28px 20px",
    display: "flex", alignItems: "center", justifyContent: "center",
    cursor: "pointer", transition: "all 0.25s", minHeight: "100px",
  },
  dropZoneActive: { borderColor: "#6366f1", background: "rgba(99,102,241,0.08)" },
  dropZoneHasFile: { borderColor: "rgba(16,185,129,0.4)", borderStyle: "solid", background: "rgba(16,185,129,0.05)" },
  dropContent: { display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" },
  dropIcon: { fontSize: "32px" },
  dropText: { fontSize: "14px", color: "#cbd5e1", fontWeight: 500 },
  dropSubText: { fontSize: "12px", color: "#64748b" },
  fileInfo: { display: "flex", alignItems: "center", gap: "14px", width: "100%" },
  fileIcon: { fontSize: "28px" },
  fileName: { fontSize: "14px", color: "#f1f5f9", fontWeight: 600 },
  fileSize: { fontSize: "12px", color: "#94a3b8" },
  removeFileBtn: {
    marginLeft: "auto", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)",
    borderRadius: "6px", color: "#f87171", cursor: "pointer", padding: "4px 8px", fontSize: "12px",
  },
  errorBox: {
    background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)",
    borderRadius: "10px", padding: "12px 16px", color: "#fca5a5", fontSize: "13px",
  },
  importBtn: {
    background: "linear-gradient(135deg, #6366f1, #8b5cf6)", border: "none",
    borderRadius: "12px", color: "#fff", padding: "13px 24px", fontSize: "15px",
    fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center",
    justifyContent: "center", gap: "8px", transition: "all 0.2s",
    boxShadow: "0 4px 20px rgba(99,102,241,0.35)",
  },
  importBtnDisabled: { opacity: 0.6, cursor: "not-allowed", boxShadow: "none" },
  spinner: {
    display: "inline-block", width: "14px", height: "14px",
    border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff",
    borderRadius: "50%", animation: "spin 0.7s linear infinite",
  },
  reportCard: {
    background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: "14px", padding: "20px",
  },
  reportHeader: { fontSize: "15px", fontWeight: 700, color: "#f1f5f9", marginBottom: "16px" },
  reportStats: { display: "flex", gap: "12px", marginBottom: "16px" },
  reportStat: {
    flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "4px",
    padding: "14px 10px", borderRadius: "10px", border: "1px solid",
  },
  reportStatNum: { fontSize: "28px", fontWeight: 800 },
  reportStatLabel: { fontSize: "11px", color: "#94a3b8", fontWeight: 600, textAlign: "center" },
  errorListTitle: { fontSize: "13px", fontWeight: 600, color: "#fca5a5", marginBottom: "8px" },
  errorList: { maxHeight: "200px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "6px" },
  errorItem: {
    background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.15)",
    borderRadius: "8px", padding: "8px 12px", display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap",
  },
  errorLine: {
    background: "rgba(239,68,68,0.15)", borderRadius: "5px", padding: "2px 8px",
    fontSize: "11px", color: "#f87171", fontWeight: 700, whiteSpace: "nowrap",
  },
  errorReason: { fontSize: "12px", color: "#fca5a5", flex: 1 },
  errorMat: { fontSize: "11px", color: "#94a3b8", fontFamily: "monospace" },
  successMsg: {
    background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)",
    borderRadius: "10px", padding: "12px 16px", color: "#6ee7b7", fontSize: "13px", fontWeight: 500,
    marginTop: "12px",
  },
};

export default ImportStudentsModal;