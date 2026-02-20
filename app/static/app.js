async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
const el = (id) => document.getElementById(id);

let cachedState = null;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

async function loadState() {
  cachedState = await api("/api/state");
  return cachedState;
}

function renderRoundSelect(state) {
  const sel = el("roundSelect");
  sel.innerHTML = "";
  const rounds = Number(state.rounds || 10);
  for (let i = 1; i <= rounds; i++) {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = `Round ${i}`;
    sel.appendChild(opt);
  }
}

function getSelectedRound() {
  return Number(el("roundSelect").value || "1");
}

function getRoundSavedResults(state, roundNum) {
  const key = String(roundNum);
  return (state.round_results && state.round_results[key]) ? state.round_results[key] : {};
}

function getRoundSavedAlliances(state, roundNum) {
  const key = String(roundNum);
  return (state.loot_alliances && state.loot_alliances[key]) ? state.loot_alliances[key] : [];
}

function alliancesToText(alliances) {
  // alliances is [ [A,B], [C,D] ]
  return alliances.map(pair => `${pair[0]},${pair[1]}`).join("\n");
}

function textToAlliances(text) {
  const lines = String(text || "").split("\n").map(s => s.trim()).filter(Boolean);
  const pairs = [];
  for (const line of lines) {
    const parts = line.split(",").map(s => s.trim()).filter(Boolean);
    if (parts.length === 2) pairs.push([parts[0], parts[1]]);
  }
  return pairs;
}

function renderEntryTable(state, roundNum) {
  const wrap = el("entryTableWrap");
  const players = state.players || [];
  const saved = getRoundSavedResults(state, roundNum);

  let html = `<table>
    <thead>
      <tr>
        <th>Player</th>
        <th>Bid</th>
        <th>Tricks</th>
        <th>Bonus Override</th>
        ${state.scoring_mode === "rascal" ? "<th>Rascal Load</th>" : ""}
      </tr>
    </thead>
    <tbody>`;

  for (const p of players) {
    const pr = saved[p] || {};
    const bid = pr.bid ?? "";
    const tricks = pr.tricks ?? "";
    const bonusOverride = (pr.bonuses && pr.bonuses.bonus_override != null) ? pr.bonuses.bonus_override : "";
    const rascalLoad = pr.rascal_load ?? "";

    html += `<tr>
      <td><b>${escapeHtml(p)}</b></td>
      <td><input type="number" min="0" step="1" data-player="${escapeHtml(p)}" data-field="bid" value="${escapeHtml(bid)}" style="width:90px;"></td>
      <td><input type="number" min="0" step="1" data-player="${escapeHtml(p)}" data-field="tricks" value="${escapeHtml(tricks)}" style="width:90px;"></td>
      <td><input type="number" step="1" data-player="${escapeHtml(p)}" data-field="bonus_override" value="${escapeHtml(bonusOverride)}" style="width:140px;"></td>
      ${
        state.scoring_mode === "rascal"
        ? `<td>
            <select data-player="${escapeHtml(p)}" data-field="rascal_load">
              <option value="" ${rascalLoad === "" ? "selected":""}>standard</option>
              <option value="grapeshot" ${rascalLoad === "grapeshot" ? "selected":""}>grapeshot</option>
              <option value="cannonball" ${rascalLoad === "cannonball" ? "selected":""}>cannonball</option>
            </select>
          </td>`
        : ""
      }
    </tr>`;
  }

  html += `</tbody></table>`;
  wrap.innerHTML = html;

  // Alliances textarea
  const alliances = getRoundSavedAlliances(state, roundNum);
  el("alliances").value = alliancesToText(alliances);
}

