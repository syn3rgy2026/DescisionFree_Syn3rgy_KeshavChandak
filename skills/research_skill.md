# Deep Research Skill

## What This Skill Does

Enables the agent to conduct thorough, multi-source research on complex topics
without overflowing its context window. Instead of holding all web content in
memory, the agent writes key facts to a local temp file after each page and
synthesises the final report from that file at the end.

---

## When This Skill Is Activated

Triggered automatically when the task contains any of:
`research`, `deep dive`, `investigate`, `analyze`, `analyse`,
`deep research`, `in-depth`, `comprehensive`

---

## The Research Protocol — Follow This Exactly

### Phase 1 — Decompose The Query (do this first, before any searches)

Break the topic into 3–4 focused sub-topics. Write them out as a numbered list
before touching any tool. Example:

```
Topic: "Top AI agent frameworks in 2025"
Sub-topics:
  1. What frameworks exist and their core features
  2. Benchmark comparisons and performance metrics
  3. Community adoption and GitHub activity
  4. Real-world use cases and limitations
```

Announce: `[Step 1/4] Breaking topic into sub-topics...`

---

### Phase 2 — Search and Read (one sub-topic at a time)

For each sub-topic:

1. Call `search_web("<sub-topic query>")` — get the top result URLs
2. Pick the 2 most relevant URLs
3. For each URL:
   - Announce: `[Step 2/4] Reading: <url>`
   - Call `visit_url("<url>")` to fetch clean page text
   - Extract only the key facts relevant to the sub-topic
   - **Immediately** call `write_file` to APPEND those facts to the notes file:

```
write_file("output/temp_research_notes.txt",
    "\n\n<b>Sub-topic:</b> <name>\n<b>Source:</b> <url>\n\n<bullet facts here>")
```

4. Add a brief pause between pages — do not hammer sources.

Rules while reading:
- Extract facts, not entire paragraphs — bullet points only
- Each bullet must be a concrete fact, number, or insight
- Ignore ads, navigation text, cookie notices
- If a page is irrelevant, discard it and move to the next URL

---

### Phase 3 — Verify Notes Exist

After all sub-topics are researched:

- Announce: `[Step 3/4] Verifying notes file...`
- Call `read_file("output/temp_research_notes.txt")` to confirm it has content
- If the file is empty or missing, re-run Phase 2 for the weakest sub-topic

---

### Phase 4 — Synthesise and Clean Up

- Announce: `[Step 4/4] Synthesising final report...`
- Call `read_file("output/temp_research_notes.txt")` — this is your source of truth
- Write the final report using ONLY the facts in the notes file
- Do not invent information not found in your notes
- Structure the report as:

```
<b>[Topic Title]</b>

<b>Executive Summary</b>
2–3 sentence overview of the key finding.

<b>[Sub-topic 1 Heading]</b>
...

<b>[Sub-topic 2 Heading]</b>
...

<b>Key Takeaways</b>
- Bullet list of the 5 most important findings

<b>Sources</b>
- [URL 1]
- [URL 2]
- ...
```

- Save the final report: `write_file("output/research_<topic>_<date>.docx", <report>)`
- Delete the temp file: `delete_file("output/temp_research_notes.txt")`
- Announce: `Done. Report saved to output/research_<topic>_<date>.docx`

---

## Rules That Must Never Be Broken

1. **Never skip the temp file step.** Write facts after every single page.
2. **Never paste full page text into memory.** Extract only bullet facts.
3. **Never claim a task is done** without verifying the output file exists and has content.
4. **Always delete** `temp_research_notes.txt` at the end — it is a working file, not output.
5. **Always cite sources** in the final report — include the URL for every major fact.
6. **If blocked by a site** (403, empty content, paywall) — skip it and try the next URL.
   Do not retry the same blocked URL more than once.
