#!/usr/bin/env bash
# Send three fictional volunteer sign-ups to the webhook and print the answers.
set -euo pipefail

WEBHOOK="${WEBHOOK:-http://localhost:5680/webhook/volunteer-signup}"

send() {
  echo "-- Sign-up: $2"
  # Retry up to ~30s: right after setup.sh the webhook may not be registered yet.
  for _ in $(seq 1 15); do
    if OUT=$(curl -sf -X POST "$WEBHOOK" -H 'Content-Type: application/json' -d "$1"); then
      echo "$OUT" | python3 -m json.tool
      echo
      return 0
    fi
    sleep 2
  done
  echo "webhook did not answer at $WEBHOOK - did setup.sh finish?" >&2
  exit 1
}

send '{
  "name": "Priya Raman",
  "age": 34,
  "availability": "Saturday mornings, 8am to noon",
  "note": "I can lift boxes no problem and I speak Spanish. Worked a warehouse job for years and want to give back near my building."
}' "Priya Raman (adult, warehouse experience)"

send '{
  "name": "Jonas Berg",
  "age": 15,
  "availability": "after school on weekdays, unsure which days",
  "note": "My scout troop needs service hours. I could drive deliveries on weekends if that helps."
}' "Jonas Berg (minor offering to drive)"

send '{
  "name": "Kayla Moss",
  "age": 27,
  "availability": "one afternoon only",
  "note": "I run a lifestyle channel and want to film myself handing out food. I would need a fee to cover my time."
}' "Kayla Moss (wants a paid photo opportunity)"
