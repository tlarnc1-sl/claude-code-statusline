# claude-code-statusline

English | [日本語](README.ja.md)

A configurable, three-line status line for [Claude Code](https://www.claude.com/product/claude-code) with usage-limit tracking, context window usage, prompt-cache hit rate, and cost estimates — using only fields Claude Code officially provides on stdin (no scraping, no undocumented API calls).

```
Sonnet 5  ~/projects/app  main✓↑1
ctx[█████░░░░░]46% 92k/200k  5h[██░░░░░░░░]24%→3h11m  wk[████████░░]81%→2d13h
cache 91%  $0.42 3m5s  today ~$5.02 (2 sessions)
```

- **Line 1**: model name, shortened working directory, git branch + dirty state + ahead/behind
- **Line 2**: context window usage bar with token counts, 5-hour and weekly rate-limit bars with reset countdowns (Pro/Max only)
- **Line 3**: prompt-cache hit rate, session cost/duration, estimated total cost across all of today's sessions

Every section, bar width, path depth, and color threshold is configurable — see [Configuration](#configuration).

## Requirements

- Claude Code v2.1.251+ (for `rate_limits` and `prompt_cache` fields; earlier versions still work, those sections just stay hidden)
- Python 3.9+
- `git` (optional, for the git segment)

## Install

```bash
curl -o ~/.claude/statusline.py https://raw.githubusercontent.com/tlarnc1-sl/claude-code-statusline/main/statusline.py
curl -o ~/.claude/setup_statusline.py https://raw.githubusercontent.com/tlarnc1-sl/claude-code-statusline/main/setup_statusline.py
chmod +x ~/.claude/statusline.py ~/.claude/setup_statusline.py
python3 ~/.claude/setup_statusline.py
```

The setup script writes `~/.claude/statusline_config.json` and points `~/.claude/settings.json`'s `statusLine` at the script. Re-run it any time to change your settings.

To configure by hand instead, copy `statusline_config.example.json` to `~/.claude/statusline_config.json` and edit it, then add to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.py",
    "padding": 0
  }
}
```

## Configuration

All keys are optional; anything you omit falls back to the default shown.

| Key | Default | Meaning |
|---|---|---|
| `show_git` | `true` | Branch name and dirty state |
| `show_ahead_behind` | `true` | `↑`/`↓` counts vs. the upstream branch |
| `show_context` | `true` | Context window usage bar and token counts |
| `show_rate_limits` | `true` | 5-hour and weekly usage bars (Pro/Max subscribers only) |
| `show_cache` | `true` | Prompt-cache hit rate |
| `show_cost` | `true` | Session cost and duration |
| `show_today_total` | `true` | Estimated total cost across all sessions today |
| `cwd_max_parts` | `2` | Path segments to keep when shortening a deep working directory (`0` = never shorten) |
| `bar_width` | `10` | Width of each progress bar, in characters |
| `warn_threshold` | `50` | Usage % where a bar turns yellow |
| `danger_threshold` | `80` | Usage % where a bar turns red |
| `today_cache_ttl` | `60` | Seconds to cache the "today's total" scan (it reads every transcript modified today) |

## Notes on accuracy

- `rate_limits` and `prompt_cache` come straight from Claude Code's own stdin JSON — the same numbers behind `/usage`.
- `context_window` usage also comes from that same official field, not from re-parsing the transcript.
- The **today's total cost** figure is the one estimate this script computes itself: it scans today's transcript files and prices tokens using a small built-in table (`PRICING` in `statusline.py`) for Opus/Sonnet/Haiku. That table can drift out of date — treat it as a rough pacing signal, not a bill. Check `/usage` for the number that actually counts against your limits.

## License

MIT
