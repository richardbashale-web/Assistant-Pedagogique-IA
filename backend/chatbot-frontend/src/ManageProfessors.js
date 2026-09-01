import { useState, useEffect, useCallback } from "react";
import FacultySelector from "./FacultySelector";
import { useToast } from "./Toast";

function ManageProfessors({ token, secretaryMode = false }) {
  const [nom, setNom] = useState("");
  const [postnom, setPostnom] = useState("");
  const [prenom, setPrenom] = useState("");
  const [sexe, setSexe] = useState("");
  const [email, setEmail] = useState("");
  const [specialite, setSpecialite] = useState("");
  const [grade, setGrade] = useState("");
  const [faculte, setFaculte] = useState("");
  const [telephone, setTelephone] = useState("");

  // Identifiants du compte
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [list, setList] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [search, setSearch] = useState("");

  const { toastContainer, showToast } = useToast();

  const API_BASE_URL =
    process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

  const API_URL = `${API_BASE_URL}/api/professors/`;

  const fetchProfessors = useCallback(async () => {
    try {
      setFetching(true);

      const res = await fetch(API_URL, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        const data = await res.json();
        setList(Array.isArray(data) ? data : []);
      } else {
        console.error(
          "Erreur lors du chargement des enseignants:",
          res.status
        );
      }
    } catch (e) {
      console.error(
        "Erreur lors du chargement des enseignants:",
        e
      );
    } finally {
      setFetching(false);
    }
  }, [token, API_URL]);

  useEffect(() => {
    if (token) {
      fetchProfessors();
    }
  }, [token, fetchProfessors]);

  // Récupération de la faculté de la secrétaire
  useEffect(() => {
    if (!secretaryMode || !token) return;

    fetch(`${API_BASE_URL}/api/me/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((response) =>
        response.ok ? response.json() : null
      )
      .then((data) => {
        if (data?.faculte) {
          setFaculte(data.faculte);
        }
      })
      .catch((error) => {
        console.error(
          "Erreur récupération faculté:",
          error
        );
      });
  }, [token, secretaryMode, API_BASE_URL]);

  const resetForm = () => {
    setNom("");
    setPostnom("");
    setPrenom("");
    setSexe("");
    setEmail("");
    setSpecialite("");
    setGrade("");
    setFaculte("");
    setTelephone("");

    setUsername("");
    setPassword("");

    setEditingId(null);
  };

  const handleSubmit = async () => {
    // Validation faculté
    if (!faculte) {
      showToast(
        "Veuillez sélectionner une faculté.",
        "error"
      );
      return;
    }

    // Validation données personnelles
    if (
      !nom ||
      !prenom ||
      !email ||
      !specialite ||
      !username
    ) {
      showToast(
        "Nom, prénom, email, spécialité et nom d'utilisateur sont obligatoires.",
        "error"
      );
      return;
    }

    // Mot de passe obligatoire uniquement à la création
    if (!editingId && !password) {
      showToast(
        "Le mot de passe est obligatoire pour créer le compte.",
        "error"
      );
      return;
    }

    if (!editingId && password.length < 8) {
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

    // Données envoyées à Django
    const data = {
      nom,
      postnom,
      prenom,
      sexe,
      email,
      specialite,
      grade,
      faculte,
      telephone,
      username,
    };

    // Ne pas envoyer password vide pendant une modification
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
            ? "Enseignant modifié avec succès !"
            : "Enseignant et compte utilisateur créés avec succès !",
          "success"
        );

        resetForm();

        await fetchProfessors();
      } else {
        let err = {};

        try {
          err = await res.json();
        } catch {
          err = {};
        }

        let msg = "Opération impossible.";

        if (err.error) {
          msg = err.error;
        } else if (err.detail) {
          msg = err.detail;
        } else if (typeof err === "object") {
          const messages = [];

          Object.entries(err).forEach(
            ([field, errors]) => {
              if (Array.isArray(errors)) {
                messages.push(
                  `${field}: ${errors.join(" ")}`
                );
              } else if (typeof errors === "string") {
                messages.push(
                  `${field}: ${errors}`
                );
              }
            }
          );

          if (messages.length > 0) {
            msg = messages.join(" | ");
          }
        }

        showToast(`Erreur : ${msg}`, "error");
      }
    } catch (error) {
      console.error(error);

      showToast(
        "Erreur réseau. Vérifiez la connexion au serveur.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  const editProfessor = (p) => {
    setNom(p.nom || "");
    setPostnom(p.postnom || "");
    setPrenom(p.prenom || "");
    setSexe(p.sexe || "");
    setEmail(p.email || "");
    setSpecialite(p.specialite || "");
    setGrade(p.grade || "");
    setFaculte(p.faculte || "");
    setTelephone(p.telephone || "");

    // Le serializer retourne user_username
    setUsername(p.user_username || "");

    // Ne jamais récupérer/pré-remplir le password
    setPassword("");

    setEditingId(p.id);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const deleteProfessor = async (id) => {
    if (
      !window.confirm(
        "Supprimer cet enseignant et son compte utilisateur ?"
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
          "Enseignant et compte utilisateur supprimés.",
          "success"
        );

        fetchProfessors();
      } else {
        let err = {};

        try {
          err = await res.json();
        } catch {
          err = {};
        }

        showToast(
          err.error ||
            "Erreur lors de la suppression.",
          "error"
        );
      }
    } catch {
      showToast(
        "Erreur réseau.",
        "error"
      );
    }
  };

  const toggleProfessorActive = async (professor) => {
    const action =
      professor.is_active !== false
        ? "désactiver"
        : "activer";

    if (
      !window.confirm(
        `Voulez-vous ${action} cet enseignant ?`
      )
    ) {
      return;
    }

    try {
      const res = await fetch(
        `${API_URL}${professor.id}/toggle-active/`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!res.ok) {
        throw new Error();
      }

      const data = await res.json();

      setList((current) =>
        current.map((item) =>
          item.id === professor.id
            ? {
                ...item,
                is_active: data.is_active,
              }
            : item
        )
      );

      showToast(
        `Enseignant ${
          data.is_active
            ? "activé"
            : "désactivé"
        }.`,
        "success"
      );
    } catch {
      showToast(
        "Impossible de modifier le statut.",
        "error"
      );
    }
  };

  const filtered = list.filter((p) =>
    `${p.nom || ""} ${p.postnom || ""} ${
      p.prenom || ""
    } ${p.specialite || ""} ${
      p.email || ""
    } ${p.user_username || ""}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="page-section">
      {toastContainer}

      <div className="section-header">
        <div>
          <h2>Gestion des Enseignants</h2>

          <p>
            {editingId
              ? "Modifiez les informations de l'enseignant sélectionné."
              : "Enregistrez et gérez les comptes des enseignants de votre faculté."}
          </p>
        </div>
      </div>

      <div className="card notes-card">
        <div className="form-grid">

          {/* NOM */}
          <label className="field-label">
            Nom *
            <input
              placeholder="Ex: Bashale"
              value={nom}
              onChange={(e) =>
                setNom(e.target.value)
              }
              disabled={loading}
            />
          </label>

          {/* POSTNOM */}
          <label className="field-label">
            Postnom
            <input
              placeholder="Ex: Kanku"
              value={postnom}
              onChange={(e) =>
                setPostnom(e.target.value)
              }
              disabled={loading}
            />
          </label>

          {/* PRENOM */}
          <label className="field-label">
            Prénom *
            <input
              placeholder="Ex: Richard"
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
                backgroundColor: "#1e293b",
                padding: "10px",
                borderRadius: "8px",
                border:
                  "1px solid rgba(255,255,255,0.1)",
                color: "#f8fafc",
                width: "100%",
              }}
            >
              <option value="">
                -- Sélectionner --
              </option>

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
              placeholder="Ex: rbashale@uwb.edu"
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              disabled={loading}
            />
          </label>

          {/* USERNAME */}
          <label className="field-label">
            Nom d'utilisateur *
            <input
              placeholder="Ex: rbashale"
              value={username}
              onChange={(e) =>
                setUsername(e.target.value)
              }
              disabled={loading}
              autoComplete="off"
            />
          </label>

          {/* PASSWORD */}
          <label className="field-label">
            Mot de passe {!editingId && "*"}
            <input
              type="password"
              placeholder={
                editingId
                  ? "Laisser vide pour conserver"
                  : "Minimum 8 caractères"
              }
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              disabled={loading}
              autoComplete="new-password"
            />
          </label>

          {/* SPECIALITE */}
          <label className="field-label">
            Spécialité *
            <input
              placeholder="Ex: Intelligence Artificielle"
              value={specialite}
              onChange={(e) =>
                setSpecialite(e.target.value)
              }
              disabled={loading}
            />
          </label>

          {/* GRADE */}
          <label className="field-label">
            Grade
            <input
              placeholder="Ex: Enseignant ordinaire"
              value={grade}
              onChange={(e) =>
                setGrade(e.target.value)
              }
              disabled={loading}
            />
          </label>

          {/* TELEPHONE */}
          <label className="field-label">
            Téléphone
            <input
              placeholder="Ex: +243..."
              value={telephone}
              onChange={(e) =>
                setTelephone(e.target.value)
              }
              disabled={loading}
            />
          </label>

          {/* FACULTE */}
          {secretaryMode ? (
            <label className="field-label">
              Votre faculté
              <input
                value={
                  faculte || "Chargement..."
                }
                disabled
              />
            </label>
          ) : (
            <FacultySelector
              token={token}
              value={faculte}
              onChange={(e) =>
                setFaculte(e.target.value)
              }
              label="Sélectionner la faculté *"
            />
          )}

          {/* BOUTONS */}
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
                : "Ajouter l'enseignant"}
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

      {/* LISTE */}
      <div className="section-header section-header-tight">
        <h3>Enseignants existants</h3>

        <input
          placeholder="🔍 Rechercher..."
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
            width: "220px",
          }}
        />
      </div>

      {fetching ? (
        <div className="empty-state">
          Chargement des enseignants...
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          {search
            ? "Aucun résultat pour votre recherche."
            : "Aucun enseignant enregistré pour le moment."}
        </div>
      ) : (
        <div className="progress-table-wrapper">
          <table className="progress-table">
            <thead>
              <tr>
                <th>Nom complet</th>
                <th>Username</th>
                <th>Spécialité</th>
                <th>Email</th>
                <th>Téléphone</th>
                <th>Faculté</th>
                <th style={{ textAlign: "center" }}>
                  Actions
                </th>
              </tr>
            </thead>

            <tbody>
              {filtered.map((p) => (
                <tr
                  key={p.id}
                  style={
                    editingId === p.id
                      ? {
                          background:
                            "rgba(99,102,241,0.08)",
                        }
                      : {}
                  }
                >
                  <td
                    style={{
                      fontWeight: 600,
                    }}
                  >
                    {[
                      p.nom,
                      p.postnom,
                      p.prenom,
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  </td>

                  <td>
                    <span
                      style={{
                        fontFamily:
                          "monospace",
                        fontWeight: 600,
                      }}
                    >
                      {p.user_username || "-"}
                    </span>
                  </td>

                  <td>
                    {p.specialite || "-"}
                  </td>

                  <td>
                    {p.email || "-"}
                  </td>

                  <td>
                    {p.telephone || "-"}
                  </td>

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
                        color: "#a5b4fc",
                      }}
                    >
                      {p.faculte || "-"}
                    </span>
                  </td>

                  <td
                    style={{
                      textAlign: "center",
                    }}
                  >
                    <button
                      onClick={() =>
                        editProfessor(p)
                      }
                      style={{
                        background:
                          "rgba(99,102,241,0.12)",
                        border:
                          "1px solid rgba(99,102,241,0.25)",
                        borderRadius: "8px",
                        padding:
                          "6px 10px",
                        marginRight: "8px",
                        cursor:
                          "pointer",
                        color: "#a5b4fc",
                      }}
                      title="Modifier"
                    >
                      ✏️ Modifier
                    </button>

                    <button
                      onClick={() =>
                        toggleProfessorActive(
                          p
                        )
                      }
                      style={{
                        background:
                          "rgba(245,158,11,0.1)",
                        border:
                          "1px solid rgba(245,158,11,0.25)",
                        borderRadius: "8px",
                        padding:
                          "6px 10px",
                        marginRight: "8px",
                        cursor:
                          "pointer",
                        color: "#fbbf24",
                      }}
                      title={
                        p.is_active !==
                        false
                          ? "Désactiver"
                          : "Activer"
                      }
                    >
                      {p.is_active !==
                      false
                        ? "🔒 Désactiver"
                        : "🔓 Activer"}
                    </button>

                    <button
                      onClick={() =>
                        deleteProfessor(
                          p.id
                        )
                      }
                      style={{
                        background:
                          "rgba(239,68,68,0.1)",
                        border:
                          "1px solid rgba(239,68,68,0.2)",
                        borderRadius: "8px",
                        padding:
                          "6px 10px",
                        cursor:
                          "pointer",
                        color: "#f87171",
                      }}
                      title="Supprimer"
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

export default ManageProfessors;