"""Extract gameplay datasets and endpoints from a decoded KingsCall APK tree.

This script expects an apktool-style decode directory, then:
1) Scans Cocos `cc.JsonAsset` wrapper files under config/import.
2) Extracts named tables (card, skill, monster, etc.) into JSON.
3) Builds CSV exports for easy analysis/training pipelines.
4) Collects network endpoints from manifest/config files.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Extract KingsCall gameplay data pack")
    parser.add_argument(
        "--apktool-dir",
        type=str,
        default="analysis/kingscall_apktool",
        help="Path to apktool-decoded APK directory",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="analysis/kingscall_data_pack",
        help="Where to write extracted JSON/CSV artifacts",
    )
    return parser.parse_args()


def read_json(file_path: Path) -> Any:
    """Read JSON file with tolerant UTF-8 decoding."""
    return json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))


def iter_cc_jsonasset_entries(payload: Any):
    """Yield (name, table_payload) entries from Cocos JsonAsset wrapper arrays."""
    if isinstance(payload, list):
        if (
            len(payload) >= 3
            and payload[0] == 0
            and isinstance(payload[1], str)
            and isinstance(payload[2], (dict, list))
        ):
            yield payload[1], payload[2]
        for item in payload:
            yield from iter_cc_jsonasset_entries(item)
        return

    if isinstance(payload, dict):
        for value in payload.values():
            yield from iter_cc_jsonasset_entries(value)


def collect_tables(config_import_dir: Path) -> dict[str, dict[str, Any]]:
    """Collect first-seen table for each JsonAsset name."""
    table_map: dict[str, dict[str, Any]] = {}
    for file_path in sorted(config_import_dir.rglob("*.json")):
        try:
            payload = read_json(file_path)
        except Exception:
            continue

        for table_name, table_payload in iter_cc_jsonasset_entries(payload):
            if table_name not in table_map:
                table_map[table_name] = {
                    "source": str(file_path),
                    "payload": table_payload,
                    "duplicates": 0,
                }
            else:
                table_map[table_name]["duplicates"] += 1
    return table_map


def looks_number(value: Any) -> bool:
    """Heuristic check for numeric cell values."""
    text = str(value).strip()
    if not text:
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False


def has_chinese(text: str) -> bool:
    """Whether text contains CJK characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def normalize_header_cells(cells: list[str]) -> list[str]:
    """Normalize and deduplicate spreadsheet header names."""
    normalized: list[str] = []
    seen: dict[str, int] = {}
    for index, raw in enumerate(cells):
        name = str(raw).strip()
        if not name:
            name = f"col_{index + 1}"
        count = seen.get(name, 0)
        seen[name] = count + 1
        if count > 0:
            name = f"{name}_{count + 1}"
        normalized.append(name)
    return normalized


def extract_cell_text(cell: dict[str, Any]) -> str:
    """Extract text payload from an XML-converted Spreadsheet cell."""
    data = cell.get("Data")
    if isinstance(data, dict):
        return str(data.get("#text", ""))
    if data is None:
        return ""
    return str(data)


def parse_spreadsheet_row(row_obj: dict[str, Any]) -> list[str]:
    """Convert Spreadsheet XML row object to dense list of cell text."""
    cells = row_obj.get("Cell", [])
    if isinstance(cells, dict):
        cells = [cells]

    dense: list[str] = []
    current_index = 1
    for cell in cells:
        if not isinstance(cell, dict):
            continue

        explicit_index = cell.get("ss:Index")
        if explicit_index is not None:
            try:
                current_index = int(explicit_index)
            except Exception:
                pass

        while len(dense) < current_index - 1:
            dense.append("")

        dense.append(extract_cell_text(cell))

        merge_across = 0
        if cell.get("ss:MergeAcross") is not None:
            try:
                merge_across = int(cell["ss:MergeAcross"])
            except Exception:
                merge_across = 0
        for _ in range(max(0, merge_across)):
            dense.append("")

        current_index = len(dense) + 1

    while dense and not str(dense[-1]).strip():
        dense.pop()
    return dense


