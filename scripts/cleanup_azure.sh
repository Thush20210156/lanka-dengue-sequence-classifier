#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RG=${RG:-$(python3 -c "import json;print(json.load(open('deployment-state.json'))['resource_group'])")}
az resource list -g "$RG" -o table
printf 'This removes the application, registry and other resources in %s.\n' "$RG"
read -r -p 'Type the exact resource group name to continue: ' CONFIRM
[[ "$CONFIRM" == "$RG" ]] || { echo 'No deletion performed.'; exit 1; }
az group delete -n "$RG"
