# Vercel production verification

The frontend is a standard Vite SPA. Vercel supports React deployments, and the included `frontend/vercel.json` sets the Vite build command/output and SPA fallback rewrite.

## Local production-build verification

From PowerShell at the repository root:

```powershell
.\scripts\verify_frontend.ps1
```

This installs dependencies and runs `npm run build`, then requires `frontend/dist/index.html` to exist.

## Live production verification

After the site is deployed, run:

```powershell
.\scripts\verify_vercel.ps1 -Url "https://YOUR-VERCEL-DOMAIN.vercel.app"
```

This checks the live HTTP response. A successful HTTP check is not the same as a full browser QA pass; browser/camera behavior still needs to be exercised on the deployed site.

## Current environment result

The build environment used for this package has no npm registry connectivity and no cached `node_modules`, so `npm install` / `npm run build` could not be executed here. The Vercel project URL was also not available to this build process, so a live production HTTP check could not be performed here.
