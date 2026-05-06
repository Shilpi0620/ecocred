import { useEffect, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000").replace(/\/$/, "");

const styles = `
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');

* { box-sizing: border-box; }

:root {
  --ink: #1a1208;
  --ink-soft: #43311a;
  --cream: #faf6ef;
  --paper: #f2ead8;
  --sand: #dfcfb3;
  --leaf: #2f6c3f;
  --leaf-soft: #5ba56d;
  --amber: #c77924;
  --sky: #2958a6;
  --rose: #b94c4c;
  --white: #ffffff;
  --shadow: rgba(29, 18, 8, 0.08);
  --shadow-strong: rgba(29, 18, 8, 0.16);
}

html, body, #root {
  margin: 0;
  min-height: 100%;
  background: var(--cream);
  color: var(--ink);
  font-family: 'Outfit', sans-serif;
}

body {
  background:
    radial-gradient(circle at top left, rgba(47, 108, 63, 0.08), transparent 32%),
    radial-gradient(circle at top right, rgba(199, 121, 36, 0.08), transparent 28%),
    var(--cream);
}

.app-shell { min-height: 100vh; }

.role-screen {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px;
}

.role-card {
  width: min(1180px, 100%);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(223, 207, 179, 0.8);
  border-radius: 28px;
  box-shadow: 0 28px 80px var(--shadow);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.role-hero {
  padding: 56px 56px 36px;
  border-bottom: 1px solid rgba(223, 207, 179, 0.8);
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--leaf);
  font-weight: 700;
}

.brand {
  margin: 10px 0 8px;
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(44px, 7vw, 72px);
  line-height: 0.95;
}

.brand em {
  font-style: italic;
  color: var(--leaf);
}

.intro {
  max-width: 760px;
  color: var(--ink-soft);
  font-size: 18px;
  line-height: 1.7;
}

.split-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(340px, 0.8fr);
  gap: 24px;
  padding: 36px 56px 40px;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.picker {
  background: var(--white);
  border: 1px solid rgba(223, 207, 179, 0.9);
  border-radius: 22px;
  padding: 24px;
  text-align: left;
}

.picker-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 24px;
  margin-bottom: 14px;
}

.picker-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 28px;
  margin: 0 0 8px;
}

.picker-text {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.65;
}

.auth-card {
  background: var(--white);
  border: 1px solid rgba(223, 207, 179, 0.95);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 12px 32px var(--shadow);
}

.auth-tabs {
  display: inline-flex;
  gap: 8px;
  margin-bottom: 18px;
  padding: 6px;
  border-radius: 999px;
  background: var(--paper);
}

.auth-tab {
  border: 0;
  background: transparent;
  border-radius: 999px;
  padding: 10px 16px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  color: var(--ink-soft);
}

.auth-tab.active {
  background: var(--ink);
  color: var(--white);
}

.auth-title {
  margin: 0 0 8px;
  font-family: 'Cormorant Garamond', serif;
  font-size: 34px;
}

.auth-copy {
  margin: 0 0 18px;
  color: var(--ink-soft);
  line-height: 1.65;
}

.auth-form {
  display: grid;
  gap: 12px;
}

.auth-form label {
  display: grid;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-soft);
}

.auth-form input,
.auth-form select,
.auth-form textarea {
  width: 100%;
  border: 1px solid rgba(223, 207, 179, 1);
  background: #fffdfa;
  border-radius: 14px;
  padding: 12px 14px;
  font: inherit;
  color: var(--ink);
}

.auth-form textarea {
  min-height: 96px;
  resize: vertical;
}

.auth-form input[type="file"] {
  padding: 10px 12px;
  background: var(--paper);
}

.auth-error {
  color: var(--rose);
  font-size: 14px;
  line-height: 1.5;
}

.auth-success {
  color: var(--leaf);
  font-size: 14px;
  line-height: 1.5;
}

.auth-meta {
  margin-top: 14px;
  color: var(--ink-soft);
  font-size: 13px;
  line-height: 1.6;
}

.status-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  border-top: 1px solid rgba(223, 207, 179, 0.8);
  background: rgba(242, 234, 216, 0.7);
  color: var(--ink-soft);
  font-size: 14px;
}

.status-inline {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.status-dot.ok { background: var(--leaf); }
.status-dot.bad { background: var(--rose); }
.status-dot.pending { background: var(--amber); }

.dashboard {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  min-height: 100vh;
}

.sidebar {
  background: var(--ink);
  color: var(--cream);
  padding: 28px 18px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sidebar-brand {
  padding: 0 12px;
}

.sidebar-brand h1 {
  margin: 0;
  font-family: 'Cormorant Garamond', serif;
  font-size: 36px;
}

.sidebar-brand em {
  color: var(--leaf-soft);
  font-style: italic;
}

.role-pill {
  display: inline-flex;
  margin-top: 10px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 700;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-button {
  border: 0;
  background: transparent;
  color: rgba(255, 255, 255, 0.72);
  text-align: left;
  border-radius: 14px;
  padding: 12px 14px;
  font: inherit;
  cursor: pointer;
}

.nav-button.active {
  background: rgba(91, 165, 109, 0.18);
  color: var(--white);
}

.nav-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--white);
}

.switch-button {
  margin-top: auto;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.05);
  color: var(--cream);
  border-radius: 14px;
  padding: 12px 14px;
  font: inherit;
  cursor: pointer;
}

.main { min-width: 0; }

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  background: rgba(250, 246, 239, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(223, 207, 179, 0.7);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 28px;
}

.topbar h2 {
  margin: 0;
  font-family: 'Cormorant Garamond', serif;
  font-size: 34px;
}

.stat-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip {
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid rgba(223, 207, 179, 0.9);
  background: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  font-weight: 600;
}

.content { padding: 28px; }

.hero {
  background: linear-gradient(135deg, var(--ink), #2f2413 60%, #3e5e30 120%);
  color: var(--white);
  border-radius: 28px;
  padding: 32px;
  box-shadow: 0 24px 60px var(--shadow);
}

.hero small {
  display: inline-block;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: rgba(255, 255, 255, 0.7);
}

.hero h3 {
  margin: 0 0 10px;
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(34px, 4vw, 54px);
  line-height: 1;
}

.hero p {
  margin: 0;
  max-width: 760px;
  color: rgba(255, 255, 255, 0.78);
  line-height: 1.7;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 26px;
}

.hero-stat {
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
}

.hero-stat strong {
  display: block;
  font-family: 'Cormorant Garamond', serif;
  font-size: 32px;
}

.section { margin-top: 28px; }

.section h4 {
  margin: 0 0 14px;
  font-family: 'Cormorant Garamond', serif;
  font-size: 30px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.card {
  background: var(--white);
  border: 1px solid rgba(223, 207, 179, 0.95);
  border-radius: 22px;
  padding: 20px;
  box-shadow: 0 8px 24px var(--shadow);
}

.card-label {
  color: var(--ink-soft);
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-weight: 700;
}

.card-value {
  margin-top: 10px;
  font-family: 'Cormorant Garamond', serif;
  font-size: 34px;
}

.card-note {
  margin-top: 8px;
  color: var(--ink-soft);
  font-size: 14px;
}

.panel {
  background: var(--white);
  border: 1px solid rgba(223, 207, 179, 0.95);
  border-radius: 22px;
  box-shadow: 0 8px 24px var(--shadow);
  overflow: hidden;
}

.panel-pad { padding: 22px; }

.table-wrap { overflow-x: auto; }

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 16px 18px;
  text-align: left;
  border-bottom: 1px solid rgba(223, 207, 179, 0.7);
}

th {
  background: var(--paper);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

tr:last-child td { border-bottom: 0; }

.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.badge.green { background: rgba(47, 108, 63, 0.1); color: var(--leaf); }
.badge.amber { background: rgba(199, 121, 36, 0.12); color: var(--amber); }
.badge.blue { background: rgba(41, 88, 166, 0.11); color: var(--sky); }
.badge.rose { background: rgba(185, 76, 76, 0.11); color: var(--rose); }

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.helper-text {
  margin: 0;
  color: var(--ink-soft);
  font-size: 14px;
  line-height: 1.6;
}

.btn {
  border: 0;
  border-radius: 14px;
  padding: 12px 18px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.btn.primary { background: var(--leaf); color: var(--white); }
.btn.outline { background: transparent; border: 1px solid rgba(223, 207, 179, 1); color: var(--ink); }

.btn:disabled {
  opacity: 0.65;
  cursor: wait;
}

.list {
  display: grid;
  gap: 14px;
}

.list-item {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 20px;
  background: var(--white);
  border: 1px solid rgba(223, 207, 179, 0.95);
  border-radius: 20px;
  box-shadow: 0 8px 24px var(--shadow);
}

.list-item h5 {
  margin: 0 0 6px;
  font-size: 18px;
}

.list-item p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

.notification {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 20;
  max-width: 360px;
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--ink);
  color: var(--white);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
}

.empty-text {
  color: var(--ink-soft);
  line-height: 1.7;
  margin: 0;
}

.loading-text {
  color: var(--ink-soft);
  margin: 0;
}

@media (max-width: 1000px) {
  .dashboard { grid-template-columns: 1fr; }
  .sidebar { height: auto; }
  .role-grid,
  .card-grid,
  .hero-stats,
  .split-grid,
  .field-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .role-screen,
  .content,
  .topbar,
  .role-hero,
  .split-grid {
    padding-left: 18px;
    padding-right: 18px;
  }

  .role-grid,
  .card-grid,
  .hero-stats,
  .split-grid,
  .field-grid {
    grid-template-columns: 1fr;
  }

  .topbar,
  .status-banner,
  .list-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
`;

const roleConfig = {
  user: {
    label: "User",
    icon: "U",
    accent: "rgba(47, 108, 63, 0.12)",
    pages: [
      { id: "overview", label: "Overview" },
      { id: "submit", label: "Submit Waste" },
      { id: "wallet", label: "Wallet" },
      { id: "guides", label: "Guides" },
    ],
  },
  aggregator: {
    label: "Aggregator",
    icon: "A",
    accent: "rgba(199, 121, 36, 0.12)",
    pages: [
      { id: "overview", label: "Overview" },
      { id: "jobs", label: "Assignments" },
      { id: "earnings", label: "Earnings" },
    ],
  },
  recycler: {
    label: "Recycler",
    icon: "R",
    accent: "rgba(41, 88, 166, 0.12)",
    pages: [
      { id: "overview", label: "Overview" },
      { id: "inventory", label: "Inventory" },
      { id: "revenue", label: "Revenue" },
    ],
  },
};

const guides = [
  {
    title: "How to sort household plastic",
    text: "Rinse bottles, separate caps where possible, and keep mixed waste out of the bag before pickup.",
  },
  {
    title: "When an image goes to manual review",
    text: "Close shots, bright lighting, and one material per photo help the verification model approve faster.",
  },
  {
    title: "How wallet payouts work",
    text: "Approved submissions add credit to your wallet, and withdrawals can be batched to reduce failed transfers.",
  },
];

function summarizeError(error) {
  if (!error) return "Something went wrong.";
  if (typeof error === "string") return error;
  if (Array.isArray(error)) return error.join(" ");
  if (typeof error === "object") {
    return Object.entries(error)
      .map(([key, value]) => `${key}: ${summarizeError(value)}`)
      .join(" | ");
  }
  return "Something went wrong.";
}

function formatCurrency(value) {
  const amount = Number(value || 0);
  return `INR ${amount.toLocaleString()}`;
}

function formatNumber(value) {
  const amount = Number(value || 0);
  return amount.toLocaleString();
}

function formatDate(value) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return value;
  }
}

