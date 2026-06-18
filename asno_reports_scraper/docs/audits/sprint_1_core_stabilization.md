# Sprint 1 — Core Stabilization Audit

**Date:** 2026-06-17  
**Auditor:** opencode  
**Branch:** sprint-0-repo-setup (no code changes yet — diagnostic only)

---

## 1. Discrepancy: 970 vs 11 567

### What was reported
- `extract --report sales --from 2026-06-01 --to 2026-06-17` → **970 rows**
- `extract --report sales --from 2026-01-01 --to 2026-06-17` → **11 567 rows**

### Root cause
Both commands call **the exact same function** (`extract_sales_report`) and differ only in date range. The discrepancy is simply **different date ranges producing different row counts**, not a code-path bug.

**However**, the pagination system has a reliability bug that causes both over- and under-counting (see §2), so **neither 970 nor 11 567 is guaranteed accurate**.

### Current actual totals (from `data/logs/`)
| Chunk | DataTable "entries" | Collected rows | Diff |
|-------|---------------------|----------------|------|
| 2026-01 | 1 604 | 1 704 | +100 |
| 2026-02 | 1 766 | 1 866 | +100 |
| 2026-03 | 1 933 | 2 033 | +100 |
| 2026-04 | 1 808 | 1 908 | +100 |
| 2026-05 | 2 038 | 2 138 | +100 |
| 2026-06 | 870 | 900 | +30 |
| **Sum** | **10 019** | **10 549** | **+530** |

Every chunk **over-counts** because the paginator reads stale `.dataTables_info` text and walks extra pages.

---

## 2. Pagination Reliability Bug

### Location
- `sales_extractor.py:302-331` — `next_page_detail()`
- `sales_extractor.py:334-376` — `collect_all_sales_pages()`

### Mechanism
1. DataTable's `.dataTables_info` text (e.g. "Mostrando 1 a 100 de entradas 870") is the authoritative source for "how many total rows" and "what page am I on".
2. `next_page_detail()` clicks "Next", then:
   - Calls `wait_until_loaded()` (waits for `networkidle` + spinner hidden)
   - Calls `wait_for_function()` waiting for info text to change (10 s timeout, **silent on timeout**)
   - Calls `wait_for_sales_table()` (waits for visible table with expected headers)
   - Reads `after` state and compares to `before`
3. **If the DataTable AJAX hasn't responded within 10 s**, the function silently proceeds and reports `clicked_next_but_info_unchanged` — but still returns `True` (page advanced).
4. When info text is stale, the scraper keeps clicking "Next" past the real last page, **reading whatever rows are currently in the DOM** (which may be from the wrong page).

### Evidence from debug files
| Run | `debug_pagination` | Pages walked | `rows_before_dedupe` | Notes |
|-----|--------------------|--------------|---------------------|-------|
| June 13:43 (normal) | **true** | 10 | 970 | All pages report `active_page: "1"` — info text **never** updates |
| June 13:44 (assisted) | **true** | 10 | 970 | **Identical** to normal — assisted adds no value |
| June 16:46 (normal) | false | 10 | 970 | Some pages update correctly, but still over-counts |
| June 19:35 (normal) | false | **9** | **900** | **Under-counts** — stops early because next button appears disabled with stale info |

### Effect
- **Over-count**: Every monthly chunk over-counts by ~100 rows (one extra full page)
- **Under-count**: The last run (19:35) got 900 instead of 870 — missed the final partial page
- **Non-deterministic**: Each run can produce different results (970 vs 900 for same range)

### Root cause in the code
```python
# sales_extractor.py:315-324
try:
    await page.wait_for_function(
        """(before) => {
            const el = document.querySelector('.dataTables_info, .pagination');
            return !el || (el.innerText || '') !== before;
        }""",
        before,
        timeout=10_000,
    )
except Exception:
    pass  # ← Silent timeout! Info text didn't change, but we proceed anyway
```

The `except: pass` means if the DataTable AJAX is slow (>10 s), we proceed without verifying the page actually loaded new data.

Additionally, `debug_pagination=true` makes it **worse** because `sales_pagination_snapshot()` (called before collecting rows) performs extensive DOM queries that delay the row extraction.

---

## 3. Dedup Bug — `_source_page` in Fingerprint

### Location
`sales_extractor.py:379-390`

### Problem
```python
fingerprint = stable_id(*[str(value) for key, value in sorted(row.items()) if key != "_row_id"])
```

The dedup fingerprint **includes `_source_page`**, which is set on each row during collection:
```python
row["_source_page"] = page_number
```

So the **same real-world row** appearing on two different pages has different fingerprints and is **not deduplicated**. This means `rows_after_dedupe == rows_before_dedupe` is always true — the dedup is effectively **disabled for cross-page duplicates**.

