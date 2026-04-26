const REFRESH_MS = 5000;

const nameEl = document.getElementById("name");
const personStatusEl = document.getElementById("person-status");
const personDescriptionEl = document.getElementById("person-description");
const deviceSectionEl = document.getElementById("device-section");
const deviceListEl = document.getElementById("device-list");
const deviceEmptyEl = document.getElementById("device-empty");
const deviceCountEl = document.getElementById("device-count");
const lastUpdatedEl = document.getElementById("last-updated");
const pulseEl = document.getElementById("pulse");

function applyCustomFont() {
  const params = new URLSearchParams(window.location.search);
  const font = params.get("font");
  if (!font) return;
  const decoded = font.replace(/\+/g, " ");
  document.documentElement.style.setProperty("--font-family", `${decoded}, sans-serif`);
}

function formatTime(date) {
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

function setBadgeClass(el, tone) {
  el.classList.remove("success", "warning", "neutral");
  if (tone) {
    el.classList.add(tone);
  }
}

function statusTone(value) {
  if (!value || value === "无状态") {
    return "neutral";
  }
  if (value.includes("忙") || value.includes("离开")) {
    return "warning";
  }
  return "success";
}

function deviceIcon(type) {
  const value = (type || "").toLowerCase();
  if (value === "win") return "WIN";
  if (value === "mac") return "MAC";
  if (value === "linux") return "LIN";
  if (value === "ios") return "IOS";
  if (value === "android") return "AND";
  return "PC";
}

function renderDevices(devices) {
  deviceListEl.innerHTML = "";
  deviceCountEl.textContent = String(devices.length);
  if (!devices.length) {
    deviceSectionEl.hidden = true;
    deviceEmptyEl.hidden = false;
    return;
  }
  deviceSectionEl.hidden = false;
  deviceEmptyEl.hidden = true;
  devices.forEach((device) => {
    const card = document.createElement("div");
    card.className = "device-card";

    const header = document.createElement("div");
    header.className = "device-header";

    const icon = document.createElement("span");
    icon.className = "device-icon";
    icon.textContent = deviceIcon(device.device_type);

    const title = document.createElement("div");
    title.className = "device-title";
    title.textContent = device.name || device.device_id;

    header.appendChild(icon);
    header.appendChild(title);

    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = device.status || "无状态";
    setBadgeClass(badge, statusTone(device.status));

    const meta = document.createElement("div");
    meta.className = "device-meta";
    const description = device.description ? ` - ${device.description}` : "";
    meta.textContent = `${device.device_type}${description}`;

    card.appendChild(header);
    card.appendChild(badge);
    card.appendChild(meta);
    deviceListEl.appendChild(card);
  });
}

function renderSummary(summary) {
  const name = summary.name || "--";
  nameEl.textContent = name;
  personStatusEl.textContent = summary.person.status || "无状态";
  personDescriptionEl.textContent = summary.person.description || "暂无描述";

  renderDevices(summary.devices || []);

  lastUpdatedEl.textContent = `更新于 ${formatTime(new Date())}`;
  pulseEl.classList.add("pulse");
  setTimeout(() => pulseEl.classList.remove("pulse"), 1200);
}

async function loadSummary() {
  try {
    const response = await fetch("/status/summary");
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    const payload = await response.json();
    renderSummary(payload);
  } catch (error) {
    personStatusEl.textContent = "加载失败";
    personDescriptionEl.textContent = "";
    renderDevices([]);
    lastUpdatedEl.textContent = "无法获取数据";
  }
}

applyCustomFont();
loadSummary();
setInterval(loadSummary, REFRESH_MS);