def workbook_to_tables(workbook_root: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Convert Workbook payload to one or more row tables."""
    worksheet_value = workbook_root.get("Worksheet")
    worksheets = worksheet_value if isinstance(worksheet_value, list) else [worksheet_value]
    output: dict[str, list[dict[str, Any]]] = {}

    for ws in worksheets:
        if not isinstance(ws, dict):
            continue
        ws_name = str(ws.get("ss:Name", ws.get("Name", "sheet"))).strip() or "sheet"
        table = ws.get("Table", {})
        if not isinstance(table, dict):
            continue

        row_value = table.get("Row", [])
        row_items = row_value if isinstance(row_value, list) else [row_value]
        parsed_rows = [parse_spreadsheet_row(row_obj) for row_obj in row_items if isinstance(row_obj, dict)]
        parsed_rows = [row for row in parsed_rows if row]
        if not parsed_rows:
            output[ws_name] = []
            continue

        header_index = 0
        for idx, row in enumerate(parsed_rows[:5]):
            non_empty = [cell for cell in row if str(cell).strip()]
            if len(non_empty) < 2:
                continue
            if all(not looks_number(cell) for cell in non_empty):
                header_index = idx
                break

        headers = normalize_header_cells(parsed_rows[header_index])
        records: list[dict[str, Any]] = []
        for idx, row in enumerate(parsed_rows[header_index + 1 :], start=header_index + 1):
            if idx == header_index + 1:
                values = [str(cell).strip() for cell in row if str(cell).strip()]
                if values and all(not looks_number(value) for value in values) and any(has_chinese(value) for value in values):
                    continue

            record: dict[str, Any] = {}
            non_empty_count = 0
            for col_idx, header in enumerate(headers):
                value = row[col_idx] if col_idx < len(row) else ""
                text = str(value).strip()
                record[header] = text
                if text:
                    non_empty_count += 1
            if non_empty_count == 0:
                continue
            records.append(record)
        output[ws_name] = records

    return output


def root_to_subtables(table_name: str, root_payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Handle XML-like root dict payloads with named list children."""
    subtables: dict[str, list[dict[str, Any]]] = {}
    for key, value in root_payload.items():
        if isinstance(value, dict):
            if "task" in value and isinstance(value["task"], list):
                subtables[f"{table_name}_{key}_task"] = value["task"]
            if "group" in value and isinstance(value["group"], list):
                subtables[f"{table_name}_{key}_group"] = value["group"]
            continue
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            subtables[f"{table_name}_{key}"] = value
    return subtables


def payload_to_subtables(table_name: str, payload: Any) -> dict[str, list[dict[str, Any]]]:
    """Normalize payload into one or more row-based subtables."""
    subtables: dict[str, list[dict[str, Any]]] = {}

    if isinstance(payload, dict):
        if "Workbook" in payload and isinstance(payload["Workbook"], dict):
            workbook_tables = workbook_to_tables(payload["Workbook"])
            for sheet_name, rows in workbook_tables.items():
                subtables[f"{table_name}_{sheet_name}"] = rows
            return subtables

        if "root" in payload and isinstance(payload["root"], dict):
            root_tables = root_to_subtables(table_name, payload["root"])
            if root_tables:
                return root_tables

        if "items" in payload and isinstance(payload["items"], dict):
            for key, value in payload["items"].items():
                if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                    subtables[f"{table_name}_{key}"] = value
            if subtables:
                return subtables

        values = list(payload.values())
        if values and all(isinstance(item, dict) for item in values):
            rows = []
            for row_key, row in payload.items():
                row_obj = dict(row)
                if "_row_key" not in row_obj:
                    row_obj["_row_key"] = str(row_key)
                rows.append(row_obj)
            subtables[table_name] = rows
            return subtables

        subtables[table_name] = [{"value": json.dumps(payload, ensure_ascii=False)}]
        return subtables

    if isinstance(payload, list):
        if payload and all(isinstance(item, dict) for item in payload):
            subtables[table_name] = payload
        else:
            subtables[table_name] = [{"index": i, "value": json.dumps(v, ensure_ascii=False)} for i, v in enumerate(payload)]
        return subtables

    subtables[table_name] = [{"value": str(payload)}]
    return subtables


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    """Write dict rows to CSV with stable header order."""
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with output_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            encoded = {
                key: (
                    json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                )
                for key, value in row.items()
            }
            writer.writerow(encoded)


def collect_endpoints(apktool_dir: Path, table_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Collect API/server endpoints from key decoded files."""
    url_regex = re.compile(r"https?://[^\"'\n\r\t <>]+")

    endpoints: dict[str, Any] = {
        "manifest_meta": {},
        "game_config": {},
        "project_manifest": {},
        "urls": [],
    }

    manifest_path = apktool_dir / "AndroidManifest.xml"
    if manifest_path.exists():
        manifest_text = manifest_path.read_text(encoding="utf-8", errors="ignore")
        for key in ("WANCMS_API", "WANCMS_SITE", "WANCMS_GAMEID", "WANCMS_APPID", "WANCMS_APPKEY"):
            match = re.search(
                rf'android:name="{re.escape(key)}" android:value="([^"]+)"',
                manifest_text,
            )
            if match:
                endpoints["manifest_meta"][key] = match.group(1)
        endpoints["urls"].extend(url_regex.findall(manifest_text))

    game_config = table_map.get("GameConfig", {}).get("payload")
    if isinstance(game_config, dict):
        config_obj = game_config.get("config", {})
        if isinstance(config_obj, dict):
            endpoints["game_config"] = {
                "APP_DOWN_URL": game_config.get("APP_DOWN_URL"),
                "domainURL": config_obj.get("domainURL"),
                "httpServer": config_obj.get("httpServer"),
                "version": config_obj.get("version"),
            }
        endpoints["urls"].extend(url_regex.findall(json.dumps(game_config, ensure_ascii=False)))

    project_manifest_path = apktool_dir / "assets" / "project.manifest"
    if project_manifest_path.exists():
        try:
            project_manifest = read_json(project_manifest_path)
            endpoints["project_manifest"] = {
                "packageUrl": project_manifest.get("packageUrl"),
                "remoteManifestUrl": project_manifest.get("remoteManifestUrl"),
                "remoteVersionUrl": project_manifest.get("remoteVersionUrl"),
                "version": project_manifest.get("version"),
            }
            endpoints["urls"].extend(url_regex.findall(json.dumps(project_manifest, ensure_ascii=False)))
        except Exception:
            pass

    bundle_path = apktool_dir / "assets" / "src" / "chunks" / "bundle.js"
    if bundle_path.exists():
        bundle_text = bundle_path.read_text(encoding="utf-8", errors="ignore")
        endpoints["urls"].extend(url_regex.findall(bundle_text))

    pay_files = [
        apktool_dir / "assets" / "AA.json",
        apktool_dir / "assets" / "s.json",
    ]
    for pay_file in pay_files:
        if pay_file.exists():
            endpoints["urls"].extend(url_regex.findall(pay_file.read_text(encoding="utf-8", errors="ignore")))

    unique_urls = sorted(set(endpoints["urls"]))
    api_markers = ("xstargame", "wancms", "apig", "api2", "game2", "cnd")
    api_urls = [url for url in unique_urls if any(marker in url.lower() for marker in api_markers)]
    other_urls = [url for url in unique_urls if url not in api_urls]
    endpoints["urls"] = unique_urls
    endpoints["api_urls"] = api_urls
    endpoints["other_urls"] = other_urls
    return endpoints


def sanitize_name(name: str) -> str:
    """Make a safe filename from table name."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "table"


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    apktool_dir = Path(args.apktool_dir)
    output_dir = Path(args.output_dir)
    raw_dir = output_dir / "raw"
    csv_dir = output_dir / "csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    config_import_dir = apktool_dir / "assets" / "assets" / "config" / "import"
    if not config_import_dir.exists():
        raise SystemExit(f"Config import path not found: {config_import_dir}")

    table_map = collect_tables(config_import_dir=config_import_dir)

    index_rows: list[dict[str, Any]] = []
    gameplay_keywords = {
        "card",
        "skill",
        "monster",
        "effect",
        "status",
        "task",
        "item",
        "pet",
        "race",
        "actor",
        "manual",
    }

    gameplay_tables: set[str] = set()
    for table_name, meta in sorted(table_map.items()):
        payload = meta["payload"]
        payload_type = type(payload).__name__
        payload_size = len(payload) if isinstance(payload, (dict, list)) else 1
        source = meta["source"]
        duplicates = int(meta.get("duplicates", 0))

        index_rows.append(
            {
                "table_name": table_name,
                "payload_type": payload_type,
                "payload_size": payload_size,
                "source": source,
                "duplicates": duplicates,
            }
        )

        lower_name = table_name.lower()
        if any(keyword in lower_name for keyword in gameplay_keywords):
            gameplay_tables.add(table_name)
        if table_name in {"GameConfig", "address", "WorldBoss"}:
            gameplay_tables.add(table_name)

    # Add direct core tables even if naming differs in future builds.
    for fixed_name in ("card", "Skill", "monster", "Effect", "Status", "Task", "items", "Pet", "PetSkill", "PetTriggers", "PetSkillRelate", "GameConfig"):
        if fixed_name in table_map:
            gameplay_tables.add(fixed_name)

    extracted_counts: dict[str, int] = {}
    for table_name in sorted(gameplay_tables):
        payload = table_map[table_name]["payload"]
        raw_file = raw_dir / f"{sanitize_name(table_name)}.json"
        raw_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        subtables = payload_to_subtables(table_name=table_name, payload=payload)
        for subtable_name, rows in subtables.items():
            csv_file = csv_dir / f"{sanitize_name(subtable_name)}.csv"
            write_csv(rows, csv_file)
            extracted_counts[subtable_name] = len(rows)

    endpoints = collect_endpoints(apktool_dir=apktool_dir, table_map=table_map)

    # Core bot-friendly slices.
    core_tables: dict[str, Any] = {}
    for key in ("card", "Skill", "monster", "Effect", "Status"):
        if key in table_map:
            payload = table_map[key]["payload"]
            rows = payload_to_subtables(table_name=key, payload=payload).get(key, [])
            core_tables[key] = rows
            write_csv(rows, csv_dir / f"{sanitize_name(key)}_core.csv")
            (raw_dir / f"{sanitize_name(key)}_core.json").write_text(
                json.dumps(rows, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    summary = {
        "apktool_dir": str(apktool_dir),
        "output_dir": str(output_dir),
        "tables_found": len(table_map),
        "gameplay_tables_exported": len(gameplay_tables),
        "csv_files_exported": len(extracted_counts),
        "urls_found": len(endpoints.get("urls", [])),
        "table_index": index_rows,
        "extracted_row_counts": extracted_counts,
    }

    (output_dir / "tables_index.json").write_text(
        json.dumps(index_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "endpoints.json").write_text(
        json.dumps(endpoints, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    endpoints_csv = csv_dir / "endpoints.csv"
    endpoint_rows = [{"url": url} for url in endpoints.get("urls", [])]
    write_csv(endpoint_rows, endpoints_csv)

    print(f"tables_found={summary['tables_found']}")
    print(f"gameplay_tables_exported={summary['gameplay_tables_exported']}")
    print(f"csv_files_exported={summary['csv_files_exported']}")
    print(f"urls_found={summary['urls_found']}")
    print(f"output_dir={output_dir}")


if __name__ == "__main__":
    main()
