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
const pageEl = document.querySelector(".page");
const themeButtons = Array.from(document.querySelectorAll(".theme-pill-btn"));
const THEME_STORAGE_KEY = "statusinsights-theme-mode";
const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
let requestSeq = 0;
let lastRenderedSeq = 0;
let currentController = null;

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

function deviceImageSource(type) {
    const value = (type || "").toLowerCase();
    if (value === "ios" || value === "mac") return "/static/apple.svg";
    if (value === "android") return "/static/android.svg";
    if (value === "linux") return "/static/linux.svg";
    if (value === "win") return "/static/win.svg";
    return "";
}

function resolveTheme(mode) {
    if (mode === "light") return "light";
    if (mode === "dark") return "dark";
    return mediaQuery.matches ? "dark" : "light";
}

function applyTheme(theme, animated = false) {
    document.documentElement.setAttribute("data-theme", theme);
    if (animated && pageEl) {
        pageEl.classList.remove("theme-animating");
        void pageEl.offsetWidth;
        pageEl.classList.add("theme-animating");
        setTimeout(() => pageEl.classList.remove("theme-animating"), 340);
    }
}

function getSavedThemeMode() {
    const mode = localStorage.getItem(THEME_STORAGE_KEY);
    if (mode === "auto" || mode === "light" || mode === "dark") {
        return mode;
    }
    return "auto";
}

function applyThemeMode(mode, animated = false) {
    const previousTheme = document.documentElement.getAttribute("data-theme");
    const theme = resolveTheme(mode);
    const shouldAnimate = animated && previousTheme !== null && previousTheme !== theme;
    applyTheme(theme, shouldAnimate);
    themeButtons.forEach((button) => {
        const isActive = button.dataset.themeMode === mode;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
}

function initThemeMode() {
    const savedMode = getSavedThemeMode();
    applyThemeMode(savedMode, false);

    themeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const mode = button.dataset.themeMode;
            if (mode !== "auto" && mode !== "light" && mode !== "dark") {
                return;
            }
            localStorage.setItem(THEME_STORAGE_KEY, mode);
            applyThemeMode(mode, true);
        });
    });

    mediaQuery.addEventListener("change", () => {
        if (getSavedThemeMode() === "auto") {
            applyThemeMode("auto", true);
        }
    });
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

        const image = document.createElement("img");
        image.className = "device-image";
        const imageSrc = deviceImageSource(device.device_type);
        if (imageSrc) {
            image.src = imageSrc;
            image.alt = `${device.device_type || "device"} icon`;
            image.loading = "lazy";
            card.appendChild(image);
        }

        const name = document.createElement("div");
        name.className = "device-name";
        name.textContent = device.name || device.device_id;

        const description = document.createElement("div");
        description.className = "device-description caption";
        description.textContent = device.description || "暂无描述";

        const divider = document.createElement("div");
        divider.className = "device-divider";

        const usage = document.createElement("div");
        usage.className = "device-usage";
        usage.textContent = "正在使用";

        const status = document.createElement("div");
        status.className = "device-status";
        status.textContent = device.status || "无状态";
        setBadgeClass(status, statusTone(device.status));

        card.appendChild(name);
        card.appendChild(description);
        card.appendChild(divider);
        card.appendChild(usage);
        card.appendChild(status);
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
    requestSeq += 1;
    const seq = requestSeq;
    if (currentController) {
        currentController.abort();
    }
    currentController = new AbortController();
    try {
        const response = await fetch("/status/summary", {signal: currentController.signal});
        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }
        const payload = await response.json();
        if (seq < lastRenderedSeq) {
            return;
        }
        lastRenderedSeq = seq;
        renderSummary(payload);
    } catch (error) {
        if (error && error.name === "AbortError") {
            return;
        }
        if (seq < lastRenderedSeq) {
            return;
        }
        lastRenderedSeq = seq;
        personStatusEl.textContent = "加载失败";
        personDescriptionEl.textContent = "";
        renderDevices([]);
        lastUpdatedEl.textContent = "无法获取数据";
    } finally {
        if (seq === requestSeq) {
            currentController = null;
        }
    }
}

applyCustomFont();
initThemeMode();
loadSummary();
setInterval(loadSummary, REFRESH_MS);