function toResults(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.results)) return payload.results;
  return [];
}

async function fetchJson(path, token) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : undefined,
  });

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!response.ok) {
    throw new Error(summarizeError(data) || `Request failed: ${response.status}`);
  }

  return data;
}

async function sendJson(path, token, method, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!response.ok) {
    throw new Error(summarizeError(data) || `Request failed: ${response.status}`);
  }

  return data;
}

async function sendFormData(path, token, method, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: payload,
  });

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!response.ok) {
    throw new Error(summarizeError(data) || `Request failed: ${response.status}`);
  }

  return data;
}

function SectionTitle({ title }) {
  return (
    <div className="section">
      <h4>{title}</h4>
    </div>
  );
}

function InfoPanel({ title, children }) {
  return (
    <>
      <SectionTitle title={title} />
      <div className="panel">
        <div className="panel-pad">{children}</div>
      </div>
    </>
  );
}

function AuthPanel({ authMode, setAuthMode, onAuthSuccess, backendStatus, notify }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    phone: "",
    role: "user",
  });

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const endpoint = authMode === "login" ? "/api/auth/login/" : "/api/auth/register/";
      const payload =
        authMode === "login"
          ? {
              username: form.username,
              password: form.password,
            }
          : {
              username: form.username,
              email: form.email,
              password: form.password,
              confirm_password: form.confirmPassword,
              phone: form.phone,
              role: form.role,
            };

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(summarizeError(data));
      }

      localStorage.setItem("ecocred_auth", JSON.stringify(data));
      setSuccess(authMode === "login" ? "Signed in successfully." : "Account created successfully.");
      notify(authMode === "login" ? "Backend login succeeded." : "Backend registration succeeded.");
      onAuthSuccess(data);
    } catch (submissionError) {
      setError(submissionError.message || "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-tabs">
        <button className={`auth-tab ${authMode === "login" ? "active" : ""}`} onClick={() => setAuthMode("login")} type="button">
          Login
        </button>
        <button className={`auth-tab ${authMode === "register" ? "active" : ""}`} onClick={() => setAuthMode("register")} type="button">
          Register
        </button>
      </div>

      <h3 className="auth-title">{authMode === "login" ? "Sign in" : "Create account"}</h3>
      <p className="auth-copy">
        {authMode === "login"
          ? "Use your backend account to load live data into the correct workspace."
          : "Create a backend user first so the frontend can switch into the matching role automatically."}
      </p>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Username
          <input value={form.username} onChange={(event) => updateField("username", event.target.value)} required />
        </label>

        {authMode === "register" ? (
          <>
            <label>
              Email
              <input type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} required />
            </label>
            <label>
              Phone
              <input value={form.phone} onChange={(event) => updateField("phone", event.target.value)} />
            </label>
            <label>
              Role
              <select value={form.role} onChange={(event) => updateField("role", event.target.value)}>
                <option value="user">User</option>
                <option value="aggregator">Aggregator</option>
                <option value="recycler">Recycler</option>
              </select>
            </label>
          </>
        ) : null}

        <label>
          Password
          <input type="password" value={form.password} onChange={(event) => updateField("password", event.target.value)} required />
        </label>

        {authMode === "register" ? (
          <label>
            Confirm password
            <input
              type="password"
              value={form.confirmPassword}
              onChange={(event) => updateField("confirmPassword", event.target.value)}
              required
            />
          </label>
        ) : null}

        {error ? <div className="auth-error">{error}</div> : null}
        {success ? <div className="auth-success">{success}</div> : null}

        <button className="btn primary" type="submit" disabled={loading || !backendStatus.ok}>
          {loading ? "Submitting..." : authMode === "login" ? "Login with backend" : "Register with backend"}
        </button>
      </form>

      <div className="auth-meta">
        Backend status: {backendStatus.loading ? "checking..." : backendStatus.ok ? "connected" : "offline"}
      </div>
    </div>
  );
}

