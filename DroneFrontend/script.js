const ROWS = 6;
const COLS = 8;
const GRID_CELLS = ROWS * COLS;
const SEARCH_WAYPOINTS = GRID_CELLS;
const RESCUE_WAYPOINTS = 3;
const RESCUE_LOCATION = {
  lat: 17.9806,
  lon: 79.5329,
};

const state = {
  route: [],
  searchRoute: [],
  rescueRoute: [],
  currentIndex: 0,
  running: true,
  phase: "initializing",
  returning: false,
  rerouting: false,

  frameCount: 0,
  startTime: Date.now(),
  battery: 78,

  detections: [],
  detectedIndexes: new Set(),

  dronePosition: 0,
};

const detectionEvents = [
  {
    waypoint: 10,
    type: "person",
    label: "Victim 01",
    confidence: 89.98,
    lat: RESCUE_LOCATION.lat,
    lon: RESCUE_LOCATION.lon,
    x: 0.22,
    y: 0.43,
    w: 0.16,
    h: 0.27,
  },

  {
    waypoint: 30,
    type: "person",
    label: "Victim 02",
    confidence: 89.98,
    lat: RESCUE_LOCATION.lat,
    lon: RESCUE_LOCATION.lon,
    x: 0.58,
    y: 0.35,
    w: 0.18,
    h: 0.23,
  },
];

const elements = {
  mapGrid: document.getElementById("mapGrid"),
  plannedRoute: document.getElementById("plannedRoute"),
  completedRoute: document.getElementById("completedRoute"),
  rescueRoute: document.getElementById("rescueRoute"),
  droneMarker: document.getElementById("droneMarker"),
  mapDetections: document.getElementById("mapDetections"),

  detections: document.getElementById("detections"),
  detectionCount: document.getElementById("detection-count"),

  cameraDetections: document.getElementById("cameraDetections"),

  frameCoords: document.getElementById("frame-coords"),
  mapLat: document.getElementById("mapLat"),
  mapLon: document.getElementById("mapLon"),

  frameCount: document.getElementById("frame-count"),

  routeProgress: document.getElementById("route-progress"),
  coverageValue: document.getElementById("coverageValue"),
  currentWaypoint: document.getElementById("currentWaypoint"),

  routeBadge: document.getElementById("route-badge"),
  pathStatus: document.getElementById("pathStatus"),
  flightMode: document.getElementById("flightMode"),

  controlStatus: document.getElementById("controlStatus"),

  pauseBtn: document.getElementById("pauseBtn"),
  rerouteBtn: document.getElementById("rerouteBtn"),
  rtbBtn: document.getElementById("rtbBtn"),
  rescueBtn: document.getElementById("rescueBtn"),

  clock: document.getElementById("clock"),
  missionClock: document.getElementById("mission-clock"),

  battery: document.getElementById("tel-batt"),
  batteryBar: document.getElementById("tel-batt-bar"),
  altitude: document.getElementById("tel-alt"),

  lora: document.getElementById("tel-lora"),
  loraDot: document.getElementById("lora-dot"),

  gps: document.getElementById("tel-gps"),
  gpsDot: document.getElementById("gps-dot"),
};

/* =========================================================
   BUILD SEARCH GRID
========================================================= */

function buildGrid() {
  elements.mapGrid.innerHTML = "";

  for (let i = 0; i < GRID_CELLS; i++) {
    const cell = document.createElement("div");

    cell.className = "search-cell";
    cell.dataset.index = i;

    elements.mapGrid.appendChild(cell);
  }
}

/* =========================================================
   BUILD SHORTEST RESCUE ROUTE
========================================================= */

function buildRoute() {
  state.searchRoute = [];

  for (let row = 0; row < ROWS; row++) {
    const columns = Array.from({ length: COLS }, (_, col) => col);

    if (row % 2 === 1) {
      columns.reverse();
    }

    columns.forEach((col) => {
      state.searchRoute.push({
        x: 50 + col * (700 / (COLS - 1)),
        y: 42 + row * (416 / (ROWS - 1)),
      });
    });
  }

  state.rescueRoute = [
    { x: 40, y: 440 },
    { x: 150, y: 291 },
    { x: 550, y: 125 },
  ];

  state.route = state.searchRoute;

  drawPlannedRoute();
  drawRescueRoute();
}

