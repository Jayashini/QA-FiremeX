# FiremeX QA/Staging Environment Setup

| Document field | Value |
|---|---|
| Document ID | FIREMEX-QA-ENV-01 |
| Project | FiremeX QA and staging test harness |
| Version | 1.0 |
| Prepared by | QA / DevOps |
| Date | 27 October 2026 |
| Status | Setup guide; see the implementation gaps in Section 12 |

## 1. Purpose and scope

This document describes how to prepare the QA-FiremeX repository's local QA
services, connect them to a separately running FiremeX application, and execute
the repository's API and UI automation.

The repository is primarily a QA/test repository. Its current Docker Compose
configuration provisions PostgreSQL and Home Assistant; it does not provision
the FiremeX backend, frontend, AI inference service, CCTV/NVR hardware, message
queue, notification gateway, or mock fire-panel API. Those application
components must be supplied separately for end-to-end testing.

The project architecture describes a CCTV/RTSP stream flowing through frame
capture and preprocessing to PyTorch/YOLO inference, with detections and saved
frames feeding the FiremeX backend, database, dashboard, and test integrations.
This QA repository does not include or deploy that complete runtime pipeline.

## 2. Environment profile

Use this environment for functional, integration, and regression testing with
non-production data. Do not connect it to live cameras, production databases,
real emergency services, or customer notification accounts.

### 2.1 Supported local test workstation

- Windows 11 or a compatible development workstation.
- Docker Desktop with Docker Compose v2.
- Python 3 and `pip` for API/UI automation.
- A Chromium-based browser for Selenium UI tests.
- Network access to the separately deployed FiremeX frontend and backend.
- Additional disk and memory appropriate to the PostgreSQL data volume,
  Home Assistant, browser automation, and any separately hosted model service.

The repository does not declare or validate a production server sizing
baseline. GPU, camera, NVR, and bandwidth requirements depend on the separately
deployed inference and video pipeline.

### 2.2 QA service inventory

| Component | Available in this repository | Intended local endpoint | Notes |
|---|---:|---|---|
| PostgreSQL | Yes, Compose service `db` | Host `localhost:5433` | Database `firemex_qa`; verify/fix the port mismatch in Section 4. |
| Home Assistant | Yes, Compose service `homeassistant` | `http://localhost:8124` | Container listens on 8123; config is persisted under `homeassistant_config/`. |
| FiremeX API/backend | No | Default test URL `http://localhost:8080` | Start the application separately; API tests may require a valid token. |
| FiremeX frontend | No | UI test default `http://localhost:5173/FiremeX` | Start the application separately. Confirm the application’s actual base path/case. |
| AI inference service | No | Not configured by this repository | Provide separately if detection tests require inference. |
| RTSP cameras/NVR | No | N/A | Use approved test streams or simulated footage in an isolated test network. |
| RabbitMQ, InfluxDB, notification gateway, mock fire panel | No | N/A | Not defined in the current QA Compose file. |

The repository's test defaults are not evidence that a service is deployed or
healthy. Set test environment variables to the actual URLs and credentials for
the application under test.

## 3. Network and ports

| Service | Host port | Container/service port | Purpose |
|---|---:|---:|---|
| PostgreSQL | 5433 | 5432 (recommended) | Host-based application/test client connection |
| Home Assistant | 8124 | 8123 | Local Home Assistant UI/API |
| FiremeX backend | 8080 by API-test default | Application-defined | API and registration/login routes |
| FiremeX frontend | 5173 by UI-test default | Application-defined | Browser-based application |

The database port mapping is `host:container`. A backend running directly on
the workstation should normally connect to `localhost:5433`. A backend running
on the same Compose network should connect to `db:5432`.

Only the PostgreSQL and Home Assistant ports are declared in
`docker-compose.qa.yml`. The backend/frontend ports must be managed by the
separate FiremeX application setup.

## 4. Prerequisites and database configuration

1. Install and start Docker Desktop.
2. From the repository root, inspect the resolved Compose configuration:

   ```powershell
   docker compose -f .\docker-compose.qa.yml config
   ```

3. **Resolve the PostgreSQL port mismatch before starting the database.** The
   current Compose file sets PostgreSQL's internal listening port to 5433 with
   `command: ["postgres", "-c", "port=5433"]`, but publishes `5433:5432`.
   With that combination, Docker forwards traffic to container port 5432 while
   PostgreSQL listens on 5433.

   Recommended local setup: remove the custom `command` line so PostgreSQL
   listens on its default container port 5432; keep the mapping as
   `"5433:5432"`. Alternatively, if PostgreSQL must listen on 5433 inside the
   container, change the mapping to `"5433:5433"` and use `db:5433` from
   containers on the Compose network.

4. Start the QA services:

   ```powershell
   docker compose -f .\docker-compose.qa.yml up -d
   docker compose -f .\docker-compose.qa.yml ps
   ```

5. Verify PostgreSQL inside the container (use the actual internal port chosen
   above):

   ```powershell
   docker exec firemex_qa_db pg_isready -U admin -d firemex_qa -p 5432
   ```

   For the alternative internal-5433 configuration, use `-p 5433`.

