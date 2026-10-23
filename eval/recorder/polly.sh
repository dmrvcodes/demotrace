#!/bin/bash
# Synthesize a case's narration lines with Amazon Polly (neural voice Arthur) and print durations.
# Usage: polly.sh <case_id>   (credentials come from the DemoTrace project's .env profile)
set -euo pipefail
CASE="$1"; DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$DIR/audio/$CASE"
set -a; . "$HOME/Work/hackathon/demotrace/.env" >/dev/null 2>&1; set +a
i=0
node -e "for (const l of require('$DIR/$CASE.lines.json')) console.log(l.text)" | while IFS= read -r text; do
  i=$((i+1))
  aws polly synthesize-speech --region us-east-1 --engine neural --voice-id Arthur \
    --output-format mp3 --sample-rate 24000 --text "$text" "$DIR/audio/$CASE/l$i.mp3" >/dev/null
  printf "l%s %ss  %s\n" "$i" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$DIR/audio/$CASE/l$i.mp3")" "$text"
done
