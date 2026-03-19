#!/usr/bin/env bash
# setup_nanoclaw.sh
#
# Clones nanoclaw into nanoclaw/app/ and prepares it for Docker.
# Run this once before: docker compose up -d
#
# Usage:
#   bash scripts/setup_nanoclaw.sh
#
# What it does:
#   1. Clones github.com/qwibitai/nanoclaw into nanoclaw/app/
#   2. Installs Node.js dependencies
#   3. Builds the TypeScript project
#   4. Confirms the group config is in place

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NANOCLAW_DIR="$REPO_ROOT/nanoclaw/app"
NANOCLAW_REPO="https://github.com/qwibitai/nanoclaw.git"
GROUP_CONFIG="$REPO_ROOT/nanoclaw/groups/nycpolicyscope/CLAUDE.md"

echo "NYC PolicyScope — nanoclaw setup"
echo "================================="

# ── 1. Clone nanoclaw ────────────────────────────────────────────────────────
if [ -d "$NANOCLAW_DIR/.git" ]; then
  echo "nanoclaw already cloned. Pulling latest..."
  git -C "$NANOCLAW_DIR" pull origin main || echo "  Warning: git pull failed — continuing with existing version."
else
  echo "Cloning nanoclaw into nanoclaw/app/ ..."
  git clone "$NANOCLAW_REPO" "$NANOCLAW_DIR"
  echo "  Cloned."
fi

# ── 2. Install dependencies ───────────────────────────────────────────────────
echo ""
echo "Installing Node.js dependencies..."
cd "$NANOCLAW_DIR"

if ! command -v node &>/dev/null; then
  echo "ERROR: Node.js is not installed. Install Node.js 20+ and retry."
  exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 20 ]; then
  echo "ERROR: Node.js 20+ required. Found: v$NODE_VERSION"
  exit 1
fi

npm install
echo "  Dependencies installed."

# ── 3. Build TypeScript ───────────────────────────────────────────────────────
echo ""
echo "Building TypeScript..."
npm run build
echo "  Build complete."

# ── 4. Check group config ─────────────────────────────────────────────────────
echo ""
if [ -f "$GROUP_CONFIG" ]; then
  echo "Group config found: nanoclaw/groups/nycpolicyscope/CLAUDE.md"
else
  echo "WARNING: Group config not found at: $GROUP_CONFIG"
  echo "  Something may have gone wrong. Check the nanoclaw/groups/ directory."
fi

# ── 5. Check .env ─────────────────────────────────────────────────────────────
echo ""
ENV_FILE="$REPO_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
  echo ".env file found."

  # Check required vars
  MISSING=()
  check_var() {
    local var="$1"
    if ! grep -q "^${var}=.\+" "$ENV_FILE" 2>/dev/null; then
      MISSING+=("$var")
    fi
  }

  check_var "ANTHROPIC_API_KEY"
  check_var "DISCORD_BOT_TOKEN"
  check_var "DISCORD_CHANNEL_ID"
  check_var "GOOGLE_AI_API_KEY"
  check_var "N8N_WEBHOOK_TOKEN"

  if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    echo "WARNING: The following .env variables are not set:"
    for v in "${MISSING[@]}"; do
      echo "  - $v"
    done
    echo "  Fill these in before running docker compose."
  else
    echo "  All required env vars are set."
  fi
else
  echo "WARNING: No .env file found."
  echo "  Copy .env.example to .env and fill in your keys before running docker compose."
fi

echo ""
echo "Setup complete. Next steps:"
echo "  1. Fill in .env (if not done)"
echo "  2. In your Discord server, create a bot and invite it with Send Messages + Read Message History"
echo "  3. cd docker && docker compose up -d"
echo "  4. Import workflows from n8n/workflows/ into n8n UI (localhost:5678)"
echo "  5. In Discord, type: @policy run pipeline"
