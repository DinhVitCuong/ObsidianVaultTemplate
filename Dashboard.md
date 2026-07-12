---
type: dashboard
status: active
cssclasses:
  - dashboard-purple
tags:
  - dashboard
  - home
---

# NezuMiii Lazy Dashboard

> [!dashboard-visuals]
> > [!dashboard-panel]
> > ![[Assets/Dashboard/reference-layout.png|Dashboard reference]]
>
> > [!dashboard-panel]
> > ```juggl
> > local: Dashboard
> > layout: force-directed
> > width: 100%
> > height: 20rem
> > limit: 160
> > navigator: false
> > toolbar: false
> > ```

> [!dashboard-graph-seed]
> [[TODO]] · [[Daily Notes]] · [[Machine/Graph/retrieval-map]] · [[Machine/Graph/GRAPH_REPORT]] · [[Sources/github_trending_targets]] · [[Sources/hf_hub_targets]]

```dataviewjs
const now = dv.luxon.DateTime.now();
const todayPath = `daily_notes/${now.toFormat("yyyy/MM/dd")}`;
const allPages = dv.pages().where(p => !p.file.path.startsWith(".")).array();
const dailyPages = dv.pages('"daily_notes"').array();
const tasks = dv.pages().file.tasks;
const doneTasks = tasks.where(t => t.completed);
const graphPages = dv.pages('"Machine/Graph"').array();
const graphReport = graphPages.find(p => p.type === "graph-report");
const retrievalMap = graphPages.find(p => p.type === "retrieval-map");
function asDate(value) {
  if (!value) return null;
  const date = dv.date(value);
  return date && date.isValid !== false ? date : null;
}
function formatDate(value, format, fallback = "") {
  const date = asDate(value);
  return date ? date.toFormat(format) : fallback;
}
const graphGeneratedAt = graphReport?.generated_at
  ? formatDate(graphReport.generated_at, "MM-dd HH:mm", "pending")
  : "pending";
const jugglPluginId = "juggl";
const jugglAvailable = !!app.plugins?.plugins?.[jugglPluginId];
const plotlyPath = "Assets/vendor/plotly-2.35.2.min.js";
const taskGanttFolderPath = "Machine/TaskGantt/Start-of-Day";
const plotlyExists = !!app.vault.getAbstractFileByPath(plotlyPath);
const plotlySrc = plotlyExists && typeof app.vault.adapter.getResourcePath === "function"
  ? app.vault.adapter.getResourcePath(plotlyPath)
  : plotlyPath;

const startOfDayTasks = [];
for (const page of dailyPages) {
  const text = await dv.io.load(page.file.path);
  const lines = text.split("\n");
  const startLine = lines.findIndex(line => /^## Start of day\s*$/.test(line));
  const endLine = lines.findIndex(line => /^## End of day\s*$/.test(line));
  if (startLine === -1 || endLine === -1) continue;

  const pageTasks = page.file.tasks
    .where(task => task.line > startLine && task.line < endLine)
    .array();
  startOfDayTasks.push(...pageTasks);
}

const openTasks = dv.array(startOfDayTasks).where(t => !t.completed);
const overdueTasks = openTasks.where(t => t.due && t.due < now.startOf("day"));

const dailyDates = new Set(dailyPages
  .map(p => {
    if (p.date) return formatDate(p.date, "yyyy-MM-dd", null);
    const match = p.file.path.match(/daily_notes\/(\d{4})\/(\d{2})\/(\d{2})\.md$/);
    return match ? `${match[1]}-${match[2]}-${match[3]}` : null;
  })
  .filter(Boolean));

let streak = 0;
let cursor = now.startOf("day");
while (dailyDates.has(cursor.toFormat("yyyy-MM-dd"))) {
  streak++;
  cursor = cursor.minus({ days: 1 });
}

const recentPages = allPages
  .filter(p => !p.file.path.startsWith("Machine/Graph/") && !p.file.path.startsWith("graphify-out/"))
  .sort((a, b) => b.file.mtime - a.file.mtime)
  .slice(0, 6);

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function link(path, label = null) {
  const clean = String(path).replace(/\.md$/, "");
  return `<a class="internal-link" data-href="${esc(clean)}" href="${esc(clean)}">${esc(label ?? clean)}</a>`;
}

function noteLabel(page) {
  const path = page.file.path;
  const dailyMatch = path.match(/^daily_notes\/(\d{4})\/(\d{2})\/(\d{2})\.md$/);
  if (dailyMatch) return `Daily ${dailyMatch[1]}-${dailyMatch[2]}-${dailyMatch[3]}`;

  const inboxMatch = path.match(/^Inbox\/([^/]+)\/(\d{4})\/(\d{2})\/(\d{2})\.md$/);
  if (inboxMatch) return `${inboxMatch[1]} ${inboxMatch[2]}-${inboxMatch[3]}-${inboxMatch[4]}`;

  return page.file.name;
}

function dailyLink(path, label, date) {
  const clean = String(path).replace(/\.md$/, "");
  return `<a class="internal-link dash-daily-link" data-href="${esc(clean)}" href="${esc(clean)}" data-daily-path="${esc(clean)}.md" data-daily-date="${esc(date.toFormat("yyyy-MM-dd"))}">${esc(label)}</a>`;
}

function table(headers, rows) {
  return `<table><thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${
    rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("")
  }</tbody></table>`;
}

function taskRows(source, limit = 5) {
  return source.limit(limit).map(t => {
    const path = t.path ? t.path.replace(/\.md$/, "") : "";
    const due = formatDate(t.due, "MM-dd");
    return [esc(t.text), due || "-", path ? link(path, "note") : ""];
  });
}

function dailyKeyFromPath(path) {
  const match = String(path ?? "").match(/^daily_notes\/(\d{4})\/(\d{2})\/(\d{2})\.md$/);
  return match ? `${match[1]}-${match[2]}-${match[3]}` : null;
}

function taskDate(task) {
  const dailyKey = dailyKeyFromPath(task.path);
  return dailyKey ? asDate(dailyKey) : asDate(task.due);
}

function taskTrendContainer(id) {
  return `<div class="task-trend-widget">
    <div id="${esc(id)}" class="plotly-card-chart"></div>
    <div class="task-trend-range" aria-label="Task trend date range">
      <div class="task-trend-range-labels">
        <span data-range-start-label></span>
        <span>Date range</span>
        <span data-range-end-label></span>
      </div>
      <div class="task-trend-range-inputs">
        <span class="task-trend-selected" data-range-selected></span>
        <span class="task-trend-handle task-trend-handle-start" data-range-start-handle></span>
        <span class="task-trend-handle task-trend-handle-end" data-range-end-handle></span>
      </div>
    </div>
  </div>`;
}

function taskTrendDateRange(source) {
  const dates = source
    .map(task => taskDate(task))
    .filter(Boolean)
    .map(date => date.startOf("day"))
    .array()
    .sort((a, b) => a.toMillis() - b.toMillis());

  if (!dates.length) {
    const today = now.startOf("day");
    return { min: today, max: today };
  }

  const min = dates[0];
  const maxTaskDate = dates[dates.length - 1];
  const max = maxTaskDate > now.startOf("day") ? maxTaskDate : now.startOf("day");
  return { min, max };
}

function buildTaskTrend(source) {
  const { min, max } = taskTrendDateRange(source);
  const items = source
    .map(task => ({ task, date: taskDate(task) }))
    .filter(item => item.date)
    .array();
  const points = [];
  let cursor = min.startOf("day");
  const end = max.startOf("day");

  while (cursor <= end) {
    const dayEnd = cursor.endOf("day");
    const scoped = dv.array(items).where(item => item.date <= dayEnd);
    points.push({
      date: cursor.toFormat("yyyy-MM-dd"),
      label: cursor.toFormat("MMM dd, yyyy"),
      pending: scoped.where(item => !item.task.completed).length,
      completed: scoped.where(item => item.task.completed).length,
    });
    cursor = cursor.plus({ days: 1 });
  }

  return points;
}

function taskPriority(task) {
  const text = String(task.text ?? "");
  if (task.priority) return String(task.priority).toLowerCase();
  if (text.includes("⏫")) return "highest";
  if (text.includes("🔼")) return "high";
  if (text.includes("🔺")) return "medium";
  if (text.includes("🔽")) return "low";
  if (text.includes("⏬")) return "lowest";
  return "normal";
}

function cleanTaskText(text) {
  return String(text ?? "")
    .replace(/[🛫📅✅➕⏳]\s*\d{4}-\d{2}-\d{2}/g, "")
    .replace(/[⏫🔼🔺🔽⏬]/g, "")
    .replace(/\b(?:due|scheduled|start|created|done)\s+\d{4}-\d{2}-\d{2}\b/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function safeTaskGanttFileName(value) {
  return String(value ?? "Task")
    .replace(/[\\/:*?"<>|#^\[\]]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 90)
    .replace(/[. ]+$/g, "") || "Task";
}

function yamlString(value) {
  return `"${String(value ?? "").replaceAll("\\", "\\\\").replaceAll('"', '\\"')}"`;
}

function taskGanttNote(task, index) {
  const sourceDate = taskDate(task) || now.startOf("day");
  const due = asDate(task.due) || sourceDate;
  const source = task.path || "";
  const priority = taskPriority(task);
  const completed = !!task.completed;
  return [
    "---",
    `start: ${sourceDate.toFormat("yyyy-MM-dd")}`,
    `end: ${due.toFormat("yyyy-MM-dd")}`,
    `status: ${completed ? "done" : "todo"}`,
    `source: ${yamlString(source)}`,
    `source_line: ${task.line ?? ""}`,
    "tags:",
    "  - task-gantt",
    "  - start-of-day",
    `  - priority/${priority}`,
    completed ? "  - done" : "",
    "---",
    "",
    `- [${completed ? "x" : " "}] ${task.text}`,
    "",
    source ? `Source: [[${source.replace(/\.md$/, "")}]]` : "",
    "",
    "<!-- Generated from TODO.md > Daily Start-of-Day Tasks. Edit the source daily note, then reopen Task Gantt. -->",
    "",
  ].join("\n");
}

async function syncTaskGanttNotes() {
  await ensureFolder(`${taskGanttFolderPath}/.keep`);
  const existing = app.vault.getFiles()
    .filter(file => file.path.startsWith(`${taskGanttFolderPath}/`) && file.extension === "md");
  for (const file of existing) {
    await app.vault.delete(file);
  }

  const items = dv.array(startOfDayTasks)
    .sort(t => taskDate(t) ?? now.plus({ years: 10 }))
    .array();

  for (const [index, task] of items.entries()) {
    const filename = `${String(index + 1).padStart(3, "0")} - ${safeTaskGanttFileName(task.text)}.md`;
    await app.vault.create(`${taskGanttFolderPath}/${filename}`, taskGanttNote(task, index + 1));
  }
}

function taskGanttPanel(source) {
  const items = source
    .sort(t => taskDate(t) ?? now.plus({ years: 10 }))
    .limit(12)
    .array()
    .map(task => {
      const start = taskDate(task) || now.startOf("day");
      const due = asDate(task.due);
      const end = due && due >= start ? due : start.plus({ days: 1 });
      return { task, start: start.startOf("day"), end: end.startOf("day") };
    });

  if (!items.length) {
    return `<div class="inline-gantt empty-gantt">
      <div class="inline-gantt-toolbar">
        ${link("TODO#Daily Start-of-Day Tasks", "Daily Start-of-Day Tasks")}
        <button class="gantt-plugin-open" type="button">Open Plugin</button>
      </div>
      <p class="muted">No open start-of-day tasks.</p>
    </div>`;
  }

  let min = items[0].start;
  let max = items[0].end;
  for (const item of items.slice(1)) {
    if (item.start < min) min = item.start;
    if (item.end > max) max = item.end;
  }
  max = max.plus({ days: 1 });
  const totalDays = Math.max(1, Math.ceil(max.diff(min, "days").days));
  const scale = Array.from({ length: Math.min(totalDays + 1, 8) }, (_, index) => {
    const day = min.plus({ days: Math.round((totalDays * index) / Math.min(totalDays, 7)) });
    return `<span style="left:${Math.min(100, (day.diff(min, "days").days / totalDays) * 100)}%">${esc(day.toFormat("MM-dd"))}</span>`;
  }).join("");

  const rows = items.map(({ task, start, end }) => {
    const offset = Math.max(0, start.diff(min, "days").days);
    const duration = Math.max(1, end.diff(start, "days").days);
    const left = Math.min(96, (offset / totalDays) * 100);
    const width = Math.max(4, Math.min(100 - left, (duration / totalDays) * 100));
    const sourceDate = taskDate(task);
    const due = formatDate(task.due, "MM-dd", "no due");
    const path = task.path ? task.path.replace(/\.md$/, "") : "";
    const priority = taskPriority(task);
    const title = cleanTaskText(task.text) || task.text;
    return `<details class="inline-gantt-row priority-${esc(priority)}">
      <summary>
        <span class="gantt-task-title">${esc(title)}</span>
        <span class="gantt-track" aria-label="${esc(title)} from ${esc(start.toFormat("yyyy-MM-dd"))} to ${esc(end.toFormat("yyyy-MM-dd"))}">
          <i style="left:${left}%;width:${width}%"></i>
        </span>
        <span class="gantt-due">${esc(due)}</span>
      </summary>
      <div class="gantt-row-detail">
        <span>${esc(sourceDate ? sourceDate.toFormat("yyyy-MM-dd") : "undated")}</span>
        ${path ? link(path, "open note") : ""}
      </div>
    </details>`;
  }).join("");

  return `<div class="inline-gantt">
    <div class="inline-gantt-toolbar">
      ${link("TODO#Daily Start-of-Day Tasks", "Daily Start-of-Day Tasks")}
      <button class="gantt-plugin-open" type="button">Open Plugin</button>
    </div>
    <div class="inline-gantt-scale">${scale}</div>
    ${rows}
  </div>`;
}

async function ensurePlotly() {
  if (window.Plotly) return window.Plotly;
  if (!plotlyExists) throw new Error("Plotly local asset is missing");

  const existing = document.querySelector(`script[data-dashboard-plotly="${plotlyPath}"]`);
  if (existing) {
    await new Promise((resolve, reject) => {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", reject, { once: true });
      if (window.Plotly) resolve();
    });
    return window.Plotly;
  }

  await new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = plotlySrc;
    script.dataset.dashboardPlotly = plotlyPath;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
  return window.Plotly;
}

async function renderTaskTrendPlot() {
  const el = page.querySelector("#task-trend-plot");
  if (!el) return;
  const widget = el.closest(".task-trend-widget");
  const rangeEl = widget?.querySelector(".task-trend-range");
  const rangeTrack = rangeEl?.querySelector(".task-trend-range-inputs");
  const startLabel = rangeEl?.querySelector("[data-range-start-label]");
  const endLabel = rangeEl?.querySelector("[data-range-end-label]");
  const selectedRail = rangeEl?.querySelector("[data-range-selected]");
  const startHandle = rangeEl?.querySelector("[data-range-start-handle]");
  const endHandle = rangeEl?.querySelector("[data-range-end-handle]");

  try {
    const Plotly = await ensurePlotly();
    if (!taskTrend.length) {
      el.innerHTML = `<div class="muted">No dated start-of-day tasks yet.</div>`;
      if (rangeEl) rangeEl.hidden = true;
      return;
    }

    let startIndex = 0;
    let endIndex = taskTrend.length - 1;

    function syncRangeLabels() {
      if (startLabel) startLabel.textContent = taskTrend[startIndex].label;
      if (endLabel) endLabel.textContent = taskTrend[endIndex].label;
      const maxIndex = Math.max(1, taskTrend.length - 1);
      const startPct = (startIndex / maxIndex) * 100;
      const endPct = (endIndex / maxIndex) * 100;
      if (selectedRail) {
        selectedRail.style.left = `${startPct}%`;
        selectedRail.style.width = `${Math.max(0, endPct - startPct)}%`;
      }
      if (startHandle) {
        startHandle.style.left = startPct === 0 ? "0" : `calc(${startPct}% - 0.35rem)`;
      }
      if (endHandle) {
        endHandle.style.left = endPct === 100 ? "calc(100% - 0.7rem)" : `calc(${endPct}% - 0.35rem)`;
      }
      if (startHandle) {
        startHandle.setAttribute("aria-valuenow", String(startIndex));
        startHandle.setAttribute("aria-valuetext", taskTrend[startIndex].label);
      }
      if (endHandle) {
        endHandle.setAttribute("aria-valuenow", String(endIndex));
        endHandle.setAttribute("aria-valuetext", taskTrend[endIndex].label);
      }
    }

    function selectedTrend() {
      return taskTrend.slice(startIndex, endIndex + 1);
    }

    function drawTrend() {
      const visibleTrend = selectedTrend();
      syncRangeLabels();

      Plotly.react(el, [
        {
          x: visibleTrend.map(p => p.date),
          y: visibleTrend.map(p => p.pending),
          text: visibleTrend.map(p => p.label),
          name: "Pending",
          mode: "lines+markers",
          line: { color: "#e95d4f", width: 3 },
          marker: { size: 7 },
          hovertemplate: "Pending: %{y}<extra></extra>",
        },
        {
          x: visibleTrend.map(p => p.date),
          y: visibleTrend.map(p => p.completed),
          text: visibleTrend.map(p => p.label),
          name: "Completed",
          mode: "lines+markers",
          line: { color: "#0f9f9c", width: 3 },
          marker: { size: 7 },
          hovertemplate: "Completed: %{y}<extra></extra>",
        },
      ], {
        margin: { l: 34, r: 12, t: 8, b: 34 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        hovermode: "x unified",
        xaxis: {
          type: "date",
          fixedrange: false,
          showgrid: false,
          tickformat: "%b %-d",
          hoverformat: "%b %-d, %Y",
        },
        yaxis: { rangemode: "tozero", fixedrange: false, gridcolor: "rgba(109,40,217,0.12)" },
        legend: { orientation: "h", x: 0, y: 1.18 },
        font: { size: 11 },
      }, { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["lasso2d", "select2d"] });
    }

    if (rangeTrack && startHandle && endHandle) {
      const maxIndex = taskTrend.length - 1;
      const updateHandle = (which, nextIndex) => {
        const index = Math.max(0, Math.min(maxIndex, nextIndex));
        if (which === "start") startIndex = Math.min(index, endIndex);
        else endIndex = Math.max(index, startIndex);
        drawTrend();
      };

      const indexFromEvent = event => {
        const rect = rangeTrack.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
        return Math.round(ratio * maxIndex);
      };

      const beginDrag = (which, event) => {
        event.preventDefault();
        if (taskTrend.length < 2) return;
        updateHandle(which, indexFromEvent(event));
        const move = moveEvent => updateHandle(which, indexFromEvent(moveEvent));
        const stop = () => {
          window.removeEventListener("pointermove", move);
          window.removeEventListener("pointerup", stop);
        };
        window.addEventListener("pointermove", move);
        window.addEventListener("pointerup", stop, { once: true });
      };

      const handleKey = (which, event) => {
        const delta = event.key === "ArrowLeft" ? -1 : event.key === "ArrowRight" ? 1 : 0;
        if (!delta) return;
        event.preventDefault();
        updateHandle(which, (which === "start" ? startIndex : endIndex) + delta);
      };

      for (const [handle, which, label] of [
        [startHandle, "start", "Start date"],
        [endHandle, "end", "End date"],
      ]) {
        handle.tabIndex = 0;
        handle.setAttribute("role", "slider");
        handle.setAttribute("aria-label", label);
        handle.setAttribute("aria-valuemin", "0");
        handle.setAttribute("aria-valuemax", String(maxIndex));
        handle.addEventListener("pointerdown", event => beginDrag(which, event));
        handle.addEventListener("keydown", event => handleKey(which, event));
      }

      rangeTrack.addEventListener("pointerdown", event => {
        if (event.target === startHandle || event.target === endHandle) return;
        const nextIndex = indexFromEvent(event);
        const startDistance = Math.abs(nextIndex - startIndex);
        const endDistance = Math.abs(nextIndex - endIndex);
        beginDrag(startDistance <= endDistance ? "start" : "end", event);
      });
    }

    drawTrend();
  } catch (error) {
    console.error("Failed to render Plotly task trend", error);
    el.innerHTML = `<div class="muted">Plotly could not load from ${esc(plotlyPath)}.</div>`;
  }
}

const taskTrend = buildTaskTrend(dv.array(startOfDayTasks));

const page = dv.el("div", "", { cls: "dash-page" });
const shell = document.createElement("div");
shell.className = "dash-shell";
const layout = document.createElement("div");
layout.className = "dash-main dash-layout";
const sidebar = document.createElement("aside");
sidebar.className = "dash-sidebar";
shell.appendChild(layout);
shell.appendChild(sidebar);
page.appendChild(shell);

function card(title, body, cls = "", target = layout) {
  const section = document.createElement("section");
  section.className = `dash-card ${cls}`;
  section.innerHTML = `<header>${esc(title)}</header><div class="dash-card-body">${body}</div>`;
  target.appendChild(section);
}

function sideCard(title, body, cls = "") {
  card(title, body, cls, sidebar);
}

function pill(label, value) {
  return `<div class="metric"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`;
}

const monthStart = now.startOf("month").startOf("week");
const monthEnd = now.endOf("month").endOf("week");
const calendarRows = [];
let day = monthStart;
while (day <= monthEnd) {
  const week = [];
  for (let i = 0; i < 7; i++) {
    const path = `daily_notes/${day.toFormat("yyyy/MM/dd")}`;
    const state = [
      day.hasSame(now, "day") ? "is-today" : "",
      day.month === now.month ? "" : "is-muted",
      dailyDates.has(day.toFormat("yyyy-MM-dd")) ? "has-note" : "",
    ].filter(Boolean).join(" ");
    week.push(`<span class="${state}">${dailyLink(path, day.toFormat("dd"), day)}</span>`);
    day = day.plus({ days: 1 });
  }
  calendarRows.push(week);
}

const tagCounts = new Map();
for (const page of allPages) {
  for (const tag of page.file.tags || []) tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
}
const topTags = [...tagCounts.entries()]
  .sort((a, b) => b[1] - a[1])
  .slice(0, 10)
  .map(([tag, count]) => `<span class="dash-pill">${esc(tag)} ${count}</span>`)
  .join("");

card("Start Here", `
  <div class="quick-links">
    ${dailyLink(todayPath, now.toFormat("cccc, dd LLL yyyy"), now)}
    ${link("TODO", "TODO")}
    ${link("Daily Notes", "Daily Notes")}
    ${link("Machine/Graph/retrieval-map", "Retrieval Map")}
    ${link("Machine/Graph/GRAPH_REPORT", "Graph Report")}
    ${link("Sources/github_trending_targets", "GitHub targets")}
    ${link("Sources/hf_hub_targets", "HF targets")}
  </div>