/* =========================================================
   MAP COORDINATES
========================================================= */

function getMapPosition(index) {
  const point = state.route[index];

  if (!point) {
    return {
      x: 50,
      y: 42,
    };
  }

  return {
    x: point.x,
    y: point.y,
  };
}

/* =========================================================
   DRAW PLANNED ROUTE
========================================================= */

function drawPlannedRoute() {
  const points = state.searchRoute
    .map(({ x, y }) => `${x},${y}`)
    .join(" ");

  elements.plannedRoute.setAttribute("points", points);

  elements.completedRoute.setAttribute("points", "");
}

function drawRescueRoute() {
  const points = state.rescueRoute
    .map(({ x, y }) => `${x},${y}`)
    .join(" ");

  elements.rescueRoute.setAttribute("points", points);
}

/* =========================================================
   MOVE DRONE
========================================================= */

function moveDrone(index) {
  const point = state.route[index];

  if (!point) {
    return;
  }

  const p = getMapPosition(index);

  elements.droneMarker.style.left = `${(p.x / 800) * 100}%`;

  elements.droneMarker.style.top = `${(p.y / 500) * 100}%`;

  state.dronePosition = index;

  updateWaypointUI(index);
  updateCompletedRoute(index);
  markScannedCells(index);

  updateCoordinates(point);
}

/* =========================================================
   COMPLETED ROUTE
========================================================= */

function updateCompletedRoute(index) {
  if (index < 0) {
    return;
  }

  const points = state.route
    .slice(0, index + 1)
    .map((_, i) => {
      const p = getMapPosition(i);

      return `${p.x},${p.y}`;
    })
    .join(" ");

  elements.completedRoute.setAttribute("points", points);
}

/* =========================================================
   SCANNED GRID CELLS
========================================================= */

function markScannedCells(index) {
  const cells = document.querySelectorAll(".search-cell");

  cells.forEach((cell) => {
    const cellIndex = Number(cell.dataset.index);

    if (cellIndex <= index) {
      cell.classList.add("scanned");
    }
  });
}

/* =========================================================
   WAYPOINT UI
========================================================= */

function updateWaypointUI(index) {
  if (state.returning) {
    elements.flightMode.textContent = "RETURN";

    elements.pathStatus.textContent = "Returning to base along completed route";
  } else {
    elements.flightMode.textContent = "SEARCH";

    elements.pathStatus.textContent = "Autonomous sector traversal active";
  }

  const totalWaypoints = state.route === state.searchRoute
    ? SEARCH_WAYPOINTS
    : RESCUE_WAYPOINTS;
  const displayIndex = Math.min(index + 1, totalWaypoints);

  elements.currentWaypoint.textContent = `${displayIndex} / ${totalWaypoints}`;

  const progress = ((index + 1) / totalWaypoints) * 100;

  elements.routeProgress.style.width = `${Math.max(0, Math.min(100, progress))}%`;

  if (!state.returning) {
    elements.coverageValue.textContent = `${Math.round(progress)}%`;
  }
}

/* =========================================================
   GPS
========================================================= */

function updateCoordinates(point) {
  const lat = RESCUE_LOCATION.lat;

  const lon = RESCUE_LOCATION.lon;

  const text = `${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E`;

  elements.frameCoords.textContent = text;

  elements.mapLat.textContent = `${lat.toFixed(4)}°N`;

  elements.mapLon.textContent = `${lon.toFixed(4)}°E`;
}

/* =========================================================
   DETECTION CHECK
   THIS IS THE IMPORTANT PART
========================================================= */

function checkDetection(index) {
  if (state.returning) {
    return;
  }

  const event = detectionEvents.find(
    (d) => d.waypoint === index && !state.detectedIndexes.has(d.waypoint),
  );

  if (!event) {
    return;
  }

  state.detectedIndexes.add(event.waypoint);

  triggerDetection(event);

  elements.routeBadge.textContent = "SEARCHING";
  elements.pathStatus.textContent = `${event.label} detected during zig-zag scan`;
}

/* =========================================================
   TRIGGER DETECTION
========================================================= */

