# Flask Backend

This backend provides Render-friendly onboarding, preferences, skill radar, and TinyFish-powered skill ingestion APIs for a career and job matching app, using PostgreSQL.

## Setup

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

## Environment variables

- `DATABASE_URL`: SQLAlchemy database URL.
- `MAX_CONTENT_LENGTH_MB`: maximum resume upload size in MB.
- `DEBUG`: Flask debug mode.
- `TINYFISH_API_KEY`: TinyFish API key.
- `TINYFISH_BASE_URL`: TinyFish API base URL. Default: `https://agent.tinyfish.ai`.
- `TINYFISH_API_TIMEOUT_SECONDS`: HTTP timeout for TinyFish requests.
- `TINYFISH_DEFAULT_BROWSER_PROFILE`: `lite` or `stealth`.
- `TINYFISH_DEFAULT_PROXY_ENABLED`: default proxy toggle.
- `TINYFISH_DEFAULT_PROXY_COUNTRY_CODE`: default proxy country code.

Sensitive TinyFish settings are now expected in [backend/.env](/home/mx/tinyFishHackathon/backend/.env), and example placeholders are in [backend/.env.example](/home/mx/tinyFishHackathon/backend/.env.example).

## API endpoints

### Core

- `GET /api/health`

### Onboarding

- `POST /api/onboarding/session`
- `GET /api/onboarding/session/<session_id>`
- `PUT /api/onboarding/session/<session_id>`
- `POST /api/onboarding/session/<session_id>/resume`
- `POST /api/onboarding/session/<session_id>/questions/generate`
- `POST /api/onboarding/session/<session_id>/answers`
- `POST /api/onboarding/session/<session_id>/finalize`

### Preferences Engine

- `GET /api/preferences/<user_id>`
- `POST /api/preferences/<user_id>`
- `POST /api/preferences/normalize`

### Skill Radar and Gap Analysis

- `GET /api/skills/radar?user_id=<uuid>&target_role=<role>`
- `GET /api/skills/trends?target_role=<role>&window_days=90&limit=10`

### TinyFish ingestion

- `POST /api/skills/ingest/tinyfish/start`
- `GET /api/skills/ingest/tinyfish/runs/<run_id>`
- `POST /api/skills/ingest/tinyfish/runs/<run_id>/ingest`

## TinyFish integration flow

The backend uses TinyFish's async automation API to gather job posting data and convert it into normalized role-skill aggregates.

1. Start an async TinyFish run for a source URL and target role.
2. TinyFish returns a `run_id` immediately.
3. Poll the run until TinyFish reports `COMPLETED`.
4. Ingest the completed run into local Postgres tables.
5. The ingestion pipeline updates `role_skill_mappings` and appends a new `role_skill_trends` snapshot.

### TinyFish request contract used by the backend

The backend sends TinyFish:

- `url`: source job board or listings page
- `goal`: asks TinyFish to return JSON only with a `jobs` array
- `browser_profile`: `lite` by default, overrideable per request
- optional `proxy_config`

Expected TinyFish result shape:

```json
{
  "target_role": "Backend Engineer",
  "jobs": [
    {
      "title": "Backend Engineer",
      "company": "Example Co",
      "location": "Singapore",
      "posted_at": "2026-03-28",
      "skills": ["Python", "SQL", "Docker"],
      "required_skills": ["Python", "REST API"],
      "preferred_skills": ["AWS"]
    }
  ]
}
```

### Example: start TinyFish ingestion

```bash
curl -X POST http://127.0.0.1:5000/api/skills/ingest/tinyfish/start \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://example.com/jobs/backend-engineer",
    "target_role": "Backend Engineer",
    "max_jobs": 20,
    "browser_profile": "lite"
  }'
```

### Example: check run status

```bash
curl http://127.0.0.1:5000/api/skills/ingest/tinyfish/runs/<run_id>
```

### Example: ingest completed run

```bash
curl -X POST http://127.0.0.1:5000/api/skills/ingest/tinyfish/runs/<run_id>/ingest
```

## Skill Radar data model

### `normalized_skills`

Master taxonomy for canonical skill names.

### `skill_synonyms`

Explicit synonym mapping for canonicalization.

### `role_skill_mappings`

Aggregated role-skill requirements used for matching.

### `role_skill_trends`

Time-series aggregates used to compute trending skills.

### `tinyfish_ingestion_runs`

Stores TinyFish run metadata, last remote response, and ingestion summary for traceability.

## Skill comparison algorithm

1. Gather user skills from onboarding profile and latest onboarding session.
2. Normalize user skills through canonical skill names and synonyms.
3. Preserve confidence scores for manual vs AI-extracted skills.
4. Compare against `role_skill_mappings` for the selected role.
5. Bucket into matched skills, missing core skills, and emerging skills.
6. Return chart-ready radar axes and summary coverage metrics.

