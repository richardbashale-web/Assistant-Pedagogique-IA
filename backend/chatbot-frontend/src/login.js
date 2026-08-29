import { useState } from "react";

function Login({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/api/token/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (data.access) {
        setToken(data.access);
        localStorage.setItem("token", data.access);
      } else {
        alert("Login échoué : identifiants incorrects");
      }
    } catch (error) {
      console.error("Erreur de connexion:", error);
      alert("Erreur de connexion au serveur");
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Connexion 🎓</h2>
        <p style={styles.subtitle}>Accédez à votre assistant pédagogique</p>
        
        <div style={styles.inputGroup}>
          <input
            type="text"
            placeholder="Nom d'utilisateur"
            onChange={(e) => setUsername(e.target.value)}
            style={styles.input}
          />
        </div>

        <div style={styles.inputGroup}>
          <input
            type="password"
            placeholder="Mot de passe"
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
            onKeyPress={(e) => e.key === "Enter" && handleLogin()}
          />
        </div>

        <button onClick={handleLogin} style={styles.button}>
          Se connecter
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
    fontFamily: "'Inter', sans-serif"
  },
  card: {
    padding: "40px",
    backgroundColor: "#ffffff",
    borderRadius: "16px",
    boxShadow: "0 10px 25px rgba(0,0,0,0.05)",
    width: "100%",
    maxWidth: "400px",
    boxSizing: "border-box",
    textAlign: "center"
  },
  title: {
    margin: "0 0 10px 0",
    fontSize: "24px",
    fontWeight: "bold",
    color: "#111827"
  },
  subtitle: {
    color: "#6b7280",
    marginBottom: "30px",
    fontSize: "14px"
  },
  inputGroup: {
    marginBottom: "20px"
  },
  input: {
    width: "100%",
    padding: "12px 16px",
    borderRadius: "10px",
    border: "1px solid #d1d5db",
    fontSize: "15px",
    outline: "none",
    boxSizing: "border-box",
    transition: "border-color 0.2s"
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
    transition: "background-color 0.2s",
    marginTop: "10px"
  }
};

export default Login;