/* DemoMonitor live metrics — hits only same-origin APIs. */
(function (global) {
  "use strict";

  var REFRESH_MS = 10000;

  function formatBytes(n) {
    if (n == null || isNaN(n)) return "—";
    var units = ["B", "KB", "MB", "GB", "TB"];
    var v = Number(n);
    var i = 0;
    while (v >= 1024 && i < units.length - 1) {
      v /= 1024;
      i += 1;
    }
    return (i === 0 ? String(Math.round(v)) : v.toFixed(1)) + " " + units[i];
  }

  function setStatus(el, status, errorText) {
    if (!el) return;
    var label = status || "error";
    el.textContent = label;
    el.className = "status-pill status-" + label;
    if (errorText) el.title = errorText;
    else el.removeAttribute("title");
  }

  function applyCard(card, item) {
    var m = item.metrics || {};
    var status = m.status || "error";
    setStatus(card.querySelector('[data-role="status"]'), status, m.error || "");
    var cpu = card.querySelector('[data-role="cpu"]');
    var mem = card.querySelector('[data-role="mem"]');
    var rx = card.querySelector('[data-role="rx"]');
    var tx = card.querySelector('[data-role="tx"]');
    var err = card.querySelector('[data-role="error"]');
    if (status === "ok") {
      if (cpu) cpu.textContent = (m.cpu_percent != null ? m.cpu_percent : "—") + "%";
      if (mem) mem.textContent = m.memory ? m.memory.percent + "%" : "—";
      if (rx) rx.textContent = m.network ? formatBytes(m.network.bytes_recv) : "—";
      if (tx) tx.textContent = m.network ? formatBytes(m.network.bytes_sent) : "—";
      if (err) {
        err.hidden = true;
        err.textContent = "";
      }
    } else {
      if (cpu) cpu.textContent = "—";
      if (mem) mem.textContent = "—";
      if (rx) rx.textContent = "—";
      if (tx) tx.textContent = "—";
      if (err) {
        err.hidden = !m.error;
        err.textContent = m.error || "Unable to collect metrics.";
      }
    }
  }

  function stampMeta(el) {
    if (!el) return;
    var now = new Date();
    el.textContent =
      "Updated " +
      now.toLocaleTimeString() +
      " · auto-refresh every 10s";
  }

  function fetchJSON(url) {
    return fetch(url, {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    }).then(function (res) {
      if (res.status === 401 || res.redirected) {
        window.location.href = "/login";
        throw new Error("auth");
      }
      if (!res.ok) throw new Error("request failed");
      return res.json();
    });
  }

  function initDashboard() {
    var root = document.getElementById("dashboard-root");
    if (!root || root.getAttribute("data-has-servers") !== "1") return;
    var meta = document.getElementById("refresh-meta");
    var btn = document.getElementById("refresh-btn");
    var timer = null;

    function refresh() {
      return fetchJSON("/api/servers/metrics")
        .then(function (data) {
          (data.servers || []).forEach(function (item) {
            var card = document.getElementById("server-card-" + item.id);
            if (card) applyCard(card, item);
          });
          stampMeta(meta);
        })
        .catch(function () {
          if (meta) meta.textContent = "Refresh failed — will retry";
        });
    }

    function schedule() {
      if (timer) clearInterval(timer);
      timer = setInterval(refresh, REFRESH_MS);
    }

    if (btn) {
      btn.addEventListener("click", function () {
        refresh().then(schedule);
      });
    }
    refresh();
    schedule();
  }

  function initDetail(serverId) {
    var statusPill = document.getElementById("status-pill");
    var cpuEl = document.getElementById("metric-cpu");
    var memEl = document.getElementById("metric-mem");
    var memDetail = document.getElementById("metric-mem-detail");
    var netEl = document.getElementById("metric-net");
    var portsBody = document.getElementById("ports-body");
    var errEl = document.getElementById("metric-error");
    var meta = document.getElementById("refresh-meta");
    var btn = document.getElementById("refresh-btn");
    var timer = null;

    function renderPorts(ports) {
      if (!portsBody) return;
      portsBody.innerHTML = "";
      if (!ports || !ports.length) {
        var empty = document.createElement("tr");
        var td = document.createElement("td");
        td.colSpan = 3;
        td.textContent = "No listening ports reported.";
        empty.appendChild(td);
        portsBody.appendChild(empty);
        return;
      }
      ports.forEach(function (p) {
        var tr = document.createElement("tr");
        ["proto", "address", "port"].forEach(function (key) {
          var td = document.createElement("td");
          td.textContent = String(p[key]);
          tr.appendChild(td);
        });
        portsBody.appendChild(tr);
      });
    }

    function refresh() {
      return fetchJSON("/api/servers/" + serverId + "/metrics")
        .then(function (m) {
          setStatus(statusPill, m.status, m.error || "");
          if (m.status === "ok") {
            if (cpuEl) cpuEl.textContent = (m.cpu_percent != null ? m.cpu_percent : "—") + "%";
            if (memEl && m.memory) memEl.textContent = m.memory.percent + "%";
            if (memDetail && m.memory) {
              memDetail.textContent =
                formatBytes(m.memory.used_bytes) +
                " / " +
                formatBytes(m.memory.total_bytes);
            }
            if (netEl && m.network) {
              netEl.textContent =
                formatBytes(m.network.bytes_recv) +
                " · " +
                formatBytes(m.network.bytes_sent);
            }
            if (errEl) {
              errEl.hidden = true;
              errEl.textContent = "";
            }
            renderPorts(m.listening_ports || []);
          } else {
            if (cpuEl) cpuEl.textContent = "—";
            if (memEl) memEl.textContent = "—";
            if (memDetail) memDetail.textContent = "used / total";
            if (netEl) netEl.textContent = "—";
            if (errEl) {
              errEl.hidden = false;
              errEl.textContent = m.error || "Unable to collect metrics.";
            }
            renderPorts([]);
          }
          stampMeta(meta);
        })
        .catch(function () {
          setStatus(statusPill, "error", "Refresh failed");
          if (meta) meta.textContent = "Refresh failed — will retry";
        });
    }

    function schedule() {
      if (timer) clearInterval(timer);
      timer = setInterval(refresh, REFRESH_MS);
    }

    if (btn) {
      btn.addEventListener("click", function () {
        refresh().then(schedule);
      });
    }
    refresh();
    schedule();
  }

  global.DemoMonitor = {
    initDashboard: initDashboard,
    initDetail: initDetail,
    formatBytes: formatBytes,
  };
})(window);
