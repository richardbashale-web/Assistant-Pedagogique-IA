import { useState } from "react";
import ManageGestionnaires from "./ManageGestionnaires";
import ManageSecretaires from "./ManageSecretaires";
import ManageProfessors from "./ManageProfessors";
import ManageStudents from "./ManageStudents";
import ManageCourses from "./ManageCourses";

const accountTypes = [
  { id: "gestionnaire", label: "Gestionnaire", description: "Créer un administrateur gestionnaire." },
  { id: "secretaire", label: "Secrétaire", description: "Créer un secrétaire facultaire." },
  { id: "enseignant", label: "enseignant", description: "Créer un compte enseignant." },
  { id: "etudiant", label: "Étudiant", description: "Créer ou gérer un compte étudiant." },
  { id: "cours", label: "Cours", description: "Créer et gérer les cours." },
];

function AccountCreation({ token }) {
  const [selectedType, setSelectedType] = useState("gestionnaire");
  const selected = accountTypes.find((type) => type.id === selectedType);

  return (
    <div className="page-section">
      <div className="section-header"><div><h2>Création de compte</h2><p>Choisissez le type de compte à créer ou à administrer.</p></div></div>
      <div className="card notes-card" style={{ marginBottom: "24px" }}>
        <div className="form-grid">
          <div className="field-label field-full">Type de compte
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "10px" }}>
              {accountTypes.map((type) => (
                <button
                  key={type.id}
                  type="button"
                  className="primary-btn"
                  onClick={() => setSelectedType(type.id)}
                  style={selectedType === type.id
                    ? {}
                    : { background: "rgba(30,41,59,0.8)", border: "1px solid rgba(255,255,255,0.12)", color: "#cbd5e1" }}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>
          <p className="field-full" style={{ margin: 0, color: "var(--text-muted)", fontSize: "13px" }}>{selected.description}</p>
        </div>
      </div>
      {selectedType === "gestionnaire" && <ManageGestionnaires token={token} />}
      {selectedType === "secretaire" && <ManageSecretaires token={token} />}
      {selectedType === "enseignant" && <ManageProfessors token={token} />}
      {selectedType === "etudiant" && <ManageStudents token={token} />}
      {selectedType === "cours" && <ManageCourses token={token} />}
    </div>
  );
}

export default AccountCreation;