6. Confirm the host-port mapping and connectivity:

   ```powershell
   docker port firemex_qa_db
   Test-NetConnection localhost -Port 5433
   ```

   A successful TCP check verifies that a process accepts a connection on the
   port; it does not, by itself, prove that the process is PostgreSQL. Confirm
   the container mapping and `pg_isready` result as well.

The Compose file currently contains development database credentials. Do not
reuse them outside an isolated local QA environment. Use secrets or protected
environment variables for shared staging, and do not commit credentials.

## 5. Home Assistant setup

Home Assistant is published at `http://localhost:8124`; its container port is
8123. The configuration directory is mounted from `homeassistant_config/`.

Start or inspect the service:

```powershell
docker compose -f .\docker-compose.qa.yml up -d homeassistant
docker compose -f .\docker-compose.qa.yml logs --tail 100 homeassistant
```

Complete Home Assistant's initial setup through the browser if this is a fresh
configuration. If the FiremeX application needs Home Assistant API access,
configure its base URL and a dedicated test long-lived access token in the
application's own environment. Do not paste tokens into this document or
commit them.

The Compose dependency on `db` only controls container start order; it does not
configure a FiremeX-to-Home-Assistant integration or guarantee that Home
Assistant is healthy.

## 6. FiremeX application under test

The application backend and frontend are maintained/deployed separately from
this QA repository. Before testing:

1. Start the backend using the application team's supported instructions.
2. Configure it to use the QA PostgreSQL database and the correct connection
   endpoint for where it runs:
   - Workstation process: `localhost:5433` when using the recommended mapping.
   - Compose-network process: `db:5432` when using the recommended mapping.
3. Start the frontend using the application team's supported instructions.
4. Configure the frontend API URL or development proxy to target the backend.
5. Open `/ping` on the backend and verify an HTTP success response before
   running API tests.
6. Open the frontend login/registration page and verify its API calls in the
   browser Network panel.

The QA API fixture defaults to `http://localhost:8080` and accepts
`FIREMEX_API_URL` or `API_BASE_URL` overrides. UI tests commonly default to
`http://localhost:5173/FiremeX` and accept `FIREMEX_BASE_URL` in some test
modules. Set each variable to the actual deployment URL; some older UI scripts
use a hard-coded URL and may need to be updated before they can target a
different environment.

## 7. Test automation setup

### 7.1 API automation

The API suite is under `API-Automation/`. It uses pytest and Playwright's API
request context.

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\API-Automation\requirements.txt
```

Configure the API URL and any credentials required by the selected tests in
`API-Automation/.env` (copy the example as a starting point, then replace
placeholders). The fixture reads that file if it exists. Do not commit it.

```env
FIREMEX_API_URL=http://localhost:8080
FIREMEX_TEST_EMAIL=<QA account email>
FIREMEX_TEST_PASSWORD=<QA account password>
FIREMEX_API_TOKEN=<scoped QA token if required>
```

Run the API tests:

```powershell
Set-Location .\API-Automation
python -m pytest
```

The valid-login tests require `FIREMEX_TEST_EMAIL` and
`FIREMEX_TEST_PASSWORD`. Authenticated endpoint tests may require a valid
`FIREMEX_API_TOKEN`/`API_TOKEN`. Use dedicated QA accounts and data.

### 7.2 UI automation

UI automation scripts are in `UIAutomation/` and `tests/`. They use Selenium
and a Chromium browser. Install Selenium and a compatible browser/driver in the
chosen Python environment before running those tests; the API
`requirements.txt` does not declare Selenium.

Set `FIREMEX_BASE_URL` to the actual frontend URL where supported, and
`FIREMEX_HEADLESS=1` for the dashboard suite in headless environments. Some
older scripts hard-code `http://localhost:5173/`; inspect the test before
running it against another environment.

Example:

```powershell
$env:FIREMEX_BASE_URL = "http://localhost:5173/FiremeX"
$env:FIREMEX_HEADLESS = "1"
python -m pytest .\tests
```

The UI suite includes test code with fallback credentials. Override them with
dedicated QA test users and never use production accounts. A failed
authentication setup can make later UI assertions fail before the target
feature is reached.

## 8. Environment validation / smoke tests

Run these checks before a test cycle and record the results:

| Check | Validation | Expected result |
|---|---|---|
| Compose services | `docker compose -f .\docker-compose.qa.yml ps` | PostgreSQL and Home Assistant are running. |
| Database readiness | `docker exec firemex_qa_db pg_isready -U admin -d firemex_qa -p 5432` | Reports accepting connections on the configured internal port. |
| Database host port | `Test-NetConnection localhost -Port 5433` plus `docker port firemex_qa_db` | Host port maps to the port PostgreSQL actually listens on. |
| Home Assistant | Browse to `http://localhost:8124` | Login/setup page responds. |
| Backend | Browse/curl the deployed backend `/ping` route | HTTP success and JSON response. |
| Frontend | Open the configured frontend URL | Login/registration UI loads. |
| Frontend-to-backend | Submit a controlled test request and inspect browser Network tab | Request reaches the intended backend; no proxy/CORS/network error. |
| API automation | Run `python -m pytest` from `API-Automation` | Required tests pass with configured QA credentials. |
| UI automation | Run the selected Selenium suite | Browser can load the app and test account can authenticate. |