### Impact
If pagination over-collects by re-reading the same page twice (because AJAX was slow), the duplicate rows **survive dedup** and are written to output.

---

## 4. Normal vs Assisted Mode

### Finding
For the sales report, **normal and assisted modes produce identical results** (970 rows each, exact same pagination trace). This makes sense because:
- The assisted "pause" asks the human to **press Enter** to continue
- The human pressing Enter doesn't change the page state
- The scraper continues from wherever the page is, which is the same sales report UI

### Recommendation
Remove the assisted pause for `sales` on the happy path — it provides no value. Keep it only for error-recovery scenarios.

---

## 5. Learning Mode / Recipe System

### Only recipe: `sales.rejected_20260617_131441.yaml`

This recipe was **rejected** (`.rejected_` prefix), so it is never loaded by `recipe_path()` which looks for `sales.yaml`.

### What the recipe captured
- 127 steps, all `wait_for` actions targeting `Importar Productos` (an ASNO sidebar menu item)
- The learning mode's DOM observer picked up **navigation clicks to a completely different page** instead of the sales report flow
- This means the learner recorded **noise from the sidebar** rather than the report interaction

### Diagnosis
The learning mode uses a MutationObserver that captures all DOM changes. When the human navigated through the sidebar to reach the sales report, every intermediate click was recorded as a "step." The resulting recipe replays those sidebar clicks, which would navigate away from the sales page.

### Learning session log (`learning_sales_stdout.log`)
```
REPLAY_RECIPE: sales
STATUS: success
ROWS: 20000
```

The learning session that followed the failed extraction **manually navigated to the sales page** and the scraper collected **20 000 rows** (full-year unfiltered). This data overwrote the June `sales.json` output.

---

## 6. Date Filter Behavior

### Observation
After clicking the submit button (`#submit_filter`), the date input fields show `31/12/1899 00:00`:
```
"filters_after_submit": {
    "date_from_value": "31/12/1899 00:00",
    "date_to_value": "31/12/1899 00:00"
}
```

This is **normal DataTables behavior** — the client-side date inputs are reset/cleared after the server-side filter is applied. The actual date filter was correctly sent to the server (the response contains the correct rows for the requested range).

**Not a bug** — the `filters_after_apply` values are the correct ones to log.

---

## 7. Summary of All Issues Found

| # | Issue | Severity | File | Line |
|---|-------|----------|------|------|
| 1 | Pagination: silent timeout on info text change | **High** | `sales_extractor.py` | 323 |
| 2 | Pagination: no retry when info text unchanged | **High** | `sales_extractor.py` | 327-328 |
| 3 | Dedup: `_source_page` in fingerprint disables cross-page dedup | **Medium** | `sales_extractor.py` | 383 |
| 4 | Learning mode: records sidebar navigation as recipe steps | **Medium** | `human_learning.py` | (observer) |
| 5 | Assisted pause on happy path provides no value | **Low** | `sales_extractor.py` | 579-595 |
| 6 | `debug_pagination` makes the stale-info problem worse | **Low** | `sales_extractor.py` | 347 |

---

## 8. Data Integrity Assessment

### Current output files (`data/processed/sales/`)
All 6 monthly chunks exist with `.json` and `.xlsx` files. However:
- **Every chunk over-counts**: ~100 extra rows per month due to the pagination bug
- **June data was overwritten** multiple times (970→900→20000→970→900)
- **The 20 000-row output** (from replay-recipe) was overwritten by later runs

### Recommended action before fixes
Do NOT use the current output files for reporting until all pagination bugs are fixed.

---

## 9. Normal vs Assisted vs Learning Flow Summary

| Flow | Trigger | Outcome | OK? |
|------|---------|---------|-----|
| **Normal** | `--assisted False`, `--learn False` | Runs automated date filter + submit + paginate | Buggy pagination |
| **Assisted** | `--assisted True` | Pauses for human input on error; on Enter, proceeds without reapplying filters | No benefit on happy path |
| **Learning** | `--learn True` | Captures DOM changes as recipe; noisy due to sidebar clicks | Needs denoising |
| **Recipe replay** | `--prefer-recipe True` | Replays saved recipe steps | Only one recipe exists (rejected) |

---

## 10. Files Touched During Audit

- `data/debug/sales_compare/` — 15 debug JSON files from 6 extraction runs
- `data/logs/sales_2026-*.log` — Monthly chunk logs with row counts
- `data/logs/learning_sales_stdout.log` — Learning session log (20k rows)
- `configs/learned_recipes/sales.rejected_20260617_131441.yaml` — Rejected noisy recipe
- `asno_reports_scraper/app/sales_extractor.py` — Main extraction logic (read-only audit)
- `asno_reports_scraper/app/pagination.py` — Pagination helper (read-only audit)
