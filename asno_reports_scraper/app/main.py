from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import date

from .browser import browser_page
from .config import ROOT_DIR, Settings
from .extraction_targets import generate_extraction_targets, list_targets_rows
from .login import login
from .human_learning import delete_learned_recipe, list_learned_recipes
from .extraction_planner import generate_extraction_plan
from .generic_runner import extract_generic_module, extract_generic_pattern
from .pattern_builder import build_learned_patterns
from .report_detector import inspect_report
from .report_extractor import extract_all, extract_report, month_chunks
from .reports_audit import audit_reports
from .reports_index import discover_reports
from .sales_extractor import extract_sales_report
from .site_patterns_audit import audit_site_patterns, audit_system
from .storage import read_json, write_json
from .teach_mode import resolve_teach_target, start_teach_mode


def _date(value: str) -> date:
    return date.fromisoformat(value)


def choose_report(reports: list[dict], query: str) -> dict | None:
    q = query.lower()
    candidates = [
        item
        for item in reports
        if q == str(item.get("id", "")).lower() or q == str(item.get("name", "")).lower()
    ]
    if not candidates:
        candidates = [item for item in reports if q in str(item.get("name", "")).lower()]
    candidates.sort(
        key=lambda item: (
            0 if "/admin/reports/" in str(item.get("href", "")) else 1,
            len(str(item.get("name", ""))),
        )
    )
    return candidates[0] if candidates else None


