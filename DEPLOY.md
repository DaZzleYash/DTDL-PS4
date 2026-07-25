# Deploy in ~30 minutes (Render + Vercel)

## 1. Backend on Render (~12 min)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New → Blueprint**.
3. Connect the `DTDL-PS4` repo — Render reads `render.yaml` automatically.
4. Click **Apply**. Wait for the web service + Postgres to finish (first deploy ~5–8 min).
5. Copy your API URL, e.g. `https://dtdl-ps4-api.onrender.com`.
6. Smoke test:

```bash
curl https://YOUR-API.onrender.com/health
curl https://YOUR-API.onrender.com/api/rules/
```

> Free tier sleeps after ~15 min idle. Open `/health` once before a demo to wake it.

### After frontend is live

In Render → **dtdl-ps4-api → Environment**, set:

```
CORS_ORIGINS=https://YOUR-APP.vercel.app
```

(Replace `*` with your real Vercel URL for tighter security, or keep `*` for demos.)

---

## 2. Frontend on Vercel (~10 min)

1. Push `DTDL-PS4-frontend` to GitHub.
2. Go to [vercel.com](https://vercel.com) → **Add New Project** → import the frontend repo.
3. Framework: **Vite** (auto-detected).
4. Add environment variable:

| Name | Value |
|---|---|
| `VITE_API_URL` | `https://YOUR-API.onrender.com` |

5. Deploy. Open the Vercel URL and test Dashboard → Rules → Evaluate.

---

## 3. Local Docker (optional, no public URL)

```powershell
# Backend
cd C:\DTDL-PS4
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml exec app python -m app.finance.seed_rules

# Frontend
cd C:\DTDL-PS4-frontend
docker compose up --build -d
```

Open http://localhost:5173
