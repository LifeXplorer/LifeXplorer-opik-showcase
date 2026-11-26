#!/usr/bin/env bash
# Wait until Opik holds at least N traces for this example's project (default 3),
# then print each trace with its span names. Uses only Opik's public REST API.
#   OPIK_API_URL   default http://localhost:5173/api   (Opik Cloud: https://www.comet.com/opik/api)
#   OPIK_WORKSPACE default "default"
#   OPIK_API_KEY   optional; only needed for Opik Cloud
set -euo pipefail

WANT="${1:-3}"
PROJECT="n8n-foodbank-volunteer-screening"
BASE="${OPIK_API_URL:-http://localhost:5173/api}"
WS="${OPIK_WORKSPACE:-default}"

# No empty-array expansion here: under `set -u`, macOS bash 3.2 treats "${ARR[@]}" of an empty array as an error.
get() {
  if [ -n "${OPIK_API_KEY:-}" ]; then
    curl -sf -G "$BASE/v1/private/$1" -H "Authorization: $OPIK_API_KEY" -H "Comet-Workspace: $WS" "${@:2}"
  else
    curl -sf -G "$BASE/v1/private/$1" -H "Comet-Workspace: $WS" "${@:2}"
  fi
}

echo -n "==> Waiting for $WANT trace(s) in Opik project '$PROJECT'"
for _ in $(seq 1 30); do
  N=$(get traces --data-urlencode "project_name=$PROJECT" --data-urlencode "size=100" 2>/dev/null \
      | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('content',[])))" 2>/dev/null || echo 0)
  [ "$N" -ge "$WANT" ] && break
  echo -n "."; sleep 2
done
echo " found $N"
[ "$N" -ge "$WANT" ] || { echo "traces did not arrive - is Opik reachable from the n8n container?" >&2; exit 1; }

get traces --data-urlencode "project_name=$PROJECT" --data-urlencode "size=100" > /tmp/foodbank_traces.json
python3 - "$BASE" "$WS" "$PROJECT" <<'PY'
import json, subprocess, sys, os
base, ws, project = sys.argv[1:4]
traces = json.load(open("/tmp/foodbank_traces.json"))["content"]
auth = ["-H", "Authorization: " + os.environ["OPIK_API_KEY"]] if os.environ.get("OPIK_API_KEY") else []
for t in sorted(traces, key=lambda t: t["start_time"]):
    out = subprocess.run(
        ["curl", "-sf", "-G", f"{base}/v1/private/spans", *auth, "-H", f"Comet-Workspace: {ws}",
         "--data-urlencode", f"project_name={project}", "--data-urlencode", f"trace_id={t['id']}",
         "--data-urlencode", "size=100"], capture_output=True, text=True).stdout
    spans = json.loads(out).get("content", [])
    print(f"trace {t['id']}  name={t.get('name')}  spans={len(spans)}")
    for s in sorted(spans, key=lambda s: s["start_time"]):
        print(f"    [{s.get('type')}] {s['name']}")
PY
rm -f /tmp/foodbank_traces.json
