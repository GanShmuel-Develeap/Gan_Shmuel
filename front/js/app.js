/* ========================================
   GAN SHMUEL BILLING — app.js
   All API calls mapped to routes.py
   Base URL: same origin (relative paths)
   ======================================== */

const API = "http://localhost:8080"; // same origin; change to e.g. 'http://localhost:8080' for dev
const WEIGHT_API = "http://localhost:8081";

// ── NAVIGATION ─────────────────────────────────

const pages = {
  dashboard: {
    el: "page-dashboard",
    title: "Dashboard",
    onEnter: loadDashboard,
  },
  transactions: {
    el: "page-transactions",
    title: "Transactions",
    onEnter: null,
  },
  providers: {
    el: "page-providers",
    title: "Providers",
    onEnter: loadProviders,
  },
  trucks: { el: "page-trucks", title: "Trucks", onEnter: null },
  rates: { el: "page-rates", title: "Rates", onEnter: null },
  // Weight Pages
  "weight-dashboard": {
    el: "page-weight-dashboard",
    title: "Weight Dashboard",
    onEnter: checkWeightHealth,
  },
  "weight-form": {
    el: "page-weight-form",
    title: "Weighing Form",
    onEnter: null,
  },
  "weight-batch": {
    el: "page-weight-batch",
    title: "Batch Upload",
    onEnter: null,
  },
  "weight-unknown": {
    el: "page-weight-unknown",
    title: "Unknown Containers",
    onEnter: loadUnknown,
  },
  "weight-lookup": { el: "page-weight-lookup", title: "Lookup", onEnter: null },
};

let currentPage = "dashboard";

function navigate(pageKey) {
  if (!pages[pageKey]) return;

  // Hide all pages
  document
    .querySelectorAll(".page")
    .forEach((p) => p.classList.remove("active"));
  document
    .querySelectorAll(".nav-btn")
    .forEach((b) => b.classList.remove("active"));

  // Show target
  document.getElementById(pages[pageKey].el).classList.add("active");
  document.querySelector(`[data-page="${pageKey}"]`).classList.add("active");
  document.getElementById("page-title").textContent = pages[pageKey].title;

  currentPage = pageKey;

  if (pages[pageKey].onEnter) pages[pageKey].onEnter();
}

function switchMode(mode) {
  // Toggle buttons
  document.getElementById("mode-btn-billing").className =
    `btn-mode ${mode === "billing" ? "active" : ""}`;
  document.getElementById("mode-btn-weight").className =
    `btn-mode ${mode === "weight" ? "active" : ""}`;

  // Toggle Navs
  document.getElementById("nav-billing").style.display =
    mode === "billing" ? "block" : "none";
  document.getElementById("nav-weight").style.display =
    mode === "weight" ? "block" : "none";

  navigate(mode === "billing" ? "dashboard" : "weight-dashboard");
}

// ── HELPERS ────────────────────────────────────

function showMsg(id, type, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `msg ${type}`;
  el.textContent = text;
}

function clearMsg(id) {
  const el = document.getElementById(id);
  if (el) {
    el.className = "msg";
    el.textContent = "";
  }
}

function clearField(inputId, msgId) {
  const el = document.getElementById(inputId);
  if (el) el.value = "";
  if (msgId) clearMsg(msgId);
}

function clearFields(ids, msgId) {
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  if (msgId) clearMsg(msgId);
}

async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

async function weightApiFetch(path, options = {}) {
  const res = await fetch(WEIGHT_API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

// ── DROPDOWN POPULATION ────────────────────────

async function populateProviderDropdowns() {
  try {
    const { ok, data } = await apiFetch("/providers");
    if (!ok || !Array.isArray(data)) return;
    const selects = document.querySelectorAll(
      "#dash-truck-provider, #create-truck-provider, #update-truck-provider, #update-provider-id",
    );
    selects.forEach((sel) => {
      const current = sel.value;
      const firstOpt = sel.querySelector("option:first-child");
      sel.innerHTML = "";
      sel.appendChild(firstOpt);
      data.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `#${p.id} — ${p.name}`;
        sel.appendChild(opt);
      });
      if (current) sel.value = current;
    });
  } catch {}
}

