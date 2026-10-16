import { useState } from "react";
import logoUwb from "./logo-uwb.webp";

const API_BASE_URL = process.env.REACT_APP_API_URL;
console.log("API utilisée par React :", API_BASE_URL);

function Login({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      alert("Veuillez remplir tous les champs.");
      return;
    }

    setLoading(true);

    try {
      console.log("=== TEST CONNEXION ===");
      console.log("API_BASE_URL :", API_BASE_URL);
      console.log("URL finale :", `${API_BASE_URL}/api/token/`);
      console.log("Username :", username);

      const response = await fetch(`${API_BASE_URL}/api/token/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      });

      console.log("FETCH TERMINÉ");
      console.log("Status :", response.status);
      console.log("OK :", response.ok);
      console.log(
        "Content-Type :",
        response.headers.get("content-type")
      );

      const text = await response.text();

      console.log("Réponse brute :", text);

      let data;

      try {
        data = JSON.parse(text);
      } catch (e) {
        console.error("La réponse n'est pas du JSON :", e);
        alert(
          "Le serveur a renvoyé une réponse qui n'est pas du JSON."
        );
        return;
      }

      console.log("Réponse JSON :", data);

      if (response.ok && data.access) {
        setToken(data.access);
        localStorage.setItem("token", data.access);

        if (data.refresh) {
          localStorage.setItem("refreshToken", data.refresh);
        }

        console.log("Connexion réussie !");
      } else {
        console.error("Erreur serveur :", data);

        if (response.status === 401) {
          alert("Nom d'utilisateur ou mot de passe incorrect.");
        } else {
          alert(
            data.detail ||
              "Erreur lors de la connexion. Veuillez réessayer."
          );
        }
      }
    } catch (error) {
      console.error("ERREUR FETCH :", error);
      console.error("Message :", error.message);

      alert(
        "Impossible de contacter le serveur : " + error.message
      );
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
        <h2 style={styles.title}>Connexion </h2>

        <p style={styles.subtitle}>
          Accédez à votre assistant pédagogique
        </p>

        <div style={styles.inputGroup}>
          <input
            type="text"
            placeholder="Nom d'utilisateur"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={styles.input}
            disabled={loading}
          />
        </div>

        <div style={styles.inputGroup}>
          <input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleLogin();
              }
            }}
          />
        </div>

        <button
          onClick={handleLogin}
          style={styles.button}
          disabled={loading}
        >
          {loading ? "Connexion..." : "Se connecter"}
        </button>
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
    backgroundImage: "linear-gradient(135deg, rgba(239,246,255,0.88), rgba(248,250,252,0.94))",
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
};

export default Login;