## Trend calculation logic

Trending skills are computed from `role_skill_trends` snapshots.

- `skill_frequency`: normalized occurrence rate from aggregated job postings.
- `movement = latest_frequency - earliest_frequency`
- `movement_pct = movement / earliest_frequency` when earliest is non-zero.
- `direction` is `up`, `stable`, or `down` based on movement thresholds.

## TinyFish ingestion aggregation logic

When a TinyFish run is ingested:

- the backend extracts `skills`, `required_skills`, and `preferred_skills` from each job
- raw skills are normalized through existing synonyms where possible
- unknown skills are added to the normalized taxonomy as `unclassified`
- `skill_frequency` is computed as `jobs_with_skill / total_jobs`
- `importance_score` is derived from skill frequency and mention share
- skills with frequency `>= 0.55` are marked as core for that ingestion snapshot
- existing `role_skill_mappings` for that role are replaced by the latest TinyFish aggregate
- a new `role_skill_trends` snapshot row is appended for each aggregated skill

## Example skill radar response

```json
{
  "message": "OK",
  "data": {
    "target_role": "Backend Engineer",
    "matched_skills": [{"skill": "Python", "confidence": 1.0}],
    "missing_core_skills": [{"skill": "System Design", "role_importance": 0.81}],
    "emerging_skills": [{"skill": "AI Orchestration", "trend_movement": 0.12}],
    "summary": {"core_coverage_pct": 62.5, "weighted_match_score": 58.3},
    "chart": {"radar_axes": [{"skill": "Python", "role_importance": 0.96, "user_strength": 1.0}]}
  }
}
```

## Example trending response

```json
{
  "message": "OK",
  "data": {
    "target_role": "Backend Engineer",
    "skills": [
      {
        "skill": "AI Orchestration",
        "movement": 0.12,
        "movement_pct": 300.0,
        "direction": "up"
      }
    ],
    "chart": {
      "series": [
        {
          "skill": "AI Orchestration",
          "points": [
            {"date": "2026-01-01T00:00:00+00:00", "frequency": 0.04, "importance_score": 0.33},
            {"date": "2026-03-28T00:00:00+00:00", "frequency": 0.16, "importance_score": 0.33}
          ]
        }
      ]
    }
  }
}
```

## Render deployment notes

- Create a free Render Postgres database in the same region as your web service.
- Copy the database's internal connection URL into the web service env var `DATABASE_URL`.
- Set TinyFish credentials in Render environment variables.
- Use a start command such as `gunicorn run:app` with the service root set to `backend`.
- Render provides `PORT`; `run.py` also respects it for local parity.

## AI Job Matching and Scoring Engine

### Job matching endpoints

- `GET /api/jobs/recommendations?user_id=<uuid>&limit=10`
- `GET /api/jobs/<job_id>/match?user_id=<uuid>`

### Normalized job postings schema

The matching engine ranks jobs from the `normalized_job_postings` table.

Key fields:

- `title`, `role_key`, `role_name`
- `company_name`, `company_size`, `company_type`
- `locations`, `work_arrangement`, `job_type`
- `industries`
- `seniority_level`, `years_experience_min`, `years_experience_max`
- `salary_min`, `salary_max`, `salary_currency`, `salary_period`
- `normalized_skills`, `core_skills`, `preferred_skills`
- `description_summary`, `source`, `source_url`

### Scoring formula design

The engine uses modular weighted factors so weights can be adjusted later without rewriting the ranking pipeline.

Default weights:

- `skill_match`: `0.35`
- `preference_match`: `0.20`
- `location_match`: `0.10`
- `work_arrangement_match`: `0.10`
- `seniority_fit`: `0.15`
- `salary_fit`: `0.10`

Formula:

```text
match_score = sum(factor_score * factor_weight for active factors) / sum(active factor weights)
```

Factor details:

- `skill_match`: compares normalized user skills against job `core_skills` and `preferred_skills`. Core skills carry higher weight, and AI-extracted skills use confidence scores.
- `preference_match`: compares target roles, industries, job type, company size, and company type against saved normalized preferences.
- `location_match`: scores overlap between preferred locations and job locations.
- `work_arrangement_match`: scores fit between preferred arrangements and the job's normalized work arrangement.
- `seniority_fit`: compares user years of experience against the job's experience band and seniority target.
- `salary_fit`: optional; only active when both the user and job have salary data.

### Ranking pipeline

1. Build user context from:
   - onboarding profile
   - latest onboarding session
   - extracted skills with confidence
   - saved preferences
2. Load normalized job postings.
3. Score each job with the six factor scorers.
4. Reweight active factors dynamically if salary or preference data is missing.
5. Sort descending by numerical match score.
6. Return both structured explanations and human-readable summaries.

### Explainability response format

Each scored job returns:

