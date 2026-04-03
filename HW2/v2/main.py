import json
import os
import sys
import time
import argparse
import re  # 需求 1：導入正則表達式模組
from datetime import datetime

# ==========================================
# 儲存管理類別 (Storage Layer)
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

    def add_rule(self, keyword, level, mode="plain"):
        # 需求 1：驗證 Regex 合法性
        if mode == "regex":
            try:
                re.compile(keyword)
            except re.error as e:
                print(f"[Error] Invalid regular expression: {e}")
                sys.exit(1)

        new_id = max([r['id'] for r in self.rules], default=0) + 1
        new_rule = {
            "id": new_id,
            "keyword": keyword,
            "level": level.upper(),
            "mode": mode,  # 需求 1：記錄比對模式
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
# ==========================================
class LogScanner:
    def __init__(self, rules):
        self.rules = rules

    # 需求 1：統一的比對邏輯輔助函式
    def _is_match(self, rule, line):
        if rule.get('mode') == 'regex':
            return bool(re.search(rule['keyword'], line))
        return rule['keyword'] in line

    def scan_file(self, file_path, output_path=None, filter_level=None):
        if not os.path.exists(file_path):
            print(f"[Error] File not found: {file_path}")
            sys.exit(1)

        # 需求 3：檢查等級是否存在
        if filter_level:
            valid_levels = {r['level'] for r in self.rules}
            if filter_level.upper() not in valid_levels:
                print(f"[Hint] No rules found for level '{filter_level}'. Available levels: {', '.join(valid_levels)}")
                # 這裡不退出，依照需求給予友善提示

        hits_by_keyword = {rule['keyword']: [] for rule in self.rules}
        total_alerts = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                for rule in self.rules:
                    # 需求 3：等級過濾邏輯
                    if filter_level and rule['level'] != filter_level.upper():
                        continue
                    
                    if self._is_match(rule, line):
                        hits_by_keyword[rule['keyword']].append((i, line.strip(), rule['level']))
                        print(f"[ALERT-{rule['level']}] Line {i}: {line.strip()}")
                        total_alerts += 1

        if total_alerts == 0:
            print("[Info] Scan completed. No matching keywords found.")

        if output_path:
            self._write_report(file_path, hits_by_keyword, output_path)

    def _write_report(self, scanned_file, hits_by_keyword, output_path):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [f"LogAlert Scan Report v2.0", f"Generated : {ts}", f"Source    : {scanned_file}", "=" * 60]

        for keyword, hits in hits_by_keyword.items():
            if not hits: continue # 報表只顯示有命中的（可選優化）
            lines.append(f"\n[Keyword: {keyword}] ({len(hits)} matches)")
            for line_no, text, level in hits:
                lines.append(f"  [ALERT-{level}] Line {line_no}: {text}")

        lines.append("\n" + "=" * 60)
        total = sum(len(v) for v in hits_by_keyword.values())
        lines.append(f"Total alerts: {total}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
        print(f"[Info] Report saved to '{output_path}'.")

    # 需求 4：規則統計功能
    def get_stats(self, file_path):
        if not os.path.exists(file_path):
            print(f"[Error] File not found: {file_path}")
            sys.exit(1)
        
        stats = {r['id']: {'keyword': r['keyword'], 'level': r['level'], 'hits': 0} for r in self.rules}
        total_hits = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                for rule in self.rules:
                    if self._is_match(rule, line):
                        stats[rule['id']]['hits'] += 1
                        total_hits += 1
        return stats, total_hits

    def rule_hits(self, file_path, rule_id):
        if not os.path.exists(file_path):
            print(f"[Error] File not found: {file_path}")
            sys.exit(1)

        target = next((r for r in self.rules if r['id'] == rule_id), None)
        if target is None:
            print(f"[Error] Rule ID {rule_id} not found.")
            sys.exit(1)

        mode = target.get('mode', 'plain')
        print(f"[Rule #{target['id']}] Keyword='{target['keyword']}' | Level={target['level']} | Mode={mode}")
        print("-" * 55)

        hits = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if self._is_match(target, line):
                    hits.append((i, line.strip()))
                    print(f"  Line {i}: {line.strip()}")

        print("-" * 55)
        if hits:
            print(f"[Info] {len(hits)} match(es) found in '{file_path}'.")
        else:
            print(f"[Info] No matches found in '{file_path}'.")

    def monitor_file(self, file_path, interval=1.0, log_output=None):
        if not os.path.exists(file_path):
            print(f"[Error] File not found: {file_path}")
            sys.exit(1)

        print(f"[Monitor] Watching: {file_path}  (Press Ctrl+C to stop)")
        alerts_count = 0 # 需求 2：摘要統計計數器

        # 先計算目前已有的行數，讓警報顯示正確行號
        with open(file_path, 'r', encoding='utf-8') as counter:
            line_number = sum(1 for _ in counter)

        with open(file_path, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            try:
                while True:
                    line = f.readline()
                    if line:
                        line_number += 1
                        for rule in self.rules:
                            if self._is_match(rule, line):
                                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                alert_msg = f"[{ts}][ALERT-{rule['level']}] Line {line_number}: {line.strip()}"
                                print(alert_msg)
                                alerts_count += 1

                                # 需求 2：同步寫入檔案
                                if log_output:
                                    with open(log_output, 'a', encoding='utf-8') as log_f:
                                        log_f.write(alert_msg + "\n")
                    else:
                        time.sleep(interval)
            except KeyboardInterrupt:
                print(f"\n[Monitor] Stopped. Total alerts detected during this session: {alerts_count}")

# ==========================================
# CLI 介面處理 (Interface Layer)
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="LogAlert CLI v2.0")
    subparsers = parser.add_subparsers(dest="command")

    # rule_add (新增 --mode)
    p_add = subparsers.add_parser("rule_add")
    p_add.add_argument("--keyword", required=True)
    p_add.add_argument("--level", default="INFO")
    p_add.add_argument("--mode", choices=["plain", "regex"], default="plain")

    # rule_list, rule_delete (維持原樣)
    subparsers.add_parser("rule_list")
    p_del = subparsers.add_parser("rule_delete")
    p_del.add_argument("--id", type=int, required=True)

    # scan (新增 --level)
    p_scan = subparsers.add_parser("scan")
    p_scan.add_argument("--file", required=True)
    p_scan.add_argument("--output", default=None)
    p_scan.add_argument("--level", help="Filter by specific alert level")

    # monitor (新增 --log-output)
    p_mon = subparsers.add_parser("monitor")
    p_mon.add_argument("--file", required=True)
    p_mon.add_argument("--interval", type=float, default=1.0)
    p_mon.add_argument("--log-output", help="Path to save alerts during monitoring")

    # rule_hits (v1.0 保留，v2.0 自動套用 plain/regex 比對)
    p_hits = subparsers.add_parser("rule_hits")
    p_hits.add_argument("--id", type=int, required=True)
    p_hits.add_argument("--file", required=True)

    # rule_stats (需求 4：新指令)
    p_stats = subparsers.add_parser("rule_stats")
    p_stats.add_argument("--file", required=True)

    args = parser.parse_args()
    storage = RuleStorage()
    scanner = LogScanner(storage.list_rules())

    if args.command == "rule_add":
        rule = storage.add_rule(args.keyword, args.level, args.mode)
        print(f"[Success] Rule added: ID={rule['id']}, Keyword={rule['keyword']}, Mode={rule['mode']}")

    elif args.command == "rule_list":
        rules = storage.list_rules()
        if not rules:
            print("[Info] No rules defined yet. Use 'rule_add' to create one.")
        else:
            print(f"{'ID':<5} | {'Mode':<8} | {'Keyword':<15} | {'Level':<10} | {'Created At'}")
            print("-" * 60)
            for r in rules:
                mode = r.get('mode', 'plain') # 相容舊資料
                print(f"{r['id']:<5} | {mode:<8} | {r['keyword']:<15} | {r['level']:<10} | {r['created_at']}")

    elif args.command == "scan":
        scanner.scan_file(args.file, output_path=args.output, filter_level=args.level)

    elif args.command == "monitor":
        scanner.monitor_file(args.file, interval=args.interval, log_output=args.log_output)

    elif args.command == "rule_hits":
        scanner.rule_hits(args.file, args.id)

    elif args.command == "rule_stats":
        if not storage.list_rules():
            print("[Info] No rules found. Please add a rule first.")
        else:
            stats, total = scanner.get_stats(args.file)
            print(f"Rule Statistics for '{args.file}':")
            print(f"{'ID':<5} | {'Keyword':<15} | {'Level':<10} | {'Hits':<5}")
            print("-" * 50)
            for rid, info in stats.items():
                print(f"{rid:<5} | {info['keyword']:<15} | {info['level']:<10} | {info['hits']:<5}")
            print("-" * 50)
            print(f"Total Matching Hits: {total}")

    elif args.command == "rule_delete":
        if storage.delete_rule(args.id):
            print(f"[Success] Rule ID {args.id} deleted.")
        else:
            print(f"[Error] Rule ID {args.id} not found.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()