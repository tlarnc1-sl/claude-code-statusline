#!/usr/bin/env bash
# Installs claude-code-statusline: downloads the scripts into ~/.claude,
# wires up ~/.claude/settings.json, adds a `ccstatus` shell alias for the
# settings wizard, and runs that wizard once so you can pick your options.
set -euo pipefail

REPO_RAW="https://raw.githubusercontent.com/tlarnc1-sl/claude-code-statusline/main"
CLAUDE_DIR="$HOME/.claude"
ALIAS_NAME="ccstatus"

mkdir -p "$CLAUDE_DIR"

echo "Downloading statusline.py and setup_statusline.py..."
curl -fsSL "$REPO_RAW/statusline.py" -o "$CLAUDE_DIR/statusline.py"
curl -fsSL "$REPO_RAW/setup_statusline.py" -o "$CLAUDE_DIR/setup_statusline.py"
chmod +x "$CLAUDE_DIR/statusline.py" "$CLAUDE_DIR/setup_statusline.py"

# Pick a shell rc file to add the ccstatus alias to.
SHELL_RC=""
case "${SHELL:-}" in
  */zsh) SHELL_RC="$HOME/.zshrc" ;;
  */bash) SHELL_RC="$HOME/.bashrc" ;;
esac

if [ -n "$SHELL_RC" ]; then
  touch "$SHELL_RC"
  if ! grep -q "alias ${ALIAS_NAME}=" "$SHELL_RC" 2>/dev/null; then
    {
      echo ""
      echo "# Claude Code statusline settings (added by claude-code-statusline installer)"
      echo "alias ${ALIAS_NAME}=\"python3 ${CLAUDE_DIR}/setup_statusline.py\""
    } >> "$SHELL_RC"
    echo "Added '${ALIAS_NAME}' alias to ${SHELL_RC}"
  else
    echo "'${ALIAS_NAME}' alias already present in ${SHELL_RC}"
  fi
else
  echo "Could not detect zsh or bash; add this alias to your shell config manually:"
  echo "  alias ${ALIAS_NAME}=\"python3 ${CLAUDE_DIR}/setup_statusline.py\""
fi

echo ""
echo "Running the interactive setup..."
python3 "$CLAUDE_DIR/setup_statusline.py"

echo ""
echo "Done. Open a new terminal (or run 'source ${SHELL_RC:-your shell config}')"
echo "then type '${ALIAS_NAME}' any time to change your settings."
