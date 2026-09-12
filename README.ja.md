# claude-code-statusline

[English](README.md) | 日本語

[Claude Code](https://www.claude.com/product/claude-code) 用の、設定可能な3行ステータスラインです。利用制限の使用率、コンテキストウィンドウ使用量、プロンプトキャッシュのヒット率、コスト見積もりを表示します。Claude Codeが公式にstdinで渡すフィールドだけを使っており、スクレイピングや非公開APIの呼び出しは一切行っていません。

```
Sonnet 5  ~/projects/app  main✓↑1
ctx▕████▋░░░░░❙46% 92k/200k  5h▕██▍░░░░░░░❙24%→3h11m  wk▕████████▏░❙81%→2d13h
cache 91%  $0.42 3m5s  today ~$5.02 (2 sessions)
```

- **1行目**: モデル名、短縮した作業ディレクトリ、gitブランチ + 変更有無 + リモートとのahead/behind
- **2行目**: コンテキストウィンドウ使用量のバー(トークン数付き)、5時間/週間の利用制限バーとリセットまでのカウントダウン(Pro/Maxプランのみ)
- **3行目**: プロンプトキャッシュのヒット率、セッションのコスト・経過時間、今日の全セッション合計コストの推定値

各セクションの表示/非表示、バーの幅、パスの表示階層、色が変わるしきい値はすべて設定可能です。詳しくは[設定](#設定)を参照してください。

## 必要環境

- Claude Code v2.1.251以降(`rate_limits` と `prompt_cache` フィールドを使うため。それより古いバージョンでも動きますが、該当セクションは表示されません)
- Python 3.9以降
- `git`(gitの表示セクションを使う場合のみ)

## インストール

```bash
curl -o ~/.claude/statusline.py https://raw.githubusercontent.com/tlarnc1-sl/claude-code-statusline/main/statusline.py
curl -o ~/.claude/setup_statusline.py https://raw.githubusercontent.com/tlarnc1-sl/claude-code-statusline/main/setup_statusline.py
chmod +x ~/.claude/statusline.py ~/.claude/setup_statusline.py
python3 ~/.claude/setup_statusline.py
```

セットアップスクリプトが `~/.claude/statusline_config.json` を作成し、`~/.claude/settings.json` の `statusLine` をこのスクリプトに向けます。設定を変えたくなったら、いつでも再実行してください。

手動で設定したい場合は、`statusline_config.example.json` を `~/.claude/statusline_config.json` としてコピーして編集し、`~/.claude/settings.json` に以下を追加してください。

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.py",
    "padding": 0
  }
}
```

## 設定

すべての項目は省略可能です。省略した項目は表内のデフォルト値になります。

| キー | デフォルト | 内容 |
|---|---|---|
| `show_git` | `true` | ブランチ名と変更有無 |
| `show_ahead_behind` | `true` | upstreamブランチとの `↑`/`↓` 差分 |
| `show_context` | `true` | コンテキストウィンドウ使用率のバーとトークン数 |
| `show_rate_limits` | `true` | 5時間/週間の使用率バー(Pro/Maxプランのみ) |
| `show_cache` | `true` | プロンプトキャッシュのヒット率 |
| `show_cost` | `true` | セッションのコストと経過時間 |
| `show_today_total` | `true` | 今日の全セッション合計コストの推定値 |
| `cwd_max_parts` | `2` | 深い階層のディレクトリを短縮する際に残す階層数(`0` で短縮しない) |
| `bar_width` | `10` | 各プログレスバーの幅(文字数) |
| `warn_threshold` | `50` | バーが黄色になる使用率(%) |
| `danger_threshold` | `80` | バーが赤色になる使用率(%) |
| `today_cache_ttl` | `60` | 「今日の合計コスト」の再計算間隔(秒)。今日更新された全トランスクリプトを読むため |

## 精度についての注意

- `rate_limits` と `prompt_cache` は、Claude Code自身がstdinのJSONで渡す値をそのまま使っています。`/usage` コマンドが表示するのと同じ数値です。
- `context_window` の使用量も、トランスクリプトを再解析するのではなく同じ公式フィールドから取得しています。
- **今日の合計コスト**だけは、このスクリプトが自前で計算する唯一の推定値です。今日更新されたトランスクリプトを走査し、`statusline.py` 内の `PRICING` という簡易的な単価表(Opus/Sonnet/Haiku)でトークンを価格換算しています。この単価表は実際の価格改定に追従できず古くなる可能性があるため、正確な請求額としてではなく、あくまで大まかなペース確認用として扱ってください。実際に制限へカウントされる正確な数値は `/usage` コマンドで確認してください。

## ライセンス

MIT
