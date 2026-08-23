import { useState } from "react";
import ManageProfessors from "./ManageProfessors";
import ManageCourses from "./ManageCourses";

function SecretaryAccountCreation({ token }) {
  const [selection, setSelection] = useState("enseignant");
  return (
    <div className="page-section">
      <div className="section-header"><div><h2>Création de compte</h2><p>Choisissez ce que vous souhaitez créer pour votre faculté.</p></div></div>
      <div className="card notes-card" style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
          <button type="button" className="primary-btn" onClick={() => setSelection("enseignant")} style={selection === "enseignant" ? {} : { background: "rgba(30,41,59,0.8)" }}>Enseignant</button>
          <button type="button" className="primary-btn" onClick={() => setSelection("cours")} style={selection === "cours" ? {} : { background: "rgba(30,41,59,0.8)" }}>Cours</button>
        </div>
      </div>
      {selection === "enseignant" && <ManageProfessors token={token} secretaryMode />}
      {selection === "cours" && <ManageCourses token={token} />}
    </div>
  );
}

export default SecretaryAccountCreation;