def configure_logging(settings: Settings) -> None:
    settings.ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(settings.logs_dir / "asno_reports.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


async def run(args: argparse.Namespace) -> None:
    require_reports_url = args.command in {"audit-reports", "discover", "inspect", "extract-all"}
    if args.command == "extract" and getattr(args, "report", "").lower() != "sales":
        require_reports_url = True
    settings = Settings.load(args.env_file, require_reports_url=require_reports_url)
    configure_logging(settings)

    if args.command == "build-patterns":
        result = build_learned_patterns(settings)
        print("PATTERNS_BUILT")
        print(f"PATTERNS_CONFIG: {result['paths']['patterns_yaml']}")
        print(f"LEARNED_AUDIT_MARKDOWN: {result['paths']['markdown']}")
        print(f"LEARNED_SUMMARY_JSON: {result['paths']['summary_json']}")
        print(f"TEACH_SESSIONS: {result['teach_sessions_count']}")
        print(f"ASSISTED_EVENTS: {result['assisted_events_count']}")
        print(f"PATTERNS_DETECTED: {len(result['patterns'])}")
        print(f"GENERIC_EXTRACTORS_READY: {len(result['generic_extractors_ready'])}")
        return

    if args.command == "extract-system":
        if not args.plan_only:
            raise SystemExit("extract-system only supports --plan-only for now. No se ejecuta extracción histórica todavía.")
        plan = generate_extraction_plan(settings, plan_only=True)
        print("EXTRACTION_PLAN_CREATED")
        print(f"PLAN_JSON: {plan['paths']['json']}")
        print(f"PLAN_MARKDOWN: {plan['paths']['markdown']}")
        print(f"PACKAGE_ROOT: {plan['data_package_design']['root']}")
        print(f"MODULES_PLANNED: {len(plan['modules'])}")
        return

    if args.command == "list-targets":
        generate_extraction_targets(settings)
        rows = list_targets_rows(settings)
        print("TARGET_ID | NAME | MODULE | PATTERN | PRIORITY | SAFE | STATUS | URL")
        for row in rows:
            print(
                f"{row['target_id']} | {row['name']} | {row['module']} | {row['pattern']} | "
                f"{row['priority']} | {row['safe_read_only']} | {row['status']} | {row['url']}"
            )
        print(f"TARGETS: {len(rows)}")
        print(f"TARGETS_CONFIG: {ROOT_DIR / 'configs' / 'extraction_targets.yaml'}")
        print(f"TARGETS_GENERATED: {ROOT_DIR / 'configs' / 'extraction_targets.generated.yaml'}")
        return

    if args.command == "list-recipes":
        recipes = list_learned_recipes()
        if not recipes:
            print("LEARNED_RECIPES: none")
        for path in recipes:
            print(path)
        return

    if args.command == "delete-recipe":
        deleted = delete_learned_recipe(args.report)
        print(f"RECIPE_DELETED: {args.report} => {deleted}")
        return

    async with browser_page(settings) as page:
        login_result = await login(page, settings, close_session_first=args.close_session_first)
        logging.info("Login status=%s url=%s", login_result.status, login_result.url)

        if args.command == "discover":
            reports = await discover_reports(page, settings)
            print(f"REPORTS_DETECTED: {len(reports)}")
            print(f"REPORTS_INDEX: {settings.raw_dir / 'reports_index.json'}")
            return

        if args.command == "audit-reports":
            audit = await audit_reports(page, settings, assisted=args.assisted, limit_reports=args.limit_reports)
            chatgpt_report_path = ROOT_DIR / "ASNO_REPORTS_AUDIT_FOR_CHATGPT.md"
            audited = sum(1 for item in audit.get("reports", []) if item.get("opened_successfully"))
            failed = sum(1 for item in audit.get("reports", []) if item.get("diagnostics", {}).get("error"))
            print(f"REPORTS_DETECTED: {audit['total_reports_detected']}")
            print(f"REPORTS_AUDITED: {audited}")
            print(f"REPORTS_WITH_WARNINGS_OR_ERRORS: {failed}")
            print(f"AUDIT_JSON: {settings.audit_dir / 'reports_audit.json'}")
            print(f"AUDIT_MARKDOWN: {ROOT_DIR / 'docs' / 'audits' / 'asno_reports_audit.md'}")
            print(f"CHATGPT_AUDIT_MARKDOWN: {chatgpt_report_path}")
            print("")
            print(chatgpt_report_path.read_text(encoding="utf-8"))
            return

        if args.command == "audit-site-patterns":
            audit = await audit_site_patterns(page, settings, assisted=args.assisted, limit_pages=args.limit_pages)
            markdown_path = ROOT_DIR / "docs" / "audits" / "asno_site_patterns_audit.md"
            print(f"SITE_PAGES_DETECTED: {audit['total_pages']}")
            print(f"SITE_PAGES_AUDITED: {audit['total_pages_audited']}")
            print(f"SITE_PATTERNS_FOUND: {audit['total_patterns']}")
            print(f"UNKNOWN_PAGES: {len(audit.get('unknown_pages', []))}")
            print(f"DANGEROUS_PAGES: {len(audit.get('dangerous_pages', []))}")
            print(f"SITE_PATTERNS_JSON: {settings.audit_dir / 'site_patterns.json'}")
            print(f"SITE_PATTERNS_MARKDOWN: {markdown_path}")
            return

        if args.command == "audit-system":
            audit = await audit_system(page, settings, assisted=args.assisted, limit_pages=args.limit_pages, patterns=args.patterns)
            markdown_path = ROOT_DIR / "docs" / "audits" / "asno_system_audit.md"
            print(f"SYSTEM_URLS_DETECTED: {audit['total_urls_detected']}")
            print(f"SYSTEM_PAGES_AUDITED: {audit['total_pages_audited']}")
            print(f"SYSTEM_MODULES_FOUND: {len(audit['modules_detected'])}")
            print(f"SYSTEM_PATTERNS_FOUND: {len(audit['patterns_detected'])}")
            print(f"UNKNOWN_PAGES: {len(audit.get('unknown_pages', []))}")
            print(f"DANGEROUS_PAGES: {len(audit.get('dangerous_pages', []))}")
            print(f"SYSTEM_MAP_JSON: {settings.audit_dir / 'system_map.json'}")
            print(f"SYSTEM_AUDIT_MARKDOWN: {markdown_path}")
            return

        if args.command == "teach":
            target = resolve_teach_target(settings, args.module, args.url, args.name)
            session = await start_teach_mode(page, settings, target)
            print("TEACH_SESSION_CREATED")
            print(f"MODULE: {session['module']}")
            print(f"NAME: {session['name']}")
            print(f"SESSION_DIR: {session['paths']['directory']}")
            print(f"EVENTS: {session['paths']['events']}")
            print(f"DOM_SNAPSHOTS: {session['paths']['dom_snapshots']}")
            print(f"SESSION_JSON: {session['paths']['teach_session']}")
            print(f"RECIPE: {session['paths']['inferred_recipe']}")
            print(f"DIAGNOSIS: {session['paths']['module_diagnosis']}")
            return

        if args.command == "extract-pattern":
            summary = await extract_generic_pattern(
                page,
                settings,
                pattern=args.pattern,
                module=args.module,
                name=args.name,
                url=args.url,
                date_from=_date(args.from_date) if args.from_date else None,
                date_to=_date(args.to_date) if args.to_date else None,
                max_pages=args.max_pages,
                assisted=args.assisted,
                optimize_page_size=args.optimize_page_size,
            )
            print(f"GENERIC_PATTERN: {summary['pattern']}")
            print(f"TARGET: {summary['module']} / {summary['name']}")
            print(f"STATUS: {summary['status']}")
            print(f"ROWS: {summary.get('row_count', 0)}")
            diagnostics = summary.get("diagnostics", {})
            pagination = diagnostics.get("pagination", {})
            counts = diagnostics.get("counts", {})
            print(f"PAGES_WALKED: {pagination.get('pages_walked')}")
            print(f"TERMINATION_REASON: {pagination.get('termination_reason')}")
            print(f"ROWS_BEFORE_DEDUPE: {counts.get('rows_before_dedupe')}")
            print(f"ROWS_AFTER_DEDUPE: {counts.get('rows_after_dedupe')}")
            for key, value in summary.get("outputs", {}).items():
                print(f"{key.upper()}: {value}")
            return

        if args.command == "extract-generic":
            if not args.target and not args.module:
                raise SystemExit("extract-generic requiere --target o --module.")
            summary = await extract_generic_module(
                page,
                settings,
                module=args.module or "",
                target_id=args.target,
                date_from=_date(args.from_date),
                date_to=_date(args.to_date),
                limit_pages=args.limit_pages,
                assisted=args.assisted,
                debug_counts=args.debug_counts,
                optimize_page_size=args.optimize_page_size,
            )
            print(f"GENERIC_MODULE: {summary['module']}")
            print(f"TARGET_ID: {summary.get('target_id')}")
            print(f"STATUS: {summary['status']}")
            print(f"TARGETS: {summary['targets_count']}")
            print(f"CHUNKS: {summary['chunks_count']}")
            print(f"LIMIT_PAGES: {summary['limit_pages']}")
            print(f"ROWS: {summary['totals'].get('rows')}")
            print(f"FAILED_CHUNKS: {summary['totals'].get('failed_chunks')}")
            if args.debug_counts:
                print(f"PAGES_WALKED: {summary['totals'].get('pages_walked')}")
                print(f"ROWS_BEFORE_DEDUPE: {summary['totals'].get('rows_before_dedupe')}")
                print(f"ROWS_AFTER_DEDUPE: {summary['totals'].get('rows_after_dedupe')}")
                print(f"UNIQUE_IDS: {summary['totals'].get('unique_ids')}")
            print(f"SUMMARY: {summary['summary_path']}")
            for item in summary.get("summaries", []):
                print(
                    f"CHUNK {item.get('name')} {item.get('date_from')}..{item.get('date_to')} "
                    f"status={item.get('status')} rows={item.get('row_count')}"
                )
                if args.debug_counts:
                    counts = item.get("diagnostics", {}).get("counts", {})
                    pagination = item.get("diagnostics", {}).get("pagination", {})
                    print(f"  pages_detected={counts.get('pages_detected')} pages_walked={pagination.get('pages_walked')} termination={pagination.get('termination_reason')}")
                    print(f"  visible_rows={counts.get('visible_rows_total')} extracted={counts.get('rows_before_dedupe')} unique={counts.get('unique_ids')}")
                outputs = item.get("outputs", {})
                for key in ("raw_html", "json", "xlsx", "log", "debug"):
                    if outputs.get(key):
                        print(f"  {key.upper()}: {outputs[key]}")
            return

        reports = read_json(settings.raw_dir / "reports_index.json", [])
        if not reports:
            reports = await discover_reports(page, settings)

        if args.command == "inspect":
            report = choose_report(reports, args.report)
            if not report:
                raise SystemExit(f"Report not found: {args.report}")
            from .report_extractor import open_modal_if_needed

            await open_modal_if_needed(page, report)
            data = await inspect_report(page, report)
            path = settings.raw_dir / f"{report['id']}_inspection.json"
            write_json(path, data)
            print(f"INSPECTION_PATH: {path}")
            return

        if args.command == "extract":
            if args.report.lower() == "sales":
                start = _date(args.from_date)
                end = _date(args.to_date)
                chunks = month_chunks(start, end) if args.chunk == "monthly" else [(start, end)]
                summaries = []
                for chunk_start, chunk_end in chunks:
                    summaries.append(
                        await extract_sales_report(
                            page,
                            settings,
                            chunk_start,
                            chunk_end,
                            learn=args.learn,
                            assisted=args.assisted,
                            debug_pagination=args.debug_pagination,
                            debug_filters=args.debug_filters,
                            debug_counts=args.debug_counts,
                        )
                    )
                total_rows = sum(item.get("row_count", 0) for item in summaries)
                failed = sum(1 for item in summaries if item.get("status") != "success")
                print("REPORT_SUMMARY: sales")
                print(f"CHUNKS: {len(summaries)}")
                print(f"ROWS: {total_rows}")
                print(f"FAILED_CHUNKS: {failed}")
                for item in summaries:
                    print(f"CHUNK {item['chunk_start']}..{item['chunk_end']} status={item['status']} rows={item.get('row_count', 0)}")
                    if item.get("debug", {}).get("counts"):
                        counts = item["debug"]["counts"]
                        pagination = item["debug"].get("pagination", {})
                        print(f"DEBUG_ROWS_BEFORE_DEDUPE: {counts.get('rows_before_dedupe')}")
                        print(f"DEBUG_ROWS_AFTER_DEDUPE: {counts.get('rows_after_dedupe')}")
                        print(f"DEBUG_UNIQUE_IDS: {counts.get('unique_ids_after_dedupe')}")
                        print(f"DEBUG_PAGES_WALKED: {pagination.get('pages_walked')}")
                        print(f"DEBUG_TERMINATION_REASON: {pagination.get('termination_reason')}")
                    for key, value in item.get("outputs", {}).items():
                        print(f"{key.upper()}: {value}")
                return
            report = choose_report(reports, args.report)
            if not report:
                raise SystemExit(f"Report not found: {args.report}")
            summary = await extract_report(page, settings, report, _date(args.from_date), _date(args.to_date))
            print(f"REPORT_SUMMARY: {summary['report_id']}")
            return

        if args.command == "replay-recipe":
            if args.report.lower() != "sales":
                raise SystemExit("replay-recipe currently supports configured report extractors; available: sales")
            summary = await extract_sales_report(
                page,
                settings,
                _date(args.from_date),
                _date(args.to_date),
                learn=args.learn,
                prefer_recipe=True,
            )
            print(f"REPLAY_RECIPE: {args.report}")
            print(f"STATUS: {summary['status']}")
            print(f"ROWS: {summary.get('row_count', 0)}")
            if summary.get("error"):
                print(f"ERROR: {summary['error']}")
            for key, value in summary.get("outputs", {}).items():
                print(f"{key.upper()}: {value}")
            return

        if args.command == "extract-all":
            summary = await extract_all(page, settings, _date(args.from_date), _date(args.to_date))
            print(f"REPORTS_DETECTED: {summary['reports_detected']}")
            print(f"REPORTS_EXTRACTED: {summary['reports_extracted']}")
            print(f"REPORTS_FAILED: {summary['reports_failed']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ASNO reports scraper")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--close-session-first", action="store_true")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover")
    audit_parser = sub.add_parser("audit-reports")
    audit_parser.add_argument("--assisted", action="store_true")
    audit_parser.add_argument("--limit-reports", type=int, default=None)
    site_patterns_parser = sub.add_parser("audit-site-patterns")
    site_patterns_parser.add_argument("--assisted", action="store_true")
    site_patterns_parser.add_argument("--limit-pages", type=int, default=None)
    system_parser = sub.add_parser("audit-system")
    system_parser.add_argument("--assisted", action="store_true")
    system_parser.add_argument("--limit-pages", type=int, default=None)
    system_parser.add_argument("--patterns", action="store_true")
    sub.add_parser("build-patterns")
    extract_system_parser = sub.add_parser("extract-system")
    extract_system_parser.add_argument("--plan-only", action="store_true")
    teach_parser = sub.add_parser("teach")
    teach_parser.add_argument("--module", default=None)
    teach_parser.add_argument("--url", default=None)
    teach_parser.add_argument("--name", default=None)
    sub.add_parser("list-recipes")

    delete_parser = sub.add_parser("delete-recipe")
    delete_parser.add_argument("--report", required=True)

    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--report", required=True)

    extract_parser = sub.add_parser("extract")
    extract_parser.add_argument("--report", required=True)
    extract_parser.add_argument("--from", dest="from_date", required=True)
    extract_parser.add_argument("--to", dest="to_date", required=True)
    extract_parser.add_argument("--chunk", choices=["monthly"], default="monthly")
    extract_parser.add_argument("--learn", action="store_true")
    extract_parser.add_argument("--assisted", action="store_true")
    extract_parser.add_argument("--debug-pagination", action="store_true")
    extract_parser.add_argument("--debug-filters", action="store_true")
    extract_parser.add_argument("--debug-counts", action="store_true")

    extract_pattern_parser = sub.add_parser("extract-pattern")
    extract_pattern_parser.add_argument("--pattern", required=True, choices=["filter_paginated_table", "paginated_table"])
    extract_pattern_parser.add_argument("--module", default=None)
    extract_pattern_parser.add_argument("--name", default=None)
    extract_pattern_parser.add_argument("--url", default=None)
    extract_pattern_parser.add_argument("--from", dest="from_date", default=None)
    extract_pattern_parser.add_argument("--to", dest="to_date", default=None)
    extract_pattern_parser.add_argument("--max-pages", type=int, default=10)
    extract_pattern_parser.add_argument("--assisted", action="store_true")
    extract_pattern_parser.add_argument("--optimize-page-size", action="store_true")

    extract_generic_parser = sub.add_parser("extract-generic")
    extract_generic_parser.add_argument("--module", default=None)
    extract_generic_parser.add_argument("--target", default=None)
    extract_generic_parser.add_argument("--from", dest="from_date", required=True)
    extract_generic_parser.add_argument("--to", dest="to_date", required=True)
    extract_generic_parser.add_argument("--limit-pages", type=int, default=None)
    extract_generic_parser.add_argument("--assisted", action="store_true")
    extract_generic_parser.add_argument("--debug-counts", action="store_true")
    extract_generic_parser.add_argument("--optimize-page-size", action="store_true")
    sub.add_parser("list-targets")

    replay_parser = sub.add_parser("replay-recipe")
    replay_parser.add_argument("--report", required=True)
    replay_parser.add_argument("--from", dest="from_date", required=True)
    replay_parser.add_argument("--to", dest="to_date", required=True)
    replay_parser.add_argument("--learn", action="store_true")

    extract_all_parser = sub.add_parser("extract-all")
    extract_all_parser.add_argument("--from", dest="from_date", required=True)
    extract_all_parser.add_argument("--to", dest="to_date", required=True)
    extract_all_parser.add_argument("--chunk", choices=["monthly"], default="monthly")
    return parser


def main() -> None:
    asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    main()
