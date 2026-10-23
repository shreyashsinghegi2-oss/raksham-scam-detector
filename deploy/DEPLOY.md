# Deploy the Raksham scam detector to Vercel (its own project)

This folder is the whole deployable app: `api/` (FastAPI, NumPy only), `model/` (1.8 MB), `public/index.html` (demo page), `vercel.json`, `requirements.txt`. It is separate from any other project.

From a terminal on your computer, with Node.js installed:

```bash
npm install -g vercel
vercel login
cd deploy            # this folder
vercel --prod
```

Answer the prompts: set up and deploy: yes; link to an existing project: no; project name: `raksham-scam-detector`; code directory: `./`. Vercel prints the live URL when it finishes (about a minute).

Check it:

```bash
curl https://YOUR-URL.vercel.app/api/health          # "status": "ok", "self_check": [true, true]
curl -X POST https://YOUR-URL.vercel.app/api/predict -H "content-type: application/json" \
  -d '{"messages": ["Your KYC has expired. Share the OTP now."]}'
```

Open `https://YOUR-URL.vercel.app/` for the demo page.

Notes:
- If the page asks you to sign in to Vercel, open the project, then Settings, Deployment Protection, and turn it off for production (or keep it on for a private demo).
- To require a key on `/api/predict`, add an environment variable `RAKSHAM_API_KEY` in Project Settings, then redeploy. Callers send it as the `x-api-key` header. `/api/health` stays open.
- Messages are scored in memory. The app does not store them and does not log request bodies.
- To change the model, retrain in the full project (`raksham-train`, then `raksham-export`) and copy the new `deploy/model/` here.

## Front end source

The page in `deploy/public/` is a React + Tailwind build. Its source is in `web/`. After changing it, run `cd web && npm ci && npm run build`; the build writes into `deploy/public/`, which is committed so Vercel needs no build step. `npm run dev` proxies `/api` to a local API on port 8000.