`, "span-12 hero-card");

card("Monitor", `<div class="metrics-row">
  ${pill("streak", streak)}
  ${pill("daily notes", dailyPages.length)}
  ${pill("open tasks", openTasks.length)}
  ${pill("overdue", overdueTasks.length)}
  ${pill("done", doneTasks.length)}
  ${pill("notes", allPages.length)}
  ${pill("graph index", graphReport ? "ready" : "pending")}
  ${pill("inline graph", jugglAvailable ? "ready" : "reload")}
</div>`, "span-12");

card("Task Trend", taskTrendContainer("task-trend-plot"), "span-6");

card("Task Gantt", taskGanttPanel(openTasks), "span-6 gantt-card");

card("TODO Radar", table(["Task", "Due", "File"], taskRows(openTasks.sort(t => t.due ?? "9999-12-31"), 8)), "span-6 scroll-card");

card("Today", `
  <div class="today-stack">
    <strong>${dailyLink(todayPath, now.toFormat("EEEE, dd LLLL yyyy"), now)}</strong>
    <p>One good daily note, one clean task list, one useful learning signal.</p>
    <div class="mini-actions">
      <label><input type="checkbox"> Write today's note</label>
      <label><input type="checkbox"> Pick top 3 priorities</label>
      <label><input type="checkbox"> Review blockers</label>
    </div>
  </div>
