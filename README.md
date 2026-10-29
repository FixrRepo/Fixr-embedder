# Fixr Image Processor

The Fixr Image Processor is a Python worker that consumes report embedding jobs from RabbitMQ. It creates CLIP text and visual embeddings, stores them on the report embedding row created by the Spring service, searches nearby reports, scores visual similarity, and publishes the result back to RabbitMQ.

## Processing flow

1. Spring creates the report and its `report_embedding` row, including the report coordinate, then publishes an embedding request.
2. The worker reads the request from the configured RabbitMQ queue.
3. CLIP generates an optional text embedding from the description, image embeddings for each image URL, and frame embeddings from each video URL.
4. The worker persists the embeddings in PostgreSQL. Existing visual embeddings for that report are replaced, making retries idempotent.
5. PostgreSQL/PostGIS calculates geography distances and filters reports within the configured radius. The incoming and candidate coordinates are compared in SQL; a loaded geometry is not rebound as a query parameter.
6. The worker scores nearby candidates using visual similarity and distance, then publishes a completion event. Processing errors produce a failure event.

Visual similarity is the mean, over incoming visual vectors, of each vector's best cosine match against the candidate's visual vectors. Candidate similarity is:

```text
visual_score * VISUAL_SIMILARITY_SCORE_WEIGHT
+ exp(-distance_meters / EXPONENTIAL_DECAY_RATE)^2
  * DISTANCE_SIMILARITY_SCORE_WEIGHT
```

Reports with no visual embeddings to compare are omitted from the candidate list. Text embeddings are stored but are not currently included in candidate scoring.

## Requirements

- Python 3.14 (the Dockerfile's base image is `python:3.14-slim`)
- PostgreSQL with PostGIS and the schema/tables managed by the Spring service
- RabbitMQ with the request queue and completion exchange already declared and bound
- Network access to the image and video URLs in embedding jobs
- CPU or CUDA-compatible hardware; the worker uses CUDA when PyTorch detects it and otherwise uses CPU

The worker expects Spring to create the report embedding before it processes the corresponding job. Its `report_embedding.id` must match the task's `reportId`, and the row must have a valid `POINT` coordinate in SRID 4326. The worker does not create database tables.

## Configuration

Set these environment variables before starting the worker. Defaults are shown where the code defines one.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | `admin` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5532` | PostgreSQL port |
| `DB_NAME` | `postgres` | PostgreSQL database name |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | RabbitMQ connection URL |
| `FIXR_RABBITMQ_REQUEST_QUEUE` | `embedding.request` | Durable request queue consumed by the worker |
| `FIXR_RABBITMQ_EXCHANGE` | `fixr.exchange` | Existing exchange used to publish completion/failure events |
| `FIXR_RABBITMQ_COMPLETED_ROUTING_KEY` | `embedding.completed` | Completion routing key |
| `FIXR_RABBITMQ_REQUEST_FAILED_ROUTING_KEY` | `embedding.failed` | Failure routing key |
| `DUPLICATE_SEARCH_RADIUS_METERS` | `50` | Nearby candidate search radius in metres |
| `DUPLICATE_CANDIDATE_LIMIT` | `5` | Maximum number of scored candidates published |
| `VISUAL_SIMILARITY_SCORE_WEIGHT` | `0.6` | Visual score contribution weight |
| `DISTANCE_SIMILARITY_SCORE_WEIGHT` | `0.4` | Distance score contribution weight |
| `EXPONENTIAL_DECAY_RATE` | `89` | Distance decay scale in metres |

`REDIS_URL` and `EMBEDDING_RESULT_TTL` are defined for the older Redis result-store code, but the current worker path does not use Redis. Embeddings are written directly to PostgreSQL.

> The exchange setting is named `EMBEDDING_COMPLETED_QUEUE` in the current configuration even though it contains an exchange name. The worker declares it as an existing (passive) exchange; it does not create the exchange or queue.

## Run locally

From the repository root, create and activate a virtual environment, install dependencies, set the environment variables above, and run:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
python main.py
```

CLIP's `ViT-B/32` weights are loaded by `clip.load` when the worker starts. Ensure the environment can retrieve the model weights on first startup.

## RabbitMQ message format

The request queue receives JSON with this shape:

```json
{
  "event": "EMBEDDING_REQUESTED",
  "jobId": "967ed47d-094e-4a82-9912-3c7565d99599",
  "reportId": "e2941bc2-d49b-4414-bb43-09656ffa5099",
  "description": "A report description",
  "media": {
    "images": ["https://example.com/image.jpg"],
    "videos": []
  }
}
```

`reportId` must be a UUID matching the existing report embedding row. Media values are URLs that the worker can access. Video frames are sampled and stored as visual embeddings alongside image embeddings.

On success, the worker publishes to the configured completion routing key:

```json
{
  "event": "EMBEDDING_COMPLETED",
  "jobId": "967ed47d-094e-4a82-9912-3c7565d99599",
  "reportId": "e2941bc2-d49b-4414-bb43-09656ffa5099",
  "status": "COMPLETED",
  "candidates": [
    {
      "reportId": "candidate-report-uuid",
      "visualScore": 0.91,
      "distanceMeters": 12.5,
      "distanceScore": 0.755,
      "similarityScore": 0.848,
      "rank": 1
    }
  ]
}
```

The candidate values above are illustrative. A failure publishes `EMBEDDING_FAILED` to the configured failure routing key, with `jobId`, `reportId`, `status: "FAILED"`, and an `error` message. The worker then re-raises the processing error; `aio-pika`'s `message.process()` context rejects the request message, using its default `requeue=False` behavior. Configure a dead-letter exchange if rejected messages need to be retained for inspection.

## Docker

`compose.yaml` and `Dockerfile` are present, but the current Dockerfile creates a virtual environment and copies `requirements.txt` without installing those dependencies into the environment. As written, the image is not ready to run the worker. Install the requirements in the build stage before using the image, and configure the service's database and RabbitMQ environment before deploying it. The Compose file currently defines only the worker; it does not start PostgreSQL or RabbitMQ.

## Operational notes

- The worker uses `prefetch_count=1`, so each consumer processes one unacknowledged task at a time.
- It requires the completion exchange and request queue to exist already; passive declaration fails if either is missing.
- Failed processing publishes a failure event and then raises the error. Confirm the queue's dead-letter/retry policy to avoid repeatedly processing a permanently invalid task.
- Keep database credentials and broker URLs in deployment secrets or environment configuration; do not commit them to the repository.
