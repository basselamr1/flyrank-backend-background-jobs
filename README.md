# FlyRank Backend Background Jobs

A FastAPI backend demonstrating reliable background job processing with **Inngest**.

The project exposes a small report API where report creation returns immediately with `202 Accepted`, while the slow report generation runs asynchronously in the background. It also demonstrates **retries**, **input validation**, and a **scheduled heartbeat** using an Inngest cron trigger.

## Tech Stack

* Python
* FastAPI
* Inngest Python SDK
* uv
* Inngest Dev Server

---

## How to Run

### 1. Start the API

From the project root:

```powershell
$env:INNGEST_DEV="1"
uv run uvicorn main:app --reload --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

### 2. Start the Inngest Dev Server

Open a **second terminal** in the same project directory:

```powershell
npx inngest-cli@latest dev --no-discovery -u http://localhost:8000/api/inngest
```

The Inngest dashboard will be available at:

```text
http://localhost:8288
```

Keep both terminals running.

---

## API Endpoints

| Method | Endpoint               | Description                           | Response                   |
| ------ | ---------------------- | ------------------------------------- | -------------------------- |
| `GET`  | `/health`              | Checks whether the API is running     | `200 OK`                   |
| `POST` | `/reports`             | Creates a report background job       | `202 Accepted`             |
| `GET`  | `/reports/{report_id}` | Gets the current report status/result | `200 OK` / `404 Not Found` |

### Create a Report

```http
POST /reports
Content-Type: application/json

{
  "topic": "cats"
}
```

The API immediately creates a report with `pending` status and sends a `report/requested` event to Inngest.

### Get Report Status

```http
GET /reports/{report_id}
```

The report initially appears as `pending` and becomes `done` after the background job finishes.

---

## Inngest Functions

| Function      | Trigger                  | Purpose                                                             |
| ------------- | ------------------------ | ------------------------------------------------------------------- |
| `say-hello`   | `test/hello` event       | Demonstrates a basic background function with a 5-second step sleep |
| `make-report` | `report/requested` event | Performs the slow report generation and demonstrates retries        |
| `heartbeat`   | `* * * * *` cron         | Runs every minute and logs pending, done, and failed report counts  |

### `make-report` Retries

The report function is configured with:

```python
retries=2
```

This means one initial attempt plus two retries, for a maximum of **3 attempts**.

When the topic is `"fail"`, the background job intentionally raises an exception so the retry behavior can be observed in the Inngest dashboard.

---

## Proof: Report Creation and Polling

The following demonstrates the complete background-job flow.

### 1. Create the report

```powershell
curl.exe -i -X POST http://localhost:8000/reports -H "Content-Type: application/json" -d "{\"topic\":\"cats\"}"
```

Response:

```text
HTTP/1.1 202 Accepted

{
    "id": "YOUR_REPORT_ID",
    "status": "pending"
}
```

### 2. First poll — report is still processing

```powershell
curl.exe http://localhost:8000/reports/YOUR_REPORT_ID
```

Response:

```json
{
    "id": "YOUR_REPORT_ID",
    "topic": "cats",
    "status": "pending"
}
```

### 3. Second poll — background job completed

After the background job finishes:

```powershell
curl.exe http://localhost:8000/reports/YOUR_REPORT_ID
```

Response:

```json
{
    "id": "YOUR_REPORT_ID",
    "topic": "cats",
    "status": "done",
    "result": "Report about cats is ready."
}
```

This demonstrates that the API request does **not** wait for the slow work to finish. The client receives `202 Accepted` immediately and can poll the report status afterward.

---

## Stage 3 — Retries and Validation

**Invalid input is rejected at the API boundary without creating a job, while retryable failures during background execution are retried by Inngest.**

A missing topic returns `400 Bad Request` before an Inngest event is sent.

A report with the topic `"fail"` intentionally fails and demonstrates the configured three total attempts in the Inngest dashboard.

---

## Stage 4 — Scheduled Heartbeat

**The heartbeat uses an Inngest cron trigger to periodically monitor the number of pending, done, and failed reports without requiring an API request or event.**

The development schedule is:

```text
* * * * *
```

which runs every minute.

The heartbeat logs messages such as:

```text
Heartbeat: pending=0, done=1, failed=0
```

The required cron expressions are:

```text
Every day at 08:00:
0 8 * * *

Every Sunday at 22:00:
0 22 * * 0
```

---

## Dashboard Proof

The Inngest dashboard should show the registered functions and their executions, including the background report runs, retry attempts, and scheduled heartbeat executions.

> **Screenshot:** 


(screenshots/Dashboard.png)

The screenshot should clearly show the **Functions/Run history** with runs for:

* `make-report`
* `heartbeat`
* `say-hello` (if triggered)

For Stage 3, the dashboard should also show the failed `"fail"` report with its retry attempts.

---

## Project Structure

```text
flyrank-backend-background-jobs/
│
├── main.py
├── pyproject.toml
├── uv.lock
├── README.md
└── .gitignore
```

---


