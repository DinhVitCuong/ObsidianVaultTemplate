---
type: daily
status: active
date: "{{date: YYYY-MM-DD}}"
created: "{{date: YYYY-MM-DD}} {{time: HH:mm}}"
day: "{{date: dddd}}"
tags:
  - daily
  - ai-engineering
---

# {{date: dddd, MMMM D, YYYY}}

[[Dashboard]] | [[Daily Notes]] | [[TODO]]

## Start of day

### Today's Focus
- One thing:
- Priority 2:
- Priority 3:

### Goals
- [ ] 

### What I want to learn today
- 

### Tasks
- [ ] 

### Calendar / hard stops
- 

### Coding tasks
- 

### Questions to investigate
- 

---

## End of day

### Wins
- 

### Finished tasks
```dataviewjs
const current = dv.current();
const targetDate = dv.date(current.date).toFormat("yyyy-MM-dd");

function taskDoneDate(task) {
  if (task.completion) return dv.date(task.completion).toFormat("yyyy-MM-dd");
  const match = String(task.text).match(/✅\s*(\d{4}-\d{2}-\d{2})/);
  return match ? match[1] : null;
}

const finished = [];
for (const page of dv.pages('"daily_notes"').array()) {
  const text = await dv.io.load(page.file.path);
  const lines = text.split("\n");
  const startLine = lines.findIndex(line => /^## Start of day\s*$/.test(line));
  const endLine = lines.findIndex(line => /^## End of day\s*$/.test(line));
  if (startLine === -1 || endLine === -1) continue;

  const tasks = page.file.tasks
    .where(task =>
      task.completed &&
      task.line > startLine &&
      task.line < endLine &&
      taskDoneDate(task) === targetDate
    )
    .array();
  finished.push(...tasks);
}

finished.sort((a, b) => a.path.localeCompare(b.path) || a.line - b.line);

if (finished.length) {
  dv.taskList(finished, true);
} else {
  dv.paragraph("No tasks completed on this date yet.");
}
```

### What I searched today
- 

### What I learned
- 

### What I coded
- 

### New methods / tools / concepts
- 

### Bugs / blockers
- 

### Reusable snippets
- 

### Tomorrow follow-up
- 

### Human reflection
- 
