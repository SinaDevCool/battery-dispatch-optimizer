# Azure App Service Deployment Plan

This product is designed to run as two Azure web apps:

```text
Next.js frontend  -> Azure App Service or Azure Static Web Apps
FastAPI backend   -> Azure App Service
```

Use Azure-managed services around the apps:

```text
Secrets           -> Azure Key Vault or App Service app settings
Database          -> Azure Database for PostgreSQL
Files/reports     -> Azure Blob Storage
Auth              -> Microsoft Entra ID / Entra External ID
Monitoring        -> Application Insights
API gateway later -> Azure API Management
```

## Backend App Service

Deploy the repository root as a Python App Service.

Recommended startup command:

```bash
bash startup.sh
```

Equivalent App Service startup command:

```bash
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
```

## Backend App Settings

Configure these in Azure App Service > Settings > Environment variables:

```text
APP_ENV=production
SERVICE_NAME=battery-dispatch-optimizer-api
API_PUBLIC_BASE_URL=https://your-backend-app.azurewebsites.net
FRONTEND_ORIGIN=https://your-frontend-app.azurewebsites.net
AUTH_MODE=dev
STORAGE_BACKEND=local
ENTSOE_API_KEY=<use Key Vault reference or App Setting>
ENTSOE_VERIFY_SSL=true
APPLICATIONINSIGHTS_CONNECTION_STRING=<from Application Insights>
```

For early pilots, `STORAGE_BACKEND=local` is acceptable only if you understand
that App Service file storage is not a durable product data layer. The next
production step is to implement Azure Blob Storage for forecasts, signals,
reports, and run outputs.

## Frontend App Service

Deploy `frontend/` as a Node.js App Service.

Build command:

```bash
npm install
npm run build
```

Startup command:

```bash
npm run start -- --port $PORT
```

Frontend environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-backend-app.azurewebsites.net
```

Copy the frontend example settings from:

```text
frontend/.env.azure.example
```

If you deploy the frontend as App Service, set its startup command to:

```bash
bash startup.sh
```

## Recommended Commercial Roadmap

1. Deploy backend and frontend to separate App Services.
2. Move secrets to Key Vault references.
3. Add Azure PostgreSQL-backed repositories for tenants, assets, runs, signals,
   forecasts, and revenue-stack results.
4. Add Azure Blob Storage for forecast files, reports, and generated outputs.
5. Add Entra ID authentication and role checks.
6. Add Application Insights dashboards and alerts.
7. Add API Management when external customers or partners need governed API
   access.

