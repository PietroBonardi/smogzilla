# Deployment & Production

How Smogzilla is built, released, and run on Render.

> Inferred from the repo history and Render's docs. Items marked **[verify]** live
> in the Render dashboard, not this repo.

---

## 1. Runtime model

Smogzilla is a **long-polling Telegram bot**, not a web app.

- `bot.py:31` calls `app.run_polling()`: it repeatedly **dials out** to Telegram
  asking for updates. It never binds a port. Telegram answers; the bot asks.
- Handlers are registered in `bot.py:25-27` (e.g. `/air` -> `handlers/air.py:7`).

```
phone (Telegram app) -> Telegram servers
bot.py (Render)      -> Telegram servers   # "any new messages?"
bot.py               <- Telegram servers   # update: "/air brescia"
handlers/air.py      -> scrape + format
bot.py               -> Telegram servers   # send reply
Telegram servers     -> phone              # user sees report
```

All traffic is outbound, so `python bot.py` is all the bot needs. Everything else
exists to satisfy the hosting platform.

---

## 2. Release flow

1. Code merged into `main` on GitHub → Render **auto-deploys on pushes to `main`**.
   **[verify]** branch + auto-deploy.
2. Build: `pip install -r requirements.txt`. Start command lives in the dashboard
   (see §4). **[verify]**
3. Env vars come from the dashboard; local `.env` is gitignored and never ships
   (`config.py:4`'s `load_dotenv()` is a no-op in prod).
4. Filesystem is **ephemeral**: anything written at runtime is wiped on
   deploy/restart.

Deploys trigger on the **merge to `main`**, not on opening a PR.

---

## 3. Why `wsgi.py` exists

`wsgi.py` is **not part of the bot** — it is a 3-line WSGI callable returning
`b"Smogzilla is alive!"`.

- Render's **Web Service** type requires a process to **bind a port**
  (`0.0.0.0`, default `10000`/`$PORT`) so health checks pass.
- The bot binds none, so `gunicorn wsgi:app` opens a port and answers the probes.
- Nothing in the repo imports `wsgi.py` or a public URL; the only caller is
  Render's health probe (verified across all files and git history).

It is an **expedient to satisfy the Web Service contract**, not a bot need.

`bot.py` and `wsgi.py` are different programs; a Web Service must run **both**:

| Start command | Port | Bot | Result |
|---|---|---|---|
| `gunicorn wsgi:app` | Yes | **No** | Healthy page, bot silent |
| `python bot.py` | No | Yes | Render kills it (no port) |
| `python bot.py & gunicorn wsgi:app` | Yes | Yes | Correct for a Web Service |

A green deploy does not prove the bot runs. Look for `Smogzilla bot is running...`
(`bot.py:30`) in the runtime logs; if absent, only gunicorn is up.

---

## 4. Service type options

| | Web Service | Background Worker |
|---|---|---|
| HTTP port required | Yes (hence `wsgi.py`) | No |
| Public URL | Yes | No |
| Free plan | Yes ($0) | No — Starter $7/mo |
| Idle spin-down | Yes on free (~15 min) | No |
| Fit for a polling bot | Workaround needed | Natural fit |

- **Option A — Web Service:** start `python bot.py & gunicorn wsgi:app`; keep
  `wsgi.py` and `gunicorn`. Must address spin-down (§5).
- **Option B — Background Worker:** start `python bot.py`; delete `wsgi.py` and
  remove `gunicorn`. No spin-down, $7/mo minimum.

Current type/plan: **[verify]**.

---

## 5. Production gotchas

- **Free-tier spin-down.** Free Web Services sleep after ~15 min without inbound
  HTTP. A polling bot gets none, so it sleeps and stops answering Telegram
  commands until the next request wakes it. Fix: paid instance or a cron ping on
  the URL. Workers are unaffected.
- **No Python pin.** `.python-version` was deleted in `acbbea8` (it held a venv
  name, not a version). Pin via `runtime.txt` or `render.yaml`.
- **Config is dashboard-only.** No `render.yaml`/`Procfile`/`Dockerfile` exists, so
  prod setup is not reproducible from source.

---

## 6. Environment variables

Dashboard in prod; `.env` locally. Template: `.env.example`.

| Variable | Used by | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `config.py:6` | Required |
| `PM25_THRESHOLD` | `config.py:8` | WHO 24h limit, default `15.0` |
| `PM10_THRESHOLD` | `config.py:9` | WHO 24h limit, default `45.0` |
| `SENSOR_RADIUS` | `config.py:10` | km, default `10` |

---

## 7. Verification checklist

- [ ] Service type: Web Service or Background Worker?
- [ ] Compute plan: free or paid?
- [ ] Start command actually launches `bot.py`?
- [ ] Runtime logs show `Smogzilla bot is running...`?
- [ ] Public URL returns `"Smogzilla is alive!"`?
- [ ] Branch `main` with auto-deploy?

---

## 8. Layout and deployment

The flat root layout **does not need restructuring for deploy**:

- `gunicorn wsgi:app` imports the root-level `wsgi.py`, so it must stay at root.
- `python bot.py` uses root-relative imports (`from config import ...`), so moving
  files into a package would break the start commands.

Deployment issues are configuration (service type, start command, timezone,
persistence), not file placement.