- `match_score`: final numerical score from `0` to `100`
- `explanation.summary`: one-paragraph explanation for the frontend
- `explanation.matched_skills`: normalized matched skills with confidence
- `explanation.missing_skills`: missing job skills, highlighting core gaps
- `explanation.matched_preferences`: saved preferences that aligned with the job
- `explanation.lower_score_reasons`: concrete reasons the score was reduced
- `explanation.factor_scores`: per-factor score trace for debugging and UI detail views

### Example recommendations request

```bash
curl -s "http://127.0.0.1:5000/api/jobs/recommendations?user_id=<USER_ID>&limit=5" | python3 -m json.tool
```

### Example recommendations response

```json
{
  "message": "OK",
  "data": {
    "user_id": "0a5b3c3a-2f51-4be4-9f18-8eb90f3aa111",
    "ranking_pipeline": {
      "weights": {
        "skill_match": 0.35,
        "preference_match": 0.20,
        "location_match": 0.10,
        "work_arrangement_match": 0.10,
        "seniority_fit": 0.15,
        "salary_fit": 0.10
      }
    },
    "jobs": [
      {
        "job_id": "b0f70fc7-8b32-4eec-b4b0-49fdb4123456",
        "title": "Backend Engineer",
        "company_name": "Harbor Labs",
        "match_score": 86.4,
        "locations": ["Singapore"],
        "work_arrangement": "hybrid",
        "summary": "This job scored 86.4 because it has matched skills like Python, SQL, Docker, role aligns with target roles: backend engineer.",
        "matched_skills": [
          {"skill": "Python", "confidence": 1.0, "is_core": true}
        ],
        "missing_skills": [
          {"skill": "AWS", "is_core": false, "priority": "medium"}
        ],
        "matched_preferences": [
          "Role aligns with target roles: Backend Engineer",
          "Job type match: full_time"
        ]
      }
    ]
  }
}
```

### Example detailed explanation request

```bash
curl -s "http://127.0.0.1:5000/api/jobs/<JOB_ID>/match?user_id=<USER_ID>" | python3 -m json.tool
```

### Example detailed explanation response

```json
{
  "message": "OK",
  "data": {
    "job": {
      "id": "b0f70fc7-8b32-4eec-b4b0-49fdb4123456",
      "title": "Backend Engineer",
      "role_name": "Backend Engineer"
    },
    "match_score": 86.4,
    "explanation": {
      "summary": "This job scored 86.4 because it has matched skills like Python, SQL, Docker. Lower score drivers include missing skills such as AWS, System Design.",
      "matched_skills": [
        {"skill": "Python", "confidence": 1.0, "is_core": true},
        {"skill": "SQL", "confidence": 1.0, "is_core": true}
      ],
      "missing_skills": [
        {"skill": "AWS", "is_core": false, "priority": "medium"},
        {"skill": "System Design", "is_core": false, "priority": "medium"}
      ],
      "matched_preferences": [
        "Role aligns with target roles: Backend Engineer",
        "Industry match: technology"
      ],
      "lower_score_reasons": [
        "Missing important job skills: AWS, System Design.",
        "Job salary is below the user's preferred minimum, reducing the score."
      ],
      "factor_scores": [
        {
          "factor": "skill_match",
          "score": 0.82,
          "weight": 0.35,
          "active": true,
          "reason": "Matched 4 of 6 normalized job skills."
        }
      ]
    }
  }
}
```

### Seeded normalized jobs

The backend currently seeds a small set of normalized jobs for immediate local testing:

- `Backend Engineer`
- `Senior Backend Platform Engineer`
- `Data Analyst`
- `AI Product Manager`

These are inserted on startup if `normalized_job_postings` is empty.

## Job Aggregation Pipeline

### Aggregation endpoints

- `POST /api/job-aggregation/runs`
- `GET /api/job-aggregation/metrics`
- `GET /api/job-aggregation/jobs?limit=20&offset=0&source=<source>&role=<role>`
- `POST /api/job-aggregation/retry-failed`

### Service architecture

The aggregation module is designed as a generic ingestion pipeline with clear stages:

1. connector layer
   - `job_aggregation_connectors.py`
   - fetches raw jobs from a specific source connector
   - ships with a `manual` connector now and is structured so new connectors can be registered later
2. normalization and parsing layer
   - `job_aggregation_service.py`
   - validates required fields, normalizes enums, parses salary text and posted dates, and canonicalizes skill names
3. deduplication layer
   - `job_aggregation_service.py`
   - computes a stable deduplication key and falls back to similarity matching for same-company same-role jobs
4. persistence layer
   - `job_aggregation_repository.py`
   - stores runs, raw jobs, normalized jobs, processing state, and monitoring metrics
5. admin API layer
   - `job_aggregation.py`
   - exposes metrics, normalized job listing, retry flow, and an admin ingestion trigger