async function populateTruckDropdowns() {
  try {
    const { ok, data } = await apiFetch("/trucks");
    if (!ok || !Array.isArray(data)) return;
    const selects = document.querySelectorAll(
      "#update-truck-id, #lookup-truck-id",
    );
    selects.forEach((sel) => {
      const current = sel.value;
      const firstOpt = sel.querySelector("option:first-child");
      sel.innerHTML = "";
      sel.appendChild(firstOpt);
      data.forEach((t) => {
        const opt = document.createElement("option");
        opt.value = t.id;
        opt.textContent = `${t.id} (${t.provider_name || "Provider #" + t.provider_id})`;
        sel.appendChild(opt);
      });
      if (current) sel.value = current;
    });
  } catch {}
}

async function populateAllDropdowns() {
  await Promise.all([populateProviderDropdowns(), populateTruckDropdowns()]);
}

// ── HEALTH CHECK ───────────────────────────────

async function checkHealth() {
  const pulse = document.getElementById("health-pulse");
  const label = document.getElementById("health-label");

  // Parallel checks
  const [billingRes, weightRes] = await Promise.all([
    apiFetch("/health").catch((e) => ({ ok: false })),
    fetch(WEIGHT_API + "/health").catch((e) => ({ ok: false })),
  ]);

  const billingOk = billingRes.ok;
  const weightOk = weightRes.ok;

  if (billingOk && weightOk) {
    pulse.className = "pulse";
    label.textContent = "All services online";
  } else {
    pulse.className = "pulse offline";
    let offlineServices = [];
    if (!billingOk) offlineServices.push("Billing");
    if (!weightOk) offlineServices.push("Weight");
    label.textContent = `${offlineServices.join(" & ")} service unavailable`;
  }

  // Update billing dashboard stat
  const billingStat = document.getElementById("stat-health");
  if (billingStat) {
    if (billingOk) {
      billingStat.textContent = "Online";
      billingStat.style.color = "var(--teal)";
    } else {
      billingStat.textContent = "Offline";
      billingStat.style.color = "var(--coral)";
    }
  }
}

async function checkWeightHealth() {
  const statusEl = document.getElementById("stat-weight-health");
  if (!statusEl) return;
  try {
    const res = await fetch(WEIGHT_API + "/health");
    if (res.ok) {
      statusEl.textContent = "Online";
      statusEl.style.color = "var(--teal)";
    } else {
      throw new Error("Offline");
    }
  } catch (e) {
    statusEl.textContent = "Offline";
    statusEl.style.color = "var(--coral)";
  }
}
// ── DASHBOARD ──────────────────────────────────

async function loadDashboard() {
  checkHealth();
  loadProviderCount();
  loadTruckCount();
  populateAllDropdowns();
}

async function loadProviderCount() {
  // We load providers list and count them
  try {
    const { ok, data } = await apiFetch("/providers");
    document.getElementById("stat-providers").textContent = ok
      ? data.length
      : "—";
  } catch {
    document.getElementById("stat-providers").textContent = "—";
  }
}

async function loadTruckCount() {
  try {
    const { ok, data } = await apiFetch("/trucks");
    if (ok) {
      document.getElementById("stat-trucks").textContent = data.length;
      document.getElementById("stat-rates").textContent = "—";
    }
  } catch {
    document.getElementById("stat-trucks").textContent = "—";
  }
}

// ── PROVIDERS ──────────────────────────────────

/**
 * POST /provider
 * Body: { name: string }
 * Returns: { id: string }
 */
async function createProvider(nameInputId, msgId) {
  const name = document.getElementById(nameInputId)?.value?.trim();
  if (!name) {
    showMsg(msgId, "warn", "Please enter a provider name.");
    return;
  }

  showMsg(msgId, "warn", "Registering…");
  const { ok, data } = await apiFetch("/provider", {
    method: "POST",
    body: JSON.stringify({ name }),
  });

  if (ok) {
    showMsg(msgId, "success", `✅ Provider registered! ID: ${data.id}`);
    document.getElementById(nameInputId).value = "";
    if (currentPage === "providers") loadProviders();
    loadDashboard();
    populateAllDropdowns();
  } else {
    showMsg(
      msgId,
      "error",
      `❌ ${data.error || "Failed to register provider"}`,
    );
  }
}

/**
 * PUT /provider/:id
 * Body: { name: string }
 */