function triggerDetection(event) {
  const detection = {
    ...event,

    id: `${event.type}-${Date.now()}`,

    confirmed: false,
    dismissed: false,

    timeAgo: "just now",
  };

  state.detections.push(detection);

  /* MAP MARKER */
  createMapDetection(detection);

  /* CAMERA BOX */
  showCameraDetection(detection);

  /* RIGHT PANEL */
  renderDetections();
}

/* =========================================================
   MAP DETECTION MARKER
========================================================= */

function createMapDetection(detection) {
  const point = state.route[detection.waypoint];

  if (!point) {
    return;
  }

  const p = getMapPosition(detection.waypoint);

  const marker = document.createElement("div");

  marker.className = `map-detection ${detection.type}`;

  marker.style.left = `${(p.x / 800) * 100}%`;

  marker.style.top = `${(p.y / 500) * 100}%`;

  let icon = "●";

  if (detection.type === "person") {
    icon = "●";
  }

  if (detection.type === "fire") {
    icon = "▲";
  }

  if (detection.type === "water") {
    icon = "≈";
  }

  marker.innerHTML = `
    <div class="map-detection-icon">
      ${icon}
    </div>

    <div class="map-detection-label">
      ${detection.label.toUpperCase()}
      ${detection.confidence}%
    </div>
  `;

  elements.mapDetections.appendChild(marker);
}

/* =========================================================
   CAMERA DETECTION
========================================================= */

function showCameraDetection(detection) {
  const box = document.createElement("div");

  box.className = `camera-detection ${detection.type}`;

  box.dataset.detectionId = detection.id;

  box.style.left = `${detection.x * 100}%`;

  box.style.top = `${detection.y * 100}%`;

  box.style.width = `${detection.w * 100}%`;

  box.style.height = `${detection.h * 100}%`;

  const label = document.createElement("span");

  label.className = "camera-detection-label";

  label.textContent = `${detection.label.toUpperCase()} ${detection.confidence}%`;

  box.appendChild(label);
  elements.cameraDetections.appendChild(box);
}

/* =========================================================
   DETECTION PANEL
========================================================= */

function renderDetections() {
  const list = elements.detections;

  const active = state.detections.filter((d) => !d.dismissed);

  elements.detectionCount.textContent = `${active.length} ACTIVE`;

  if (active.length === 0) {
    list.innerHTML = `
      <div class="empty">
        <div class="empty-radar"></div>

        <strong>SCANNING SECTOR</strong>

        <span>
          No objects identified yet.
          Detection events will appear as the drone reaches each search point.
        </span>
      </div>
    `;

    return;
  }

  list.innerHTML = "";

  active
    .slice()
    .reverse()
    .forEach((detection) => {
      const card = document.createElement("div");

      let className = "brief ";

      if (detection.type === "person") {
        className += "pending";
      }

      if (detection.type === "fire") {
        className += "hazard";
      }

      if (detection.type === "water") {
        className += "water";
      }

      card.className = className;

      let color = "#FFC168";

      if (detection.type === "fire") {
        color = "#FF6B7C";
      }

      if (detection.type === "water") {
        color = "#8FC7F0";
      }

      let icon = "●";

      if (detection.type === "fire") {
        icon = "▲";
      }

      if (detection.type === "water") {
        icon = "≈";
      }

      let action = "";

      if (detection.type === "person" && !detection.confirmed) {
        action = `
          <div class="brief-actions">

            <button
              class="btn primary"
              data-action="confirm"
              data-id="${detection.id}">
              Confirm & Dispatch
            </button>

            <button
              class="btn"
              data-action="dismiss"
              data-id="${detection.id}">
              Dismiss
            </button>

          </div>
        `;
      } else if (detection.type === "person" && detection.confirmed) {
        action = `
          <div class="status-line">
            ✓ Rescue location dispatched
          </div>
        `;
      } else {
        action = `
          <div class="brief-actions">

            <button
              class="btn"
              data-action="dismiss"
              data-id="${detection.id}">
              Acknowledge
            </button>

          </div>
        `;
      }

      card.innerHTML = `

        <div class="brief-top">

          <div class="brief-type">

            <span
              class="glyph"
              style="color:${color}">
              ${icon}
            </span>

            <span class="brief-title">
              ${detection.label}
            </span>

          </div>

          <span
            class="brief-conf"
            style="color:${color}">
            ${detection.confidence}%
          </span>

        </div>

        <div class="conf-meter">

          <span
            style="
              width:${detection.confidence}%;
              background:${color};
            ">
          </span>

        </div>

        <div class="brief-meta">

          <span>
            GPS
            <b>
              ${detection.lat.toFixed(4)},
              ${detection.lon.toFixed(4)}
            </b>
          </span>

          <span>
            Waypoint
            <b>
              ${detection.waypoint + 1}
            </b>
          </span>

          <span>
            Detected
            <b>just now</b>
          </span>

        </div>

        ${action}

      `;

      list.appendChild(card);
    });
}

