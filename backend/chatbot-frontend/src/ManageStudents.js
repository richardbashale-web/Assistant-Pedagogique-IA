import { useState, useEffect, useCallback } from "react";
import FacultySelector from "./FacultySelector";
import { useToast } from "./Toast";
import ImportStudentsModal from "./ImportStudentsModal";

const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const API_URL = `${API_BASE_URL}/api/students/`;

function ManageStudents({ token }) {
  const [students, setStudents] = useState([]);
  const [nom, setNom] = useState("");
  const [postnom, setPostnom] = useState("");
  const [prenom, setPrenom] = useState("");
  const [sexe, setSexe] = useState("M");
  const [email, setEmail] = useState("");
  const [niveau, setNiveau] = useState("");
  const [faculte, setFaculte] = useState("");
  const [matricule, setMatricule] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [search, setSearch] = useState("");
  const [showImportModal, setShowImportModal] = useState(false);
  const [togglingId, setTogglingId] = useState(null);
  const { toastContainer, showToast } = useToast();

  const fetchStudents = useCallback(async () => {
    try {
      const res = await fetch(API_URL, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        setStudents(await res.json());
      }
    } catch (e) {
      console.error(
        "Erreur lors de la récupération des étudiants:",
        e
      );
    } finally {
      setFetching(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchStudents();
    }
  }, [token, fetchStudents]);

  const resetForm = () => {
    setNom("");
    setPostnom("");
    setPrenom("");
    setSexe("M");
    setEmail("");
    setNiveau("");
    setFaculte("");
    setMatricule("");
    setEditingId(null);
  };

  const handleSubmit = async () => {
    if (!faculte) {
      showToast("Veuillez sélectionner une faculté.", "error");
      return;
    }

    if (!nom || !email || !niveau) {
      showToast(
        "Nom, email et niveau sont obligatoires.",
        "error"
      );
      return;
    }

    if (!matricule) {
      showToast("Le matricule est obligatoire.", "error");
      return;
    }

    setLoading(true);

    const method = editingId ? "PUT" : "POST";
    const url = editingId
      ? `${API_URL}${editingId}/`
      : API_URL;

    try {
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          nom,
          postnom,
          prenom,
          sexe,
          email,
          niveau,
          faculte,
          matricule,
        }),
      });

      if (res.ok) {
        showToast(
          editingId
            ? "Étudiant modifié avec succès !"
            : "Étudiant ajouté avec succès !",
          "success"
        );

        resetForm();
        fetchStudents();
      } else {
        const error = await res.json();

        const msg =
          error.matricule?.[0] ||
          error.email?.[0] ||
          error.detail ||
          "Opération impossible.";

        showToast(`Erreur : ${msg}`, "error");
      }
    } catch {
      showToast("Erreur réseau.", "error");
    } finally {
      setLoading(false);
    }
  };

  const editStudent = (s) => {
    setNom(s.nom);
    setPostnom(s.postnom || "");
    setPrenom(s.prenom || "");
    setSexe(s.sexe || "M");
    setEmail(s.email);
    setNiveau(s.niveau);
    setFaculte(s.faculte);
    setMatricule(s.matricule || "");
    setEditingId(s.id);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const deleteStudent = async (id) => {
    if (
      !window.confirm(
        "Êtes-vous sûr de vouloir supprimer cet étudiant ?"
      )
    ) {
      return;
    }

    try {
      const res = await fetch(`${API_URL}${id}/`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        showToast("Étudiant supprimé.", "success");
        fetchStudents();
      } else {
        showToast(
          "Erreur lors de la suppression.",
          "error"
        );
      }
    } catch {
      showToast("Erreur réseau.", "error");
    }
  };

  const toggleStudentActive = async (student) => {
    const action = student.is_active
      ? "désactiver"
      : "activer";

    if (
      !window.confirm(
        `Voulez-vous vraiment ${action} cet étudiant ?\n\n"${student.nom}"`
      )
    ) {
      return;
    }

    setTogglingId(student.id);

    try {
      const res = await fetch(
        `${API_URL}${student.id}/toggle-active/`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res.ok) {
        const data = await res.json();

        showToast(data.message, "success");

        setStudents((prev) =>
          prev.map((s) =>
            s.id === student.id
              ? {
                  ...s,
                  is_active: data.is_active,
                }
              : s
          )
        );
      } else {
        const err = await res.json();

        showToast(
          err.error ||
            "Erreur lors du changement d'état.",
          "error"
        );
      }
    } catch {
      showToast("Erreur réseau.", "error");
    } finally {
      setTogglingId(null);
    }
  };

  const filtered = students.filter((s) =>
    `${s.nom} ${s.matricule} ${s.niveau}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="page-section">
      {toastContainer}

      {/* Modal import */}
      {showImportModal && (
        <ImportStudentsModal
          token={token}
          onClose={() => setShowImportModal(false)}
          onImportDone={() => {
            fetchStudents();
          }}
        />
      )}

      {/* En-tête */}
      <div className="section-header">
        <div>
          <h2>Gestion des Étudiants </h2>
          <p>
            {editingId
              ? "Modifiez les informations de l'étudiant sélectionné."
              : "Enregistrez et gérez les comptes des étudiants de votre faculté."}
          </p>
        </div>

        <button
          onClick={() => setShowImportModal(true)}
          style={{
            background:
              "linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15))",
            border:
              "1px solid rgba(99,102,241,0.35)",
            borderRadius: "12px",
            color: "#a5b4fc",
            padding: "10px 18px",
            cursor: "pointer",
            fontSize: "13px",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: "8px",
            transition: "all 0.2s",
          }}
        >
          📥 Importer des étudiants
        </button>
      </div>

      {/* Formulaire ajout / modification */}
      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label">
            Nom *
            <input
              placeholder="Ex: Kabongo"
              value={nom}
              onChange={(e) => setNom(e.target.value)}
              disabled={loading}
            />
          </label>

          <label className="field-label">
            Post-nom
            <input
              placeholder="Ex: Mbeki"
              value={postnom}
              onChange={(e) =>
                setPostnom(e.target.value)
              }
              disabled={loading}
            />
          </label>

          <label className="field-label">
            Prénom
            <input
              placeholder="Ex: Alice"
              value={prenom}
              onChange={(e) =>
                setPrenom(e.target.value)
              }
              disabled={loading}
            />
          </label>

          <label className="field-label">
            Sexe
            <select
              value={sexe}
              onChange={(e) =>
                setSexe(e.target.value)
              }
              disabled={loading}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "8px",
                border:
                  "1px solid rgba(255,255,255,0.1)",
                background: "rgba(30,41,59,0.8)",
                color: "#f8fafc",
              }}
            >
              <option value="M">Masculin</option>
              <option value="F">Féminin</option>
            </select>
          </label>

          <label className="field-label">
            Adresse email *
            <input
              placeholder="Ex: alice@student.univ.edu"
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              disabled={loading}
            />
          </label>

          <label className="field-label">
            Niveau d'études *
            <input
              placeholder="Ex: L1, L2, Master 1..."
              value={niveau}
              onChange={(e) =>
                setNiveau(e.target.value)
              }
              disabled={loading}
            />
          </label>

          <label className="field-label">
            Numéro de Matricule *
            <input
              placeholder="Ex: ETU-2026-1234 (obligatoire)"
              value={matricule}
              onChange={(e) =>
                setMatricule(e.target.value)
              }
              disabled={loading}
              title="Saisissez le matricule fourni par l'université"
            />
          </label>

          <FacultySelector
            token={token}
            value={faculte}
            onChange={(e) =>
              setFaculte(e.target.value)
            }
            label="Sélectionner la faculté *"
          />

          <div
            className="field-full"
            style={{
              display: "flex",
              gap: "12px",
              marginTop: "10px",
            }}
          >
            <button
              className="primary-btn"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading
                ? "Traitement..."
                : editingId
                ? "Enregistrer les modifications"
                : "Ajouter l'étudiant"}
            </button>

            {editingId && (
              <button
                className="logout-btn"
                onClick={resetForm}
                style={{
                  background:
                    "rgba(255,255,255,0.05)",
                  border:
                    "1px solid rgba(255,255,255,0.1)",
                  color: "#cbd5e1",
                }}
              >
                Annuler
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Liste */}
      <div className="section-header section-header-tight">
        <h3>
          Étudiants existants ({filtered.length})
        </h3>

        <input
          placeholder="🔍 Rechercher par nom ou matricule..."
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
          style={{
            background: "rgba(30,41,59,0.8)",
            border:
              "1px solid rgba(255,255,255,0.12)",
            borderRadius: "12px",
            color: "#f8fafc",
            padding: "8px 14px",
            fontSize: "13px",
            outline: "none",
            width: "260px",
          }}
        />
      </div>

      {fetching ? (
        <div className="empty-state">
          Chargement des étudiants...
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          {search
            ? "Aucun résultat pour votre recherche."
            : "Aucun étudiant enregistré pour le moment."}
        </div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Matricule</th>
                <th>Nom</th>
                <th>Sexe</th>
                <th>Promotion</th>
                <th>Faculté</th>
                <th style={{ textAlign: "center" }}>
                  Statut
                </th>
                <th style={{ textAlign: "center" }}>
                  Actions
                </th>
              </tr>
            </thead>

            <tbody>
              {filtered.map((s) => (
                <tr
                  key={s.id}
                  style={
                    editingId === s.id
                      ? {
                          background:
                            "rgba(99,102,241,0.08)",
                        }
                      : {}
                  }
                >
                  <td
                    style={{
                      fontFamily: "monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                    }}
                  >
                    {s.matricule || "-"}
                  </td>

                  <td style={{ fontWeight: 600 }}>
                    {s.nom}
                  </td>

                  <td>
                    {s.sexe === "F"
                      ? "Féminin"
                      : "Masculin"}
                  </td>

                  <td>{s.niveau}</td>

                  <td>
                    <span
                      style={{
                        padding: "4px 10px",
                        borderRadius: "12px",
                        fontSize: "11px",
                        fontWeight: 700,
                        background:
                          "rgba(99,102,241,0.15)",
                        color: "#a5b4fc",
                      }}
                    >
                      {s.faculte}
                    </span>
                  </td>

                  {/* Colonne Statut */}
                  <td style={{ textAlign: "center" }}>
                    {s.is_active !== false ? (
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                          padding: "4px 10px",
                          borderRadius: "20px",
                          fontSize: "11px",
                          fontWeight: 700,
                          background:
                            "rgba(16,185,129,0.12)",
                          color: "#34d399",
                          border:
                            "1px solid rgba(16,185,129,0.25)",
                        }}
                      >
                        <span
                          style={{
                            width: "6px",
                            height: "6px",
                            borderRadius: "50%",
                            background: "#34d399",
                            display: "inline-block",
                          }}
                        ></span>
                        Actif
                      </span>
                    ) : (
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                          padding: "4px 10px",
                          borderRadius: "20px",
                          fontSize: "11px",
                          fontWeight: 700,
                          background:
                            "rgba(239,68,68,0.1)",
                          color: "#f87171",
                          border:
                            "1px solid rgba(239,68,68,0.2)",
                        }}
                      >
                        <span
                          style={{
                            width: "6px",
                            height: "6px",
                            borderRadius: "50%",
                            background: "#f87171",
                            display: "inline-block",
                          }}
                        ></span>
                        Inactif
                      </span>
                    )}
                  </td>

                  {/* Colonne Actions */}
                  <td
                    style={{
                      textAlign: "center",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {/* Modifier */}
                    <button
                      onClick={() => editStudent(s)}
                      style={{
                        background:
                          "rgba(99,102,241,0.12)",
                        border:
                          "1px solid rgba(99,102,241,0.25)",
                        borderRadius: "8px",
                        padding: "6px 10px",
                        marginRight: "6px",
                        cursor: "pointer",
                        color: "#a5b4fc",
                      }}
                      title="Modifier l'étudiant"
                    >
                      ✏️ Modifier
                    </button>

                    {/* Activer / Désactiver */}
                    <button
                      onClick={() =>
                        toggleStudentActive(s)
                      }
                      disabled={togglingId === s.id}
                      style={{
                        background:
                          s.is_active !== false
                            ? "rgba(245,158,11,0.1)"
                            : "rgba(16,185,129,0.1)",
                        border: `1px solid ${
                          s.is_active !== false
                            ? "rgba(245,158,11,0.25)"
                            : "rgba(16,185,129,0.25)"
                        }`,
                        borderRadius: "8px",
                        padding: "6px 10px",
                        marginRight: "6px",
                        cursor:
                          togglingId === s.id
                            ? "not-allowed"
                            : "pointer",
                        color:
                          s.is_active !== false
                            ? "#fbbf24"
                            : "#34d399",
                        opacity:
                          togglingId === s.id
                            ? 0.5
                            : 1,
                        fontSize: "12px",
                        fontWeight: 600,
                      }}
                      title={
                        s.is_active !== false
                          ? "Désactiver l'étudiant"
                          : "Réactiver l'étudiant"
                      }
                    >
                      {togglingId === s.id
                        ? "..."
                        : s.is_active !== false
                        ? "🔒 Désactiver"
                        : "🔓 Activer"}
                    </button>

                    {/* Supprimer */}
                    <button
                      onClick={() =>
                        deleteStudent(s.id)
                      }
                      style={{
                        background:
                          "rgba(239,68,68,0.1)",
                        border:
                          "1px solid rgba(239,68,68,0.2)",
                        borderRadius: "8px",
                        padding: "6px 10px",
                        cursor: "pointer",
                        color: "#f87171",
                      }}
                      title="Supprimer l'étudiant"
                    >
                      🗑️
                    </button>
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