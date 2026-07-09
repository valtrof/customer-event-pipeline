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

## Design decisions

**Three typed components instead of one training script.** Each stage exchanges typed KFP artifacts (`Dataset`, `Model`, `Metrics`) rather than file paths. The DAG becomes self-documenting, Vertex AI tracks lineage per artifact, and any stage can be rerun or cached independently — the reason KFP exists over a cron job running a script.

**`packages_to_install` on a slim base image, not custom images per component.** Tradeoff: slower container cold-start per run vs. zero image-registry maintenance. For a pipeline that runs on demand rather than on a tight schedule, build simplicity wins.

**Scaler lives inside the model artifact.** `StandardScaler` + `LinearRegression` are bundled in a single sklearn `Pipeline` and serialized together, so serving can never apply different preprocessing than training — the cheapest possible insurance against training/serving skew.

**Metrics logged twice, on purpose.** MAE/RMSE/R² go to the `Metrics` artifact (comparable across runs in the Vertex UI) *and* into the model's metadata alongside feature columns and target (the artifact is self-describing — a consumer needs no side channel to know what the model expects).

**Compile and submit are separate steps.** `pipeline.py` compiles the definition to YAML; `submit.py` parameterizes a run (`row_limit`, `target_col`, `test_size`). Compile once, submit many — and the YAML is diffable in code review.

**Known simplification:** features are imputed with `fillna(0)` and the model is deliberately simple — this project demonstrates pipeline engineering (artifacts, lineage, parameterization, packaging), not modeling depth.

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
