import json
import os
import sys
import time
import argparse
from datetime import datetime

# ==========================================
# 儲存管理類別 (Storage Layer)
# 要換成 SQLite，只需改寫此類別
# ==========================================
class RuleStorage:
    def __init__(self, storage_path="rules.json"):
        self.storage_path = storage_path
        self.rules = self._load_rules()

    def _load_rules(self):
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_rules(self):
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.rules, f, indent=4, ensure_ascii=False)

    def add_rule(self, keyword, level):
        new_id = max([r['id'] for r in self.rules], default=0) + 1
        new_rule = {
            "id": new_id,
            "keyword": keyword,
            "level": level.upper(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.rules.append(new_rule)
        self._save_rules()
        return new_rule

    def list_rules(self):
        return self.rules

    def delete_rule(self, rule_id):
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r['id'] != rule_id]
        if len(self.rules) < initial_count:
            self._save_rules()
            return True
        return False

# ==========================================
# 掃描邏輯類別 (Logic Layer)
#未來可在此加入正則表達式或進階過濾
# ==========================================
class LogScanner:
    def __init__(self, rules):
        self.rules = rules

    def scan_file(self, file_path, output_path=None):
        if not os.path.exists(file_path):
            print(f"[Error] File not found: {file_path}")
            sys.exit(1)

        # keyword -> list of (line_no, line_text, level)
        hits_by_keyword = {rule['keyword']: [] for rule in self.rules}

        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                for rule in self.rules:
                    if rule['keyword'] in line:
                        hits_by_keyword[rule['keyword']].append(
                            (i, line.strip(), rule['level'])
                        )
                        print(f"[ALERT-{rule['level']}] Line {i}: {line.strip()}")

        total = sum(len(v) for v in hits_by_keyword.values())
        if total == 0:
            print("[Info] Scan completed. No matching keywords found.")

        if output_path:
            self._write_report(file_path, hits_by_keyword, output_path)

    def _write_report(self, scanned_file, hits_by_keyword, output_path):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"LogAlert Scan Report",
            f"Generated : {ts}",
            f"Source    : {scanned_file}",
            "=" * 60,
        ]

        for keyword, hits in hits_by_keyword.items():
            lines.append(f"\n[Keyword: {keyword}]  ({len(hits)} match(es))")
            lines.append("-" * 40)
            if hits:
                for line_no, text, level in hits:
                    lines.append(f"  [ALERT-{level}] Line {line_no}: {text}")
            else:
                lines.append("  (no matches)")

        lines.append("\n" + "=" * 60)
        total = sum(len(v) for v in hits_by_keyword.values())
        lines.append(f"Total alerts: {total}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")

        print(f"[Info] Report saved to '{output_path}'.")

    def rule_hits(self, file_path, rule_id):
        if not os.path.exists(file_path):
            print(f"[Error] File not found: {file_path}")
            sys.exit(1)

        target = next((r for r in self.rules if r['id'] == rule_id), None)
        if target is None:
            print(f"[Error] Rule ID {rule_id} not found.")
            sys.exit(1)

        print(f"[Rule #{target['id']}] Keyword='{target['keyword']}' | Level={target['level']}")
        print("-" * 55)

        hits = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if target['keyword'] in line:
                    hits.append((i, line.strip()))
                    print(f"  Line {i}: {line.strip()}")

        print("-" * 55)
        if hits:
            print(f"[Info] {len(hits)} match(es) found in '{file_path}'.")
        else:
            print(f"[Info] No matches found in '{file_path}'.")

    def monitor_file(self, file_path, interval=1.0):
        if not os.path.exists(file_path):
            print(f"[Error] File not found: {file_path}")
            sys.exit(1)

        print(f"[Monitor] Watching: {file_path}  (Press Ctrl+C to stop)")

        with open(file_path, 'r', encoding='utf-8') as counter:
            line_number = sum(1 for _ in counter)

        with open(file_path, 'r', encoding='utf-8') as f:
            f.seek(0, 2)  # 跳到檔案末尾，只監控新增的內容

            try:
                while True:
                    line = f.readline()
                    if line:
                        line_number += 1
                        for rule in self.rules:
                            if rule['keyword'] in line:
                                ts = datetime.now().strftime("%H:%M:%S")
                                print(f"[{ts}][ALERT-{rule['level']}] Line {line_number}: {line.strip()}")
                    else:
                        time.sleep(interval)
            except KeyboardInterrupt:
                print("\n[Monitor] Stopped.")

# ==========================================
# CLI 介面處理 (Interface Layer)
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="LogAlert CLI - Local Log Monitoring Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Rule Add
    parser_add = subparsers.add_parser("rule_add", help="Add a new filter rule")
    parser_add.add_argument("--keyword", required=True, help="Keyword to search for")
    parser_add.add_argument("--level", default="INFO", help="Alert level (INFO/WARN/ERROR)")

    # Rule List
    subparsers.add_parser("rule_list", help="List all filter rules")

    # Rule Delete
    parser_del = subparsers.add_parser("rule_delete", help="Delete a rule by ID")
    parser_del.add_argument("--id", type=int, required=True, help="Rule ID to delete")

    # Scan
    parser_scan = subparsers.add_parser("scan", help="Scan a log file")
    parser_scan.add_argument("--file", required=True, help="Path to the log file")
    parser_scan.add_argument("--output", default=None, help="Save report to this file, grouped by keyword")

    # Rule Hits
    parser_hits = subparsers.add_parser("rule_hits", help="Show all lines in a log file matched by a specific rule")
    parser_hits.add_argument("--id", type=int, required=True, help="Rule ID to query")
    parser_hits.add_argument("--file", required=True, help="Path to the log file")

    # Monitor
    parser_monitor = subparsers.add_parser("monitor", help="Continuously watch a log file for new matching lines")
    parser_monitor.add_argument("--file", required=True, help="Path to the log file to watch")
    parser_monitor.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds (default: 1.0)")

    args = parser.parse_args()
    storage = RuleStorage()

    if args.command == "rule_add":
        rule = storage.add_rule(args.keyword, args.level)
        print(f"[Success] Rule added: ID={rule['id']}, Keyword={rule['keyword']}")

    elif args.command == "rule_list":
        rules = storage.list_rules()
        print(f"{'ID':<5} | {'Keyword':<15} | {'Level':<10} | {'Created At'}")
        print("-" * 50)
        for r in rules:
            print(f"{r['id']:<5} | {r['keyword']:<15} | {r['level']:<10} | {r['created_at']}")

    elif args.command == "rule_delete":
        if storage.delete_rule(args.id):
            print(f"[Success] Rule ID {args.id} deleted.")
        else:
            print(f"[Error] Rule ID {args.id} not found.")

    elif args.command == "scan":
        scanner = LogScanner(storage.list_rules())
        scanner.scan_file(args.file, output_path=args.output)

    elif args.command == "rule_hits":
        scanner = LogScanner(storage.list_rules())
        scanner.rule_hits(args.file, args.id)

    elif args.command == "monitor":
        scanner = LogScanner(storage.list_rules())
        scanner.monitor_file(args.file, interval=args.interval)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()