async function updateProvider() {
  const id = document.getElementById("update-provider-id")?.value?.trim();
  const name = document.getElementById("update-provider-name")?.value?.trim();
  const msgId = "update-provider-msg";

  if (!id || !name) {
    showMsg(msgId, "warn", "Both ID and name are required.");
    return;
  }

  showMsg(msgId, "warn", "Updating…");
  const { ok, data } = await apiFetch(`/provider/${id}`, {
    method: "PUT",
    body: JSON.stringify({ name }),
  });

  if (ok) {
    showMsg(msgId, "success", `✅ Provider ${id} updated to "${name}"`);
    loadProviders();
    populateAllDropdowns();
  } else {
    showMsg(msgId, "error", `❌ ${data.error || "Failed to update provider"}`);
  }
}

/**
 * GET /providers  (list all — if endpoint exists)
 * Falls back to showing a manual table header only
 */
async function loadProviders() {
  const wrap = document.getElementById("providers-table-wrap");
  wrap.innerHTML = '<div class="loading">Loading…</div>';

  const { ok, data } = await apiFetch("/providers");

  if (!ok || !Array.isArray(data)) {
    wrap.innerHTML =
      '<div class="empty">No provider list endpoint available. Use the forms above to manage providers.</div>';
    return;
  }

  if (data.length === 0) {
    wrap.innerHTML = '<div class="empty">No providers registered yet.</div>';
    return;
  }

  wrap.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        ${data
          .map(
            (p) => `
          <tr>
            <td><strong style="color:var(--teal)">#${p.id}</strong></td>
            <td>${p.name}</td>
            <td>
              <button class="btn btn-light sm" onclick="prefillUpdateProvider(${p.id}, '${p.name.replace(/'/g, "\\'")}')">Edit</button>
            </td>
          </tr>
        `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function prefillUpdateProvider(id, name) {
  document.getElementById("update-provider-id").value = id;
  document.getElementById("update-provider-name").value = name;
  document.getElementById("update-provider-name").focus();
}

// ── TRUCKS ─────────────────────────────────────

/**
 * POST /truck
 * Body: { id: string, provider: int }
 */
async function createTruck(truckInputId, providerInputId, msgId) {
  const id = document.getElementById(truckInputId)?.value?.trim();
  const provider = document.getElementById(providerInputId)?.value?.trim();

  if (!id || !provider) {
    showMsg(msgId, "warn", "Both Truck ID and Provider ID are required.");
    return;
  }

  showMsg(msgId, "warn", "Registering…");
  const { ok, data } = await apiFetch("/truck", {
    method: "POST",
    body: JSON.stringify({ id, provider: parseInt(provider) }),
  });

  if (ok) {
    showMsg(msgId, "success", `✅ Truck "${id}" registered successfully.`);
    document.getElementById(truckInputId).value = "";
    document.getElementById(providerInputId).value = "";
    loadDashboard();
    populateAllDropdowns();
  } else {
    showMsg(msgId, "error", `❌ ${data.error || "Failed to register truck"}`);
  }
}

/**
 * PUT /truck/:id
 * Body: { provider: int }
 */
async function updateTruck() {
  const truckId = document.getElementById("update-truck-id")?.value?.trim();
  const provider = document
    .getElementById("update-truck-provider")
    ?.value?.trim();
  const msgId = "update-truck-msg";

  if (!truckId || !provider) {
    showMsg(msgId, "warn", "Both Truck ID and Provider ID are required.");
    return;
  }

  showMsg(msgId, "warn", "Updating…");
  const { ok, data } = await apiFetch(`/truck/${truckId}`, {
    method: "PUT",
    body: JSON.stringify({ provider: parseInt(provider) }),
  });

  if (ok) {
    showMsg(
      msgId,
      "success",
      `✅ Truck "${truckId}" updated to provider #${provider}`,
    );
    populateAllDropdowns();
  } else {
    showMsg(msgId, "error", `❌ ${data.error || "Failed to update truck"}`);
  }
}

/**
 * GET /truck/:id?from=yyyymmddhhmmss&to=yyyymmddhhmmss
 * Returns: { id, tara, sessions: [] }
 */
async function lookupTruck() {
  const truckId = document.getElementById("lookup-truck-id")?.value?.trim();
  const from = document.getElementById("lookup-truck-from")?.value?.trim();
  const to = document.getElementById("lookup-truck-to")?.value?.trim();
  const result = document.getElementById("lookup-truck-result");

  if (!truckId) {
    result.style.display = "block";
    result.innerHTML =
      '<span style="color:var(--coral)">⚠️ Truck ID is required.</span>';
    return;
  }

  result.style.display = "block";
  result.innerHTML =
    '<span style="color:var(--muted-text)">⏳ Searching…</span>';

  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const qs = params.toString() ? `?${params}` : "";

  const { ok, data } = await apiFetch(`/truck/${truckId}${qs}`);

  if (!ok) {
    result.innerHTML = `<span style="color:var(--coral)">❌ ${data.error || "Truck not found"}</span>`;
    return;
  }

  const sessions = data.sessions || [];
  const sessionsHtml =
    sessions.length === 0
      ? '<div style="color:var(--muted-text);font-size:12px">No sessions in this date range.</div>'
      : sessions
          .map(
            (s) => `
        <div class="session-row">
          <span style="color:var(--muted-text);font-size:11px">Session</span>
          <span>${typeof s === "object" ? JSON.stringify(s) : s}</span>
        </div>
      `,
          )
          .join("");

  result.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 24px;margin-bottom:8px">
      <div>
        <div class="result-label">Truck ID</div>
        <strong>${data.id}</strong>
      </div>
      <div>
        <div class="result-label">Tara Weight</div>
        <strong>${data.tara != null ? data.tara + " kg" : "Unknown"}</strong>
      </div>
    </div>
    <div class="sessions-title">Sessions (${sessions.length})</div>
    ${sessionsHtml}
  `;
}

// ── RATES ──────────────────────────────────────

/**
 * POST /rates
 * Body: { file: string }
 */
async function uploadRates() {
  const filename = document.getElementById("rates-filename")?.value?.trim();
  const msgId = "rates-upload-msg";

  if (!filename) {
    showMsg(msgId, "warn", "Please enter a filename.");
    return;
  }

  showMsg(msgId, "warn", "Uploading…");
  const { ok, data } = await apiFetch("/rates", {
    method: "POST",
    body: JSON.stringify({ file: filename }),
  });

  if (ok) {
    showMsg(
      msgId,
      "success",
      `✅ ${data.message} — ${data.rows_processed} rows processed.`,
    );
    document.getElementById("rates-filename").value = "";
  } else {
    showMsg(msgId, "error", `❌ ${data.error || "Failed to upload rates"}`);
  }
}

/**
 * GET /rates
 * Returns: xlsx file download
 */
async function downloadRates() {
  const msgId = "rates-download-msg";
  showMsg(msgId, "warn", "Fetching file…");

  try {
    const res = await fetch(API + "/rates");
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showMsg(msgId, "error", `❌ ${err.error || "No rates file found"}`);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "rates.xlsx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showMsg(msgId, "success", "✅ Download started.");
  } catch (e) {
    showMsg(msgId, "error", "❌ Failed to download file.");
  }
}

// ── TRANSACTIONS ────────────────────────────────

/**
 * GET /weight?from=&to=&filter=
 * Returns list of transactions from the Weight service
 */
async function loadTransactions() {
  const from = document.getElementById("tx-from")?.value?.trim();
  const to = document.getElementById("tx-to")?.value?.trim();
  const filter =
    document.getElementById("tx-filter")?.value?.trim() || "in,out,none";
  const wrap = document.getElementById("transactions-table-wrap");

  wrap.innerHTML = '<div class="loading">Loading transactions…</div>';

  const params = new URLSearchParams({ filter });
  if (from) params.set("from", from);
  if (to) params.set("to", to);

  // Transactions come from the Weight service via its /weight endpoint
  const { ok, data } = await weightApiFetch(`/weight?${params}`);

  if (!ok) {
    wrap.innerHTML = `<div class="empty">Could not load transactions: ${data.error || "Unknown error"}</div>`;
    return;
  }

  if (!Array.isArray(data) || data.length === 0) {
    wrap.innerHTML =
      '<div class="empty">No transactions found for the selected filters.</div>';
    return;
  }

  const dirChip = (dir) => {
    if (dir === "in") return '<span class="chip chip-teal">in</span>';
    if (dir === "out") return '<span class="chip chip-amber">out</span>';
    if (dir === "none") return '<span class="chip chip-grey">none</span>';
    return dir;
  };

  wrap.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Direction</th>
          <th>Truck</th>
          <th>Containers</th>
          <th>Bruto</th>
          <th>Neto</th>
          <th>Produce</th>
        </tr>
      </thead>
      <tbody>
        ${data
          .map(
            (t) => `
          <tr>
            <td>${t.id}</td>
            <td>${dirChip(t.direction)}</td>
            <td>${t.truck_id || t.truck || "—"}</td>
            <td>${Array.isArray(t.containers) ? t.containers.join(", ") : t.containers || "—"}</td>
            <td>${t.bruto}</td>
            <td>${t.neto}</td>
            <td>${t.produce}</td>
          </tr>
        `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

// ── WEIGHT API FUNCTIONS ───────────────────────

async function submitWeight() {
  const msgId = "w-msg";
  const body = new URLSearchParams();
  body.append("direction", document.getElementById("w-direction").value);
  body.append("truck", document.getElementById("w-truck").value);
  body.append("containers", document.getElementById("w-containers").value);
  body.append("bruto", document.getElementById("w-bruto").value);
  body.append("unit", document.getElementById("w-unit").value);
  body.append("produce", document.getElementById("w-produce").value);

  showMsg(msgId, "warn", "Submitting...");

  // Note: /weight-form expects form-data or x-www-form-urlencoded
  const res = await fetch(WEIGHT_API + "/weight-form", {
    method: "POST",
    body: body,
  });

  const data = await res.json().catch(() => ({}));

  if (res.ok && data.status === "success") {
    showMsg(msgId, "success", `✅ Transaction #${data.id} recorded!`);
    document.getElementById("w-bruto").value = "";
  } else {
    showMsg(msgId, "error", `❌ ${data.message || "Error submitting weight"}`);
  }
}

async function uploadBatchWeight() {
  const filename = document.getElementById("w-batch-file").value;
  const msgId = "w-batch-msg";
  if (!filename) return showMsg(msgId, "warn", "Enter filename");

  showMsg(msgId, "warn", "Processing...");
  const body = new URLSearchParams();
  body.append("file", filename);

  const res = await fetch(WEIGHT_API + "/batch-weight", {
    method: "POST",
    body,
  });
  const data = await res.json().catch(() => ({}));

  if (res.ok) {
    showMsg(
      msgId,
      "success",
      `✅ Batch processed. Count: ${data.count || "N/A"}`,
    );
  } else {
    showMsg(msgId, "error", `❌ ${data.error || "Batch failed"}`);
  }
}

async function loadUnknown() {
  const wrap = document.getElementById("unknown-table-wrap");
  wrap.innerHTML = '<div class="loading">Loading...</div>';
  const { ok, data } = await weightApiFetch("/unknown");

  if (!ok || !Array.isArray(data)) {
    wrap.innerHTML =
      '<div class="empty">Failed to load unknown containers</div>';
    return;
  }
  if (data.length === 0) {
    wrap.innerHTML = '<div class="empty">No unknown containers found.</div>';
    return;
  }
  wrap.innerHTML = `
    <table><thead><tr><th>Container ID</th></tr></thead>
    <tbody>${data.map((id) => `<tr><td>${id}</td></tr>`).join("")}</tbody></table>
  `;
}

async function lookupWeightData() {
  const id = document.getElementById("w-lookup-id").value.trim();
  const resBox = document.getElementById("w-lookup-result");
  if (!id) return;

  resBox.style.display = "block";
  resBox.innerHTML = "Searching...";

  // Try session first
  let { ok, data } = await weightApiFetch(`/session/${id}`);
  if (ok) {
    resBox.innerHTML = `<pre style="font-size:12px">${JSON.stringify(data, null, 2)}</pre>`;
    return;
  }

  // Try item
  ({ ok, data } = await weightApiFetch(`/item/${id}`));
  if (ok) {
    resBox.innerHTML = `<pre style="font-size:12px">${JSON.stringify(data, null, 2)}</pre>`;
    return;
  }

  resBox.innerHTML =
    '<span style="color:var(--coral)">❌ Not found (Session or Item)</span>';
}