function UserPage({ page, live, notify, auth, onRefresh }) {
  const profile = live.profile || {};
  const summary = live.userSummary || {};
  const submissions = toResults(live.submissions);
  const transactions = toResults(live.transactions);
  const withdrawals = toResults(live.withdrawals);
  const tiers = toResults(live.tiers);
  const leaderboard = toResults(live.leaderboard);
  const materials = toResults(live.materials);
  const [submissionForm, setSubmissionForm] = useState({
    material_id: "",
    weight_kg: "",
    notes: "",
    preferred_pickup_date: "",
    image: null,
  });
  const [withdrawForm, setWithdrawForm] = useState({
    amount: "",
    bank_name: "GTBank",
    account_number: "",
    account_name: "",
  });
  const [submittingWaste, setSubmittingWaste] = useState(false);
  const [submittingWithdrawal, setSubmittingWithdrawal] = useState(false);

  function updateSubmissionField(key, value) {
    setSubmissionForm((current) => ({ ...current, [key]: value }));
  }

  function updateWithdrawalField(key, value) {
    setWithdrawForm((current) => ({ ...current, [key]: value }));
  }

  async function handleWasteSubmit(event) {
    event.preventDefault();
    const selectedMaterialId = submissionForm.material_id || (materials[0]?.id ? String(materials[0].id) : "");

    if (!selectedMaterialId) {
      notify("Pick a material before submitting waste.");
      return;
    }

    if (!submissionForm.image) {
      notify("Add an image before submitting waste.");
      return;
    }

    setSubmittingWaste(true);
    try {
      const payload = new FormData();
      payload.append("material_id", selectedMaterialId);
      payload.append("image", submissionForm.image);
      payload.append("weight_kg", submissionForm.weight_kg);
      payload.append("notes", submissionForm.notes);
      if (submissionForm.preferred_pickup_date) {
        payload.append("preferred_pickup_date", submissionForm.preferred_pickup_date);
      }

      await sendFormData("/api/waste/submissions/", auth.access, "POST", payload);
      setSubmissionForm({
        material_id: materials[0]?.id ? String(materials[0].id) : "",
        weight_kg: "",
        notes: "",
        preferred_pickup_date: "",
        image: null,
      });
      notify("Waste submission created successfully.");
      onRefresh();
    } catch (error) {
      notify(error.message || "Could not create submission.");
    } finally {
      setSubmittingWaste(false);
    }
  }

  async function handleWithdrawalSubmit(event) {
    event.preventDefault();
    setSubmittingWithdrawal(true);

    try {
      await sendJson("/api/rewards/withdraw/", auth.access, "POST", {
        amount: withdrawForm.amount,
        bank_name: withdrawForm.bank_name,
        account_number: withdrawForm.account_number,
        account_name: withdrawForm.account_name,
      });
      setWithdrawForm({
        amount: "",
        bank_name: "GTBank",
        account_number: "",
        account_name: "",
      });
      notify("Withdrawal request submitted.");
      onRefresh();
    } catch (error) {
      notify(error.message || "Could not submit withdrawal.");
    } finally {
      setSubmittingWithdrawal(false);
    }
  }

  if (page === "submit") {
    return (
      <>
        <InfoPanel title="Submit Waste">
          {materials.length ? (
            <>
              <p className="helper-text">
                Choose a material, add the pickup details, and upload a clear image. The submission is posted directly to the backend.
              </p>
              <form className="auth-form" onSubmit={handleWasteSubmit} style={{ marginTop: 16 }}>
                <div className="field-grid">
                  <label>
                    Material
                    <select
                      value={submissionForm.material_id || (materials[0]?.id ? String(materials[0].id) : "")}
                      onChange={(event) => updateSubmissionField("material_id", event.target.value)}
                      required
                    >
                      {materials.map((material) => (
                        <option key={material.id} value={material.id}>
                          {material.name} - {formatCurrency(material.cash_per_kg)}/kg
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Weight (kg)
                    <input
                      type="number"
                      min="0.1"
                      step="0.01"
                      value={submissionForm.weight_kg}
                      onChange={(event) => updateSubmissionField("weight_kg", event.target.value)}
                      required
                    />
                  </label>
                </div>

                <div className="field-grid">
                  <label>
                    Preferred pickup date
                    <input
                      type="date"
                      value={submissionForm.preferred_pickup_date}
                      onChange={(event) => updateSubmissionField("preferred_pickup_date", event.target.value)}
                    />
                  </label>
                  <label>
                    Waste image
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(event) => updateSubmissionField("image", event.target.files?.[0] || null)}
                      required
                    />
                  </label>
                </div>

                <label>
                  Notes
                  <textarea
                    value={submissionForm.notes}
                    onChange={(event) => updateSubmissionField("notes", event.target.value)}
                    placeholder="Add pickup notes, gate instructions, or anything helpful for verification."
                  />
                </label>

                <button className="btn primary" type="submit" disabled={submittingWaste}>
                  {submittingWaste ? "Submitting..." : "Submit waste"}
                </button>
              </form>

              <SectionTitle title="Active Materials" />
              <div className="list">
                {materials.map((material) => (
                  <div className="list-item" key={material.id}>
                    <div>
                      <h5>{material.name}</h5>
                      <p>
                        {formatNumber(material.points_per_kg)} pts per kg | {formatCurrency(material.cash_per_kg)} per kg
                      </p>
                    </div>
                    <span className="badge blue">{material.slug}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="empty-text">Materials are still loading. Refresh once the backend has seeded them.</p>
          )}
        </InfoPanel>
      </>
    );
  }

  if (page === "wallet") {
    return (
      <>
        <SectionTitle title="Wallet and Credits" />
        <div className="card-grid">
          <div className="card">
            <div className="card-label">Available balance</div>
            <div className="card-value">{formatCurrency(summary.wallet_balance)}</div>
            <div className="card-note">Pulled from reward summary</div>
          </div>
          <div className="card">
            <div className="card-label">Total points</div>
            <div className="card-value">{formatNumber(summary.total_points)}</div>
            <div className="card-note">Current reward score</div>
          </div>
          <div className="card">
            <div className="card-label">This month</div>
            <div className="card-value">{formatCurrency(summary.cash_this_month)}</div>
            <div className="card-note">Month-to-date reward value</div>
          </div>
          <div className="card">
            <div className="card-label">Current tier</div>
            <div className="card-value">{summary.current_tier?.name || "No tier"}</div>
            <div className="card-note">
              {summary.points_to_next != null ? `${summary.points_to_next} points to next tier` : "No next tier available yet"}
            </div>
          </div>
        </div>

        <SectionTitle title="Transactions" />
        <div className="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Description</th>
                <th>Points</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions.length ? (
                transactions.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDate(item.created_at)}</td>
                    <td>{item.transaction_type}</td>
                    <td>{item.description}</td>
                    <td>{formatNumber(item.points)}</td>
                    <td>{formatCurrency(item.amount)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5">No live transactions yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <InfoPanel title="Withdraw Funds">
          <p className="helper-text">
            This form posts directly to the backend withdrawal endpoint. In local development it uses a dev reference when Paystack is not configured.
          </p>
          <form className="auth-form" onSubmit={handleWithdrawalSubmit} style={{ marginTop: 16 }}>
            <div className="field-grid">
              <label>
                Amount
                <input
                  type="number"
                  min="1000"
                  step="0.01"
                  value={withdrawForm.amount}
                  onChange={(event) => updateWithdrawalField("amount", event.target.value)}
                  required
                />
              </label>
              <label>
                Bank
                <select value={withdrawForm.bank_name} onChange={(event) => updateWithdrawalField("bank_name", event.target.value)}>
                  <option value="GTBank">GTBank</option>
                  <option value="First Bank">First Bank</option>
                  <option value="Access Bank">Access Bank</option>
                  <option value="Zenith Bank">Zenith Bank</option>
                  <option value="UBA">UBA</option>
                </select>
              </label>
            </div>

            <div className="field-grid">
              <label>
                Account number
                <input
                  value={withdrawForm.account_number}
                  onChange={(event) => updateWithdrawalField("account_number", event.target.value)}
                  required
                />
              </label>
              <label>
                Account name
                <input
                  value={withdrawForm.account_name}
                  onChange={(event) => updateWithdrawalField("account_name", event.target.value)}
                  required
                />
              </label>
            </div>

            <button className="btn primary" type="submit" disabled={submittingWithdrawal}>
              {submittingWithdrawal ? "Submitting..." : "Request withdrawal"}
            </button>
          </form>
        </InfoPanel>

        <SectionTitle title="Withdrawal History" />
        <div className="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Amount</th>
                <th>Bank</th>
                <th>Account</th>
                <th>Status</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              {withdrawals.length ? (
                withdrawals.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDate(item.created_at)}</td>
                    <td>{formatCurrency(item.amount)}</td>
                    <td>{item.bank_name}</td>
                    <td>{item.account_number}</td>
                    <td><span className="badge amber">{item.status}</span></td>
                    <td>{item.paystack_reference || "-"}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6">No withdrawals yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </>
    );
  }

  if (page === "guides") {
    return (
      <>
        <SectionTitle title="Recycling Guides" />
        <div className="list">
          {guides.map((guide) => (
            <div className="list-item" key={guide.title}>
              <div>
                <h5>{guide.title}</h5>
                <p>{guide.text}</p>
              </div>
              <div className="badge blue">Guide</div>
            </div>
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <div className="hero">
        <small>User workspace</small>
        <h3>Welcome back, {profile.username || "user"}.</h3>
        <p>
          This dashboard is now pulling its profile, summary, submissions, and leaderboard data from the Django backend.
        </p>
        <div className="hero-stats">
          <div className="hero-stat">
            <strong>{formatNumber(summary.total_points)}</strong>
            <span>total points</span>
          </div>
          <div className="hero-stat">
            <strong>{formatCurrency(summary.wallet_balance)}</strong>
            <span>wallet balance</span>
          </div>
          <div className="hero-stat">
            <strong>{formatNumber(summary.total_kg_recycled)} kg</strong>
            <span>recycled so far</span>
          </div>
        </div>
      </div>

      <SectionTitle title="Live Summary" />
      <div className="card-grid">
        <div className="card">
          <div className="card-label">This week</div>
          <div className="card-value">{formatNumber(summary.points_this_week)} pts</div>
          <div className="card-note">{formatCurrency(summary.cash_this_week)} earned this week</div>
        </div>
        <div className="card">
          <div className="card-label">This month</div>
          <div className="card-value">{formatNumber(summary.points_this_month)} pts</div>
          <div className="card-note">{formatCurrency(summary.cash_this_month)} earned this month</div>
        </div>
        <div className="card">
          <div className="card-label">Current tier</div>
          <div className="card-value">{summary.current_tier?.name || "No tier"}</div>
          <div className="card-note">{tiers.length ? `${tiers.length} live tiers available` : "No tiers configured yet"}</div>
        </div>
        <div className="card">
          <div className="card-label">Leaderboard rank</div>
          <div className="card-value">
            {leaderboard.findIndex((entry) => entry.id === profile.id) >= 0
              ? `#${leaderboard.findIndex((entry) => entry.id === profile.id) + 1}`
              : "-"}
          </div>
          <div className="card-note">{leaderboard.length} live users in the board</div>
        </div>
      </div>

      <SectionTitle title="Recent Submissions" />
      <div className="panel table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Material</th>
              <th>Weight</th>
              <th>Status</th>
              <th>Reward</th>
            </tr>
          </thead>
          <tbody>
            {submissions.length ? (
              submissions.map((submission) => (
                <tr key={submission.id}>
                  <td>{formatDate(submission.created_at)}</td>
                  <td>{submission.material_name || "-"}</td>
                  <td>{formatNumber(submission.weight_kg)} kg</td>
                  <td><span className="badge blue">{submission.status}</span></td>
                  <td>{formatCurrency(submission.cash_awarded)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5">No submissions yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <SectionTitle title="Leaderboard" />
      <div className="list">
        {leaderboard.length ? (
          leaderboard.map((entry, index) => (
            <div className="list-item" key={entry.id}>
              <div>
                <h5>
                  #{index + 1} {entry.username}
                </h5>
                <p>{formatNumber(entry.total_kg_recycled)} kg recycled</p>
              </div>
              <div className="badge green">{formatNumber(entry.total_points)} pts</div>
            </div>
          ))
        ) : (
          <div className="list-item">
            <p className="empty-text">Leaderboard is empty right now.</p>
          </div>
        )}
      </div>
    </>
  );
}

function AggregatorPage({ page, live, auth, onRefresh, notify }) {
  const materials = toResults(live.materials);
  const profile = live.profile || {};
  const jobs = toResults(live.jobs);
  const commissions = toResults(live.commissions);
  const summary = live.aggregatorSummary || {};
  const [form, setForm] = useState({
    company_name: profile.company_name || "",
    address: profile.address || "",
    latitude: profile.latitude || "",
    longitude: profile.longitude || "",
    service_radius_km: profile.service_radius_km || 10,
    commission_rate_pct: profile.commission_rate_pct || 8,
    accepted_material_ids: (profile.accepted_materials || []).map((item) => item.id),
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      company_name: profile.company_name || "",
      address: profile.address || "",
      latitude: profile.latitude || "",
      longitude: profile.longitude || "",
      service_radius_km: profile.service_radius_km || 10,
      commission_rate_pct: profile.commission_rate_pct || 8,
      accepted_material_ids: (profile.accepted_materials || []).map((item) => item.id),
    });
  }, [
    profile.company_name,
    profile.address,
    profile.latitude,
    profile.longitude,
    profile.service_radius_km,
    profile.commission_rate_pct,
    profile.accepted_materials,
  ]);

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSave(event) {
    event.preventDefault();
    setSaving(true);
    try {
      await sendJson("/api/aggregators/profile/", auth.access, "PATCH", {
        ...form,
        latitude: form.latitude || null,
        longitude: form.longitude || null,
        accepted_material_ids: form.accepted_material_ids,
      });
      notify("Aggregator profile updated.");
      onRefresh();
    } catch (error) {
      notify(error.message || "Could not update aggregator profile.");
    } finally {
      setSaving(false);
    }
  }

  if (live.roleError) {
    return (
      <InfoPanel title="Aggregator Setup">
        <p className="empty-text">{live.roleError}</p>
      </InfoPanel>
    );
  }

  if (page === "jobs") {
    return (
      <>
        <SectionTitle title="Assignments" />
        <div className="list">
          {jobs.length ? (
            jobs.map((job) => (
              <div className="list-item" key={job.id}>
                <div>
                  <h5>{job.submission?.material_name || "Material pending"}</h5>
                  <p>
                    Weight: {formatNumber(job.submission?.weight_kg)} kg | Status: {job.status}
                  </p>
                </div>
                <div className="badge blue">{job.distance_km || "-"} km</div>
              </div>
            ))
          ) : (
            <div className="list-item">
              <p className="empty-text">No live jobs assigned yet.</p>
            </div>
          )}
        </div>
      </>
    );
  }

  if (page === "earnings") {
    return (
      <>
        <SectionTitle title="Commission Summary" />
        <div className="card-grid">
          <div className="card">
            <div className="card-label">Total earned</div>
            <div className="card-value">{formatCurrency(summary.total_earned)}</div>
            <div className="card-note">Live aggregator earnings</div>
          </div>
          <div className="card">
            <div className="card-label">This month</div>
            <div className="card-value">{formatCurrency(summary.this_month)}</div>
            <div className="card-note">Current month total</div>
          </div>
          <div className="card">
            <div className="card-label">This week</div>
            <div className="card-value">{formatCurrency(summary.this_week)}</div>
            <div className="card-note">Current week total</div>
          </div>
          <div className="card">
            <div className="card-label">Pending</div>
            <div className="card-value">{formatCurrency(summary.pending)}</div>
            <div className="card-note">{commissions.length} live commission rows</div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="hero">
        <small>Aggregator workspace</small>
        <h3>{profile.company_name || "Aggregator profile"}</h3>
        <p>These cards are now reading from the live aggregator summary and job endpoints.</p>
        <div className="hero-stats">
          <div className="hero-stat">
            <strong>{jobs.length}</strong>
            <span>live jobs</span>
          </div>
          <div className="hero-stat">
            <strong>{formatCurrency(summary.total_earned)}</strong>
            <span>total earned</span>
          </div>
          <div className="hero-stat">
            <strong>{formatNumber(summary.total_kg)} kg</strong>
            <span>collected total</span>
          </div>
        </div>
      </div>

      <InfoPanel title="Business Profile">
        <p className="helper-text">
          This setup form updates the live aggregator profile. Once it is filled in, the same account can receive real pickup jobs and earnings.
        </p>
        <form className="auth-form" onSubmit={handleSave} style={{ marginTop: 16 }}>
          <div className="field-grid">
            <label>
              Company name
              <input value={form.company_name} onChange={(event) => updateField("company_name", event.target.value)} required />
            </label>
            <label>
              Service radius (km)
              <input
                type="number"
                min="1"
                value={form.service_radius_km}
                onChange={(event) => updateField("service_radius_km", event.target.value)}
                required
              />
            </label>
          </div>

          <div className="field-grid">
            <label>
              Latitude
              <input value={form.latitude} onChange={(event) => updateField("latitude", event.target.value)} />
            </label>
            <label>
              Longitude
              <input value={form.longitude} onChange={(event) => updateField("longitude", event.target.value)} />
            </label>
          </div>

          <div className="field-grid">
            <label>
              Commission rate (%)
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.commission_rate_pct}
                onChange={(event) => updateField("commission_rate_pct", event.target.value)}
                required
              />
            </label>
            <label>
              Accepted materials
              <select
                multiple
                value={form.accepted_material_ids.map(String)}
                onChange={(event) =>
                  updateField(
                    "accepted_material_ids",
                    Array.from(event.target.selectedOptions, (option) => Number(option.value)),
                  )
                }
              >
                {materials.map((material) => (
                  <option key={material.id} value={material.id}>
                    {material.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label>
            Business address
            <textarea value={form.address} onChange={(event) => updateField("address", event.target.value)} required />
          </label>

          <button className="btn primary" type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save aggregator profile"}
          </button>
        </form>
      </InfoPanel>
    </>
  );
}

function RecyclerPage({ page, live, auth, onRefresh, notify }) {
  const materials = toResults(live.materials);
  const inventory = toResults(live.inventory);
  const batches = toResults(live.batches);
  const shipments = toResults(live.shipments);
  const summary = live.recyclerSummary || {};
  const profile = live.profile || {};
  const [form, setForm] = useState({
    company_name: profile.company_name || "",
    license_number: profile.license_number || "",
    address: profile.address || "",
    accepted_material_ids: (profile.accepted_materials || []).map((item) => item.id),
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      company_name: profile.company_name || "",
      license_number: profile.license_number || "",
      address: profile.address || "",
      accepted_material_ids: (profile.accepted_materials || []).map((item) => item.id),
    });
  }, [profile.company_name, profile.license_number, profile.address, profile.accepted_materials]);

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSave(event) {
    event.preventDefault();
    setSaving(true);
    try {
      await sendJson("/api/recyclers/profile/", auth.access, "PATCH", {
        ...form,
        accepted_material_ids: form.accepted_material_ids,
      });
      notify("Recycler profile updated.");
      onRefresh();
    } catch (error) {
      notify(error.message || "Could not update recycler profile.");
    } finally {
      setSaving(false);
    }
  }

  if (live.roleError) {
    return (
      <InfoPanel title="Recycler Setup">
        <p className="empty-text">{live.roleError}</p>
      </InfoPanel>
    );
  }

  if (page === "inventory") {
    return (
      <>
        <SectionTitle title="Inventory" />
        <div className="list">
          {inventory.length ? (
            inventory.map((item) => (
              <div className="list-item" key={item.id}>
                <div>
                  <h5>{item.material_name}</h5>
                  <p>{formatCurrency(item.cash_per_kg)} per kg</p>
                </div>
                <div className="badge blue">{formatNumber(item.quantity_kg)} kg</div>
              </div>
            ))
          ) : (
            <div className="list-item">
              <p className="empty-text">No live inventory yet.</p>
            </div>
          )}
        </div>
      </>
    );
  }

  if (page === "revenue") {
    return (
      <>
        <SectionTitle title="Revenue Overview" />
        <div className="card-grid">
          <div className="card">
            <div className="card-label">Total revenue</div>
            <div className="card-value">{formatCurrency(summary.total_revenue)}</div>
            <div className="card-note">Live recycler revenue</div>
          </div>
          <div className="card">
            <div className="card-label">This month</div>
            <div className="card-value">{formatCurrency(summary.this_month)}</div>
            <div className="card-note">Month-to-date total</div>
          </div>
          <div className="card">
            <div className="card-label">Processed</div>
            <div className="card-value">{formatNumber(summary.total_kg_processed)} kg</div>
            <div className="card-note">{batches.length} live batches</div>
          </div>
          <div className="card">
            <div className="card-label">Margin</div>
            <div className="card-value">{summary.margin_pct || 0}%</div>
            <div className="card-note">{shipments.length} live shipments</div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="hero">
        <small>Recycler workspace</small>
        <h3>{profile.company_name || "Recycler profile"}</h3>
        <p>These panels now read from the live recycler profile, inventory, batch, shipment, and revenue endpoints.</p>
        <div className="hero-stats">
          <div className="hero-stat">
            <strong>{inventory.length}</strong>
            <span>inventory rows</span>
          </div>
          <div className="hero-stat">
            <strong>{shipments.length}</strong>
            <span>shipments</span>
          </div>
          <div className="hero-stat">
            <strong>{formatCurrency(summary.total_revenue)}</strong>
            <span>total revenue</span>
          </div>
        </div>
      </div>

      <InfoPanel title="Facility Profile">
        <p className="helper-text">
          This profile form writes to the live recycler endpoint, so the account can be completed without leaving the frontend.
        </p>
        <form className="auth-form" onSubmit={handleSave} style={{ marginTop: 16 }}>
          <div className="field-grid">
            <label>
              Company name
              <input value={form.company_name} onChange={(event) => updateField("company_name", event.target.value)} required />
            </label>
            <label>
              License number
              <input value={form.license_number} onChange={(event) => updateField("license_number", event.target.value)} required />
            </label>
          </div>

          <label>
            Accepted materials
            <select
              multiple
              value={form.accepted_material_ids.map(String)}
              onChange={(event) =>
                updateField(
                  "accepted_material_ids",
                  Array.from(event.target.selectedOptions, (option) => Number(option.value)),
                )
              }
            >
              {materials.map((material) => (
                <option key={material.id} value={material.id}>
                  {material.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Facility address
            <textarea value={form.address} onChange={(event) => updateField("address", event.target.value)} required />
          </label>

          <button className="btn primary" type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save recycler profile"}
          </button>
        </form>
      </InfoPanel>
    </>
  );
}

function Dashboard({ role, page, setPage, setRole, notify, auth, setAuth, live, loading, onRefresh }) {
  const currentRole = roleConfig[role];

  function handleLogout() {
    localStorage.removeItem("ecocred_auth");
    setAuth(null);
    setRole(null);
    setPage("overview");
    notify("Signed out from the frontend session.");
  }

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>
            Eco<em>Cred</em>
          </h1>
          <div className="role-pill">{currentRole.label}</div>
        </div>

        <div className="nav-list">
          {currentRole.pages.map((item) => (
            <button
              key={item.id}
              className={`nav-button ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <button className="switch-button" onClick={handleLogout}>
          Logout
        </button>
      </aside>

      <main className="main">
        <div className="topbar">
          <h2>{currentRole.pages.find((item) => item.id === page)?.label ?? "Overview"}</h2>
          <div className="stat-strip">
            <div className="chip">{auth?.user?.username || "signed in"}</div>
            <div className="chip">{auth?.user?.role || role}</div>
          </div>
        </div>

        <div className="content">
          {loading ? <p className="loading-text">Loading live data...</p> : null}
          {!loading && role === "user" ? <UserPage page={page} live={live} notify={notify} auth={auth} onRefresh={onRefresh} /> : null}
          {!loading && role === "aggregator" ? (
            <AggregatorPage page={page} live={live} auth={auth} onRefresh={onRefresh} notify={notify} />
          ) : null}
          {!loading && role === "recycler" ? (
            <RecyclerPage page={page} live={live} auth={auth} onRefresh={onRefresh} notify={notify} />
          ) : null}
        </div>
      </main>
    </div>
  );
}

export default function EcoCredFrontend() {
  const [role, setRole] = useState(null);
  const [page, setPage] = useState("overview");
  const [notice, setNotice] = useState("");
  const [authMode, setAuthMode] = useState("login");
  const [backendStatus, setBackendStatus] = useState({ loading: true, ok: false, message: "Checking backend..." });
  const [auth, setAuth] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("ecocred_auth") || "null");
    } catch {
      return null;
    }
  });
  const [live, setLive] = useState({});
  const [liveLoading, setLiveLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  function notify(message) {
    setNotice(message);
    window.clearTimeout(notify.timer);
    notify.timer = window.setTimeout(() => setNotice(""), 3200);
  }

  function refreshLiveData() {
    setRefreshKey((current) => current + 1);
  }

  useEffect(() => {
    let active = true;

    async function checkBackend() {
      try {
        const data = await fetchJson("/", null);
        if (!active) return;
        setBackendStatus({
          loading: false,
          ok: true,
          message: data.message || "Backend responded.",
        });
      } catch {
        if (!active) return;
        setBackendStatus({
          loading: false,
          ok: false,
          message: "Backend is not reachable from the browser.",
        });
      }
    }

    checkBackend();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (auth?.user?.role) {
      setRole(auth.user.role);
      setPage("overview");
    }
  }, [auth]);

  useEffect(() => {
    let active = true;

    async function loadLiveData() {
      if (!auth?.access || !auth?.user?.role) {
        setLive({});
        return;
      }

      setLiveLoading(true);
      const token = auth.access;

      try {
        const profile = await fetchJson("/api/auth/profile/", token);

        if (!active) return;

        if (auth.user.role === "user") {
          const [userSummary, submissions, transactions, withdrawals, tiers, leaderboard, materials] = await Promise.all([
            fetchJson("/api/rewards/summary/", token),
            fetchJson("/api/waste/submissions/", token),
            fetchJson("/api/rewards/transactions/", token),
            fetchJson("/api/rewards/withdrawals/", token),
            fetchJson("/api/auth/tiers/", token),
            fetchJson("/api/auth/leaderboard/", token),
            fetchJson("/api/waste/materials/", token),
          ]);

          if (!active) return;
          setLive({
            profile,
            userSummary,
            submissions,
            transactions,
            withdrawals,
            tiers,
            leaderboard,
            materials,
          });
        } else if (auth.user.role === "aggregator") {
          try {
            const [aggregatorProfile, jobs, commissions, aggregatorSummary, materials] = await Promise.all([
              fetchJson("/api/aggregators/profile/", token),
              fetchJson("/api/aggregators/jobs/", token),
              fetchJson("/api/aggregators/commissions/", token),
              fetchJson("/api/aggregators/earnings/summary/", token),
              fetchJson("/api/waste/materials/", token),
            ]);

            if (!active) return;
            setLive({
              profile: aggregatorProfile,
              jobs,
              commissions,
              aggregatorSummary,
              materials,
            });
          } catch (error) {
            if (!active) return;
            setLive({
              roleError:
                error.message ||
                "Aggregator endpoints are reachable, but this account still needs an aggregator profile and related records.",
            });
          }
        } else if (auth.user.role === "recycler") {
          try {
            const [recyclerProfile, inventory, shipments, batches, recyclerSummary, materials] = await Promise.all([
              fetchJson("/api/recyclers/profile/", token),
              fetchJson("/api/recyclers/inventory/", token),
              fetchJson("/api/recyclers/shipments/", token),
              fetchJson("/api/recyclers/batches/", token),
              fetchJson("/api/recyclers/revenue/summary/", token),
              fetchJson("/api/waste/materials/", token),
            ]);

            if (!active) return;
            setLive({
              profile: recyclerProfile,
              inventory,
              shipments,
              batches,
              recyclerSummary,
              materials,
            });
          } catch (error) {
            if (!active) return;
            setLive({
              roleError:
                error.message ||
                "Recycler endpoints are reachable, but this account still needs a recycler profile and related records.",
            });
          }
        } else {
          setLive({ profile });
        }
      } catch (error) {
        if (!active) return;
        setLive({
          roleError: error.message || "Could not load live dashboard data.",
        });
      } finally {
        if (active) {
          setLiveLoading(false);
        }
      }
    }

    loadLiveData();
    return () => {
      active = false;
    };
  }, [auth, refreshKey]);

  if (!role) {
    return (
      <div className="app-shell">
        <style>{styles}</style>
        <div className="role-screen">
          <div className="role-card">
            <div className="role-hero">
              <div className="eyebrow">Recycling reimagined</div>
              <div className="brand">
                Eco<em>Cred</em>
              </div>
              <p className="intro">
                The frontend now uses live backend authentication and loads real dashboard data where the backend already exposes it.
              </p>
            </div>

            <div className="split-grid">
              <div className="role-grid">
                {Object.entries(roleConfig).map(([key, value]) => (
                  <div key={key} className="picker">
                    <div className="picker-icon" style={{ background: value.accent }}>
                      {value.icon}
                    </div>
                    <h3 className="picker-title">{value.label}</h3>
                    <p className="picker-text">
                      {key === "user" && "Live profile, reward summary, submissions, transactions, materials, and leaderboard."}
                      {key === "aggregator" && "Live profile, jobs, commissions, and earnings when an aggregator profile exists."}
                      {key === "recycler" && "Live profile, inventory, shipments, batches, and revenue when a recycler profile exists."}
                    </p>
                  </div>
                ))}
              </div>

              <AuthPanel
                authMode={authMode}
                setAuthMode={setAuthMode}
                onAuthSuccess={setAuth}
                backendStatus={backendStatus}
                notify={notify}
              />
            </div>

            <div className="status-banner">
              <div className="status-inline">
                <span className={`status-dot ${backendStatus.loading ? "pending" : backendStatus.ok ? "ok" : "bad"}`} />
                <span>{backendStatus.message}</span>
              </div>
              {auth?.user ? <span>Signed in as {auth.user.username}</span> : <span>Login to load live dashboard data.</span>}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <style>{styles}</style>
      <Dashboard
        role={role}
        page={page}
        setPage={setPage}
        setRole={setRole}
        notify={notify}
        auth={auth}
        setAuth={setAuth}
        live={live}
        loading={liveLoading}
        onRefresh={refreshLiveData}
      />
      {notice ? <div className="notification">{notice}</div> : null}
    </div>
  );
}