`, "span-3");

card("Source Watchlist", table(["Source", "Updated"], dv.pages('"Sources"')
  .array()
  .sort((a, b) => b.file.mtime - a.file.mtime)
  .map(p => [link(p.file.path.replace(/\.md$/, ""), p.file.name), formatDate(p.file.mtime, "MM-dd HH:mm", "-")])), "span-3");

async function ensureFolder(path) {
  const parts = path.split("/").slice(0, -1);
  let current = "";
  for (const part of parts) {
    current = current ? `${current}/${part}` : part;
    if (!app.vault.getAbstractFileByPath(current)) {
      await app.vault.createFolder(current);
    }
  }
}

function expandDailyTemplate(template, dateKey) {
  const date = window.moment(dateKey, "YYYY-MM-DD");
  const nowMoment = window.moment();
  return template
    .replace(/{{\s*date\s*}}/gi, date.format("YYYY/MM/DD"))
    .replace(/{{\s*time\s*}}/gi, nowMoment.format("HH:mm"))
    .replace(/{{\s*title\s*}}/gi, date.format("YYYY/MM/DD"))
    .replace(/{{\s*date\s*:\s*([^}]+?)\s*}}/gi, (_, format) => date.format(format.trim()))
    .replace(/{{\s*time\s*:\s*([^}]+?)\s*}}/gi, (_, format) => nowMoment.format(format.trim()));
}

page.addEventListener("click", async event => {
  const ganttButton = event.target.closest(".gantt-plugin-open");
  if (ganttButton) {
    event.preventDefault();
    await syncTaskGanttNotes();
    const plugin = app.plugins?.plugins?.["task-gantt"];
    if (plugin?.activateView) {
      await plugin.activateView(taskGanttFolderPath);
      return;
    }

    const commandId = "task-gantt:open-gantt";
    if (app.commands?.commands?.[commandId]) {
      app.commands.executeCommandById(commandId);
    } else if (typeof Notice !== "undefined") {
      new Notice("Reload Obsidian once to activate Task Gantt, then press this again.");
    }
    return;
  }

  const el = event.target.closest(".dash-daily-link");
  if (!el) return;

  const path = el.dataset.dailyPath;
  const dateKey = el.dataset.dailyDate;
  if (!path || !dateKey || app.vault.getAbstractFileByPath(path)) return;

  event.preventDefault();
  event.stopPropagation();

  try {
    const template = await app.vault.adapter.read("Template/Daily.md");
    await ensureFolder(path);
    const file = await app.vault.create(path, expandDailyTemplate(template, dateKey));
    await app.workspace.getLeaf(false).openFile(file);
  } catch (error) {
    console.error("Failed to create daily note from dashboard template", error);
    if (typeof Notice !== "undefined") {
      new Notice("Could not create daily note from Template/Daily.md");
    }
  }
});

sideCard(now.toFormat("LLLL yyyy"), table(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], calendarRows), "calendar-card");

sideCard("Focus Board", `
  <div class="focus-list">
    <div><b>One thing</b><span>Make today count in ${dailyLink(todayPath, "daily note", now)}</span></div>
    <div><b>Notes</b><span>Update ${link("Daily Notes", "one note")}</span></div>
    <div><b>Tasks</b><span>Triage ${link("TODO", "TODO")}</span></div>
    <div><b>Review</b><span>Wins, blockers, tomorrow</span></div>
  </div>
