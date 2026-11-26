#!/usr/bin/env bash
# One-shot, headless setup:
#   1. builds and starts n8n on http://localhost:5680
#   2. claims the instance (owner account) and mints an n8n API key
#   3. creates the OpenAI credential from $OPENAI_API_KEY (never from a file)
#   4. imports workflow/volunteer-screening.json through the public API and activates it
#
# Requires: docker, curl, python3. OPENAI_API_KEY comes from the shell or from
# the nearest .env found by walking up from this folder.
set -euo pipefail
cd "$(dirname "$0")"

N8N_URL="http://localhost:5680"
OWNER_EMAIL="volunteers@example.com"      # local-only demo owner (n8n requires one)
OWNER_PASSWORD="Foodbank-demo-1"
WORKFLOW_NAME="Volunteer screening"

# --- 0. Resolve keys ---------------------------------------------------------
dir="$PWD"
while [ "$dir" != "/" ]; do
  if [ -f "$dir/.env" ]; then set -a; . "$dir/.env"; set +a; break; fi
  dir="$(dirname "$dir")"
done
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (shell env or a .env above this folder)}"

json() { python3 -c "import json,sys; d=json.load(sys.stdin); print(d$1)"; }

# --- 1. Start n8n ------------------------------------------------------------
echo "==> Building and starting n8n"
docker compose up -d --build

echo -n "==> Waiting for n8n to be ready"
for _ in $(seq 1 90); do
  if curl -sf "$N8N_URL/healthz/readiness" >/dev/null 2>&1; then echo " - up"; break; fi
  echo -n "."; sleep 2
done
curl -sf "$N8N_URL/healthz/readiness" >/dev/null || { echo "n8n did not come up"; exit 1; }

# --- 2. Owner account + API key (REST, no browser) ---------------------------
# The session cookie is bound to a browser id, so every /rest call sends the
# same browser-id header.
COOKIES="$(mktemp)"; trap 'rm -f "$COOKIES"' EXIT
BROWSER_ID="setup-script"

echo "==> Claiming the instance (owner setup)"
SETUP_BODY=$(printf '{"email":"%s","firstName":"Food","lastName":"Bank","password":"%s"}' \
  "$OWNER_EMAIL" "$OWNER_PASSWORD")
LOGIN_BODY=$(printf '{"emailOrLdapLoginId":"%s","password":"%s"}' \
  "$OWNER_EMAIL" "$OWNER_PASSWORD")
AUTHED=""
for _ in $(seq 1 15); do
  # /rest can lag the health check on first boot, so retry; fall back to a
  # normal login when the instance is already claimed.
  if curl -sf -c "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
       -X POST "$N8N_URL/rest/owner/setup" -d "$SETUP_BODY" >/dev/null 2>&1; then
    AUTHED=yes; break
  fi
  if curl -sf -c "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
       -X POST "$N8N_URL/rest/login" -d "$LOGIN_BODY" >/dev/null 2>&1; then
    echo "    already claimed - logged in"
    AUTHED=yes; break
  fi
  sleep 2
done
[ -n "$AUTHED" ] || { echo "could not authenticate against n8n"; exit 1; }

echo "==> Minting an n8n API key"
API_KEY=$(curl -sf -b "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
  -X POST "$N8N_URL/rest/api-keys" \
  -d '{"label":"setup-script","expiresAt":null,"scopes":["workflow:create","workflow:read","workflow:update","workflow:delete","workflow:list","workflow:activate","workflow:deactivate","credential:create","credential:delete","execution:read","execution:list"]}' \
  | json "['data']['rawApiKey']")

api() { # method path [json-body]
  local method="$1" path="$2" body="${3:-}"
  if [ -n "$body" ]; then
    curl -sf -X "$method" "$N8N_URL/api/v1$path" \
      -H "X-N8N-API-KEY: $API_KEY" -H 'Content-Type: application/json' -d "$body"
  else
    curl -sf -X "$method" "$N8N_URL/api/v1$path" -H "X-N8N-API-KEY: $API_KEY"
  fi
}

# --- 3. OpenAI credential (value injected from env, never committed) ---------
echo "==> Creating the OpenAI credential"
CRED_BODY=$(printf '{"name":"OpenAI (volunteer screening)","type":"openAiApi","data":{"apiKey":"%s"}}' \
  "$OPENAI_API_KEY")
CRED_ID=$(api POST /credentials "$CRED_BODY" | json "['id']")

# --- 4. Import + activate the workflow ---------------------------------------
echo "==> Removing any previous copy of the workflow"
api GET "/workflows?name=Volunteer%20screening" \
  | python3 -c "import json,sys; [print(w['id']) for w in json.load(sys.stdin).get('data',[]) if w['name']=='$WORKFLOW_NAME']" \
  | while read -r wid; do api DELETE "/workflows/$wid" >/dev/null; echo "    deleted $wid"; done

echo "==> Importing workflow/volunteer-screening.json"
WF_BODY=$(python3 - "$CRED_ID" <<'PY'
import json, sys
wf = json.load(open("workflow/volunteer-screening.json"))
print(json.dumps(wf).replace("__OPENAI_CREDENTIAL_ID__", sys.argv[1]))
PY
)
WF_ID=$(api POST /workflows "$WF_BODY" | json "['id']")

echo "==> Activating the workflow"
api POST "/workflows/$WF_ID/activate" "" >/dev/null

# The webhook registers a few seconds after activation; demo.sh retries.
echo
echo "Done. n8n UI:      $N8N_URL  (login: $OWNER_EMAIL / $OWNER_PASSWORD)"
echo "Webhook endpoint:  $N8N_URL/webhook/volunteer-signup"
echo "Send sign-ups:     ./demo.sh"
