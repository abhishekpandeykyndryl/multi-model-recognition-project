# Deployment Plan — Azure App Service + Key Vault + CI (summary)

## 1) Prepare Azure resources
- Create a Resource Group
- Create an **App Service Plan** (Linux, B1 or better)
- Create an **Azure Web App** (Linux) — name: `myapp-backend`
- Create an **Azure Key Vault** — store secrets:
  - AZURE_FACE_KEY
  - AZURE_FACE_ENDPOINT
  - AZURE_SPEECH_KEY
  - AZURE_SPEECH_REGION
  - JWT_SECRET

## 2) Configure Managed Identity & Key Vault Access
- Enable System-assigned Managed Identity on the Web App (Identity -> System assigned -> On)
- In Key Vault -> Access Policies (or IAM), grant the Web App's managed identity `Get` and `List` secrets access.
- In Web App -> Configuration -> Add Key Vault references (use syntax like `@Microsoft.KeyVault(SecretUri=...)`) or use code to fetch via `azure-identity`.

## 3) Deploy using GitHub Actions
- Create publish profile for the Web App and add as GitHub secret `AZURE_WEBAPP_PUBLISH_PROFILE`.
- Optionally use `az webapp deployment container` or `azure/webapps-deploy` action as shown.

## 4) CI/CD: run tests, build Docker image (if desired) and deploy
- The provided GitHub Actions `infra/github-ci.yml` shows a simple deploy on push to `main`.

## 5) Production considerations
- Use Postgres (Azure Database) or Cosmos DB instead of in-memory DB
- Use Azure Key Vault for all secrets; do not store secrets in `.env` in production
- Enable HTTPS-only on App Service and enforce HSTS
- Set up alerts and monitoring (Azure Monitor / Application Insights)
- Configure scaling (App Service Plan autoscale) and rate-limit endpoints
- If you need higher throughput for face operations, consider partitioning PersonGroups
