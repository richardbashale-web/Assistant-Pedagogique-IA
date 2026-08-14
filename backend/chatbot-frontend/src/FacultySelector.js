import { useState, useEffect } from "react";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

function FacultySelector({ token, value, onChange, label = "Faculté" }) {
  const [faculties, setFaculties] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFaculties = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/faculties/`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setFaculties(data);
        }
      } catch (error) {
        console.error("Erreur lors du chargement des facultés:", error);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchFaculties();
    }
  }, [token]);

  if (loading) {
    return <div className="field-label">Chargement des facultés...</div>;
  }

  return (
    <label className="field-label">
      {label}
      <select
        id="faculty-select"
        value={value}
        onChange={onChange}
        required
      >
        <option value="" style={{backgroundColor: '#1e293b'}}>-- Sélectionner une faculté --</option>
        {faculties.map(faculty => (
          <option key={faculty.code} value={faculty.code} style={{backgroundColor: '#1e293b'}}>
            {faculty.nom}
          </option>
        ))}
      </select>
    </label>
  );
}

export default FacultySelector;