/* =========================================================
   DETECTION BUTTONS
========================================================= */

elements.detections.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");

  if (!button) {
    return;
  }

  const id = button.dataset.id;

  const detection = state.detections.find((d) => d.id === id);

  if (!detection) {
    return;
  }

  if (button.dataset.action === "confirm") {
    detection.confirmed = true;
  }

  if (button.dataset.action === "dismiss") {
    detection.dismissed = true;
  }

  renderDetections();
});

/* =========================================================
   DRONE SEARCH TRAVERSAL
========================================================= */

function startTraversal() {
  state.phase = "rescue";
  state.running = true;
  state.returning = false;
  state.currentIndex = 0;

  elements.rescueRoute.classList.remove("mission-hidden");
  elements.droneMarker.classList.remove("mission-hidden");
  elements.rescueBtn.disabled = true;
  elements.controlStatus.textContent = "AUTO";

  elements.routeBadge.classList.remove("loading");
  elements.pathStatus.classList.remove("loading");
  elements.routeBadge.textContent = "RESCUE ACTIVE";
  elements.pathStatus.textContent = "Shortest rescue path active from exit";
  elements.flightMode.textContent = "RESCUE";

  moveDrone(0);

  setTimeout(traverseNext, 700);
}

function traverseNext() {
  if (!state.running) {
    return;
  }

  if (state.returning) {
    return;
  }

  if (state.currentIndex >= SEARCH_WAYPOINTS - 1) {
    startAStarPlanning();

    return;
  }

  state.currentIndex++;

  moveDrone(state.currentIndex);

  checkDetection(state.currentIndex);

  updateBattery();

  setTimeout(traverseNext, 700);
}

/* =========================================================
   PAUSE
========================================================= */

elements.pauseBtn.addEventListener("click", () => {
  if (state.phase !== "rescue" && !state.returning) {
    return;
  }

  state.running = !state.running;

  if (state.running) {
    elements.controlStatus.textContent = "AUTO";

    elements.pauseBtn.querySelector("b").textContent = "Pause";

    if (!state.returning) {
      setTimeout(traverseNext, 200);
    } else {
      setTimeout(returnNext, 200);
    }
  } else {
    elements.controlStatus.textContent = "PAUSED";

    elements.pauseBtn.querySelector("b").textContent = "Resume";
  }
});

/* =========================================================
   RETURN TO BASE
========================================================= */

elements.rtbBtn.addEventListener("click", () => {
  if (state.phase !== "rescue") {
    return;
  }

  if (state.currentIndex === 0) {
    elements.pathStatus.textContent = "Drone already at base";

    return;
  }

  state.returning = true;
  state.running = true;

  elements.controlStatus.textContent = "RTB";

  elements.routeBadge.textContent = "RETURNING";

  elements.flightMode.textContent = "RETURN";

  elements.pathStatus.textContent = "Returning to base along completed route";

  elements.rtbBtn.disabled = true;

  setTimeout(returnNext, 300);
});

/* =========================================================
   RETURN TRAVERSAL
========================================================= */

function returnNext() {
  if (!state.running) {
    return;
  }

  if (!state.returning) {
    return;
  }

  if (state.currentIndex <= 0) {
    finishReturn();

    return;
  }

  state.currentIndex--;

  moveDrone(state.currentIndex);

  setTimeout(returnNext, 700);
}

/* =========================================================
   FINISH RETURN
========================================================= */

function finishReturn() {
  state.running = false;
  state.returning = false;
  state.currentIndex = 0;

  moveDrone(0);

  elements.routeBadge.textContent = "AT BASE";

  elements.controlStatus.textContent = "STANDBY";

  elements.flightMode.textContent = "STANDBY";

  elements.pathStatus.textContent = "Drone safely returned to base";

  elements.rtbBtn.disabled = false;

  elements.pauseBtn.querySelector("b").textContent = "Pause";
}

