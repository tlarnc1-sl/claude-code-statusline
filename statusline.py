#!/usr/bin/env python3
"""Claude Code custom statusline.

Reads the session JSON Claude Code passes on stdin and prints a
multi-line status:

  line1: model / shortened cwd / git branch+status+ahead-behind
  line2: context window usage / 5-hour & weekly rate-limit bars with
         reset countdowns
  line3: prompt-cache hit rate / session cost & duration / today's
         estimated total cost across all sessions

Every section can be turned on/off and several numbers (bar width,
color thresholds, path depth) can be tuned via a config file at
~/.claude/statusline_config.json. Run `python3 ~/.claude/setup_statusline.py`
to configure it interactively, or edit the JSON by hand.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RESET = "\033[0m"
FILLED = "█"
EMPTY = "░"

CONFIG_FILE = Path.home() / ".claude" / "statusline_config.json"

DEFAULT_CONFIG = {
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

# Rough list prices per 1M tokens (USD): (input, output, cache_write, cache_read).
# These are approximations for the daily-cost estimate only — they are not
# used for cost.total_cost_usd (which Claude Code computes itself) and may
# drift out of date. Adjust if Anthropic's pricing changes.
PRICING = {
    "opus": (15.0, 75.0, 18.75, 1.5),
    "sonnet": (3.0, 15.0, 3.75, 0.3),
    "haiku": (1.0, 5.0, 1.25, 0.1),
}


def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r") as f:
            user_config = json.load(f)
        if isinstance(user_config, dict):
            config.update(user_config)
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return config


def color(code: str, text: str) -> str:
    return f"\033[{code}m{text}{RESET}"


def threshold_color(pct: float, config: dict) -> str:
    if pct < config["warn_threshold"]:
        return "32"
    if pct < config["danger_threshold"]:
        return "33"
    return "31"


def make_bar(pct: float, config: dict) -> str:
    width = config["bar_width"]
    pct = max(0.0, min(100.0, pct))
    filled = round(pct / 100 * width)
    bar = FILLED * filled + EMPTY * (width - filled)
    return color(threshold_color(pct, config), f"[{bar}]")


def format_k(n: float) -> str:
    if n >= 1000:
        return f"{n / 1000:.0f}k"
    return str(int(n))


def format_countdown(resets_at) -> str:
    if not isinstance(resets_at, (int, float)):
        return ""
    delta = int(resets_at - time.time())
    if delta <= 0:
        return "now"
    days, rem = divmod(delta, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    if days:
        return f"{days}d{hours}h"
    if hours:
        return f"{hours}h{mins}m"
    return f"{mins}m"


def read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def get_model_name(data: dict) -> str:
    model = data.get("model", {})
    return model.get("display_name") or model.get("id") or "unknown"


def get_cwd_raw(data: dict) -> str:
    workspace = data.get("workspace", {})
    return workspace.get("current_dir") or data.get("cwd") or ""


def get_cwd_short(cwd: str, max_parts: int) -> str:
    if not cwd:
        return "?"
    home = str(Path.home())
    display = "~" + cwd[len(home):] if cwd.startswith(home) else cwd
    prefix = "~" if display.startswith("~") else ""
    body = display[1:] if prefix else display
    parts = [p for p in body.split("/") if p]
    if max_parts and len(parts) > max_parts:
        return ".../" + "/".join(parts[-max_parts:])
    return display


def run_git(cwd: str, *args: str):
    try:
        result = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True, text=True, timeout=1,
        )
        return result
    except Exception:
        return None


def get_git_info(cwd: str, config: dict) -> str:
    if not config["show_git"]:
        return ""
    if not cwd or not Path(cwd).expanduser().exists():
        return ""
    real_cwd = str(Path(cwd).expanduser())

    branch = run_git(real_cwd, "rev-parse", "--abbrev-ref", "HEAD")
    if not branch or branch.returncode != 0:
        return ""
    branch_name = branch.stdout.strip()

    status = run_git(real_cwd, "status", "--porcelain")
    dirty = bool(status and status.stdout.strip())
    marker = color("33", "✗") if dirty else color("32", "✓")

    ahead_behind = ""
    if config["show_ahead_behind"]:
        counts = run_git(
            real_cwd, "rev-list", "--left-right", "--count", "@{upstream}...HEAD"
        )
        if counts and counts.returncode == 0 and counts.stdout.strip():
            try:
                behind, ahead = (int(x) for x in counts.stdout.split())
                pieces = []
                if ahead:
                    pieces.append(color("32", f"↑{ahead}"))
                if behind:
                    pieces.append(color("31", f"↓{behind}"))
                ahead_behind = "".join(pieces)
            except ValueError:
                pass

    parts = [color("35", branch_name), marker]
    if ahead_behind:
        parts.append(ahead_behind)
    return "".join(parts)


def get_cost_info(data: dict, config: dict) -> str:
    if not config["show_cost"]:
        return ""
    cost = data.get("cost", {})
    total_cost = cost.get("total_cost_usd")
    duration_ms = cost.get("total_duration_ms")
    parts = []
    if isinstance(total_cost, (int, float)):
        parts.append(f"${total_cost:.2f}")
    if isinstance(duration_ms, (int, float)):
        seconds = int(duration_ms / 1000)
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        if hours:
            parts.append(f"{hours}h{mins}m")
        elif mins:
            parts.append(f"{mins}m{secs}s")
        else:
            parts.append(f"{secs}s")
    return " ".join(parts)


def get_context_info(data: dict, config: dict) -> str:
    """Official context-window usage (no more transcript guessing)."""
    if not config["show_context"]:
        return ""
    cw = data.get("context_window")
    if not cw:
        return ""
    pct = cw.get("used_percentage")
    if pct is None:
        return ""
    used = (cw.get("total_input_tokens") or 0) + (cw.get("total_output_tokens") or 0)
    size = cw.get("context_window_size") or 200_000
    return f"ctx{make_bar(pct, config)}{pct:.0f}% {format_k(used)}/{format_k(size)}"


def get_rate_limit_segments(data: dict, config: dict) -> list:
    if not config["show_rate_limits"]:
        return []
    rate = data.get("rate_limits", {})
    segments = []
    for key, label in (("five_hour", "5h"), ("seven_day", "wk")):
        window = rate.get(key)
        if not window or window.get("used_percentage") is None:
            continue
        pct = window["used_percentage"]
        countdown = format_countdown(window.get("resets_at"))
        text = f"{label}{make_bar(pct, config)}{pct:.0f}%"
        if countdown:
            text += color("90", f"→{countdown}")
        segments.append(text)
    return segments


def get_cache_info(data: dict, config: dict) -> str:
    if not config["show_cache"]:
        return ""
    pc = data.get("prompt_cache")
    if not pc:
        return ""
    hit_ratio = pc.get("hit_ratio")
    if hit_ratio is None:
        return ""
    pct = hit_ratio * 100
    return color(threshold_color(100 - pct, config), f"cache {pct:.0f}%")


def model_price_key(model_id: str) -> str:
    model_id = (model_id or "").lower()
    for key in PRICING:
        if key in model_id:
            return key
    return "sonnet"


def estimate_cost_from_usage(usage: dict, price_key: str) -> float:
    in_price, out_price, write_price, read_price = PRICING[price_key]
    input_tokens = usage.get("input_tokens", 0) or 0
    output_tokens = usage.get("output_tokens", 0) or 0
    cache_write = usage.get("cache_creation_input_tokens", 0) or 0
    cache_read = usage.get("cache_read_input_tokens", 0) or 0
    return (
        input_tokens * in_price
        + output_tokens * out_price
        + cache_write * write_price
        + cache_read * read_price
    ) / 1_000_000


TODAY_CACHE_FILE = Path.home() / ".claude" / ".statusline_today_cache.json"


def get_today_total(config: dict) -> str:
    """Rough estimate of today's total cost across all sessions, based on
    a local pricing table (may drift from actual billed prices)."""
    if not config["show_today_total"]:
        return ""
    today = time.strftime("%Y-%m-%d")
    now = time.time()
    ttl = config["today_cache_ttl"]
    try:
        cached = json.loads(TODAY_CACHE_FILE.read_text())
        if cached.get("date") == today and now - cached.get("ts", 0) < ttl:
            return cached.get("text", "")
    except Exception:
        pass

    result = _compute_today_total(today)

    try:
        TODAY_CACHE_FILE.write_text(json.dumps({"ts": now, "date": today, "text": result}))
    except Exception:
        pass
    return result


def _compute_today_total(today: str) -> str:
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return ""
    total_cost = 0.0
    session_ids = set()
    try:
        for jsonl_file in projects_dir.glob("*/*.jsonl"):
            try:
                mtime = jsonl_file.stat().st_mtime
            except OSError:
                continue
            if time.strftime("%Y-%m-%d", time.localtime(mtime)) != today:
                continue
            try:
                with open(jsonl_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except Exception:
                            continue
                        ts = entry.get("timestamp")
                        if ts:
                            day = ts[:10]
                            if day != today:
                                continue
                        message = entry.get("message")
                        if not isinstance(message, dict):
                            continue
                        usage = message.get("usage")
                        if not usage:
                            continue
                        price_key = model_price_key(message.get("model", ""))
                        total_cost += estimate_cost_from_usage(usage, price_key)
                        session_id = entry.get("session_id")
                        if session_id:
                            session_ids.add(session_id)
            except OSError:
                continue
    except Exception:
        return ""
    if total_cost <= 0:
        return ""
    return color("90", f"today ~${total_cost:.2f} ({len(session_ids)} sessions)")


def main() -> None:
    config = load_config()
    data = read_input()

    model_name = color("36", get_model_name(data))
    cwd_raw = get_cwd_raw(data)
    cwd_short = get_cwd_short(cwd_raw, config["cwd_max_parts"])
    git_info = get_git_info(cwd_raw, config)
    cost_info = get_cost_info(data, config)
    ctx_info = get_context_info(data, config)
    limit_segments = get_rate_limit_segments(data, config)
    cache_info = get_cache_info(data, config)
    today_info = get_today_total(config)

    line1_parts = [model_name, color("90", cwd_short)]
    if git_info:
        line1_parts.append(git_info)
    line1 = "  ".join(line1_parts)

    line2_parts = []
    if ctx_info:
        line2_parts.append(ctx_info)
    line2_parts.extend(limit_segments)
    line2 = "  ".join(line2_parts)

    line3_parts = []
    if cache_info:
        line3_parts.append(cache_info)
    if cost_info:
        line3_parts.append(color("90", cost_info))
    if today_info:
        line3_parts.append(today_info)
    line3 = "  ".join(line3_parts)

    print(line1)
    if line2:
        print(line2)
    if line3:
        print(line3)


if __name__ == "__main__":
    main()
