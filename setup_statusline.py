#!/usr/bin/env python3
"""Interactive setup for the Claude Code statusline.

Run this any time you want to change what the statusline shows:

    python3 ~/.claude/setup_statusline.py

It writes your choices to ~/.claude/statusline_config.json and makes
sure ~/.claude/settings.json points at ~/.claude/statusline.py.
Press Enter at any prompt to keep the default (shown in [brackets]).
"""
import json
import sys
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
CONFIG_FILE = CLAUDE_DIR / "statusline_config.json"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
STATUSLINE_SCRIPT = CLAUDE_DIR / "statusline.py"

DEFAULTS = {
    "show_git": True,
    "show_ahead_behind": True,
    "show_context": True,
    "show_rate_limits": True,
    "show_cache": True,
    "show_cost": True,
    "show_today_total": True,
    "cwd_max_parts": 2,
    "bar_width": 10,
    "warn_threshold": 50,
    "danger_threshold": 80,
    "today_cache_ttl": 60,
}


def load_existing() -> dict:
    config = dict(DEFAULTS)
    try:
        with open(CONFIG_FILE, "r") as f:
            config.update(json.load(f))
    except Exception:
        pass
    return config


def ask_yes_no(prompt: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{prompt} {suffix}: ").strip().lower()
    except EOFError:
        print("(非対話環境のためデフォルトを使用)")
        return default
    if not answer:
        return default
    return answer.startswith("y")


def ask_int(prompt: str, default: int, min_val: int = 0, max_val: int = 100) -> int:
    try:
        answer = input(f"{prompt} [{default}]: ").strip()
    except EOFError:
        print("(非対話環境のためデフォルトを使用)")
        return default
    if not answer:
        return default
    try:
        value = int(answer)
    except ValueError:
        print(f"数字を入力してください。デフォルト({default})を使います。")
        return default
    return max(min_val, min(max_val, value))


def update_settings_json() -> None:
    settings = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        except Exception:
            print(f"警告: {SETTINGS_FILE} を読み込めませんでした。statusLine の設定はスキップします。")
            return

    desired = {
        "type": "command",
        "command": "~/.claude/statusline.py",
        "padding": 0,
    }
    if settings.get("statusLine") == desired:
        return  # already wired up

    settings["statusLine"] = desired
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"✓ {SETTINGS_FILE} の statusLine 設定を更新しました")


def main() -> None:
    print("=== Claude Code ステータスライン設定 ===")
    print("Enterキーでデフォルト値([...]内)を使用します。\n")

    config = load_existing()

    print("--- 表示するセクション ---")
    config["show_git"] = ask_yes_no("gitブランチ・変更状態を表示する", config["show_git"])
    if config["show_git"]:
        config["show_ahead_behind"] = ask_yes_no(
            "  └ リモートとのahead/behind(↑↓)も表示する", config["show_ahead_behind"]
        )
    config["show_context"] = ask_yes_no("コンテキストウィンドウ使用率を表示する", config["show_context"])
    config["show_rate_limits"] = ask_yes_no(
        "5時間/週間の利用制限(rate limits)を表示する [Pro/Maxのみ]", config["show_rate_limits"]
    )
    config["show_cache"] = ask_yes_no("プロンプトキャッシュのヒット率を表示する", config["show_cache"])
    config["show_cost"] = ask_yes_no("セッションのコスト・経過時間を表示する", config["show_cost"])
    config["show_today_total"] = ask_yes_no(
        "今日の推定合計コスト(全セッション横断・概算)を表示する", config["show_today_total"]
    )

    print("\n--- 見た目の調整 ---")
    config["bar_width"] = ask_int("プログレスバーの幅(文字数)", config["bar_width"], 4, 30)
    config["cwd_max_parts"] = ask_int(
        "作業ディレクトリを末尾何階層まで表示するか(0=省略しない)", config["cwd_max_parts"], 0, 10
    )
    config["warn_threshold"] = ask_int(
        "黄色警告になる使用率(%)", config["warn_threshold"], 1, 99
    )
    config["danger_threshold"] = ask_int(
        "赤色警告になる使用率(%)", config["danger_threshold"],
        config["warn_threshold"] + 1, 100,
    )
    if config["show_today_total"]:
        config["today_cache_ttl"] = ask_int(
            "今日の合計コストを再計算する間隔(秒)", config["today_cache_ttl"], 5, 3600
        )

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"\n✓ 設定を {CONFIG_FILE} に保存しました")

    try:
        STATUSLINE_SCRIPT.chmod(0o755)
    except Exception:
        pass

    update_settings_json()

    print("\n次回のプロンプトから新しい設定が反映されます。")
    print("再設定したくなったら、またこのスクリプトを実行してください:")
    print("  python3 ~/.claude/setup_statusline.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。設定は保存されていません。")
        sys.exit(1)
