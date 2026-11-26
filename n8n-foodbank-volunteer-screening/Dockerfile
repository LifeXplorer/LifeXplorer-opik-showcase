# n8n with the Opik OpenTelemetry integration baked in.
#
# n8n-observability plugs into n8n's lifecycle through EXTERNAL_HOOK_FILES and
# exports one OTel span per workflow execution and per node. Opik ingests them
# on its OTLP endpoint (configured in docker-compose.yml). No node, no code in
# the workflow itself changes.
FROM n8nio/n8n:2.41.7

USER root
RUN npm install -g n8n-observability@1.0.3

# This line is the whole "instrumentation": n8n loads the hooks at startup.
ENV EXTERNAL_HOOK_FILES=/usr/local/lib/node_modules/n8n-observability/dist/hooks.cjs

USER node
