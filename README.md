# Reef

AI-driven job matching platform for fresh graduates. Reef uses [TinyFish](https://agent.tinyfish.ai) to scrape live LinkedIn job postings, then ranks them against your profile using a 6-factor weighted matching engine — all presented through an ocean-depth metaphor where stronger matches float near the surface and stretch roles sink deeper.

## How It Works

1. **Questionnaire** — pick your target domain, work environment, job types, skills, and motivation
2. **TinyFish Scan** — an AI agent scrapes LinkedIn for live job postings matching your target role
3. **Matching Engine** — each job is scored across skill match (35%), preference match (20%), seniority fit (15%), location match (10%), work arrangement (10%), and salary fit (10%)
4. **Command Center** — view best roles to target and skills to learn next
5. **The Descent** — browse matched jobs organized by depth: Surface (90%+), Twilight Zone (82%+), Deep Water (72%+), The Abyss (<72%)

## Tech Stack

| Layer    | Stack                                                        |
| -------- | ------------------------------------------------------------ |
| Frontend | React 19, Vite 8, Tailwind CSS v4, Framer Motion            |
| Backend  | Flask 3.0, SQLAlchemy, Pydantic v2                           |
| AI Agent | TinyFish async browser automation for LinkedIn job scraping  |
| Database | SQLite (development)                                         |

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- A [TinyFish API key](https://agent.tinyfish.ai)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv ../.venv
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env   # or edit .env directly
```

Set your TinyFish API key in `backend/.env`:

```
TINYFISH_API_KEY=your-key-here
```

Start the server:

```bash
flask run
```

The backend runs on `http://127.0.0.1:5000`.

### Frontend

```bash
cd frontend

npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies `/api` requests to the Flask backend.

## Environment Variables

### Backend (`backend/.env`)

| Variable                              | Default                        | Description                          |
| ------------------------------------- | ------------------------------ | ------------------------------------ |
| `FLASK_ENV`                           | `development`                  | Flask environment                    |
| `DEBUG`                               | `true`                         | Debug mode                           |
| `SECRET_KEY`                          | `change-me`                    | Flask secret key                     |
| `DATABASE_URL`                        | `sqlite:///career_match.db`    | Database connection string           |
| `TINYFISH_API_KEY`                    | —                              | **Required.** Your TinyFish API key  |
| `TINYFISH_BASE_URL`                   | `https://agent.tinyfish.ai`    | TinyFish API base URL                |
| `TINYFISH_API_TIMEOUT_SECONDS`        | `60`                           | HTTP timeout for TinyFish calls      |
| `TINYFISH_DEFAULT_BROWSER_PROFILE`    | `lite`                         | Browser profile for scraping         |
| `TINYFISH_DEFAULT_PROXY_ENABLED`      | `false`                        | Enable proxy for TinyFish            |
| `TINYFISH_DEFAULT_PROXY_COUNTRY_CODE` | `US`                           | Proxy country code                   |

### Frontend (`frontend/.env`)

| Variable             | Default | Description            |
| -------------------- | ------- | ---------------------- |
| `VITE_API_BASE_URL`  | `/api`  | Backend API base path  |

## API Endpoints

### Questionnaire
- `GET /api/questionnaire` — dynamic questionnaire step configuration

### Onboarding
- `POST /api/onboarding/session` — create user session with profile and skills

### Preferences
- `POST /api/preferences/:userId` — save job search preferences

### Job Aggregation
- `POST /api/job-aggregation/linkedin/sync` — trigger TinyFish LinkedIn scrape
- `GET /api/job-aggregation/linkedin/poll/:runId` — poll a running TinyFish scrape

### Jobs
- `GET /api/jobs/recommendations` — ranked job recommendations with match scores
- `GET /api/jobs/:jobId/match` — detailed match explanation for a specific job

### Skills
- `GET /api/skills/radar` — skill gap analysis against a target role
- `GET /api/skills/trends` — trending skills for a target role

## Project Structure

```
TinyFishHackathon/
  backend/
    app/
      api/            # Flask blueprints (routes)
      models/         # SQLAlchemy models
      repositories/   # Data access layer
      schemas/        # Pydantic validation schemas
      services/       # Business logic + TinyFish client
      utils/          # Response helpers
    instance/         # SQLite database
    .env              # Environment config
  frontend/
    src/
      components/     # React components (SplashScreen, Questionnaire, SonarScan, Zone3Descent, JobModal)
      data/           # Domain/environment option catalogs
      api.js          # Backend API client
      App.jsx         # Main app orchestrator
    vite.config.js    # Vite dev server + proxy config
```
