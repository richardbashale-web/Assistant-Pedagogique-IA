import { useCallback, useEffect, useState } from "react";
import { useToast } from "./Toast";

const PROMOTION_OPTIONS = ["L1", "L2", "L3", "M1", "M2"];
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

function CourseAssignments({ token }) {
  const [courses, setCourses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [courseId, setCourseId] = useState("");
  const [teacherIds, setTeacherIds] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(false);
  const { toastContainer, showToast } = useToast();

  const headers = { Authorization: `Bearer ${token}` };
  const selectedCourse = courses.find((course) => String(course.id) === courseId);

  const loadData = useCallback(async () => {
    try {
      const [coursesResponse, teachersResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/courses/`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_BASE_URL}/api/professors/`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (coursesResponse.ok) setCourses(await coursesResponse.json());
      if (teachersResponse.ok) setTeachers(await teachersResponse.json());
    } catch {
      showToast("Impossible de charger les cours ou les enseignants.", "error");
    }
  }, [token, showToast]);

  useEffect(() => { loadData(); }, [loadData]);

  const selectCourse = (event) => {
    const id = event.target.value;
    const course = courses.find((item) => String(item.id) === id);
    setCourseId(id);
    setTeacherIds(course?.enseignants?.map(String) || []);
    setPromotions(course?.promotions || []);
  };

  const toggleTeacher = (id) => {
    const normalizedId = String(id);
    setTeacherIds((current) => current.includes(normalizedId)
      ? current.filter((item) => item !== normalizedId)
      : [...current, normalizedId]);
  };

  const togglePromotion = (promotion) => {
    setPromotions((current) => current.includes(promotion)
      ? current.filter((item) => item !== promotion)
      : [...current, promotion]);
  };

  const saveAssignments = async () => {
    if (!courseId) { showToast("Sélectionnez d'abord un cours.", "error"); return; }
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/courses/${courseId}/assignments/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ enseignants: teacherIds.map(Number), promotions }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.enseignants?.[0] || error.error || "Attribution impossible.");
      }
      showToast("Attributions enregistrées avec succès.", "success");
      await loadData();
    } catch (error) {
      showToast(error.message || "Erreur réseau.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-section">
      {toastContainer}
      <div className="section-header"><div><h2>Attribution des cours</h2><p>Associez un cours à un ou plusieurs enseignants, puis choisissez les promotions concernées.</p></div></div>
      <div className="card notes-card">
        <div className="form-grid">
          <label className="field-label field-full">Cours à attribuer
            <select value={courseId} onChange={selectCourse} disabled={loading}>
              <option value="">-- Sélectionner un cours --</option>
              {courses.map((course) => <option key={course.id} value={course.id}>{course.titre}</option>)}
            </select>
          </label>

          {selectedCourse && <>
            <div className="field-label field-full">Enseignants
              <div className="selection-list">
                {teachers.map((teacher) => <label key={teacher.id} className="selection-item">
                  <input type="checkbox" checked={teacherIds.includes(String(teacher.id))} onChange={() => toggleTeacher(teacher.id)} disabled={loading} />
                  <span>{teacher.nom} — {teacher.specialite || "Sans spécialité"}</span>
                </label>)}
              </div>
            </div>
            <div className="field-label field-full">Promotions
              <div className="selection-list selection-list--inline">
                {PROMOTION_OPTIONS.map((promotion) => <label key={promotion} className="selection-item">
                  <input type="checkbox" checked={promotions.includes(promotion)} onChange={() => togglePromotion(promotion)} disabled={loading} />
                  <span>{promotion}</span>
                </label>)}
              </div>
            </div>
            <div className="field-full"><button className="primary-btn" onClick={saveAssignments} disabled={loading}>{loading ? "Enregistrement..." : "Enregistrer les attributions"}</button></div>
          </>}
        </div>
      </div>
    </div>
  );
}

export default CourseAssignments;