`);

sideCard("Recent Notes", table(["Note", "Updated"], recentPages.map(p => [
  link(p.file.path.replace(/\.md$/, ""), noteLabel(p)),
  formatDate(p.file.mtime, "MM-dd HH:mm", "-")
])), "scroll-card");

sideCard("Weekly Pulse", table(["Day", "Note"], Array.from({ length: 7 }, (_, i) => {
  const d = now.startOf("day").minus({ days: 6 - i });
  const key = d.toFormat("yyyy-MM-dd");
  const path = `daily_notes/${d.toFormat("yyyy/MM/dd")}`;
  return [d.toFormat("ccc dd"), dailyDates.has(key) ? link(path, "done") : dailyLink(path, "open", d)];
})));

card("Vault Graph", `
  <div class="graph-status">
    <div><b>Juggl inline graph</b><span class="${jugglAvailable ? "status-ready" : "status-pending"}">${jugglAvailable ? "ready" : "reload"}</span></div>
    <div><b>Codex retrieval index</b><span class="${graphReport ? "status-ready" : "status-pending"}">${graphReport ? "ready" : "pending"}</span></div>
    <div><b>Last local index</b><span>${esc(graphGeneratedAt)}</span></div>
  </div>
  <p>${jugglAvailable
    ? "The interactive graph is beside the dashboard image."
    : "Reload Obsidian once to activate the inline graph."}</p>
  ${table(["Output", "Purpose"], [
    [retrievalMap ? link("Machine/Graph/retrieval-map", "retrieval-map.md") : "retrieval-map.md", "Codex first-read map"],
    [graphReport ? link("Machine/Graph/GRAPH_REPORT", "GRAPH_REPORT.md") : "GRAPH_REPORT.md", "Human graph summary"],
    [link("Machine/Graph/graph.json", "graph.json"), "Machine-readable fallback graph"],
  ])}
`, "span-4");

card("Graph Files", table(["File", "Updated"], graphPages
  .filter(p => p.type === "graph-report" || p.type === "retrieval-map")
  .sort((a, b) => a.file.name.localeCompare(b.file.name))
  .map(p => [link(p.file.path.replace(/\.md$/, ""), p.file.name), formatDate(p.file.mtime, "MM-dd HH:mm", "-")])), "span-4");

card("Tag Pulse", `<div class="tag-cloud">${topTags || '<span class="muted">No tags yet</span>'}</div>`, "span-4");

renderTaskTrendPlot();
```