/* =========================================================
   FINISH SEARCH
========================================================= */

function startAStarPlanning() {
  state.phase = "planning";
  state.running = false;

  elements.routeBadge.classList.add("loading");
  elements.pathStatus.classList.add("loading");
  elements.routeBadge.textContent = "A* PLANNING";
  elements.controlStatus.textContent = "A*";
  elements.flightMode.textContent = "A*";
  elements.pathStatus.textContent = "Finding shortest rescue path...";

  setTimeout(() => {
    state.route = state.rescueRoute;
    state.currentIndex = 0;
    state.phase = "rescue";
    state.running = true;

    elements.plannedRoute.setAttribute("points", "");
    elements.completedRoute.setAttribute("points", "");
    elements.rescueRoute.classList.remove("mission-hidden");
    elements.droneMarker.classList.remove("mission-hidden");
    elements.routeBadge.classList.remove("loading");
    elements.pathStatus.classList.remove("loading");
    elements.routeBadge.textContent = "RESCUE ACTIVE";
    elements.controlStatus.textContent = "AUTO";
    elements.flightMode.textContent = "RESCUE";
    elements.pathStatus.textContent = "Shortest A* path active from exit";

    moveDrone(0);
    setTimeout(traverseRescueNext, 700);
  }, 3000);
}

function startReturnFromRescue() {
  state.returning = true;
  state.running = true;
  elements.routeBadge.textContent = "RETURNING";
  elements.controlStatus.textContent = "RTB";
  elements.flightMode.textContent = "RETURN";
  elements.pathStatus.textContent = "Returning along the same A* rescue path";
  elements.rtbBtn.disabled = true;
  setTimeout(returnNext, 700);
}

/* =========================================================
   VICTIM DETECTION AND A* PLANNING SEQUENCE
========================================================= */

function startMissionSequence() {
  state.phase = "scanning";
  state.running = true;
  state.route = state.searchRoute;
  state.currentIndex = 0;

  elements.rescueRoute.classList.add("mission-hidden");
  elements.plannedRoute.classList.remove("mission-hidden");
  elements.droneMarker.classList.remove("mission-hidden");
  elements.routeBadge.classList.add("loading");
  elements.pathStatus.classList.add("loading");
  elements.routeBadge.textContent = "SEARCHING";
  elements.pathStatus.textContent = "Scanning zig-zag route for victims...";
  elements.flightMode.textContent = "SCAN";
  elements.controlStatus.textContent = "AUTO";

  moveDrone(0);
  setTimeout(traverseNext, 700);
}

function traverseRescueNext() {
  if (!state.running || state.returning) {
    return;
  }

  if (state.currentIndex >= RESCUE_WAYPOINTS - 1) {
    startReturnFromRescue();
    return;
  }

  state.currentIndex++;
  moveDrone(state.currentIndex);
  updateBattery();
  setTimeout(traverseRescueNext, 700);
}

/* =========================================================
   REROUTE
========================================================= */

elements.rerouteBtn.addEventListener("click", () => {
  if (state.returning) {
    return;
  }

  elements.routeBadge.textContent = "REROUTING";

  elements.controlStatus.textContent = "REROUTE";

  elements.pathStatus.textContent = "Calculating alternate coverage path...";

  state.running = false;

  setTimeout(() => {
    state.running = true;

    elements.routeBadge.textContent = "SEARCH ACTIVE";

    elements.controlStatus.textContent = "AUTO";

    elements.pathStatus.textContent = "Alternate search route active";

    setTimeout(traverseNext, 300);
  }, 1000);
});

/* =========================================================
   BATTERY
========================================================= */

function updateBattery() {
  state.battery = Math.max(20, state.battery - 0.12);

  const value = Math.round(state.battery);

  elements.battery.textContent = `${value}%`;

  elements.batteryBar.style.width = `${value}%`;

  if (value > 50) {
    elements.batteryBar.style.background = "var(--mint)";
  } else if (value > 25) {
    elements.batteryBar.style.background = "var(--gold)";
  } else {
    elements.batteryBar.style.background = "var(--coral)";
  }
}

