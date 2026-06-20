#!/usr/bin/env sh
set -e
REPO="${SMARTSTUDY_REPO:-https://github.com/Ffgags13/SmartStudy_RAG.git}"
DIR="${SMARTSTUDY_DIR:-SmartStudy_RAG}"
git clone --depth 1 "$REPO" "$DIR"
cd "$DIR"
sh run.sh
