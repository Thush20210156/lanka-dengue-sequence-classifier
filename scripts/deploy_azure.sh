#!/usr/bin/env bash
# Run in Bash from a trusted checkout. Creates billable student-account resources.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v az >/dev/null || { echo 'Install Azure CLI first. See docs/AZURE_GUIDE.md.'; exit 1; }
if ! az account show >/dev/null 2>&1; then az login; fi
if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then az account set --subscription "$AZURE_SUBSCRIPTION_ID"; fi
az account show --query '{Subscription:name,State:state}' -o table
LOCATION=${LOCATION:-southeastasia}
RG=${RG:-rg-lanka-dengue-assignment}
APP=${APP:-lanka-dengue-explorer}
ENVIRONMENT=${ENVIRONMENT:-env-lanka-dengue}
BUILD_MODE=${BUILD_MODE:-cloud}
case "$BUILD_MODE" in cloud|docker) ;; *) echo 'BUILD_MODE must be cloud or docker.'; exit 1;; esac
if [[ "$BUILD_MODE" == docker ]]; then command -v docker >/dev/null && docker info >/dev/null || { echo 'Start Docker Desktop, then retry.'; exit 1; }; fi
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
# Stable globally scoped name avoids a new idle registry on each invocation.
SUFFIX=$(python3 -c 'import hashlib,sys;print(hashlib.sha256((sys.argv[1]+sys.argv[2]).encode()).hexdigest()[:12])' "$SUBSCRIPTION_ID" "$RG")
ACR=${ACR:-lkdengue$SUFFIX}
TAG=${IMAGE_TAG:-v$(date -u +%Y%m%d%H%M%S)}
az extension add --name containerapp --upgrade --only-show-errors
for PROVIDER in Microsoft.App Microsoft.OperationalInsights Microsoft.ContainerRegistry Microsoft.ManagedIdentity; do az provider register --namespace "$PROVIDER" --wait; done
az group create -n "$RG" -l "$LOCATION" --tags project=lanka-dengue-assignment >/dev/null
if ! az acr show -n "$ACR" >/dev/null 2>&1; then az acr create -g "$RG" -n "$ACR" --sku Basic >/dev/null; fi
LOGIN_SERVER=$(az acr show -n "$ACR" --query loginServer -o tsv)
IMAGE="$LOGIN_SERVER/dengue-app:$TAG"
if [[ "$BUILD_MODE" == cloud ]]; then
  if ! az acr build -r "$ACR" -t "dengue-app:$TAG" .; then
    echo 'Cloud build failed. Read the actual error. If student ACR Tasks are unsupported, start Docker Desktop and rerun with BUILD_MODE=docker.'
    echo "Resources already created can consume credits. Resource group: $RG"
    exit 1
  fi
else
  az acr login -n "$ACR"
  docker build --platform linux/amd64 -t "$IMAGE" .
  docker push "$IMAGE"
fi
az identity create -g "$RG" -n dengue-image-pull >/dev/null
IDENTITY_ID=$(az identity show -g "$RG" -n dengue-image-pull --query id -o tsv)
PRINCIPAL_ID=$(az identity show -g "$RG" -n dengue-image-pull --query principalId -o tsv)
ACR_ID=$(az acr show -n "$ACR" --query id -o tsv)
EXISTING=$(az role assignment list --scope "$ACR_ID" --query "[?principalId=='$PRINCIPAL_ID' && roleDefinitionName=='AcrPull'] | length(@)" -o tsv)
if [[ "$EXISTING" == 0 ]]; then
  az role assignment create --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal --role AcrPull --scope "$ACR_ID" >/dev/null
fi
az acr config authentication-as-arm update -r "$ACR" --status enabled >/dev/null
if ! az containerapp env show -g "$RG" -n "$ENVIRONMENT" >/dev/null 2>&1; then
  az containerapp env create -g "$RG" -n "$ENVIRONMENT" -l "$LOCATION" >/dev/null
fi
if az containerapp show -g "$RG" -n "$APP" >/dev/null 2>&1; then
  az containerapp update -g "$RG" -n "$APP" --image "$IMAGE" --min-replicas 0 --max-replicas 1 >/dev/null
else
  az containerapp create -g "$RG" -n "$APP" --environment "$ENVIRONMENT" --image "$IMAGE" \
    --user-assigned "$IDENTITY_ID" --registry-server "$LOGIN_SERVER" --registry-identity "$IDENTITY_ID" \
    --ingress external --target-port 8501 --cpu 0.5 --memory 1Gi --min-replicas 0 --max-replicas 1 >/dev/null
fi
FQDN=$(az containerapp show -g "$RG" -n "$APP" --query properties.configuration.ingress.fqdn -o tsv)
python3 - "$RG" "$APP" "$ACR" "$ENVIRONMENT" "$IMAGE" "$FQDN" <<'PY'
import json,sys,datetime
keys=['resource_group','app','registry','environment','image','hostname']
data=dict(zip(keys,sys.argv[1:]));data['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
open('deployment-state.json','w').write(json.dumps(data,indent=2))
PY
echo "Application: https://$FQDN"
echo 'Checking the Streamlit health endpoint (cold starts may take time)...'
curl --fail --retry 12 --retry-delay 10 --retry-all-errors "https://$FQDN/_stcore/health"
echo
echo 'Health passed. Now test all four serotype examples manually in the browser.'
echo "After marking, review and delete this dedicated resource group: $RG"