function collectEntryTable(state) {
  const players = state.players || [];
  const results = {};

  for (const p of players) {
    results[p] = { bid: 0, tricks: 0, bonuses: {} };
  }

  const inputs = el("entryTableWrap").querySelectorAll("input, select");
  inputs.forEach(inp => {
    const player = inp.getAttribute("data-player");
    const field = inp.getAttribute("data-field");
    if (!player || !field) return;

    if (!results[player]) results[player] = { bid: 0, tricks: 0, bonuses: {} };

    if (field === "bid" || field === "tricks") {
      const v = inp.value === "" ? 0 : Number(inp.value);
      results[player][field] = Number.isFinite(v) ? v : 0;
    } else if (field === "bonus_override") {
      if (inp.value !== "") {
        const v = Number(inp.value);
        if (Number.isFinite(v)) results[player].bonuses.bonus_override = v;
      } else {
        // remove if empty
        delete results[player].bonuses.bonus_override;
      }
    } else if (field === "rascal_load") {
      const v = String(inp.value || "");
      if (v) results[player].rascal_load = v;
      else delete results[player].rascal_load;
    }
  });

  return results;
}

async function refreshScoreboard() {
  const sb = await api("/api/scoreboard");
  const out = el("out");
  out.innerHTML = "";

  const h = document.createElement("div");
  h.innerHTML = `<b>${escapeHtml(sb.state.name)}</b> — mode: ${escapeHtml(sb.state.scoring_mode)}`;
  out.appendChild(h);

  const ul = document.createElement("ul");
  sb.leaderboard.forEach(x => {
    const li = document.createElement("li");
    li.textContent = `${x.player}: ${x.total}`;
    ul.appendChild(li);
  });
  out.appendChild(ul);

  sb.rounds.forEach(r => {
    const t = document.createElement("table");
    t.innerHTML = `<thead><tr>
      <th>Round ${r.round}</th><th>Bid</th><th>Tricks</th><th>Base</th><th>Bonus</th><th>Round</th><th>Total</th>
    </tr></thead>`;
    const tb = document.createElement("tbody");
    r.rows.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${escapeHtml(row.player)}</td><td>${row.bid}</td><td>${row.tricks}</td>
        <td>${row.base}</td><td>${row.bonus}</td><td>${row.round_points}</td><td>${row.running_total}</td>`;
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    out.appendChild(t);
  });
}

async function loadRoundUI() {
  const state = cachedState || await loadState();
  const roundNum = getSelectedRound();
  renderEntryTable(state, roundNum);
}

async function saveRoundUI() {
  const state = cachedState || await loadState();
  const roundNum = getSelectedRound();

  const results = collectEntryTable(state);
  const alliances = textToAlliances(el("alliances").value);

  el("saveStatus").textContent = "Saving...";
  try {
    await api(`/api/round/${roundNum}`, {
      method: "PUT",
      body: JSON.stringify({ results, alliances }),
    });
    // refresh local cache + scoreboard
    await loadState();
    await refreshScoreboard();
    el("saveStatus").textContent = "Saved ✅";
    setTimeout(() => (el("saveStatus").textContent = ""), 1500);
  } catch (e) {
    el("saveStatus").textContent = "Save failed ❌";
    alert(String(e));
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  el("newBtn").onclick = async () => {
  const name = el("name").value;
  const scoring_mode = el("mode").value;
  const rounds = Number(el("rounds").value || 10);
  const players = el("players").value.split(",").map(s => s.trim()).filter(Boolean);

  await api("/api/new_game", {
    method: "POST",
    body: JSON.stringify({ name, scoring_mode, rounds, players }),
  });

  await loadState();
  renderRoundSelect(cachedState);
  await loadRoundUI();
  await refreshScoreboard();
};

el("downloadJsonBtn").onclick = () => {
  window.location.href = "/api/export?format=json&save=true";
};
el("downloadCsvBtn").onclick = () => {
  window.location.href = "/api/export?format=csv&save=true";
};


  el("refreshBtn").onclick = refreshScoreboard;
  el("loadRoundBtn").onclick = loadRoundUI;
  el("saveRoundBtn").onclick = saveRoundUI;

  // initial load
  await loadState();
  renderRoundSelect(cachedState);
  await loadRoundUI();
  await refreshScoreboard();
});
