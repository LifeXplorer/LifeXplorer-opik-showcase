#!/usr/bin/env bash
# Build, start the service on :8310, ask the scripted questions, stop it.
set -euo pipefail
cd "$(dirname "$0")"

# Pick up keys from a local .env or the repo-root one.
for f in ../.env .env; do [[ -f "$f" ]] && { set -a; . "$f"; set +a; }; done
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (see .env.example)}"

PORT=8310
mvn -q -DskipTests package
java -jar target/quarkus-app/quarkus-run.jar > target/app.log 2>&1 &
APP=$!
trap 'kill $APP 2>/dev/null || true; wait $APP 2>/dev/null || true' EXIT

# Wait for Quarkus to report it is listening (startup also embeds the FAQ docs).
for _ in $(seq 1 90); do
  grep -q "Listening on" target/app.log 2>/dev/null && break
  kill -0 $APP 2>/dev/null || { cat target/app.log; exit 1; }
  sleep 1
done

while IFS= read -r q; do
  echo "Q: $q"
  echo "A: $(curl -sG "localhost:$PORT/ask" --data-urlencode "q=$q")"
  echo
done <<'QUESTIONS'
What mash temperature gives a dry, crisp pale ale?
How much priming sugar do I add for a 5-gallon batch?
Why shouldn't I use bleach to sanitize my fermenter?
Can I age my beer in oak barrels with Brettanomyces?
QUESTIONS

# Let the last batch (200 ms delay) leave before shutdown. Stopping right after the final answer lost that
# question's trace in our runs, even though the EXIT trap sends SIGTERM and waits for a graceful exit.
sleep 2
