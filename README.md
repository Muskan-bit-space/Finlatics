# QuantNova / Finlatics — project mental model

Educational demo of a marketing site for **QuantNova Fund** (also called Finlatics in the positioning page): an India-focused, multi-strategy, AI-themed hedge fund. It is not a trading system, not a brokerage, and not investment advice. The footer and landing page say so explicitly.

This document reverse-engineers the code as it exists. It separates three things:

- **What the code definitely does**
- **What the copy appears to intend** (SEBI fund, blockchain NAV, alt-data, cloud) but is not implemented
- **What is uncertain** because a file or service is missing from this repo

No application source was changed to produce this guide.

## How to run (unchanged from the original quickstart)

```bash
# terminal 1
cd server
cp .env.example .env    # .env.example is NOT in this repo; create .env yourself
# put your MongoDB URI in MONGODB_URI
npm install
npm run dev

# terminal 2
cd client
cp .env.example .env    # also not in this repo
npm install
npm run dev

# terminal 3 — only needed for next-day return prediction
cd model
.venv\Scripts\activate
python -m uvicorn app:app --reload --port 8000
```

Open the client (usually http://localhost:5173).

> Disclaimer in the product: this demo is not investment advice and is for educational purposes only.

---

# PHASE 1 — PROJECT OVERVIEW

## 1. What problem it solves

It is a **pitch and demo website**. A visitor can read a story about the fund, try two small analytics toys (a fake allocator and a real-but-tiny return model), look at a volatility chart served by another host, and leave their contact details.

It does **not** manage money, compute a real NAV, run KYC, or place trades.

## 2. What a user can do right now

| Action | Works? | Notes |
| --- | --- | --- |
| Read the landing pitch | Yes | Copy comes from the API, with hardcoded fallbacks. |
| Read strategy cards | Yes | Card text is in the React page. Order can come from the API. |
| Move a regime / volatility control and see weights | Yes | Formula in Express. Nothing is saved. |
| Type a ticker and see a next-day return | Only if the Python service is up **and** `axios` is installed on the server | See known issues. |
| Search a symbol and chart volatility | Only if `https://quantnova.onrender.com` answers | The model code is **not in this repo**. |
| Submit a contact / “request access” form | Yes, if MongoDB is connected | This is the only database write. |
| Download a pitch deck PDF | Yes, if `server/public/pitch-deck.pdf` exists | A placeholder PDF is in the repo. |
| Log in, sign up, see an admin list of leads | **Not present** | |

## 3. Major features actually implemented

1. Multi-page marketing site (React Router).
2. Static content API (`GET /api/stats`) backed by a JavaScript file, not a database.
3. Contact lead capture into MongoDB.
4. Pitch-deck file download.
5. Illustrative portfolio allocator (`POST /api/allocate`).
6. Next-day return microservice (FastAPI + scikit-learn + Yahoo Finance), proxied by Express.
7. Volatility chart UI that calls a deployed Render URL.
8. Optional production mode: if `client/dist` exists, Express serves the built React app.

## 4. Technologies actually in the repo

**Frontend:** React 19, React DOM, Vite 7, React Router 7, Axios, Chart.js, react-chartjs-2, ESLint.

**Backend:** Node.js (ES modules), Express 4, Mongoose 8, CORS, Morgan, dotenv, node-fetch. `server.js` also imports `axios`, but `axios` is **not** listed in `server/package.json` or `server/package-lock.json`.

**ML:** Python, FastAPI, Uvicorn, pandas, scikit-learn `LinearRegression`, yfinance.

**Database:** MongoDB, database name hardcoded as `quantnova`, one collection `leads`.

**Not in the code, even though the marketing copy names them:** TensorFlow, PyTorch, AWS, GCP, Docker, Kubernetes, blockchain, smart contracts, AML/KYC automation, satellite data.

## 5. Frontend architecture

Single-page app. No global store (no Redux, Zustand, or React Context). Each page keeps its own `useState`. One shared Axios instance in `client/src/api.js`. Routing is declared in `App.jsx`. Navigation is `Nav.jsx`. Almost every page is a route component, not a deep component tree.

## 6. Backend architecture

One Express file: `server/server.js`. There is **no** controller layer, **no** service layer, and **no** router modules. Routes are anonymous functions registered on `app`. The only model is `server/models/Lead.js`. Static marketing data is `server/data/stats.js`. The Python app is a second process, not imported by Node.

## 7. Database / storage

- **MongoDB:** investor leads only.
- **Disk:** `server/public/pitch-deck.pdf`.
- **Source file:** site copy in `stats.js`.
- **Memory, then discarded:** allocation math, Yahoo prices, the regression model (retrained on every predict call).

## 8. External services

| Service | Used by | For |
| --- | --- | --- |
| MongoDB (URI from env) | Express via Mongoose | Saving leads |
| Yahoo Finance via `yfinance` | `model/ml.py` | Daily prices for the return model |
| `https://quantnova.onrender.com` | `VolatilityChart.jsx` directly | Volatility series |
| `MODEL_ORIGIN` (env) | Express `GET /api/volatility` | Same idea, server-side proxy. The React chart does not use this proxy. |
| Google Fonts (Inter) | `client/index.html` | Typeface only |

## 9. Authentication / authorization

**Not present.** No users, passwords, JWT, sessions, cookies, or protected routes. Anyone who can reach `POST /api/leads` can insert a lead. Anyone who can reach the API can read `/api/stats`. There is no endpoint that lists leads, so the database is write-only from this app.

## 10. Deployment / runtime

Three processes in development:

```text
Browser
  → Vite on :5173          (client)
  → Express on :5000       (server)  → MongoDB
  → Uvicorn on :8000       (model)   → Yahoo Finance
```

The volatility chart skips the local server and calls Render.

`client/vercel.json` rewrites every path to `/`, which is what a Vite SPA needs on Vercel so `/contact` does not 404. That file does not deploy the API.

If `client/dist` exists, Express serves it and registers a `GET *` fallback **before** `GET /api/ml/predict`. That ordering bug is explained in Phase 16.

## Architecture diagram (only layers that exist)

```text
User
 ↓
Browser
 ↓
index.html  →  main.jsx  →  <BrowserRouter>  →  App
 ↓
Nav + <Routes> page + Footer
 ↓
Page useState / useEffect
 ↓
axios instance (api.js)          OR  raw fetch() for the volatility chart
 ↓
Express route in server.js       OR  https://quantnova.onrender.com/api/volatility
 ↓                                  OR  (for /api/ml/predict only) FastAPI :8000
 ↓
One of:
  - res.json(stats.js)                         no database
  - Lead.create()  →  MongoDB quantnova.leads
  - in-memory weight formula                   no database
  - fs sendFile pitch-deck.pdf
  - fetch(MODEL_ORIGIN)                        volatility service, code not in repo
  - axios GET localhost:8000/predict
       → yfinance download
       → LinearRegression.fit + predict
 ↓
JSON or PDF
 ↓
setState in the page
 ↓
React re-render
```

There is no controller, no service class, and no frontend global store. Do not describe those layers as if they exist.

---

# PHASE 2 — PROJECT STRUCTURE

```text
Finlatics/
├── README.md                  this guide (plus how to run)
├── .gitignore                 ignores .env, node_modules, __pycache__
├── client/                    React + Vite SPA
│   ├── index.html             HTML shell, mounts #root, loads main.jsx
│   ├── vite.config.js         Vite + dev proxy /api → :5000
│   ├── vercel.json            SPA rewrite for Vercel
│   ├── package.json           frontend scripts and dependencies
│   ├── eslint.config.js       lint config
│   ├── public/vite.svg        favicon
│   └── src/
│       ├── main.jsx           frontend entry
│       ├── App.jsx            route table
│       ├── api.js             Axios client + ML helper
│       ├── styles.css         global styles
│       ├── components/
│       │   ├── Nav.jsx
│       │   └── Footer.jsx
│       └── pages/
│           ├── Landing.jsx
│           ├── Strategies.jsx
│           ├── Portfolio.jsx
│           ├── Capital.jsx
│           ├── Technology.jsx
│           ├── Compliance.jsx
│           ├── Risk.jsx
│           ├── Positioning.jsx
│           ├── Contact.jsx
│           ├── VolatilityChart.jsx
│           └── volatility-chart.css
├── server/
│   ├── server.js              entire HTTP API
│   ├── package.json
│   ├── models/Lead.js         only Mongoose model
│   ├── data/stats.js          static site copy
│   ├── public/pitch-deck.pdf  downloadable file
│   └── README.md              short endpoint list
└── model/
    ├── app.py                 FastAPI app
    ├── ml.py                  yfinance + linear regression
    └── requirements.txt
```

| File / folder | Purpose | Important contents | Depends on | Used by |
| --- | --- | --- | --- | --- |
| `client/index.html` | Browser entry HTML | `#root`, script `/src/main.jsx`, Inter font | nothing in app | Vite |
| `client/src/main.jsx` | React entry | `createRoot`, `BrowserRouter` | `App.jsx`, `styles.css` | `index.html` |
| `client/src/App.jsx` | Route table and page shell | `Nav`, `Routes`, `Footer` | all pages | `main.jsx` |
| `client/src/api.js` | HTTP client | Axios `baseURL`, `fetchReturnPrediction` | `VITE_API_URL` | Landing, Strategies, Portfolio, Technology, Contact |
| `client/src/components/Nav.jsx` | Top links and mobile menu | local `open` state | React Router | `App` |
| `client/src/components/Footer.jsx` | Disclaimer footer | year, “illustrative” labels | none | `App` |
| `client/src/pages/Landing.jsx` | Home | `stats` state, pitch-deck link | `api` | route `/` |
| `client/src/pages/Strategies.jsx` | Strategy cards | local copy + API order | `api` | route `/strategies` |
| `client/src/pages/Portfolio.jsx` | Allocator + ML return | `regime`, `vol`, `alloc`, `ticker` | `api`, `fetchReturnPrediction` | route `/portfolio` (nav label “Risk”) |
| `client/src/pages/Capital.jsx` | Static capital-raising copy | none | none | route `/capital` |
| `client/src/pages/Technology.jsx` | Tech bullets from API | `tech` state | `api` | route `/technology` (not in nav) |
| `client/src/pages/Compliance.jsx` | Static compliance copy | none | none | **imported by App, never routed** |
| `client/src/pages/Risk.jsx` | Static risk/mitigation table | `rows` constant | none | route `/risk` (not in nav) |
| `client/src/pages/Positioning.jsx` | “Why us” bullets | `bullets` constant | none | route `/positioning` |
| `client/src/pages/Contact.jsx` | Lead form | `lead`, `leadOk` | `api` | route `/contact` |
| `client/src/pages/VolatilityChart.jsx` | Symbol search + Chart.js | chart state, `COMPANIES` | Render URL, Chart.js | route `/chart` |
| `client/vite.config.js` | Dev server | proxy `/api` → `127.0.0.1:5000` | Vite | `npm run dev` |
| `client/vercel.json` | Hosting rewrite | `/(.*) → /` | Vercel | production frontend host |
| `server/server.js` | API process | all routes, Mongo connect, listen | Mongoose, Lead, stats, env | client and curl |
| `server/models/Lead.js` | Lead schema | fields below | mongoose | `POST /api/leads` |
| `server/data/stats.js` | CMS substitute | tagline, strategies, risk, tech | none | `GET /api/stats` |
| `server/public/pitch-deck.pdf` | Download | binary PDF | none | `GET /api/pitch-deck` |
| `model/app.py` | ML HTTP service | `GET /predict` | `ml.py` | Express `/api/ml/predict` |
| `model/ml.py` | Train-and-predict | `load_market_data`, `prepare_features`, `predict_next_day_return` | yfinance, sklearn | `app.py` |

### Classification

| Kind | Files |
| --- | --- |
| Core | `main.jsx`, `App.jsx`, `api.js`, `server.js`, `Lead.js`, `app.py`, `ml.py`, `Contact.jsx`, `Portfolio.jsx`, `VolatilityChart.jsx` |
| Supporting | `Nav`, `Footer`, `Landing`, `Strategies`, `stats.js`, `styles.css` |
| Static / marketing only | `Capital`, `Technology`, `Risk`, `Positioning`, `Compliance` |
| Configuration | `package.json` (both), `vite.config.js`, `vercel.json`, `eslint.config.js`, `.gitignore`, `requirements.txt` |
| Possibly unused | `Compliance.jsx` (no route). `volatility-chart.css` is not imported by `VolatilityChart.jsx` (that page uses inline styles). `GET /api/volatility` on Express is unused by the current chart. |
| Generated / ignore | `node_modules/`, `client/dist/`, `__pycache__/`, `.env` |
| Safe to ignore while learning behavior | lockfiles, `client/README.md` (default Vite text), ESLint config, `vite.svg` |

**Missing files that block a full trace**

- `.env` and `.env.example` are not in the repo (gitignored or never committed). Variable *names* are visible in code; values are not.
- The volatility model (`/api/volatility` implementation: how RMSE, dates, actual, and predicted are computed) is **not in this repository**.

There are no custom hooks, no React context, no controllers, no services, and no auth modules.

---

# PHASE 3 — ENTRY POINTS

## Backend: `npm run dev` inside `server/`

```text
server/package.json
  "dev": "nodemon server.js"
  "start": "node server.js"
        ↓
server/server.js  (top to bottom, ES module, runs once on import)
        ↓
dotenv.config()                         reads server/.env into process.env
        ↓
express()
        ↓
middleware:
  express.json()                        parse JSON bodies
  morgan("dev")                         log each request
  cors({ origin: allowedOrigin })       one allowed browser origin
        ↓
if MONGODB_URI missing → console.error + process.exit(1)
mongoose.connect(mongoUri, { dbName: "quantnova" })
  success → log "MongoDB connected"
  failure → log + process.exit(1)
        ↓
import Lead, import stats               (imports are hoisted, but conceptually here)
        ↓
register routes: health, stats, leads, pitch-deck, allocate, /public, volatility
        ↓
if client/dist exists:
  express.static(clientDist)
  app.get("*") SPA fallback             ← registered BEFORE the ML route
        ↓
app.get("/api/ml/predict")              ← too late if the "*" route exists
        ↓
app.listen(port || 5000)
```

`axios` is imported on line 10. Node resolves imports before any of the code above runs. If `axios` is not installed, **the process crashes before Mongo connects and before** `listen`. `npm install` from the current `package.json` does not install it.

## Frontend: `npm run dev` inside `client/`

```text
client/package.json
  "dev": "vite"
        ↓
vite.config.js
  plugin: @vitejs/plugin-react
  server.proxy["/api"] = "http://127.0.0.1:5000"
        ↓
client/index.html
  <div id="root">
  <script type="module" src="/src/main.jsx">
        ↓
main.jsx
  createRoot(#root).render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  )
  imports ./styles.css
        ↓
App.jsx
  <Nav />
  <Routes> … </Routes>
  <Footer />
        ↓
React Router matches location.pathname
  default path "/" → <Landing />
        ↓
Landing useEffect → api.get("/api/stats")
```

`npm run build` runs `vite build` and writes `client/dist`. `npm run preview` serves that build. The production API base URL is **not** the Vite proxy. Axios uses `import.meta.env.VITE_API_URL` or `http://localhost:5000`.

## Model: Uvicorn

```text
python -m uvicorn app:app --reload --port 8000
        ↓
model/app.py
  app = FastAPI(...)
  route GET /predict  →  predict(ticker)
        ↓
model/ml.py predict_next_day_return
```

Nothing starts this process automatically. Express assumes it is already on port 8000.

---

# PHASE 4 — TECHNOLOGY STACK

### React

UI library. Function components and hooks only (`useState`, `useEffect`, `useMemo`, `useRef`). No class components. Removing it removes the entire client.

### React DOM `createRoot`

Mounts the tree into `#root` in `main.jsx`. One call. That is the frontend process start.

### Vite

Dev server, bundler, and env injection (`import.meta.env.VITE_*`). `vite.config.js` proxies `/api` during dev so a relative `/api/...` call hits Express. Axios does **not** use a relative URL; it uses an absolute `baseURL`, so the proxy only helps if something calls `/api` on the Vite origin. Today the pages use the Axios absolute URL, and the chart uses Render. The proxy is mostly unused by current calls.

### React Router (`BrowserRouter`, `Routes`, `Route`, `Link`, `NavLink`)

Client-side URLs with no page reload. Declared only in `App.jsx` and used by `Nav` and `Landing`. There is no loader, no protected route, no nested route layout beyond Nav/Footer wrapping everything.

### Axios

`client/src/api.js` creates one instance. Pages call `api.get` / `api.post`. `fetchReturnPrediction` wraps `GET /api/ml/predict` and returns `null` on failure. Server-side `import axios from "axios"` is a second, undeclared use.

### Chart.js and react-chartjs-2

Only `VolatilityChart.jsx`. Registers `LineElement`, `PointElement`, `LinearScale`, `CategoryScale`, `Tooltip`, `Legend`, `Filler`, then renders `<Line>`. Removing them blanks the chart page only.

### Express

HTTP server. All behavior is in `server.js`. JSON in, JSON or a file out.

### Mongoose

ODM for MongoDB. Connects in `server.js`, schema in `Lead.js`, one call: `Lead.create`. Removing it removes lead storage. The rest of the site still runs only if you also remove the connect-or-exit block; today a failed Mongo connection kills the whole API, including stats and the allocator.

### cors

Sets `Access-Control-Allow-Origin` to a **single** origin. Browsers on a different origin (Vercel vs localhost, or Render) will block Axios calls unless `CLIENT_ORIGIN` matches the page’s origin. The volatility `fetch` to Render is cross-origin the other way: the chart page must be allowed by Render, which this repo cannot see.

### morgan

Dev request logger. Safe to remove; no behavior depends on it.

### dotenv

Loads `server/.env`. Without it, `MONGODB_URI` is missing and the process exits.

### node-fetch

Used only by `GET /api/volatility` to call `MODEL_ORIGIN`. Node 18+ has global `fetch`; this dependency is the explicit one.

### FastAPI + Uvicorn

Python HTTP for `GET /predict`. Uvicorn is the process that binds port 8000. Not imported by Node.

### pandas

Builds the return column and the feature matrix in `ml.py`.

### scikit-learn `LinearRegression`

Fit on each request. No model file is saved.

### yfinance

Downloads daily OHLCV. Needs outbound internet. This is the market-data dependency.

### ESLint

`npm run lint` in the client. Does not run in the request path.

---

# PHASE 5 — FRONTEND DEEP DIVE

When the user opens the application, Vite (or a static host) returns `index.html`. The module script runs `main.jsx`, which paints `App` inside the router. `App` always paints `Nav` and `Footer`, and exactly one page from the URL.

## A. Rendering

```text
BrowserRouter                         main.jsx
└── App                               App.jsx
    ├── Nav                           components/Nav.jsx
    │   └── NavLink / Link buttons
    ├── Routes                        one of:
    │   ├── Landing                   /
    │   ├── Strategies                /strategies
    │   ├── Portfolio                 /portfolio     nav calls this "Risk"
    │   ├── Capital                   /capital
    │   ├── Technology                /technology    no nav link
    │   ├── VolatilityChart           /chart         nav calls this "Volatility"
    │   ├── Risk                      /risk          no nav link
    │   ├── Positioning               /positioning   nav calls this "Why Us"
    │   └── Contact                   /contact       nav calls this "Request Access"
    └── Footer
```

`Compliance` is imported in `App.jsx` and then unused. There is no `/compliance` route.

Reusable pieces that exist:

- `Nav`, `Footer` — layout, used on every page.
- `Toggle` — defined **inside** `Portfolio.jsx`, not shared.
- `Card` — defined **inside** `Strategies.jsx`, not shared.

Business logic in the browser:

- `Contact.submitLead` — builds the lead body and posts it.
- `Portfolio` effects — load risk copy; recompute allocation when `regime` or `vol` changes; `runMlPrediction`.
- `VolatilityChart.fetchData` plus search/filter helpers.
- Strategy descriptions are hardcoded JSX, not fetched. Only the **order** of names prefers `stats.strategies`.

Pages with no logic: `Capital`, `Positioning`, `Compliance`, `Risk` (static array), `Footer`.

## B. State

There is no global state, no context, no `localStorage`, and no `sessionStorage`. Server data lives in component state after a fetch. Refreshing the page drops it. MongoDB is the only persistence, and the UI never reads it back.

| State | Where | Represents | Who changes it | Who reads it |
| --- | --- | --- | --- | --- |
| `open` | `Nav` | mobile menu | hamburger `setOpen` | `className` and `aria-expanded` |
| `stats` | `Landing` | tagline, subtext, quick tags | `useEffect` → `GET /api/stats` | hero text. Fallback strings if null |
| `stats` | `Strategies` | same payload, only `strategies` used | same GET | card order |
| `risk` | `Portfolio` | `stats.risk` string array | GET on mount | risk cards |
| `regime` | `Portfolio` | `"Growth"` / `"Inflation"` / `"Recession"` | `Toggle` | allocation effect |
| `vol` | `Portfolio` | slider 5–30, starts at 15 | range `onChange` | label + allocation effect |
| `alloc` | `Portfolio` | `{ regime, volatility, allocation[] }` | POST `/api/allocate` | weight cards |
| `ticker` | `Portfolio` | symbol, default `AAPL` | text input, uppercased | `runMlPrediction` |
| `mlPrediction` | `Portfolio` | number or null | `runMlPrediction` | “Predicted next-day return” |
| `mlLoading` | `Portfolio` | button spinner text | `runMlPrediction` | button label / disabled |
| `lead` | `Contact` | form fields | each input | POST body |
| `leadOk` | `Contact` | success or error string | `submitLead` | message under the button |
| `tech` | `Technology` | string array | GET `/api/stats` | cards |
| `symbol`, `windowSize` | `VolatilityChart` | query for the model | search, chips, slider | `fetchData` |
| `loading`, `error`, `rmse`, `title`, `dataResp` | `VolatilityChart` | chart request lifecycle | `fetchData` | button, error box, `<Line>` |
| `searchTerm`, `showDropdown`, `focusedIndex` | `VolatilityChart` | typeahead | keyboard and input | dropdown |
| `regimes` | `Portfolio` `useMemo` | the three regime labels | never, empty deps | `Toggle` |
| `filteredCompanies` | `VolatilityChart` `useMemo` | search hits, max 15 | derived from `searchTerm` | dropdown |
| `chartData`, `chartOptions` | `VolatilityChart` `useMemo` | Chart.js config | derived from `dataResp` | `<Line>` |

Props are almost unused. `Card` receives `title` and `children`. `Toggle` receives `options`, `value`, `onChange`. Pages do not pass data to each other.

## C. User interactions (short traces; full journeys are Phase 11)

**Submit contact form**

```text
form onSubmit
 → Contact.submitLead
 → api.post("/api/leads", lead)
 → setLeadOk("Thanks...") or "Something went wrong"
 → setLead(empty object) on success
 → re-render message
```

**Change regime or volatility**

```text
Toggle onClick / range onChange
 → setRegime / setVol
 → useEffect dependency [regime, vol]
 → api.post("/api/allocate", { regime, volatility: Number(vol) })
 → setAlloc(data)
 → map alloc.allocation into cards
```

**Run ML**

```text
button onClick
 → Portfolio.runMlPrediction
 → fetchReturnPrediction(ticker) in api.js
 → GET /api/ml/predict?ticker=
 → setMlPrediction(result.predicted_return) only if that field exists
```

**Run volatility**

```text
Run button or Enter with no highlighted row
 → VolatilityChart.fetchData
 → fetch("https://quantnova.onrender.com/api/volatility?symbol&window")
 → setRmse, setTitle, setDataResp
 → useMemo builds chartData
 → <Line> draws
```

**Navigate**

```text
NavLink click
 → React Router changes the path
 → matching Route element mounts
 → previous page state is destroyed
```

---

# PHASE 6 — BACKEND DEEP DIVE

Express has no controller/service split. The route function **is** the processing.

```text
HTTP request
 → cors, express.json, morgan          (every request)
 → matching app.get / app.post         (first match wins)
 → inline function in server.js
 → Mongoose OR file OR in-memory math OR HTTP call
 → res.status().json() or res.sendFile()
```

Startup is not a request: Mongo connects before `listen`. If it fails, there is no server.

| Method | Endpoint | Purpose | Input | Processing | Output | Used by |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/api/health` | Liveness | none | builds a timestamp | `200 { ok: true, time }` | nothing in the UI |
| GET | `/api/stats` | Marketing copy | none | returns imported `stats` object | `200` JSON | Landing, Strategies, Portfolio, Technology |
| POST | `/api/leads` | Save a lead | JSON body | validate name/email, `Lead.create` | `201 { ok, lead }` or `400` / `500` | `Contact.submitLead` |
| GET | `/api/pitch-deck` | PDF download | none | `fs.existsSync` + `sendFile` | PDF or `404` JSON | Landing anchor |
| POST | `/api/allocate` | Fake weights | `{ regime, volatility }` | formula, then normalize to 100 | `200 { regime, volatility, allocation }` | `Portfolio` effect |
| GET | `/api/volatility` | Proxy | query `symbol`, `window`, `start`, `end` | `fetch(MODEL_ORIGIN/api/volatility)` | upstream status + JSON, or `500` | **not the React chart** |
| GET | `/public/...` | Static files | path | `express.static(server/public)` | file | not linked by the UI except via pitch-deck route |
| GET | `/api/ml/predict` | Proxy to FastAPI | query `ticker` | `axios.get("http://localhost:8000/predict")` | FastAPI JSON, or `400` if no ticker, or `500` | `fetchReturnPrediction` |
| GET | `*` | SPA fallback | any non-file path | only if `client/dist` exists. `/api` and `/public` get `404` JSON; other paths get `index.html` | HTML or 404 | browser refresh on a client route in that mode |

### Plain English for each endpoint

**GET /api/health.** Nothing checks Mongo. A process that is up but has a dead database cannot happen with the current startup code, because a dead database exits the process. The route is still not a database ping.

**GET /api/stats.** Returns the object in `server/data/stats.js`: `tagline`, `subtext`, `quick[]`, `strategies[]`, `risk[]`, `tech[]`. Editing that file changes the site after a server restart (nodemon restarts on save).

**POST /api/leads.** Reads `name`, `email`, `investorType`, `message`, `requestPitchDeck`. Missing name or email → 400 `"Name and email are required."`. Otherwise `Lead.create`. Mongoose adds `_id`, `createdAt`, `updatedAt`. Success → 201 and the document, including the email you just sent. Any throw, including a bad enum, → 500 `"Server error"` and `console.error`.

**GET /api/pitch-deck.** Looks for `server/public/pitch-deck.pdf`. Found → file bytes. Missing → 404 JSON telling you to drop the file there. The contact checkbox does not call this route.

**POST /api/allocate.** Defaults `regime = "Growth"`, `volatility = 15`. Starts from fixed weights (Factor Equity 30, Stat-Arb 15, Volatility Trading 15, AI/ML Alpha 20, Alternative Data 10, Macro Overlays 10). If `regime` lowercased starts with `"inflation"`, Macro Overlays `+5`. If it starts with `"recession"`, Macro Overlays `+10`. `volAdj = clamp(15 - volatility, -5, 5)` is **subtracted** from Volatility Trading. Weights floored at 0, then divided by their sum and rounded to integers that should add to about 100. No try/catch. No database.

**GET /api/volatility.** Forwards the query string to `${process.env.MODEL_ORIGIN}/api/volatility`. Also `console.log`s `MODEL_ORIGIN` on every call. The FastAPI app in `model/app.py` does not implement this path. Whatever host `MODEL_ORIGIN` points at must implement it. The chart does not use this route; it calls Render itself.

**GET /api/ml/predict.** Requires `ticker`. Calls `http://localhost:8000/predict` with that query param. Returns `response.data` as-is: `{ ticker, predicted_return }`. Network or HTTP errors become 500 `"ML prediction service unavailable"`. The URL is hardcoded. It does not use `MODEL_ORIGIN`.

**SPA** `GET` ***.** Registered only when `client/dist` exists, and registered **before** `/api/ml/predict`. A request to `/api/ml/predict` in that mode matches `*` first. The handler sees a path starting with `/api` and returns **404** `{ error: "Not found" }`. The ML route never runs. Other `/api` routes still work because they were registered earlier.

---

# PHASE 7 — DATABASE / DATA MODEL

## What is stored

One MongoDB database, name `quantnova` (second argument to `mongoose.connect`, so it wins over a database name in the URI).

One collection. Mongoose model name `"Lead"` → collection `leads`.

```text
leads
  _id                ObjectId
  name               String, required
  email              String, required, not unique
  investorType       String enum, default "Other"
                     Institution | HNWI/Family Office | NRI/Foreign | Other
  message            String, optional
  requestPitchDeck   Boolean, default false
  createdAt          Date
  updatedAt          Date
```

No other collections. No users. No portfolios. No prices. No relationship to another model. An ER diagram with one box is the honest one:

```text
Lead
  (standalone document)
```

## CRUD

| Operation | Present? | Where |
| --- | --- | --- |
| Create | Yes | `Lead.create` in `POST /api/leads` |
| Read | **Not present** | no `find`, no admin UI |
| Update | **Not present** | |
| Delete | **Not present** | |

Validation is the schema (`required`, `enum`) plus the route’s name/email check. No unique index, so the same email can be inserted many times. No transactions. No migrations. Old documents are not rewritten if you add a field later; Mongoose only applies defaults on new writes.

## One complete write, end to end

1. User is on `/contact`. `lead` state holds the form.
2. Submit calls `submitLead`, which `POST`s that object to `/api/leads`.
3. `express.json` parses the body.
4. The route rejects empty name or email.
5. `Lead.create` inserts one document. Mongo assigns `_id`. Mongoose sets timestamps.
6. Response `201`:

```json
{
  "ok": true,
  "lead": {
    "name": "Ada",
    "email": "ada@example.com",
    "investorType": "Institution",
    "message": "…",
    "requestPitchDeck": true,
    "_id": "…",
    "createdAt": "…",
    "updatedAt": "…",
    "__v": 0
  }
}
```

7. `submitLead` checks `data.ok`, sets the thank-you string, and resets `lead` to empty strings / false.
8. The UI never shows the stored `_id`. The only way to see the row is a Mongo client (Compass, Atlas, `mongosh`), because this app has no read API.

`requestPitchDeck: true` does not send email and does not attach the PDF. It is a boolean flag for a human to notice later.

---

# PHASE 8 — API / DATA FLOW

### 1. Site copy

```text
Landing useEffect / Strategies useEffect / Portfolio useEffect / Technology useEffect
 → api.get("/api/stats")
 → GET {VITE_API_URL or http://localhost:5000}/api/stats
 → no body, no query
 → server.js app.get("/api/stats")
 → res.json(stats) from data/stats.js
 → 200 JSON
 → setStats / setRisk / setTech
 → hero, cards, or risk list
```

Landing’s `.catch(() => {})` swallows errors and keeps fallback copy. Strategies has **no** `.catch`. A network failure rejects the promise with no UI message. Portfolio’s stats effect is the same. The allocation effect uses empty `catch {}`.

### 2. Create lead

```text
Contact.submitLead
 → POST /api/leads
 → body: { name, email, investorType, message, requestPitchDeck }
 → Lead.create
 → 201 { ok: true, lead }  or  400 { error }  or  500 { error: "Server error" }
 → if data.ok: thank-you + reset form
 → else axios throws on 400/500 → catch sets "Something went wrong"
```

Axios throws for any status outside 2xx, so the `if (data.ok)` branch only runs on 201.

### 3. Pitch deck

```text
<a href="{VITE_API_URL}/api/pitch-deck" target="_blank">
 → browser GET, not Axios
 → sendFile PDF  or  404 JSON
```

No frontend state.

### 4. Allocation

```text
Portfolio useEffect [regime, vol]
 → POST /api/allocate
 → body: { regime: "Growth"|"Inflation"|"Recession", volatility: number }
 → formula in server.js
 → 200 { regime, volatility, allocation: [{ strategy, weight }, ...] }
 → setAlloc
 → cards show a.strategy and a.weight + "%"
```

No PUT, PATCH, or DELETE anywhere in the project.

### 5. Next-day return

```text
Portfolio.runMlPrediction
 → fetchReturnPrediction(ticker)          client/src/api.js
 → GET /api/ml/predict?ticker=AAPL
 → server requires ticker else 400 { error: "Ticker is required" }
 → axios GET http://localhost:8000/predict?ticker=AAPL
 → FastAPI predict()
 → predict_next_day_return(ticker.upper())
      yf.download(ticker, period="6mo", interval="1d")
      if fewer than 15 rows: return None → HTTP 400
         detail "Not enough market data to generate prediction"
      daily_return = Close.pct_change()
      rows: 5 past returns → next return
      LinearRegression.fit(X, y)
      predict on the last feature row
 → { ticker, predicted_return } rounded to 6 decimals
 → Express res.json(that)
 → client: if predicted_return !== undefined, setMlPrediction
 → UI: (mlPrediction * 100).toFixed(2) + "%"
```

Query parameter on both hops: `ticker`. No request body.

**Training detail you should be able to say.** The model is not loaded from disk. Every click downloads six months of prices and fits a new line. Features are the previous 5 daily returns. The label is the following day’s return. The vector that is predicted is `X.iloc[-1]`, which is also the last training row. So the number on screen is the model’s fit on a window it just trained on, not a held-out future day. There is no train/test split and no RMSE on this endpoint (RMSE belongs to the volatility service).

If FastAPI returns 400, Axios on the server throws, and Express answers **500**, not 400. The original “not enough data” detail is dropped. The React helper then returns `null`, and the page clears `mlPrediction` and shows no error text.

### 6. Volatility chart

```text
VolatilityChart.fetchData
 → fetch GET https://quantnova.onrender.com/api/volatility?symbol=SPY&window=10
 → expects JSON: { title, rmse, dates, actual, predicted, detail? }
 → res.ok false → throw Error(payload.detail or "Request failed") → setError
 → success → setRmse, setTitle, setDataResp
 → chartData useMemo → <Line> two datasets
```

`start` and `end` are not sent by the client. The unused Express proxy would default them to `2015-01-01` and `2025-01-01`.

Status codes that exist in this repo:

| Code | When |
| --- | --- |
| 200 | health, stats, allocate, successful proxies, PDF |
| 201 | lead created |
| 400 | lead missing name/email; ML route missing ticker; FastAPI not enough rows |
| 404 | PDF missing; SPA catch-all for unknown `/api` when dist exists |
| 500 | lead exception; volatility proxy exception; ML proxy exception |

---

# PHASE 9 — AUTHENTICATION & AUTHORIZATION

**Not present in the codebase.**

No login, signup, logout, password hashing, JWT, cookies, `localStorage` tokens, auth middleware, roles, or route guards. `investorType` is a form label, not an authorization role.

Consequence you can say in an interview: the lead API is open. Security of the data depends on the MongoDB network rules and on not exposing the URI, not on application auth.

---

# PHASE 10 — IMPORTANT FUNCTIONS

| Name | File | Purpose | Called by | Calls | Why it matters |
| --- | --- | --- | --- | --- | --- |
| `createRoot(...).render` | `main.jsx` | Mount React | browser | `App` | Nothing paints without it |
| `App` | `App.jsx` | Routes | `main.jsx` | pages | URL → page map |
| `Nav` | `Nav.jsx` | Links | `App` | router | How users move |
| axios `api` | `api.js` | Base URL | most pages | HTTP | Every JSON call except the chart |
| `fetchReturnPrediction` | `api.js` | ML GET | `runMlPrediction` | `api.get` | Hides errors as `null` |
| `Landing` | `Landing.jsx` | Hero | route `/` | `GET /api/stats` | First page |
| `submitLead` | `Contact.jsx` | Save lead | form submit | `POST /api/leads` | Only DB write from UI |
| `Portfolio` effect (alloc) | `Portfolio.jsx` | Sandbox | `regime`, `vol` | `POST /api/allocate` | Demo “risk engine” |
| `runMlPrediction` | `Portfolio.jsx` | Show return | button | `fetchReturnPrediction` | Demo “AI” |
| `Toggle` | `Portfolio.jsx` | Regime buttons | Portfolio | `onChange` | Sets `regime` |
| `fetchData` | `VolatilityChart.jsx` | Load series | Run button | `fetch` Render | Chart data |
| `handleSearchChange` | `VolatilityChart.jsx` | Typeahead | input | `setSymbol` | Symbol selection |
| `selectCompany` | `VolatilityChart.jsx` | Pick a row | click / Enter | setters | Symbol selection |
| `handleKeyDown` | `VolatilityChart.jsx` | Arrow keys | input | `selectCompany` / `fetchData` | Keyboard UX |
| `express()` app routes | `server.js` | Whole API | HTTP | Mongoose, fs, fetch, axios | Backend |
| `mongoose.connect` | `server.js` | DB boot | process start | MongoDB | API dies without it |
| `Lead.create` | via route | Insert | `POST /api/leads` | MongoDB | Persistence |
| allocate handler | `server.js` | Weights | `POST /api/allocate` | none | Business formula |
| `predict` | `model/app.py` | HTTP predict | Uvicorn | `predict_next_day_return` | ML boundary |
| `load_market_data` | `model/ml.py` | Prices | predict function | `yf.download` | External data |
| `prepare_features` | `model/ml.py` | 5-day windows | predict function | pandas | Supervised dataset |
| `predict_next_day_return` | `model/ml.py` | Fit and predict | `predict` | the two above, sklearn | The model |
| `Footer` | `Footer.jsx` | Disclaimer | `App` | none | Legal tone of the demo |
| `Card` | `Strategies.jsx` | Strategy tile | Strategies | none | Presentation |

### `submitLead`

1. Sends the access request.
2. Input: form event, reads `lead` state.
3. Output: none. Side effect is HTTP and two `setState` calls.
4. Clears `leadOk` first so an old error disappears.
5. Database: insert through the API, not from the browser.
6. Depends on `api`. If removed, the form does nothing useful.

### `predict_next_day_return`

1. Turns a ticker into one float.
2. Input: ticker string. Output: `float` or `None`.
3. Side effects: network to Yahoo; a model object that is discarded.
4. No React state. FastAPI wraps `None` as HTTP 400.
5. Depends on `load_market_data` and `prepare_features`.
6. If removed, `/predict` crashes and the portfolio “Run ML” button goes quiet.

### Allocate handler

1. Turns two controls into six weights that sum to ~100.
2. Input: JSON `regime`, `volatility`. Output: JSON allocation.
3. No I/O. If removed, the portfolio effect fails silently (`catch {}`) and cards stay empty.

### `fetchData`

1. Fills the chart.
2. Does not go through `api.js` or local Express.
3. If removed, the Run button has no handler. Search still changes `symbol` locally.

---

# PHASE 11 — COMPLETE USER JOURNEYS

## Feature: Read the landing page

### What the user does

Opens `/`.

### What the frontend does

```text
Landing mounts
 → useEffect
 → api.get("/api/stats")
```

### What the backend does

```text
GET /api/stats
 → res.json(stats.js)
```

No database.

### What comes back

`setStats`. The `<h1>` uses `stats.tagline` or the fallback “Turning Volatility into Opportunity.” Quick tags render from `stats.quick`. Three links: `/strategies`, the PDF URL, `/contact`.

## Feature: Request access (database)

### What the user does

Opens Request Access, fills name, email, investor type, optional message, optional pitch-deck checkbox, submits.

### What the frontend does

```text
Contact form onSubmit
 → submitLead(e) prevents default
 → setLeadOk("")
 → api.post("/api/leads", lead)
```

### What the backend does

```text
POST /api/leads
 → if !name or !email: 400
 → Lead.create({ ..., requestPitchDeck: Boolean(...) })
 → MongoDB quantnova.leads insert
 → 201 { ok: true, lead }
```

### What comes back

```text
data.ok → setLeadOk("Thanks! We'll reach out soon.")
 → setLead(blank)
 → button stays, green/success text appears, inputs empty
```

The pitch deck is not emailed. A teammate would have to read MongoDB.

## Feature: Download pitch deck

### What the user does

Clicks “Download Pitch Deck” on the landing page.

### What the frontend does

Normal `<a href>` to `{VITE_API_URL}/api/pitch-deck` in a new tab. No handler.

### What the backend does

```text
GET /api/pitch-deck
 → path.join(__dirname, "public", "pitch-deck.pdf")
 → sendFile or 404 JSON
```

### What comes back

The browser’s PDF viewer, or a JSON error if the file is gone.

## Feature: Simulated allocation

### What the user does

Opens Risk in the nav (URL `/portfolio`). Clicks Growth, Inflation, or Recession. Moves “Target Volatility”.

### What the frontend does

```text
Toggle / <input type="range">
 → setRegime or setVol
 → useEffect
 → api.post("/api/allocate", { regime, volatility: Number(vol) })
```

On first paint the effect runs immediately with Growth and 15, so cards appear without a click. A separate effect loads `risk` strings from `/api/stats`.

### What the backend does

Inline formula in `server.js` (Phase 6). No model, no database.

### What comes back

`setAlloc`. Six cards, for example Factor Equity and a rounded percent. The ML panel below is independent and stays idle until “Run ML”.

## Feature: Next-day return

### What the user does

Types a ticker (default AAPL) and clicks “Run ML”.

### What the frontend does

```text
runMlPrediction
 → setMlLoading(true); setMlPrediction(null)
 → fetchReturnPrediction(ticker)
 → GET /api/ml/predict?ticker=
```

### What the backend does

```text
Express checks ticker
 → GET http://localhost:8000/predict?ticker=
 → FastAPI predict
 → ml.predict_next_day_return
 → Yahoo Finance + LinearRegression
```

### What comes back

```text
{ ticker, predicted_return }
 → setMlPrediction(number)
 → setMlLoading(false)
 → "Predicted next-day return: X.XX%"
```

If Python is down: server 500, client `null`, loading stops, **no error sentence**.

## Feature: Volatility chart

### What the user does

Opens Volatility (`/chart`). Searches “Apple” or clicks the AAPL chip. Sets window 2–60. Clicks Run.

### What the frontend does

```text
selectCompany or chip → setSymbol + setSearchTerm
 → fetchData
 → fetch(quantnova.onrender.com/api/volatility?symbol&window)
```

Local company list is a constant `COMPANIES` in the file (stocks, ETFs, crypto `-USD` pairs). It is not loaded from an API. Unknown text is still uppercased into `symbol`, so a custom ticker can be sent.

### What the backend in this repo does

Nothing on this path. Render is outside the repo. Express has a similar proxy that this page does not call.

### What comes back

`dates`, `actual`, `predicted` become the line chart. `rmse` prints as “Test RMSE”. `title` becomes a heading. Failure sets `error` in a red box. Empty state before the first successful run: “Run a volatility forecasting model…”.

## Feature: Static explanation pages

Strategies, Capital, Why Us (`/positioning`), Technology, and `/risk` only render text. Strategies still GETs `/api/stats` so the **order** of pods follows `stats.strategies`, while the paragraphs live in `sections` inside `Strategies.jsx`. If the API returns a name that is not in `sections`, the card title appears with empty body (`d: null`).

---

# PHASE 12 — ERROR HANDLING

| Failure | What the code does |
| --- | --- |
| No `MONGODB_URI` | Process exits before listen. The UI cannot load stats either. |
| Mongo connection error | Same: `process.exit(1)`. |
| Lead missing name/email | 400 JSON. Axios throws. Contact shows “Something went wrong.” It does not show the server’s “Name and email are required.” HTML `required` usually blocks this in the browser. |
| Lead enum invalid | Mongoose throws. 500 “Server error”. Same generic UI string. |
| Stats GET fails on landing | Empty catch. Fallback headline stays. |
| Stats GET fails on Strategies | Unhandled rejection. Page heading still shows; cards can be empty or stale. |
| Allocate POST fails | Empty catch. Previous `alloc` remains or stays `null` (blank grid). |
| ML proxy down | 500 generic. Client returns `null`. No message. Button re-enables. |
| FastAPI “not enough data” | FastAPI 400, Express converts to 500, client shows nothing. |
| Ticker missing on ML route | 400. The UI always sends the state string; empty string is still sent and the server rejects it. UI still shows nothing. |
| Volatility HTTP error | `setError` with `detail` or “Request failed”. Chart unchanged. |
| Volatility network error | `setError(err.message)`. |
| PDF missing | 404 JSON in the new tab. Landing link does not pre-check. |
| Unknown client URL on Vite | Vite SPA fallback shows the app; `Routes` match nothing, so Nav + Footer and a blank middle. No 404 page component. |
| CORS mismatch | Browser blocks Axios. Contact goes to the generic catch. Landing falls back. |

What is weak, without changing it:

- No Express error-handling middleware (`app.use((err, req, res, next) => …)`).
- 400 vs 500 is collapsed in the contact UI.
- ML and allocation failures are silent.
- `GET /api/health` does not report Mongo state.
- Server `console.log(process.env.MODEL_ORIGIN)` at startup and again inside the volatility proxy can leak the internal URL into logs.
- The lead response returns the full document, including email, to whoever submitted. That is fine for the submitter; there is no auth if this endpoint is ever made listable.

Loading states exist for ML (`mlLoading`) and the chart (`loading`). Contact has no “submitting…” disabled state, so a double click can insert two leads. Empty states exist for the chart (no data yet) and for allocation (blank until the POST returns).

---

# PHASE 13 — ENVIRONMENT & CONFIGURATION

| Name | Process | Required? | What the code does with it |
| --- | --- | --- | --- |
| `MONGODB_URI` | server | Yes, or exit | `mongoose.connect` |
| `CLIENT_ORIGIN` | server | No | CORS allow-list. If unset, next fallback is used |
| `MODEL_ORIGIN` | server | Only for `/api/volatility` | Proxy base URL. Also logged |
| `PORT` | server | No | Default `5000` |
| `VITE_API_URL` | client build | No | Axios base and the pitch-deck link. Default `http://localhost:5000` |

**Safe to talk about:** the names above, the database name `quantnova`, ports 5173 / 5000 / 8000, the Render host string that is hardcoded in `VolatilityChart.jsx`.

**Secret, do not paste into slides or chat:** the value of `MONGODB_URI` (it contains credentials). `.env` is gitignored at the repo root, in `client/`, and in `server/`. This workspace has no `.env` or `.env.example` checked in, even though the old README says `cp .env.example .env`.

CORS line, exactly:

```js
const allowedOrigin = process.env.CLIENT_ORIGIN
  || process.env.MODEL_ORIGIN
  || "http://localhost:5173"
  || "http://127.0.0.1:8000/";
```

The last `||` never runs, because the localhost string is always truthy. If `CLIENT_ORIGIN` is unset, browsers are allowed only from `http://localhost:5173`, not from the Python origin. `MODEL_ORIGIN` is only used for CORS when `CLIENT_ORIGIN` is also unset — and then it replaces the localhost default. One variable is doing two jobs.

Development vs production:

- Dev: three terminals, Vite, nodemon, uvicorn.
- Client production: `vite build`. Hosting hint is Vercel rewrites.
- API production: `npm start` → `node server.js`. If `client/dist` sits next to `server/`, Express serves the SPA **and** the API on one port. ML route ordering breaks in that mode (Phase 16).
- ML production: not scripted. The Express ML URL is hardcoded to `localhost:8000`, so a remote API host cannot reach a model on the developer laptop, and a deployed API would call its **own** localhost unless you change that string.

---

# PHASE 14 — DEPENDENCY MAP

```text
index.html
  → main.jsx
      → App.jsx
          → Nav, Footer
          → page
              → api.js  →  Express server.js
                              → Lead.js → MongoDB
                              → stats.js
                              → pitch-deck.pdf
                              → MODEL_ORIGIN (volatility proxy, unused by UI)
                              → localhost:8000/predict
                                    → app.py → ml.py → Yahoo Finance

VolatilityChart.jsx
  → quantnova.onrender.com     (bypasses api.js and server.js)
```

High coupling:

- `server.js` **is the whole backend.** A bad edit in the allocator can prevent the file from loading, which also kills leads, stats, and Mongo startup.
- `stats.js` **shape** is shared by four pages. Renaming `risk` or `strategies` breaks those pages without a type error (this project is JavaScript, not TypeScript).
- **Lead field names** must match in `Contact.jsx` state, the POST body, and `Lead.js`. There is no shared schema package.
- `/api/ml/predict` **response field** `predicted_return` must match `Portfolio.jsx` (`result?.predicted_return`). FastAPI and the React check are string-coupled.
- **Chart JSON fields** `dates`, `actual`, `predicted`, `rmse`, `title`, `detail` are coupled to a service whose source is not here.
- **Mongo connect failure takes down unrelated routes.** Stats do not need a database, but they live in the same process.

Low coupling:

- `Capital`, `Positioning`, `Risk.jsx`, `Footer` can change without API changes.
- Chart.js is confined to one page.

---

# PHASE 15 — IF I CHANGE THIS, WHAT BREAKS?

| If I change… | Potentially affected | Why |
| --- | --- | --- |
| `Lead.js` field name or enum | `Contact.jsx` option values, `POST` body, existing Mongo docs | Write path and stored shape must match. Old rows keep old values. New enum rejects old strings only on new writes. |
| `POST /api/leads` response (`ok`, `lead`) | `submitLead` `data.ok` check | Success UI keys off `ok`. |
| `stats.js` keys | Landing, Strategies, Portfolio, Technology | Each page reads a different key. |
| `stats.strategies` strings | Strategy card order and empty cards | `Strategies.jsx` joins API names to local paragraphs by exact string. |
| Allocator `strategy` labels | Portfolio cards only | Display is generic over the array. Changing a weight rule changes numbers, not the UI code. |
| Route path in `App.jsx` | `Nav.jsx` `to=` and any `Link` | Mismatch → blank page or a link to nowhere. `/portfolio` is labeled Risk. |
| `VITE_API_URL` | Every Axios call and the PDF link | Chart ignores it and still calls Render. |
| `MONGODB_URI` | Entire API process | Missing or bad URI exits. |
| `CLIENT_ORIGIN` | All browser calls to Express | Wrong origin → CORS errors that look like “API is down”. |
| `MODEL_ORIGIN` | Express volatility proxy and, if `CLIENT_ORIGIN` is unset, CORS | Chart does not read this variable. |
| `predicted_return` key in FastAPI | `runMlPrediction` condition | UI stops showing a number and does not say why. |
| Port 8000 hardcode | ML button | Python on another port looks “unavailable”. |
| Moving `app.get("/api/ml/predict")` | Production SPA hosting | It must be registered **before** `app.get("*")`. |
| `COMPANIES` symbols | Search dropdown only | Run still sends whatever string is in `symbol`. |
| Removing `axios` import on the server | Server boot | Today the import can already crash boot because the package is not declared. |
| Adding auth | Every open route | Nothing is structured for middleware yet; you would add it in `server.js`. |

---

# PHASE 16 — CODE SMELLS / TECHNICAL DEBT

These are behaviors in the current code, not a rewrite.

### 1. `axios` imported, not installed

`server.js` line 10 imports `axios`. `server/package.json` does not depend on it, and the lockfile has no `axios`. Node fails at startup with a module-not-found error unless someone installed it outside the lockfile. **Serious** for the ML feature and for booting the API. Fix would be adding the dependency or using the `node-fetch` already used by the volatility proxy.

### 2. ML route registered after the SPA catch-all

`app.get("*")` is registered only when `client/dist` exists, and it is registered before `/api/ml/predict`. Paths under `/api` inside that catch-all return 404. **Serious in the “one process serves the built client” mode.** In local dev without `dist`, the catch-all is skipped and the route works. Fix would be registering `/api/ml/predict` with the other API routes, above the catch-all.

### 3. ML client hides every error

`fetchReturnPrediction` returns `null`. `runMlPrediction` only checks `predicted_return`. **Moderate.** The button looks like it worked and then shows nothing.

### 4. FastAPI 400 becomes Express 500

The proxy `catch` does not forward `err.response.status` or `detail`. **Moderate.** Callers cannot tell “bad ticker” from “Python is down”.

### 5. Prediction uses the last training row

`latest_window = X.iloc[-1]`. That row was inside `fit`. **Moderate if you claim forecast quality.** Fine if you describe it as a demo fit. A real next step would predict from the last 5 returns *after* the last label, or split a test window.

### 6. Allocator is a fixed formula

Marketing says “ML-driven regime switching”. The code adds 5 or 10 points and clamps volatility. **Serious only if you describe it as a model.** As a demo sandbox it is honest if you say “illustrative”.

### 7. Chart and proxy disagree

UI calls Render with `symbol` and `window`. Server proxy calls `MODEL_ORIGIN` and also sends `start` and `end`. Python in-repo implements neither. **Serious for explaining ownership:** you cannot debug the volatility math from this repo. **Missing file:** the service that implements `/api/volatility`.

### 8. Dead and misleading navigation

`Compliance.jsx` is imported and never routed. `/risk` exists but the nav “Risk” link goes to `/portfolio`. Technology route exists; nav link is commented out. `volatility-chart.css` is unused. **Low**, confusing when you demo.

### 9. CORS expression

`|| "http://localhost:5173" || "http://127.0.0.1:8000/"` — the last term is dead. `MODEL_ORIGIN` is reused as a browser origin. **Moderate** when deploying the client to another host.

### 10. Mongo is required for non-database routes

Stats, PDF, and allocator die if Mongo is down. **Moderate** for local demos.

### 11. No auth on lead creation, no rate limit, double submit

**Moderate** on a public URL (spam inserts). Not a read leak, because there is no list endpoint.

### 12. Contact success check is redundant with Axios

`if (data.ok)` only runs after a 2xx. Fine, slightly noisy.

### 13. `server.js` logs `MODEL_ORIGIN` at import time

**Low** information leak in logs.

### 14. Marketing stack is not the code stack

`stats.js` lists TensorFlow, PyTorch, Kubernetes, blockchain. **Serious in an interview if you claim you built those.** The implemented ML stack is scikit-learn linear regression plus a volatility service you did not vendor.

### 15. JavaScript only

No TypeScript. A renamed JSON field fails at runtime. **Low**, normal for this size.

Stylistic only, not defects: inline styles on the chart versus `styles.css` elsewhere; `Toggle` and `Card` not extracted; both `node-fetch` and `axios` on the server.

---

# PHASE 17 — MEMORIZE VS LOOK UP

### MUST KNOW

- It is a three-process demo: React, Express, FastAPI. Mongo stores only leads.
- Entry files: `client/src/main.jsx`, `server/server.js`, `model/app.py`.
- The only write is `POST /api/leads` → `Lead.create` → `quantnova.leads`.
- Page map: `/` landing, `/strategies`, `/portfolio` (nav: Risk), `/capital`, `/chart`, `/positioning`, `/contact`. `/technology` and `/risk` exist without nav links. Compliance is unrouted.
- Allocator is arithmetic in `server.js`. Return model is linear regression on 5 past daily returns, refit every request from Yahoo data.
- Volatility UI calls `quantnova.onrender.com`, and that model source is not in the repo.
- No authentication.
- Env names: `MONGODB_URI`, `CLIENT_ORIGIN`, `MODEL_ORIGIN`, `PORT`, `VITE_API_URL`.

### SHOULD UNDERSTAND

- You can trace submit → `submitLead` → route → schema → 201 → `leadOk`.
- You can trace Run ML → `fetchReturnPrediction` → Express → `predict` → `predict_next_day_return`.
- Why a missing Mongo URI takes down `/api/stats`.
- Why `/api/ml/predict` can 404 when `client/dist` exists.
- Why the displayed return is not a clean out-of-sample forecast.
- CORS is a single origin string.

### CAN LOOK UP

- Exact base weights (30/15/15/20/10/10) and the ±5/±10 adjustments.
- The full `COMPANIES` list.
- Chart.js color values and CSS class names.
- Mongoose `__v` and timestamp option details.
- ESLint and Vercel JSON internals.
- The wording of each strategy paragraph.

---

# PHASE 18 — INTERVIEW-STYLE QUESTIONS

Try these before reading the answer key. Say the file and function names out loud.

### Level 1 — Basic

1. What does this project do, in two sentences a non-engineer understands?
2. What are the three processes and their ports?
3. What is the frontend entry file? The backend entry file? The model entry file?
4. Which database, which database name, which collection?
5. Which user action writes to the database?

### Level 2 — Code tracing

6. User submits the contact form. List the functions and the HTTP call in order. What do they see on success?
7. User clicks Run ML on AAPL. Where does the ticker string travel before Yahoo Finance?
8. User moves the volatility slider. Which effect runs, and which endpoint? Is Mongo involved?
9. User clicks Run on the volatility page. Why is `server.js` not in that path?

### Level 3 — Architecture

10. Why can `/api/stats` not be served when MongoDB is down, even though stats are not stored in Mongo?
11. Why is there no service layer to point at?
12. Which pages break if you rename `strategies` inside `stats.js`?
13. What is the difference between “Risk” in the navbar and `Risk.jsx`?

### Level 4 — Debugging

14. The contact button shows “Something went wrong,” and the Mongo collection is empty. Where do you look, in order?
15. Run ML spins and then shows no number and no error. Where do you look?
16. The site works on localhost:5173 but the deployed frontend cannot load stats. What config is the first suspect?
17. Leads and stats work, but `/api/ml/predict` returns 404 only on the machine that has `client/dist`. Why?

### Level 5 — Modification

18. You must add “phone number” to the lead. Which files change? What happens to old documents?
19. You must show a list of leads to an admin. What does not exist yet that you would have to add?
20. You must move the return model to another host. Which hardcoded URL must change? Which env var will *not* do that today?

### Answer key

1. A website that explains a fictional/demo hedge fund and lets a visitor request access. It also shows a toy allocation, a small return prediction, and a volatility chart.
2. Vite 5173, Express 5000, Uvicorn 8000. Chart also uses Render.
3. `client/src/main.jsx`, `server/server.js`, `model/app.py` (logic in `ml.py`).
4. MongoDB, database `quantnova`, collection `leads`.
5. Contact form submit.
6. `submitLead` → `api.post("/api/leads")` → route in `server.js` → `Lead.create` → 201 → `setLeadOk("Thanks! We'll reach out soon.")` and form reset.
7. Input state `ticker` → `runMlPrediction` → `fetchReturnPrediction` → Express `/api/ml/predict` → FastAPI `/predict` → `load_market_data` → `yf.download`.
8. `useEffect` on `[regime, vol]` → `POST /api/allocate`. Mongo is not involved.
9. `fetchData` calls `https://quantnova.onrender.com/api/volatility` with `fetch`, not `api.js`.
10. `mongoose.connect` failure calls `process.exit(1)` before a healthy server is useful; the listen is in the same process. A failed connect exits even though `listen` is not inside the `.catch` — the process ends, so the port does not stay up.
11. Routes are closures in `server.js`. Saying “the controller” would be inventing a file.
12. `Strategies.jsx` uses it for order. Other pages do not read `strategies`. Landing reads `tagline`, `subtext`, `quick`.
13. Nav “Risk” is `/portfolio` (`Portfolio.jsx`: allocator + ML). `Risk.jsx` is `/risk`, a static table, not linked.
14. Browser network tab: was `POST /api/leads` sent? Status 400 vs 500 vs CORS vs failed. Then server log for “Lead create error” or “Missing MONGODB_URI”. Then Mongo itself. Then the form’s generic catch, which hides the JSON `error`.
15. Is the server even up (`axios` import)? Is Uvicorn on 8000? Express log “ML service error”. Does the body contain `predicted_return`? Client drops errors to `null` in `fetchReturnPrediction`. If `dist` exists, suspect the 404 catch-all.
16. `CLIENT_ORIGIN` must be the deployed site origin. `VITE_API_URL` must be the public API, and it is baked in at **build** time by Vite.
17. `app.get("*")` is registered first and answers `/api/*` with 404. `/api/ml/predict` is registered underneath it.
18. `Contact.jsx` state and input, `Lead.js` schema, and the `Lead.create({...})` argument in `server.js` (it currently copies fields explicitly, so a new body field is **ignored** until added there). Old documents simply lack `phone`.
19. A read route (`Lead.find`), an admin page, and authentication. None of those exist. Do not add the read route without auth on a public server.
20. The string `"http://localhost:8000/predict"` in `server.js`. `MODEL_ORIGIN` is only for the volatility proxy (and accidentally CORS). `VITE_API_URL` only points the browser at Express.

---

# PHASE 19 — CHEAT SHEET

## Project purpose

Demo site for QuantNova / Finlatics. Visitor reads the pitch, tries an allocation sandbox and a return model, views volatility, or leaves a lead. Not a live fund.

## Tech stack

React 19 + Vite + React Router + Axios + Chart.js. Express + Mongoose. FastAPI + scikit-learn + yfinance. MongoDB.

## Folder structure

`client/src` UI, `server/server.js` API, `server/models/Lead.js`, `server/data/stats.js`, `model/app.py`, `model/ml.py`.

## Frontend entry point

`index.html` → `src/main.jsx` → `App.jsx`.

## Backend entry point

`server/server.js` via `nodemon` or `node`. Model: `uvicorn app:app --port 8000`.

## Database

MongoDB database `quantnova`, collection `leads`. Create only. Fields: `name`, `email`, `investorType`, `message`, `requestPitchDeck`, timestamps.

## Main APIs

- `GET /api/stats`
- `POST /api/leads`
- `GET /api/pitch-deck`
- `POST /api/allocate`
- `GET /api/ml/predict` → `GET :8000/predict`
- `GET /api/volatility` proxy (UI uses Render instead)
- `GET /api/health`

## Main components

`App`, `Nav`, `Footer`, `Landing`, `Strategies`, `Portfolio`, `Contact`, `VolatilityChart`. Static: `Capital`, `Positioning`, `Technology`, `Risk`. Unused route: `Compliance`.

## Main data models

`Lead` only. Allocation and predictions are not stored. Copy is `stats.js`.

## Authentication

None.

## Important functions

`submitLead`, allocate handler, `fetchReturnPrediction`, `runMlPrediction`, `predict`, `predict_next_day_return`, `prepare_features`, `fetchData`.

## Important user flows

Landing GET stats. Contact POST lead. Landing GET pdf. Portfolio POST allocate on every slider change. Portfolio GET ml predict on button. Chart GET Render volatility.

## Environment variables

`MONGODB_URI` (secret), `CLIENT_ORIGIN`, `MODEL_ORIGIN`, `PORT`, `VITE_API_URL`. No `.env.example` in the repo.

## Known issues

Undeclared server `axios`. ML route under the SPA `*` handler. Silent ML errors. In-sample prediction row. Volatility implementation not in repo. CORS fallback bug. Compliance page unrouted. Nav “Risk” is the portfolio page.

## Where do I look if…

| Symptom | Look here |
| --- | --- |
| UI layout / text wrong | The page in `client/src/pages/`, then `styles.css`. Hero copy: `stats.js` and Landing fallbacks. |
| API isn’t firing | `api.js` `baseURL`, `VITE_API_URL`, browser network tab, CORS `CLIENT_ORIGIN`. Chart: hardcoded Render URL, not `api.js`. |
| Backend crashes on start | `import axios` missing package; missing `MONGODB_URI`; Mongo `.catch` → `process.exit(1)`. |
| Database isn’t updating | `submitLead`, network status of `POST /api/leads`, route validation, `Lead.create` fields, Atlas/URI. Remember there is no update endpoint at all. |
| Authentication fails | There is no authentication. If a request is blocked, it is CORS or the host is down. |
| Wrong data on screen | Stats: `server/data/stats.js`. Weights: allocate handler. Percent: `predicted_return * 100`. Chart: Render payload fields. |
| Page doesn’t re-render | Setter not called (`setAlloc`, `setMlPrediction`, `setLeadOk`). Allocation effect deps are only `regime` and `vol`. ML does not run until the button. |
| ML 404 only in production with `dist` | Route order in `server.js`: `app.get("*")` above `/api/ml/predict`. |
| Form says something went wrong | Response was not 2xx. Read server log `Lead create error`. |

---

## Interview script (about 90 seconds)

“QuantNova is a three-tier demo for a hedge-fund pitch site. The React client is a set of routes with local state and one Axios client. Express on port 5000 serves marketing copy from a JS file, computes an illustrative allocation in memory, stores contact leads in MongoDB with Mongoose, and proxies a prediction call. The only collection is `leads` in database `quantnova`: name, email, investor type, message, a pitch-deck flag, and timestamps. There is no auth and no read API. A separate FastAPI service downloads six months of daily prices with yfinance and fits a linear regression on five lagged returns to estimate a next-day return. That model is trained per request and not persisted. The volatility chart calls a deployed service on Render; that model’s source is not in this repo. I treat the SEBI, blockchain, and deep-learning lines on the site as product copy, not as systems this codebase runs.”