### Database schema

#### `job_ingestion_runs`

Tracks ingestion-level workflow and metrics.

Key fields:
- `connector_type`, `connector_name`
- `source_label`, `source_url`
- `status`
- `request_payload`
- `requested_job_count`, `fetched_job_count`, `parsed_job_count`
- `normalized_job_count`, `deduplicated_job_count`, `failed_job_count`
- `metrics_json`, `error_summary`
- `started_at`, `completed_at`

#### `raw_job_postings`

Stores source-native payloads separately from normalized jobs.

Key fields:
- `ingestion_run_id`
- `source_connector`, `source_name`, `source_job_id`
- `source_url`, `apply_url`
- `processing_status`
- `processing_attempts`
- `deduplication_key`
- `raw_payload`
- `extracted_payload`
- `parse_error`
- `normalized_job_id`

#### `normalized_job_postings`

Canonical jobs used later by job matching and recommendations.

Key normalized fields:
- `title`
- `company_name`
- `description`, `description_summary`
- `locations`
- `work_arrangement`
- `posted_at`
- `salary_text`
- `source`
- `apply_url`
- `role_key`, `role_name`
- `job_type`, `industries`, `seniority_level`
- `normalized_skills`, `core_skills`, `preferred_skills`
- `deduplication_key`, `source_count`, `last_ingested_at`

### Ingestion workflow

1. Start a run with `POST /api/job-aggregation/runs`.
2. The selected connector fetches raw jobs.
3. Each raw job is stored in `raw_job_postings` with status `queued`.
4. The parser normalizes title, company, locations, work arrangement, salary, seniority, and skills.
5. The deduplicator checks for an existing canonical job.
6. If no duplicate exists, a new `normalized_job_postings` row is created.
7. If a duplicate exists, the canonical job is updated and `source_count` is incremented.
8. The raw job is marked as `normalized`, `deduplicated`, `failed_parsing`, or `failed_normalization`.
9. Run-level metrics are finalized in `job_ingestion_runs`.

### Deduplication strategy

The pipeline uses a two-stage approach:

- Stage 1: deterministic deduplication key
  - built from normalized title, company, primary location, work arrangement, and seniority
  - hashed so it can be indexed and compared efficiently
- Stage 2: similarity fallback
  - limited to jobs from the same company and normalized role
  - combines title token overlap, skill overlap, and location overlap
  - merges when similarity is `>= 0.78`

This makes the system resilient to the same job being copied across different sources with small text differences.

### Admin monitoring responses

#### Example: start a manual ingestion run

```bash
curl -X POST http://127.0.0.1:5000/api/job-aggregation/runs \
  -H "Content-Type: application/json" \
  -d '{
    "connector_type": "manual",
    "source_label": "demo import",
    "source_url": "https://example.com/jobs",
    "jobs": [
      {
        "title": "Backend Engineer",
        "company": "Oceanic Labs",
        "description": "Build Python APIs, SQL data services, and Docker-based deployments.",
        "location": "Singapore",
        "work_arrangement": "hybrid",
        "posted_date": "2026-03-28",
        "salary_text": "SGD 80000 - 100000 annual",
        "apply_url": "https://example.com/jobs/backend-engineer",
        "skills": ["Python", "SQL", "Docker"],
        "required_skills": ["Python", "REST API"],
        "preferred_skills": ["AWS"],
        "job_type": "full-time",
        "industries": ["tech"]
      }
    ]
  }'
```

#### Example: fetch ingestion metrics

```json
{
  "message": "OK",
  "data": {
    "metrics": {
      "total_runs": 3,
      "total_raw_jobs": 42,
      "total_normalized_jobs": 27,
      "duplicate_rate_pct": 21.43,
      "run_status_counts": {
        "completed": 2,
        "completed_with_errors": 1
      },
      "raw_status_counts": {
        "normalized": 25,
        "deduplicated": 9,
        "failed_parsing": 6,
        "failed_normalization": 2
      },
      "connector_counts": {
        "manual": 3
      }
    }
  }
}
```

#### Example: list ingested jobs

```json
{
  "message": "OK",
  "data": {
    "total": 27,
    "limit": 20,
    "offset": 0,
    "jobs": [
      {
        "id": "job-123",
        "title": "Backend Engineer",
        "company_name": "Oceanic Labs",
        "work_arrangement": "hybrid",
        "posted_at": "2026-03-28T00:00:00+00:00",
        "source": "demo import",
        "apply_url": "https://example.com/jobs/backend-engineer",
        "raw_job_count": 2,
        "dedupe_sources": 2
      }
    ]
  }
}
```

#### Example: retry failed parsing jobs

```bash
curl -X POST http://127.0.0.1:5000/api/job-aggregation/retry-failed \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "<RUN_ID>",
    "limit": 10
  }'
```
