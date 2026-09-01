import { useState, useEffect, useCallback } from "react";
import FacultySelector from "./FacultySelector";
import { useToast } from "./Toast";
import ImportStudentsModal from "./ImportStudentsModal";

const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const API_URL = `${API_BASE_URL}/api/students/`;

function ManageStudents({ token }) {
  const [students, setStudents] = useState([]);

  // Informations étudiant
  const [nom, setNom] = useState("");
  const [postnom, setPostnom] = useState("");
  const [prenom, setPrenom] = useState("");
  const [sexe, setSexe] = useState("M");
  const [email, setEmail] = useState("");
  const [niveau, setNiveau] = useState("");
  const [faculte, setFaculte] = useState("");
  const [matricule, setMatricule] = useState("");

  // Informations compte utilisateur
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [editingId, setEditingId] = useState(null);

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [search, setSearch] = useState("");

  const [showImportModal, setShowImportModal] = useState(false);
  const [togglingId, setTogglingId] = useState(null);

  const { toastContainer, showToast } = useToast();

  // ============================================================
  // RÉCUPÉRATION DES ÉTUDIANTS
  // ============================================================

  const fetchStudents = useCallback(async () => {
    try {
      setFetching(true);

      const res = await fetch(API_URL, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        const data = await res.json();
        setStudents(data);
      } else {
        showToast(
          "Impossible de récupérer la liste des étudiants.",
          "error"
        );
      }
    } catch (error) {
      console.error(
        "Erreur lors de la récupération des étudiants :",
        error
      );

      showToast("Erreur réseau.", "error");
    } finally {
      setFetching(false);
    }
  }, [token, showToast]);

  useEffect(() => {
    if (token) {
      fetchStudents();
    }
  }, [token, fetchStudents]);

  // ============================================================
  // RÉINITIALISATION DU FORMULAIRE
  // ============================================================

  const resetForm = () => {
    setNom("");
    setPostnom("");
    setPrenom("");
    setSexe("M");
    setEmail("");
    setNiveau("");
    setFaculte("");
    setMatricule("");

    setUsername("");
    setPassword("");

    setEditingId(null);
  };

  // ============================================================
  // AJOUT / MODIFICATION
  // ============================================================

  const handleSubmit = async () => {
    // Vérification faculté
    if (!faculte) {
      showToast(
        "Veuillez sélectionner une faculté.",
        "error"
      );
      return;
    }

    // Vérification des informations principales
    if (!nom || !email || !niveau) {
      showToast(
        "Nom, email et niveau sont obligatoires.",
        "error"
      );
      return;
    }

    // Vérification matricule
    if (!matricule) {
      showToast(
        "Le matricule est obligatoire.",
        "error"
      );
      return;
    }

    // Username obligatoire uniquement à la création
    if (!editingId && !username) {
      showToast(
        "Le nom d'utilisateur est obligatoire.",
        "error"
      );
      return;
    }

    // Password obligatoire uniquement à la création
    if (!editingId && !password) {
      showToast(
        "Le mot de passe est obligatoire.",
        "error"
      );
      return;
    }

    // Minimum 8 caractères
    if (password && password.length < 8) {
      showToast(
        "Le mot de passe doit contenir au moins 8 caractères.",
        "error"
      );
      return;
    }

    setLoading(true);

    const method = editingId ? "PUT" : "POST";

    const url = editingId
      ? `${API_URL}${editingId}/`
      : API_URL;

    // ==========================================================
    // DONNÉES ENVOYÉES AU BACKEND
    // ==========================================================

    const data = {
      nom,
      postnom,
      prenom,
      sexe,
      email,
      niveau,
      faculte,
      matricule,
    };

    // Username uniquement s'il est renseigné
    if (username) {
      data.username = username;
    }

    // Password uniquement s'il est renseigné
    if (password) {
      data.password = password;
    }

    try {
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
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

        console.error(
          "Erreur backend :",
          error
        );

        // Gestion des différentes erreurs DRF
        const msg =
          error.username?.[0] ||
          error.password?.[0] ||
          error.matricule?.[0] ||
          error.email?.[0] ||
          error.nom?.[0] ||
          error.niveau?.[0] ||
          error.faculte?.[0] ||
          error.detail ||
          "Opération impossible.";

        showToast(
          `Erreur : ${msg}`,
          "error"
        );
      }
    } catch (error) {
      console.error(
        "Erreur réseau :",
        error
      );

      showToast(
        "Erreur réseau.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // MODIFICATION D'UN ÉTUDIANT
  // ============================================================

  const editStudent = (student) => {
    setNom(student.nom || "");
    setPostnom(student.postnom || "");
    setPrenom(student.prenom || "");
    setSexe(student.sexe || "M");
    setEmail(student.email || "");
    setNiveau(student.niveau || "");
    setFaculte(student.faculte || "");
    setMatricule(student.matricule || "");

    // Username récupéré depuis user_username
    setUsername(student.user_username || "");

    // Pour des raisons de sécurité,
    // le mot de passe existant n'est jamais récupéré.
    setPassword("");

    setEditingId(student.id);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // ============================================================
  // SUPPRESSION
  // ============================================================

  const deleteStudent = async (id) => {
    if (
      !window.confirm(
        "Êtes-vous sûr de vouloir supprimer cet étudiant ?"
      )
    ) {
      return;
    }

    try {
      const res = await fetch(
        `${API_URL}${id}/`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res.ok) {
        showToast(
          "Étudiant supprimé.",
          "success"
        );

        fetchStudents();
      } else {
        const error = await res.json();

        showToast(
          error.detail ||
            "Erreur lors de la suppression.",
          "error"
        );
      }
    } catch (error) {
      console.error(
        "Erreur suppression :",
        error
      );

      showToast(
        "Erreur réseau.",
        "error"
      );
    }
  };

  // ============================================================
  // ACTIVATION / DÉSACTIVATION
  // ============================================================

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

        showToast(
          data.message,
          "success"
        );

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
        const error = await res.json();

        showToast(
          error.error ||
            "Erreur lors du changement d'état.",
          "error"
        );
      }
    } catch (error) {
      console.error(
        "Erreur activation/désactivation :",
        error
      );

      showToast(
        "Erreur réseau.",
        "error"
      );
    } finally {
      setTogglingId(null);
    }
  };

  // ============================================================
  // RECHERCHE
  // ============================================================

  const filtered = students.filter((student) =>
    `${student.nom || ""} ${
      student.postnom || ""
    } ${student.prenom || ""} ${
      student.matricule || ""
    } ${student.niveau || ""} ${
      student.user_username || ""
    }`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  // ============================================================
  // AFFICHAGE
  // ============================================================

  return (
    <div className="page-section">
      {toastContainer}

      {/* ======================================================
          MODAL IMPORT
      ====================================================== */}

      {showImportModal && (
        <ImportStudentsModal
          token={token}
          onClose={() =>
            setShowImportModal(false)
          }
          onImportDone={() => {
            fetchStudents();
          }}
        />
      )}

      {/* ======================================================
          EN-TÊTE
      ====================================================== */}

      <div className="section-header">
        <div>
          <h2>
            Gestion des Étudiants
          </h2>

          <p>
            {editingId
              ? "Modifiez les informations de l'étudiant sélectionné."
              : "Enregistrez et gérez les comptes des étudiants de votre faculté."}
          </p>
        </div>

        <button
          onClick={() =>
            setShowImportModal(true)
          }
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

      {/* ======================================================
          FORMULAIRE
      ====================================================== */}

      <div className="card notes-card">
        <div className="form-grid">

          {/* NOM */}
          <label className="field-label">
            Nom *

            <input
              placeholder="Ex: Kabongo"
              value={nom}
              onChange={(e) =>
                setNom(e.target.value)
              }
              disabled={loading}
            />
          </label>

          {/* POST-NOM */}
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

          {/* PRÉNOM */}
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

          {/* SEXE */}
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
                background:
                  "rgba(30,41,59,0.8)",
                color: "#f8fafc",
              }}
            >
              <option value="M">
                Masculin
              </option>

              <option value="F">
                Féminin
              </option>
            </select>
          </label>

          {/* EMAIL */}
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

          {/* NIVEAU */}
          <label className="field-label">
            Niveau d'études *

            <input
              placeholder="Ex: L1, L2, L3, Master 1..."
              value={niveau}
              onChange={(e) =>
                setNiveau(e.target.value)
              }
              disabled={loading}
            />
          </label>

          {/* MATRICULE */}
          <label className="field-label">
            Numéro de Matricule *

            <input
              placeholder="Ex: ETU-2026-1234"
              value={matricule}
              onChange={(e) =>
                setMatricule(e.target.value)
              }
              disabled={loading}
              title="Saisissez le matricule fourni par l'université"
            />
          </label>

          {/* FACULTÉ */}
          <FacultySelector
            token={token}
            value={faculte}
            onChange={(e) =>
              setFaculte(e.target.value)
            }
            label="Sélectionner la faculté *"
          />

          {/* ==================================================
              COMPTE UTILISATEUR
          ================================================== */}

          <label className="field-label">
            Nom d'utilisateur *

            <input
              placeholder="Ex: alice.kabongo"
              value={username}
              onChange={(e) =>
                setUsername(e.target.value)
              }
              disabled={loading}
              autoComplete="off"
            />

            {!editingId && (
              <small
                style={{
                  display: "block",
                  marginTop: "5px",
                  color: "#94a3b8",
                  fontSize: "11px",
                }}
              >
                Identifiant utilisé pour se connecter.
              </small>
            )}
          </label>

          {/* MOT DE PASSE */}
          <label className="field-label">
            Mot de passe {!editingId && "*"}

            <input
              type="password"
              placeholder={
                editingId
                  ? "Laisser vide pour conserver le mot de passe"
                  : "Minimum 8 caractères"
              }
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              disabled={loading}
              autoComplete="new-password"
            />

            <small
              style={{
                display: "block",
                marginTop: "5px",
                color: "#94a3b8",
                fontSize: "11px",
              }}
            >
              {editingId
                ? "Saisissez un nouveau mot de passe uniquement si vous souhaitez le modifier."
                : "Le mot de passe doit contenir au moins 8 caractères."}
            </small>
          </label>

          {/* ==================================================
              BOUTONS
          ================================================== */}

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
                disabled={loading}
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

      {/* ======================================================
          LISTE DES ÉTUDIANTS
      ====================================================== */}

      <div className="section-header section-header-tight">
        <h3>
          Étudiants existants (
          {filtered.length}
          )
        </h3>

        <input
          placeholder="🔍 Rechercher par nom, matricule ou username..."
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
          style={{
            background:
              "rgba(30,41,59,0.8)",
            border:
              "1px solid rgba(255,255,255,0.12)",
            borderRadius: "12px",
            color: "#f8fafc",
            padding: "8px 14px",
            fontSize: "13px",
            outline: "none",
            width: "300px",
          }}
        />
      </div>

      {/* ======================================================
          CHARGEMENT
      ====================================================== */}

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
                <th>Username</th>
                <th>Sexe</th>
                <th>Promotion</th>
                <th>Faculté</th>
                <th
                  style={{
                    textAlign: "center",
                  }}
                >
                  Statut
                </th>
                <th
                  style={{
                    textAlign: "center",
                  }}
                >
                  Actions
                </th>
              </tr>
            </thead>

            <tbody>
              {filtered.map((student) => (
                <tr
                  key={student.id}
                  style={
                    editingId === student.id
                      ? {
                          background:
                            "rgba(99,102,241,0.08)",
                        }
                      : {}
                  }
                >

                  {/* MATRICULE */}
                  <td
                    style={{
                      fontFamily:
                        "monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                    }}
                  >
                    {student.matricule ||
                      "-"}
                  </td>

                  {/* NOM COMPLET */}
                  <td
                    style={{
                      fontWeight: 600,
                    }}
                  >
                    {student.nom}

                    {student.postnom && (
                      <>
                        {" "}
                        {student.postnom}
                      </>
                    )}

                    {student.prenom && (
                      <>
                        {" "}
                        {student.prenom}
                      </>
                    )}
                  </td>

                  {/* USERNAME */}
                  <td>
                    <span
                      style={{
                        padding:
                          "4px 9px",
                        borderRadius:
                          "8px",
                        fontSize: "11px",
                        fontFamily:
                          "monospace",
                        background:
                          "rgba(59,130,246,0.1)",
                        color:
                          "#93c5fd",
                        border:
                          "1px solid rgba(59,130,246,0.2)",
                      }}
                    >
                      {student.user_username ||
                        "-"}
                    </span>
                  </td>

                  {/* SEXE */}
                  <td>
                    {student.sexe === "F"
                      ? "Féminin"
                      : "Masculin"}
                  </td>

                  {/* NIVEAU */}
                  <td>
                    {student.niveau}
                  </td>

                  {/* FACULTÉ */}
                  <td>
                    <span
                      style={{
                        padding:
                          "4px 10px",
                        borderRadius:
                          "12px",
                        fontSize: "11px",
                        fontWeight: 700,
                        background:
                          "rgba(99,102,241,0.15)",
                        color:
                          "#a5b4fc",
                      }}
                    >
                      {student.faculte}
                    </span>
                  </td>

                  {/* STATUT */}
                  <td
                    style={{
                      textAlign:
                        "center",
                    }}
                  >
                    {student.is_active !==
                    false ? (
                      <span
                        style={{
                          display:
                            "inline-flex",
                          alignItems:
                            "center",
                          gap: "5px",
                          padding:
                            "4px 10px",
                          borderRadius:
                            "20px",
                          fontSize:
                            "11px",
                          fontWeight:
                            700,
                          background:
                            "rgba(16,185,129,0.12)",
                          color:
                            "#34d399",
                          border:
                            "1px solid rgba(16,185,129,0.25)",
                        }}
                      >
                        <span
                          style={{
                            width:
                              "6px",
                            height:
                              "6px",
                            borderRadius:
                              "50%",
                            background:
                              "#34d399",
                            display:
                              "inline-block",
                          }}
                        />

                        Actif
                      </span>
                    ) : (
                      <span
                        style={{
                          display:
                            "inline-flex",
                          alignItems:
                            "center",
                          gap: "5px",
                          padding:
                            "4px 10px",
                          borderRadius:
                            "20px",
                          fontSize:
                            "11px",
                          fontWeight:
                            700,
                          background:
                            "rgba(239,68,68,0.1)",
                          color:
                            "#f87171",
                          border:
                            "1px solid rgba(239,68,68,0.2)",
                        }}
                      >
                        <span
                          style={{
                            width:
                              "6px",
                            height:
                              "6px",
                            borderRadius:
                              "50%",
                            background:
                              "#f87171",
                            display:
                              "inline-block",
                          }}
                        />

                        Inactif
                      </span>
                    )}
                  </td>

                  {/* ACTIONS */}
                  <td
                    style={{
                      textAlign:
                        "center",
                      whiteSpace:
                        "nowrap",
                    }}
                  >

                    {/* MODIFIER */}
                    <button
                      onClick={() =>
                        editStudent(
                          student
                        )
                      }
                      style={{
                        background:
                          "rgba(99,102,241,0.12)",
                        border:
                          "1px solid rgba(99,102,241,0.25)",
                        borderRadius:
                          "8px",
                        padding:
                          "6px 10px",
                        marginRight:
                          "6px",
                        cursor:
                          "pointer",
                        color:
                          "#a5b4fc",
                      }}
                      title="Modifier l'étudiant"
                    >
                      ✏️ Modifier
                    </button>

                    {/* ACTIVER / DÉSACTIVER */}
                    <button
                      onClick={() =>
                        toggleStudentActive(
                          student
                        )
                      }
                      disabled={
                        togglingId ===
                        student.id
                      }
                      style={{
                        background:
                          student.is_active !==
                          false
                            ? "rgba(245,158,11,0.1)"
                            : "rgba(16,185,129,0.1)",

                        border: `1px solid ${
                          student.is_active !==
                          false
                            ? "rgba(245,158,11,0.25)"
                            : "rgba(16,185,129,0.25)"
                        }`,

                        borderRadius:
                          "8px",

                        padding:
                          "6px 10px",

                        marginRight:
                          "6px",

                        cursor:
                          togglingId ===
                          student.id
                            ? "not-allowed"
                            : "pointer",

                        color:
                          student.is_active !==
                          false
                            ? "#fbbf24"
                            : "#34d399",

                        opacity:
                          togglingId ===
                          student.id
                            ? 0.5
                            : 1,

                        fontSize:
                          "12px",

                        fontWeight:
                          600,
                      }}
                      title={
                        student.is_active !==
                        false
                          ? "Désactiver l'étudiant"
                          : "Réactiver l'étudiant"
                      }
                    >
                      {togglingId ===
                      student.id
                        ? "..."
                        : student.is_active !==
                          false
                        ? "🔒 Désactiver"
                        : "🔓 Activer"}
                    </button>

                    {/* SUPPRIMER */}
                    <button
                      onClick={() =>
                        deleteStudent(
                          student.id
                        )
                      }
                      style={{
                        background:
                          "rgba(239,68,68,0.1)",
                        border:
                          "1px solid rgba(239,68,68,0.2)",
                        borderRadius:
                          "8px",
                        padding:
                          "6px 10px",
                        cursor:
                          "pointer",
                        color:
                          "#f87171",
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