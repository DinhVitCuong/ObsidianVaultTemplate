---
type: task-hub
status: active
cssclasses:
  - dashboard-purple
tags:
  - todo
  - dashboard
---

# TODO Hub

## Inbox

- [x] Capture the next thing that needs attention ✅ 2026-06-25
- [x] Add due dates to important tasks with `due YYYY-MM-DD` ✅ 2026-06-25
- [x] Split large tasks into 2-3 concrete next actions ✅ 2026-06-29

## This Week

- [ ] Write a daily note every day
- [ ] Summarize notes updated this week
- [ ] Review Sources and pick the themes worth tracking

## Waiting / Later

- [x] Schedule a recurring weekly review ✅ 2026-06-29
- [ ] Add project notes for larger goals

## Smart Task Views

### Daily Start-of-Day Tasks

```dataviewjs
const dailyPages = dv.pages('"daily_notes"').array();
const rows = [];

for (const page of dailyPages) {
  const text = await dv.io.load(page.file.path);
  const lines = text.split("\n");
  const startLine = lines.findIndex(line => /^## Start of day\s*$/.test(line));
  const endLine = lines.findIndex(line => /^## End of day\s*$/.test(line));
  if (startLine === -1 || endLine === -1) continue;

  const tasks = page.file.tasks
    .where(task => !task.completed && task.line > startLine && task.line < endLine)
    .array();
  rows.push(...tasks);
}

rows.sort((a, b) => {
  const aDue = a.due ? dv.date(a.due).toMillis() : Number.MAX_SAFE_INTEGER;
  const bDue = b.due ? dv.date(b.due).toMillis() : Number.MAX_SAFE_INTEGER;
  return aDue - bDue || a.path.localeCompare(b.path) || a.line - b.line;
});

if (rows.length) {
  dv.taskList(rows, false);
} else {
  dv.paragraph("No open start-of-day tasks.");
}
```

### All Open Tasks

```tasks
not done
sort by due
sort by priority
```

### Recently Finished Tasks

```tasks
done
sort by done reverse
limit 20
```