Camera-online checks, model inference, alert delivery, historical video playback,
mock fire-panel calls, and notifications are conditional on separately
provisioned services and test data. They cannot be considered passed merely
because the two Compose containers are healthy.

## 9. Data handling and environment refresh

- Use synthetic or approved test data; avoid production personal data and
  credentials.
- The PostgreSQL volume `qa_postgres_data` persists across container
  recreation.
- `docker compose down` stops and removes the containers but preserves the
  named database volume.
- `docker compose down -v` deletes the named database volume and its data. Run
  it only when a full database reset is explicitly intended.
- Home Assistant state is persisted in the host-mounted
  `homeassistant_config/` directory; removing its container does not reset
  that directory.
- Back up QA data before refreshes that could alter the schema or test records.
- Record environment defects separately from application defects, using the
  `ENV-` prefix where the team's issue-tracking process supports it.

The repository's current CI workflow is a deployment placeholder: it prints
the source commit and a deployment message but does not deploy services or run
the smoke suite. Do not treat a successful workflow run as proof that staging
was refreshed or validated.

## 10. Access, secrets, and network controls

- Restrict QA database and Home Assistant access to authorized testers.
- Keep `.env` files, API tokens, passwords, and Home Assistant tokens out of
  source control, test reports, screenshots, and chat logs.
- Use separate, least-privilege QA accounts for administrators, operators, and
  automated tests.
- Do not expose PostgreSQL, Home Assistant, or the backend directly to the
  public internet.
- For a shared staging deployment, use HTTPS at the ingress/reverse proxy and
  restrict camera/RTSP traffic to an approved isolated network.
- Use sandbox notification services and a mock fire-panel endpoint if those
  integrations are added; the current QA Compose file does not configure them.
- Rotate any development credentials that have been shared or used outside a
  local isolated setup.

## 11. Troubleshooting

### Host port 5433 accepts TCP but the DB is unreachable

Check the Compose host-to-container mapping and the PostgreSQL internal
listening port. The current file's custom `port=5433` command conflicts with
its `5433:5432` mapping. Use one of the consistent configurations in Section 4,
recreate only the database service, and verify with `pg_isready` and
`docker port`.

### API tests cannot connect

Check that the backend is running, that `/ping` responds, and that
`FIREMEX_API_URL` or `API_BASE_URL` points to the right port. A database port
is not an API port.

### Frontend reports that the backend is unavailable

Inspect the browser Network panel for the failed request URL, HTTP status, and
response body. Confirm that the frontend proxy/API base URL points to the
backend and that browser origins are allowed if the frontend calls the
backend directly. A `403` is an HTTP response; it does not, by itself, mean the
backend is stopped.

### Home Assistant container runs but integration tests fail

Check Home Assistant logs and UI setup, confirm the backend's configured
Home Assistant URL is reachable from the backend's network, and use a valid
test token. `depends_on` does not establish application credentials or
readiness.

### UI tests cannot find the page or authenticate

Confirm the frontend base URL and path, browser/driver availability, and test
account status. Several legacy scripts hard-code the port or use default test
credentials.

## 12. Known gaps and release-readiness conditions

The following are not provisioned or verified by the current QA repository:

1. FiremeX frontend/backend application deployment and API-to-database
   configuration.
2. AI model service, model artifact/version management, and camera/NVR/RTSP
   test rig.
3. RabbitMQ, InfluxDB, sandbox email/SMS/push services, and mock fire-panel
   API.
4. TLS termination, a staging DNS name, and camera VLAN/network shaping.
5. Automated environment refresh, service health gates, and CI smoke tests.
6. A coherent documented Selenium dependency manifest and complete
   configurable URLs across all legacy UI scripts.
7. Correction of the PostgreSQL internal-port/host-port mismatch in the
   current working Compose configuration before relying on host port 5433.

Before calling an environment production-like staging, assign owners and
implementation dates for these gaps, resolve the database port mapping, and
run the smoke tests against the deployed application and approved test
integrations.

## 13. Repository references

- `docker-compose.qa.yml` — local PostgreSQL and Home Assistant services.
- `.env.qa.example` — illustrative, incomplete Compose environment template;
  it contains placeholders and is not a ready-to-run configuration.
- `start.bat` / `start.sh` — choose a Home Assistant image and start the QA
  Compose services.
- `API-Automation/` — pytest API test suite and configuration.
- `UIAutomation/` and `tests/` — Selenium-based UI automation.
- `DataBaseSchema/DATABASE_SCHEMA_v1.md` — documented application database
  schema.
- `DataBaseSchema/FIREMEX_ROUTES_v1.md` — frontend route/access summary.
- `.github/workflows/qa-deploy.yml` — current deployment placeholder.
