import { useState, useEffect, useCallback } from "react";
import "./Dashboard.css";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// ─── StatCard ──────────────────────────────────────────────────────────────
function StatCard({ icon, label, value, color, delay = 0 }) {
  const [displayed, setDisplayed] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = Number(value) || 0;
    if (end === 0) { setDisplayed(0); return; }
    const duration = 1200;
    const step = Math.max(1, Math.ceil(end / (duration / 16)));
    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        setDisplayed(end);
        clearInterval(timer);
      } else {
        setDisplayed(start);
      }
    }, 16);
    return () => clearInterval(timer);
  }, [value]);

  return (
    <div className="dash-stat-card" style={{ "--accent": color, animationDelay: `${delay}ms` }}>
      <div className="dash-stat-icon" style={{ background: `${color}22`, color }}>{icon}</div>
      <div className="dash-stat-body">
        <div className="dash-stat-value" style={{ color }}>{displayed}</div>
        <div className="dash-stat-label">{label}</div>
      </div>
      <div className="dash-stat-glow" style={{ background: color }} />
    </div>
  );
}

// ─── MiniBarChart ──────────────────────────────────────────────────────────
function MiniBarChart({ data, labelKey, valueKey, color }) {
  if (!data || data.length === 0) {
    return <p className="dash-empty">Aucune donnée disponible.</p>;
  }
  const max = Math.max(...data.map(d => d[valueKey] || 0), 1);
  return (
    <div className="dash-bar-chart">
      {data.map((item, i) => (
        <div className="dash-bar-row" key={i}>
          <div className="dash-bar-label" title={item[labelKey]}>{item[labelKey] || "—"}</div>
          <div className="dash-bar-track">
            <div
              className="dash-bar-fill"
              style={{
                width: `${((item[valueKey] || 0) / max) * 100}%`,
                background: color,
                animationDelay: `${i * 80}ms`
              }}
            />
          </div>
          <div className="dash-bar-value">{item[valueKey] || 0}</div>
        </div>
      ))}
    </div>
  );
}

