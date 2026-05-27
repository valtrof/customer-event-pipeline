# customer-event-pipeline

KFP pipeline on Vertex AI that extracts Chicago taxi trip data from BigQuery, engineers features, and trains a scikit-learn LinearRegression model.

## Pipeline steps

```
BigQuery (chicago_taxi_trips)
        │
        ▼
  extract_component   →  CSV artifact
        │
        ▼
  transform_component →  Dataset artifact (trip_duration_min, avg_fare_per_mile, …)
        │
        ▼
  train_component     →  Model artifact + Metrics (MAE / RMSE / R²)
```

## Local setup

```bash
pip install -r requirements.txt
```

## Compile pipeline

```bash
python pipeline.py                        # writes pipeline.yaml
python pipeline.py --output my.yaml       # custom output path
```

## Submit to Vertex AI

```bash
python submit.py \
  --project   my-gcp-project \
  --region    us-central1 \
  --pipeline-root gs://my-bucket/pipeline-root
```

Optional flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--row-limit` | 50000 | Rows pulled from BigQuery |
| `--target-col` | fare | Regression target |
| `--test-size` | 0.2 | Train/test split ratio |
| `--service-account` | — | SA email for the pipeline job |
| `--no-compile` | false | Skip recompilation, use existing YAML |
| `--sync` | false | Block until the run finishes |

## Docker

```bash
docker build -t customer-event-pipeline .

# compile inside the container
docker run --rm \
  -v $PWD:/app/out \
  customer-event-pipeline \
  pipeline.py --output /app/out/pipeline.yaml

# submit
docker run --rm \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json \
  -v /path/to/sa.json:/secrets/sa.json \
  customer-event-pipeline \
  submit.py --project my-gcp-project --pipeline-root gs://my-bucket/pipeline-root
```

## Prerequisites

- GCP project with Vertex AI Pipelines and BigQuery APIs enabled
- A GCS bucket for pipeline artifacts
- ADC or a service account with `roles/bigquery.dataViewer`, `roles/aiplatform.user`, and `roles/storage.objectAdmin`
