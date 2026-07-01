---
type: index
status: active
cssclasses:
  - dashboard-purple
tags:
  - daily
  - index
---

# Daily Notes

## Latest

```dataview
TABLE date as "Date", file.mtime as "Updated"
FROM "daily_notes"
SORT file.name DESC
LIMIT 30
```

## Writing Streak

```dataviewjs
const today = dv.luxon.DateTime.now().startOf("day");
const notes = dv.pages('"daily_notes"').array();
const days = new Set(notes.map(p => {
if (p.date) return dv.date(p.date).toFormat("yyyy-MM-dd");
if (/^\d{2}$/.test(p.file.name)) {
  const match = p.file.path.match(/daily_notes\/(\d{4})\/(\d{2})\/(\d{2})\.md$/);
  if (match) return `${match[1]}-${match[2]}-${match[3]}`;
}
return null;
}).filter(Boolean));

let streak = 0;
let cursor = today;
while (days.has(cursor.toFormat("yyyy-MM-dd"))) {
  streak++;
  cursor = cursor.minus({ days: 1 });
}

dv.paragraph(`Current streak: **${streak} day${streak === 1 ? "" : "s"}**`);
```

## Quick Links

- [[Dashboard]]
- [[daily_notes/2026/06/24]]
- [[Template/Daily]]
