import { useState } from "react";
import logoUwb from "./logo-uwb.webp";

const API_BASE_URL = process.env.REACT_APP_API_URL;

function Login({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username.trim() || !password) {
      alert("Veuillez remplir tous les champs.");
      return;
    }

    if (!API_BASE_URL) {
      alert("Configuration du serveur manquante.");
      return;
    }

    setLoading(true);

    try {
      const apiUrl = API_BASE_URL.replace(/\/+$/, "");

      const response = await fetch(`${apiUrl}/api/token/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username.trim(),
          password: password,
        }),
      });

      const text = await response.text();
      let data;

      try {
        data = JSON.parse(text);
      } catch {
        console.error("Réponse serveur invalide :", text);
        alert("Le serveur a renvoyé une réponse inattendue.");
        return;
      }

      if (response.ok && data.access) {
        localStorage.setItem("token", data.access);

        if (data.refresh) {
          localStorage.setItem("refreshToken", data.refresh);
        }

        setToken(data.access);
      } else if (response.status === 401) {
        alert("Nom d'utilisateur ou mot de passe incorrect.");
      } else {
        alert(
          data.detail ||
            "Erreur lors de la connexion. Veuillez réessayer."
        );
      }
    } catch (error) {
      console.error("Erreur de connexion :", error);
      alert("Impossible de contacter le serveur. Vérifiez votre connexion.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <img
        src={logoUwb}
        alt=""
        aria-hidden="true"
        style={styles.backgroundLogo}
      />

      <div style={styles.card}>
        <img src={logoUwb} alt="Logo UWB" style={styles.panelLogo} />

        <h2 style={styles.title}>Connexion</h2>

        <p style={styles.subtitle}>
          Accédez à votre assistant pédagogique
        </p>

        <form
          onSubmit={(event) => {
            event.preventDefault();

            if (!loading) {
              handleLogin();
            }
          }}
        >
          <div style={styles.inputGroup}>
            <input
              type="text"
              placeholder="Nom d'utilisateur"
              aria-label="Nom d'utilisateur"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              style={styles.input}
              disabled={loading}
              required
            />
          </div>

          <div style={styles.inputGroup}>
            <div style={styles.passwordContainer}>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Mot de passe"
                aria-label="Mot de passe"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                style={styles.passwordInput}
                disabled={loading}
                required
              />

              <button
                type="button"
                onClick={() => setShowPassword((previous) => !previous)}
                style={styles.eyeButton}
                aria-label={
                  showPassword
                    ? "Masquer le mot de passe"
                    : "Afficher le mot de passe"
                }
                aria-pressed={showPassword}
                disabled={loading}
              >
                <svg
                  viewBox="0 0 24 24"
                  width="22"
                  height="22"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  {showPassword ? (
                    <>
                      <path d="M3 3l18 18" />
                      <path d="M10.6 10.6a2 2 0 002.8 2.8" />
                      <path d="M9.9 5.2A10.8 10.8 0 0112 5c5 0 8.5 4.5 9 7-.2 1.1-1 2.5-2.2 3.7" />
                      <path d="M6.2 6.2C3.8 7.8 2.3 10.2 2 12c.5 2.5 4 7 10 7 1.4 0 2.6-.3 3.7-.8" />
                    </>
                  ) : (
                    <>
                      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" />
                      <circle cx="12" cy="12" r="3" />
                    </>
                  )}
                </svg>
              </button>
            </div>
          </div>

          <button
            type="submit"
            style={{
              ...styles.button,
              ...(loading ? styles.buttonDisabled : {}),
            }}
            disabled={loading}
          >
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "100vh",
    padding: "20px",
    boxSizing: "border-box",
    backgroundColor: "#f9fafb",
    backgroundImage:
      "linear-gradient(135deg, rgba(239,246,255,0.88), rgba(248,250,252,0.94))",
    fontFamily: "'Inter', sans-serif",
    position: "relative",
    overflow: "hidden",
  },

  backgroundLogo: {
    position: "absolute",
    width: "min(92vw, 980px)",
    height: "min(92vh, 900px)",
    objectFit: "contain",
    left: "50%",
    top: "50%",
    transform: "translate(-50%, -50%)",
    opacity: 0.16,
    pointerEvents: "none",
    zIndex: 0,
  },

  card: {
    padding: "40px",
    backgroundColor: "#ffffff",
    borderRadius: "16px",
    boxShadow: "0 10px 25px rgba(0,0,0,0.05)",
    width: "100%",
    maxWidth: "400px",
    boxSizing: "border-box",
    textAlign: "center",
    position: "relative",
    zIndex: 1,
  },

  panelLogo: {
    display: "block",
    width: "96px",
    height: "96px",
    objectFit: "contain",
    margin: "0 auto 18px",
  },

  title: {
    margin: "0 0 10px 0",
    fontSize: "24px",
    fontWeight: "bold",
    color: "#111827",
  },

  subtitle: {
    color: "#6b7280",
    marginBottom: "30px",
    fontSize: "14px",
  },

  inputGroup: {
    marginBottom: "20px",
  },

  input: {
    width: "100%",
    padding: "12px 16px",
    borderRadius: "10px",
    border: "1px solid #d1d5db",
    fontSize: "15px",
    outline: "none",
    boxSizing: "border-box",
  },

  passwordContainer: {
    position: "relative",
    width: "100%",
  },

  passwordInput: {
    width: "100%",
    padding: "12px 48px 12px 16px",
    borderRadius: "10px",
    border: "1px solid #d1d5db",
    fontSize: "15px",
    outline: "none",
    boxSizing: "border-box",
  },

  eyeButton: {
    position: "absolute",
    right: "12px",
    top: "50%",
    transform: "translateY(-50%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "4px",
    border: "none",
    background: "transparent",
    color: "#4b5563",
    cursor: "pointer",
  },

  button: {
    width: "100%",
    padding: "12px",
    borderRadius: "10px",
    backgroundColor: "#4f46e5",
    color: "#ffffff",
    border: "none",
    fontWeight: "600",
    cursor: "pointer",
    fontSize: "16px",
    marginTop: "10px",
  },

  buttonDisabled: {
    opacity: 0.65,
    cursor: "not-allowed",
  },
};

export default Login;