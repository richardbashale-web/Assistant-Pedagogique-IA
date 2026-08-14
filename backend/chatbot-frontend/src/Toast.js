import { useState, useCallback } from "react";

/* ── Toast styles injectés en JS pour ne pas modifier index.css ── */
const toastStyles = `
@keyframes toastIn {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes toastOut {
  from { opacity: 1; transform: translateY(0) scale(1); }
  to   { opacity: 0; transform: translateY(-10px) scale(0.95); }
}
.toast-wrapper {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}
.toast-item {
  pointer-events: all;
  min-width: 280px;
  max-width: 400px;
  padding: 14px 18px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  animation: toastIn 0.3s ease forwards;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}
.toast-item.success {
  background: rgba(16, 185, 129, 0.18);
  border: 1px solid rgba(16, 185, 129, 0.4);
  color: #34d399;
}
.toast-item.error {
  background: rgba(239, 68, 68, 0.18);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #f87171;
}
.toast-item.info {
  background: rgba(99, 102, 241, 0.18);
  border: 1px solid rgba(99, 102, 241, 0.4);
  color: #a5b4fc;
}
.toast-close {
  margin-left: auto;
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  font-size: 16px;
  padding: 0 4px;
  line-height: 1;
}
.toast-close:hover { opacity: 1; }
`;

let _styleInjected = false;
function injectStyles() {
  if (_styleInjected) return;
  const el = document.createElement("style");
  el.textContent = toastStyles;
  document.head.appendChild(el);
  _styleInjected = true;
}

const ICONS = { success: "✅", error: "❌", info: "ℹ️" };

/**
 * useToast() — hook qui retourne { toastContainer, showToast }
 *
 * Usage :
 *   const { toastContainer, showToast } = useToast();
 *   showToast("Étudiant ajouté !", "success");
 *   return <div>... {toastContainer}</div>
 */
export function useToast() {
  injectStyles();
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((text, type = "info", duration = 3500) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const dismiss = (id) => setToasts(prev => prev.filter(t => t.id !== id));

  const toastContainer = (
    <div className="toast-wrapper">
      {toasts.map(t => (
        <div key={t.id} className={`toast-item ${t.type}`}>
          <span>{ICONS[t.type] || "ℹ️"}</span>
          <span style={{ flex: 1 }}>{t.text}</span>
          <button className="toast-close" onClick={() => dismiss(t.id)}>×</button>
        </div>
      ))}
    </div>
  );

  return { toastContainer, showToast };
}