/* =========================================================
   TELEMETRY SIMULATION
========================================================= */

let telemetryTick = 0;

setInterval(() => {
  telemetryTick++;

  elements.altitude.textContent = `${
    42 + Math.round(Math.sin(telemetryTick / 3) * 4)
  }m`;

  if (Math.random() > 0.93) {
    elements.lora.textContent = "weak";

    elements.loraDot.className = "dot warn";
  } else {
    elements.lora.textContent = "stable";

    elements.loraDot.className = "dot live";
  }
}, 2500);

/* =========================================================
   CAMERA FRAME
========================================================= */

const canvas = document.getElementById("feedCanvas");

const ctx = canvas.getContext("2d");

function resizeCanvas() {
  const rect = canvas.parentElement.getBoundingClientRect();

  canvas.width = rect.width;

  canvas.height = rect.height;
}

window.addEventListener("resize", resizeCanvas);

resizeCanvas();

function drawFrame() {
  const w = canvas.width;

  const h = canvas.height;

  if (!w || !h) {
    return;
  }

  const gradient = ctx.createRadialGradient(
    w * 0.5,
    h * 0.45,
    Math.min(w, h) * 0.05,
    w * 0.5,
    h * 0.5,
    Math.max(w, h) * 0.8,
  );

  gradient.addColorStop(0, "#24132B");

  gradient.addColorStop(1, "#08050D");

  ctx.fillStyle = gradient;

  ctx.fillRect(0, 0, w, h);

  /* terrain */

  ctx.strokeStyle = "rgba(242,145,201,.055)";

  ctx.lineWidth = 1;

  const grid = Math.max(28, Math.floor(w / 15));

  for (let x = 0; x < w; x += grid) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }

  for (let y = 0; y < h; y += grid) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  /* buildings */

  ctx.fillStyle = "rgba(242,145,201,.035)";

  ctx.strokeStyle = "rgba(242,145,201,.13)";

  [
    [0.08, 0.2, 0.25, 0.25],
    [0.53, 0.15, 0.32, 0.3],
    [0.26, 0.58, 0.2, 0.25],
    [0.68, 0.58, 0.2, 0.22],
  ].forEach(([x, y, ww, hh]) => {
    ctx.fillRect(w * x, h * y, w * ww, h * hh);

    ctx.strokeRect(w * x, h * y, w * ww, h * hh);
  });

  /* center target */

  ctx.strokeStyle = "rgba(177,133,245,.2)";

  ctx.setLineDash([4, 5]);

  ctx.beginPath();

  ctx.arc(w * 0.5, h * 0.5, Math.min(w, h) * 0.2, 0, Math.PI * 2);

  ctx.stroke();

  ctx.beginPath();

  ctx.arc(w * 0.5, h * 0.5, Math.min(w, h) * 0.38, 0, Math.PI * 2);

  ctx.stroke();

  ctx.setLineDash([]);

  state.frameCount++;

  elements.frameCount.textContent = `FRAME ${state.frameCount}`;
}

setInterval(drawFrame, 850);

drawFrame();

/* =========================================================
   CLOCK
========================================================= */

function updateClock() {
  const now = new Date();

  elements.clock.textContent = now.toLocaleTimeString("en-GB");

  const elapsed = Math.floor((Date.now() - state.startTime) / 1000);

  const h = String(Math.floor(elapsed / 3600)).padStart(2, "0");

  const m = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");

  const s = String(elapsed % 60).padStart(2, "0");

  elements.missionClock.textContent = `Elapsed ${h}:${m}:${s}`;
}

setInterval(updateClock, 1000);

updateClock();

/* =========================================================
   INITIALIZATION
========================================================= */

function init() {
  buildGrid();

  buildRoute();

  renderDetections();

  elements.rescueRoute.classList.add("mission-hidden");
  elements.droneMarker.classList.add("mission-hidden");

  elements.routeBadge.textContent = "SYSTEM READY";

  elements.pathStatus.textContent = "Preparing victim detection sequence";

  elements.coverageValue.textContent = "0%";

  /*
     Start after a short delay so the dashboard
     can be seen before the drone moves.
  */

  setTimeout(startMissionSequence, 1200);
}

init();
