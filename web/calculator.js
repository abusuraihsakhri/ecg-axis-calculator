/* ECG frontal QRS axis calculator — client-side, dependency-free. */
(function (root) {
  "use strict";
  const ANGLES = Object.freeze({I: 0, II: 60, III: 120, aVR: -150, aVL: -30, aVF: 90});
  const RAD = Math.PI / 180;
  const LIMIT_BYTES = 2 * 1024 * 1024;
  const LIMIT_ROWS = 10000;

  function canonical(name) {
    const names = {I: "I", II: "II", III: "III", AVR: "aVR", AVL: "aVL", AVF: "aVF"};
    return names[String(name || "").trim().toUpperCase()] || null;
  }
  function finite(value, label) {
    if (value === "" || value === null || value === undefined || !Number.isFinite(Number(value))) {
      throw new Error(label + " must be a finite number.");
    }
    return Number(value);
  }
  function classify(axis) {
    if (!Number.isFinite(axis)) return "indeterminate";
    const d = ((axis % 360) + 360) % 360;
    const angle = d >= 180 ? d - 360 : d;
    if (angle >= -30 && angle <= 90) return "normal";
    if (angle >= -90 && angle < -30) return "left_axis_deviation";
    if (angle > 90 && angle <= 180) return "right_axis_deviation";
    return "extreme_axis";
  }
  function pair(lead1, value1, lead2, value2) {
    const a = canonical(lead1), b = canonical(lead2);
    if (!a || !b) throw new Error("Select two valid limb leads.");
    if (a === b) throw new Error("Select two different limb leads.");
    const v1 = finite(value1, a), v2 = finite(value2, b);
    const t1 = ANGLES[a] * RAD, t2 = ANGLES[b] * RAD;
    const det = Math.sin(t2 - t1);
    if (Math.abs(det) < 1e-12) throw new Error("Lead axes are not independent.");
    const x = (v1 * Math.sin(t2) - v2 * Math.sin(t1)) / det;
    const y = (v2 * Math.cos(t1) - v1 * Math.cos(t2)) / det;
    const angle = Math.hypot(x, y) <= 1e-12 * Math.max(Math.abs(v1), Math.abs(v2)) ?
      null : Math.atan2(y, x) / RAD;
    return {axis_degrees: angle === null ? null : Math.round(angle * 10) / 10,
            classification: angle === null ? "indeterminate" : classify(angle),
            leads: [a, b]};
  }
  function multi(values) {
    const leads = {};
    Object.entries(values).forEach(function (entry) {
      const a = canonical(entry[0]), raw = entry[1];
      if (!a || raw === "" || raw === null || raw === undefined) return;
      const v = finite(raw, a);
      if (Object.prototype.hasOwnProperty.call(leads, a) && leads[a] !== v) {
        throw new Error("Conflicting measurements for " + a + ".");
      }
      leads[a] = v;
    });
    const keys = Object.keys(leads);
    if (keys.length < 2) throw new Error("Enter at least two limb-lead amplitudes.");
    let cc = 0, ss = 0, cs = 0, cb = 0, sb = 0;
    keys.forEach(function (key) {
      const t = ANGLES[key] * RAD, c = Math.cos(t), s = Math.sin(t), val = leads[key];
      cc += c * c; ss += s * s; cs += c * s; cb += c * val; sb += s * val;
    });
    const det = cc * ss - cs * cs;
    if (det <= 1e-12) throw new Error("Independent lead axes required.");
    const x = (ss * cb - cs * sb) / det, y = (cc * sb - cs * cb) / det;
    const scale = Math.max(...Object.values(leads).map(Math.abs));
    const axis = scale === 0 || Math.hypot(x, y) <= 1e-12 * scale ?
      null : Math.atan2(y, x) / RAD;
    return {axis_degrees: axis === null ? null : Math.round(axis * 10) / 10,
            classification: axis === null ? "indeterminate" : classify(axis), n_leads: keys.length};
  }

  function csvRows(source) {
    const rows = [], row = [];
    let cell = "", quotes = false;
    for (let i = 0; i < source.length; i++) {
      const c = source[i];
      if (quotes) {
        if (c === '"' && source[i + 1] === '"') { cell += '"'; i++; }
        else if (c === '"') quotes = false;
        else cell += c;
      } else if (c === '"') {
        if (cell !== "") throw new Error("Invalid quoting in CSV.");
        quotes = true;
      } else if (c === ",") {
        row.push(cell); cell = "";
      } else if (c === "\n" || c === "\r") {
        if (c === "\r" && source[i + 1] === "\n") i++;
        row.push(cell); cell = "";
        if (row.some(v => v !== "")) rows.push(row.splice(0));
        else row.length = 0;
        if (rows.length > LIMIT_ROWS + 1) throw new Error("CSV exceeds 10,000 rows.");
      } else cell += c;
    }
    if (quotes) throw new Error("Unterminated quoted CSV cell.");
    if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
    return rows;
  }
  function safeCsv(value) {
    const s = value === null || value === undefined ? "" : String(value);
    const safe = /^[=+@\t\r]/.test(s) || /^-(?![0-9.])/.test(s) ? "'" + s : s;
    return '"' + safe.replace(/"/g, '""') + '"';
  }
  function batchCsv(source) {
    const rows = csvRows(String(source || "").replace(/^\uFEFF/, ""));
    if (!rows.length) throw new Error("CSV is empty.");
    const head = rows[0].map(x => x.trim());
    if (head.some(x => !x) || new Set(head).size !== head.length) {
      throw new Error("CSV headers must be present and unique.");
    }
    const items = rows.slice(1);
    const data = [["row", "axis_degrees", "classification", "error"]];
    const quickI = head.indexOf("lead_i_net"), quickVF = head.indexOf("lead_avf_net");
    const indices = head.map((h, i) => ({lead: canonical(h), i})).filter(x => x.lead);
    if (indices.length < 2 && (quickI < 0 || quickVF < 0)) {
      throw new Error("CSV requires lead_i_net and lead_avf_net, or two named limb-lead columns.");
    }
    items.forEach(function (row, index) {
      try {
        if (row.length !== head.length) throw new Error("Unexpected CSV column count.");
        let result;
        if (indices.length >= 2) {
          const map = {};
          indices.forEach(x => { if (row[x.i].trim() !== "") map[x.lead] = row[x.i].trim(); });
          result = multi(map);
        } else result = pair("I", row[quickI].trim(), "aVF", row[quickVF].trim());
        data.push([index + 1, result.axis_degrees, result.classification, ""]);
      } catch (err) {
        data.push([index + 1, "", "", err.message]);
      }
    });
    return {csv: data.map(r => r.map(safeCsv).join(",")).join("\r\n") + "\r\n",
            total: items.length, errors: data.slice(1).filter(r => r[3]).length};
  }

  const API = {ANGLES, canonical, classify, pair, multi, batchCsv, csvRows};
  if (typeof module === "object" && module.exports) module.exports = API;
  root.EcgAxis = API;

  if (typeof document === "undefined") return;
  function el(id) { return document.getElementById(id); }
  const names = {normal: "Normal axis", left_axis_deviation: "Left axis deviation",
                 right_axis_deviation: "Right axis deviation",
                 extreme_axis: "Extreme / northwest axis",
                 indeterminate: "Indeterminate"};
  function render(result, source) {
    const angle = result.axis_degrees;
    el("axis-value").textContent = angle === null ? "—" : angle.toFixed(1) + "°";
    el("axis-class").textContent = names[result.classification];
    el("result-note").textContent = source + (angle === null ?
      " · QRS vector cannot be determined from these amplitudes." :
      " · Frontal plane, conventional adult thresholds.");
    el("result").hidden = false;
    el("error").hidden = true;
    el("axis-ray").style.transform = angle === null ? "scale(0)" : "rotate(" + angle + "deg)";
  }
  function failed(err) {
    el("error").textContent = err.message || String(err);
    el("error").hidden = false;
    el("result").hidden = true;
  }
  function switchMode(mode) {
    const many = mode === "multi";
    el("pair-form").hidden = many;
    el("multi-form").hidden = !many;
    el("tab-pair").setAttribute("aria-selected", String(!many));
    el("tab-multi").setAttribute("aria-selected", String(many));
    el("result").hidden = true;
    el("error").hidden = true;
  }
  el("tab-pair").addEventListener("click", () => switchMode("pair"));
  el("tab-multi").addEventListener("click", () => switchMode("multi"));
  el("pair-form").addEventListener("submit", function (ev) {
    ev.preventDefault();
    try { render(pair(el("lead-1").value, el("value-1").value,
                      el("lead-2").value, el("value-2").value), "Two-lead projection"); }
    catch (err) { failed(err); }
  });
  el("multi-form").addEventListener("submit", function (ev) {
    ev.preventDefault();
    const readings = {};
    Object.keys(ANGLES).forEach(name => { readings[name] = el("multi-" + name).value; });
    try { render(multi(readings), "Least-squares estimate from entered leads"); }
    catch (err) { failed(err); }
  });
  el("sample").addEventListener("click", function () {
    el("lead-1").value = "I"; el("lead-2").value = "aVF";
    el("value-1").value = "0.87"; el("value-2").value = "0.50";
    switchMode("pair");
    render(pair("I", 0.87, "aVF", 0.5), "Example values");
  });
  el("csv-file").addEventListener("change", function () {
    el("csv-status").textContent = this.files.length ?
      this.files[0].name + " selected (processed locally)." : "No file selected.";
  });
  el("csv-run").addEventListener("click", async function () {
    const file = el("csv-file").files[0];
    if (!file) { el("csv-status").textContent = "Choose a CSV file first."; return; }
    if (file.size > LIMIT_BYTES) { el("csv-status").textContent = "File limit is 2 MB."; return; }
    try {
      this.disabled = true;
      const outcome = batchCsv(await file.text());
      const url = URL.createObjectURL(new Blob([outcome.csv], {type: "text/csv;charset=utf-8"}));
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = "ecg-axis-results.csv"; anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      el("csv-status").textContent = outcome.total + " rows processed; " +
        outcome.errors + " rows with errors. Results downloaded.";
    } catch (err) { el("csv-status").textContent = err.message; }
    finally { this.disabled = false; }
  });
})(typeof window === "undefined" ? globalThis : window);