// ─── DataTable ─────────────────────────────────────────────────────────────
function DataTable({ rows, columns }) {
  if (!rows || rows.length === 0) {
    return <p className="dash-empty">Aucune donnée disponible.</p>;
  }
  return (
    <div className="dash-table-wrapper">
      <table className="dash-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map(col => (
                <td key={col.key}>{row[col.key] ?? "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Admin Central Dashboard ───────────────────────────────────────────────
function AdminCentralDashboard({ data }) {
  const { stats, charts } = data;
  const studentsData = (charts.students_by_faculty || []).map(d => ({
    label: d["faculte__nom"] || "Inconnue",
    value: d.count,
  }));
  const professorsData = (charts.professors_by_faculty || []).map(d => ({
    label: d["faculte__nom"] || "Inconnue",
    value: d.count,
  }));

  return (
    <div className="dash-content">
      <div className="dash-hero dash-hero--central">
        <div className="dash-hero-badge">⚙️ Admin Central</div>
        <h1 className="dash-hero-title">Vue globale de la plateforme</h1>
        <p className="dash-hero-sub">Supervision complète — tous les utilisateurs, toutes les facultés</p>
      </div>

      <div className="dash-stats-grid">
        {stats.map((s, i) => (
          <StatCard key={i} icon={s.icon} label={s.label} value={s.value} color={s.color} delay={i * 80} />
        ))}
      </div>

      <div className="dash-charts-row">
        <div className="dash-chart-card">
          <div className="dash-chart-title">🎓 Étudiants par faculté</div>
          <MiniBarChart data={studentsData} labelKey="label" valueKey="value" color="#f59e0b" />
        </div>
        <div className="dash-chart-card">
          <div className="dash-chart-title">👨‍🏫 Enseignants par faculté</div>
          <MiniBarChart data={professorsData} labelKey="label" valueKey="value" color="#10b981" />
        </div>
      </div>
    </div>
  );
}

// ─── Admin Gestionnaire Dashboard ──────────────────────────────────────────
function GestionnaireDashboard({ data }) {
  const { stats, charts } = data;
  const secretaires = charts.secretaires || [];

  return (
    <div className="dash-content">
      <div className="dash-hero dash-hero--gestionnaire">
        <div className="dash-hero-badge" style={{ background: "rgba(99,102,241,0.18)", color: "#a5b4fc" }}>💼 Admin Gestionnaire</div>
        <h1 className="dash-hero-title">Mon périmètre de gestion</h1>
        <p className="dash-hero-sub">Suivi de vos secrétaires et des facultés supervisées</p>
      </div>

      <div className="dash-stats-grid">
        {stats.map((s, i) => (
          <StatCard key={i} icon={s.icon} label={s.label} value={s.value} color={s.color} delay={i * 100} />
        ))}
      </div>

      <div className="dash-charts-row">
        <div className="dash-chart-card" style={{ flex: 1 }}>
          <div className="dash-chart-title">📋 Mes secrétaires facultaires</div>
          <DataTable
            rows={secretaires}
            columns={[
              { key: "nom", label: "Nom" },
              { key: "faculte", label: "Faculté" },
              { key: "nb_professors", label: "Enseignants enregistrés" },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Secrétaire Facultaire Dashboard ──────────────────────────────────────
function SecretaireDashboard({ data }) {
  const { stats, charts, faculte } = data;
  const professors = charts.professors || [];

  return (
    <div className="dash-content">
      <div className="dash-hero dash-hero--secretaire">
        <div className="dash-hero-badge" style={{ background: "rgba(6,182,212,0.18)", color: "#67e8f9" }}>📋 Secrétaire Facultaire</div>
        <h1 className="dash-hero-title">Faculté : {faculte}</h1>
        <p className="dash-hero-sub">Gestion académique des enseignants et des cours de votre faculté</p>
      </div>

      <div className="dash-stats-grid">
        {stats.map((s, i) => (
          <StatCard key={i} icon={s.icon} label={s.label} value={s.value} color={s.color} delay={i * 100} />
        ))}
      </div>

      <div className="dash-charts-row">
        <div className="dash-chart-card" style={{ flex: 1 }}>
          <div className="dash-chart-title">👨‍🏫 Enseignants de la faculté</div>
          <DataTable
            rows={professors}
            columns={[
              { key: "nom", label: "Nom" },
              { key: "specialite", label: "Spécialité" },
              { key: "email", label: "Email" },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Professeur Dashboard ──────────────────────────────────────────────────
function ProfesseurDashboard({ data }) {
  const { stats, charts } = data;
  const courses = charts.courses || [];
  const recentNotes = charts.recent_notes || [];

  return (
    <div className="dash-content">
      <div className="dash-hero dash-hero--professeur">
        <div className="dash-hero-badge" style={{ background: "rgba(16,185,129,0.18)", color: "#6ee7b7" }}>👨‍🏫 Enseignant</div>
        <h1 className="dash-hero-title">Mes activités pédagogiques</h1>
        <p className="dash-hero-sub">Aperçu de vos cours et notes publiés sur la plateforme</p>
      </div>

      <div className="dash-stats-grid">
        {stats.map((s, i) => (
          <StatCard key={i} icon={s.icon} label={s.label} value={s.value} color={s.color} delay={i * 120} />
        ))}
      </div>

      <div className="dash-charts-row">
        <div className="dash-chart-card">
          <div className="dash-chart-title">📚 Mes cours</div>
          <DataTable
            rows={courses.map(c => ({
              ...c,
              date_creation: c.date_creation ? new Date(c.date_creation).toLocaleDateString("fr-FR") : "—"
            }))}
            columns={[
              { key: "titre", label: "Titre" },
              { key: "date_creation", label: "Date création" },
            ]}
          />
        </div>
        <div className="dash-chart-card">
          <div className="dash-chart-title">📝 Notes récentes</div>
          <DataTable
            rows={recentNotes.map(n => ({
              ...n,
              created_at: n.created_at ? new Date(n.created_at).toLocaleDateString("fr-FR") : "—"
            }))}
            columns={[
              { key: "title", label: "Titre" },
              { key: "created_at", label: "Date" },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Étudiant Dashboard ────────────────────────────────────────────────────
function EtudiantDashboard({ data }) {
  const { stats, student } = data;
  const nom = student?.nom || "Étudiant";
  const initial = nom[0]?.toUpperCase() || "?";

  return (
    <div className="dash-content">
      <div className="dash-hero dash-hero--etudiant">
        <div className="dash-hero-badge" style={{ background: "rgba(245,158,11,0.18)", color: "#fcd34d" }}>🎓 Étudiant</div>
        <h1 className="dash-hero-title">Bienvenue, {nom} !</h1>
        <p className="dash-hero-sub">Suivez vos activités et accédez aux ressources pédagogiques</p>
      </div>

      <div className="dash-profile-card">
        <div className="dash-profile-avatar">{initial}</div>
        <div className="dash-profile-info">
          <div className="dash-profile-name">{nom}</div>
          <div className="dash-profile-details">
            <span>🎓 {student?.niveau || "—"}</span>
            <span>🏢 {student?.faculte || "—"}</span>
            {student?.matricule && <span>🪪 {student.matricule}</span>}
          </div>
        </div>
      </div>

      <div className="dash-stats-grid">
        {stats.map((s, i) => (
          <StatCard key={i} icon={s.icon} label={s.label} value={s.value} color={s.color} delay={i * 100} />
        ))}
      </div>

      <div className="dash-cta-box">
        <div className="dash-cta-icon">💡</div>
        <div>
          <div className="dash-cta-title">Posez vos questions à l'assistant IA</div>
          <div className="dash-cta-sub">Notre assistant pédagogique est disponible 24h/24 pour vous aider dans vos études.</div>
        </div>
      </div>
    </div>
  );
}

// ─── Main Dashboard ────────────────────────────────────────────────────────
const KNOWN_ROLES = ["admin_central", "admin_gestionnaire", "secretaire_facultaire", "professeur", "etudiant"];

export default function Dashboard({ token, onUnauthorized }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/stats/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        if (onUnauthorized) onUnauthorized();
        return;
      }
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [token, onUnauthorized]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (loading) {
    return (
      <div className="dash-loading">
        <div className="dash-spinner" />
        <span>Chargement du tableau de bord…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dash-error">
        <div className="dash-error-icon">⚠️</div>
        <div>
          <strong>Impossible de charger le tableau de bord</strong>
          <p>{error}</p>
        </div>
        <button className="dash-retry-btn" onClick={fetchStats}>Réessayer</button>
      </div>
    );
  }

  if (!data) return null;

  const role = data.role;

  return (
    <div className="dashboard-wrapper">
      {role === "admin_central" && <AdminCentralDashboard data={data} />}
      {role === "admin_gestionnaire" && <GestionnaireDashboard data={data} />}
      {role === "secretaire_facultaire" && <SecretaireDashboard data={data} />}
      {role === "professeur" && <ProfesseurDashboard data={data} />}
      {role === "etudiant" && <EtudiantDashboard data={data} />}
      {!KNOWN_ROLES.includes(role) && (
        <div className="dash-content">
          <div className="dash-hero">
            <h1 className="dash-hero-title">Tableau de bord</h1>
            <p className="dash-hero-sub">Aucune statistique disponible pour votre rôle actuel ({role || "inconnu"}).</p>
          </div>
        </div>
      )}
    </div>
  );
}