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

function formatDateTime(value) {
    if (value === null || value === undefined || value === "") {
        return "暂无上报时间";
    }
    const date = new Date(Number(value) * 1000);
    if (Number.isNaN(date.getTime())) {
        return "暂无上报时间";
    }
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${formatTime(date)}`;
}

function formatPercent(value) {
    if (value === null || value === undefined || value === "") {
        return "--";
    }
    return `${value}%`;
}

function batteryToneClass(value) {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) return "is-unknown";
    if (parsed <= 20) return "is-low";
    if (parsed <= 50) return "is-mid";
    return "is-high";
}

function formatSignal(value) {
    if (value === null || value === undefined || value === "") {
        return "--";
    }
    return `${value}`;
}

function signalToneClass(value) {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) return "is-unknown";
    if (parsed <= 1) return "is-low";
    if (parsed <= 3) return "is-mid";
    return "is-high";
}

function signalLevel(value) {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) return 0;
    return Math.max(0, Math.min(5, Math.round(parsed)));
}

function formatNetworkType(value) {
    if (!value) return "--";
    const map = {
        wifi: "Wi-Fi",
        cellular: "蜂窝网络",
        ethernet: "有线网络",
        none: "无网络",
        unknown: "未知",
    };
    return map[value] || "未知";
}

function appendMetric(parent, labelText, valueText) {
    const metric = document.createElement("div");
    metric.className = "device-metric";

    const label = document.createElement("span");
    label.textContent = labelText;

    const value = document.createElement("strong");
    value.textContent = valueText;

    metric.appendChild(label);
    metric.appendChild(value);
    parent.appendChild(metric);
}

function setupAutoMarquee(container, text) {
    container.textContent = "";
    const track = document.createElement("div");
    track.className = "auto-marquee-track";

    const primary = document.createElement("span");
    primary.className = "auto-marquee-text";
    primary.textContent = text;
    track.appendChild(primary);
    container.appendChild(track);

    requestAnimationFrame(() => {
        if (primary.scrollWidth <= container.clientWidth) {
            return;
        }
        container.classList.add("is-marquee");
        const clone = primary.cloneNode(true);
        track.appendChild(clone);
        const travel = primary.scrollWidth + 28;
        track.style.setProperty("--marquee-distance", `${travel}px`);
        const duration = Math.max(8, travel / 26);
        track.style.setProperty("--marquee-duration", `${duration}s`);
    });
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

        const topRow = document.createElement("div");
        topRow.className = "device-top-row";

        const image = document.createElement("img");
        image.className = "device-image";
        const imageSrc = deviceImageSource(device.device_type);
        if (imageSrc) {
            image.src = imageSrc;
            image.alt = `${device.device_type || "device"} icon`;
            image.loading = "lazy";
            topRow.appendChild(image);
        }

        const telemetry = document.createElement("div");
        telemetry.className = "device-telemetry";

        const battery = document.createElement("div");
        battery.className = `device-chip device-battery ${batteryToneClass(device.battery)}`;
        battery.innerHTML = `
            <svg class="battery-icon" viewBox="0 0 28 16" aria-hidden="true">
                <rect class="battery-shell" x="1" y="2" width="23" height="12" rx="4"></rect>
                <rect class="battery-tip" x="24.8" y="5.2" width="2.2" height="5.6" rx="1.1"></rect>
                <rect class="battery-level" x="3.3" y="4.3" width="18" height="7.4" rx="2.4"></rect>
            </svg>
            <span class="battery-text">${formatPercent(device.battery)}</span>
        `;
        const batteryLevelEl = battery.querySelector(".battery-level");
        if (batteryLevelEl && device.battery !== null && device.battery !== undefined && device.battery !== "") {
            const percent = Math.max(0, Math.min(100, Number(device.battery)));
            if (!Number.isNaN(percent)) {
                batteryLevelEl.setAttribute("width", String(18 * (percent / 100)));
            }
        }
        telemetry.appendChild(battery);

        const signal = document.createElement("div");
        const signalValue = device.signal_level;
        signal.className = `device-chip device-signal ${signalToneClass(signalValue)}`;
        signal.dataset.level = String(signalLevel(signalValue));
        signal.innerHTML = `
            <svg class="signal-icon" viewBox="0 0 28 16" aria-hidden="true">
                <rect class="signal-shell" x="1" y="2" width="26" height="12" rx="4"></rect>
                <rect class="signal-bar" x="4" y="10.9" width="2.8" height="2.9" rx="1.2"></rect>
                <rect class="signal-bar" x="8.7" y="9.2" width="2.8" height="4.6" rx="1.2"></rect>
                <rect class="signal-bar" x="13.4" y="7.5" width="2.8" height="6.3" rx="1.2"></rect>
                <rect class="signal-bar" x="18.1" y="5.8" width="2.8" height="8" rx="1.2"></rect>
                <rect class="signal-bar" x="22.8" y="4.1" width="2.8" height="9.7" rx="1.2"></rect>
            </svg>
            <span class="chip-text chip-network-text">${formatNetworkType(device.network_type)}</span>
        `;
        telemetry.appendChild(signal);
        topRow.appendChild(telemetry);

        const name = document.createElement("div");
        name.className = "device-name";
        setupAutoMarquee(name, device.name || device.device_id);

        const description = document.createElement("div");
        description.className = "device-description caption";
        setupAutoMarquee(description, device.description || "暂无描述");

        const divider = document.createElement("div");
        divider.className = "device-divider";

        const usage = document.createElement("div");
        usage.className = "device-usage";
        usage.textContent = "正在使用";

        const status = document.createElement("div");
        status.className = "device-status";
        status.textContent = device.status || "无状态";
        setBadgeClass(status, statusTone(device.status));

        const metrics = document.createElement("div");
        metrics.className = "device-metrics";
        appendMetric(metrics, "最后上报时间", formatDateTime(device.last_report_time));

        card.appendChild(topRow);
        card.appendChild(name);
        card.appendChild(description);
        card.appendChild(divider);
        card.appendChild(usage);
        card.appendChild(status);
        card.appendChild(metrics);
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
