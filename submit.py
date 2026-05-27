"""Submit the compiled pipeline YAML to Vertex AI Pipelines."""
import argparse
import os
import subprocess
import sys
from datetime import datetime


def compile_pipeline(output_path: str) -> None:
    result = subprocess.run(
        [sys.executable, "pipeline.py", "--output", output_path],
        check=True,
    )


def submit(
    project: str,
    region: str,
    pipeline_root: str,
    service_account: str | None,
    row_limit: int,
    target_col: str,
    test_size: float,
    pipeline_yaml: str,
    sync: bool,
) -> None:
    from google.cloud import aiplatform

    aiplatform.init(project=project, location=region)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_id = f"customer-event-pipeline-{timestamp}"

    job = aiplatform.PipelineJob(
        display_name=job_id,
        template_path=pipeline_yaml,
        pipeline_root=pipeline_root,
        parameter_values={
            "project": project,
            "row_limit": row_limit,
            "target_col": target_col,
            "test_size": test_size,
        },
        enable_caching=False,
    )

    submit_kwargs = {}
    if service_account:
        submit_kwargs["service_account"] = service_account

    job.submit(**submit_kwargs)
    print(f"Submitted pipeline job: {job.resource_name}")
    print(f"Console URL: {job._dashboard_uri()}")

    if sync:
        job.wait()
        print(f"Pipeline finished with state: {job.state}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit customer-event-pipeline to Vertex AI")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--region", default="us-central1", help="Vertex AI region")
    parser.add_argument(
        "--pipeline-root",
        required=True,
        help="GCS URI for pipeline artifacts, e.g. gs://my-bucket/pipeline-root",
    )
    parser.add_argument("--service-account", default=None, help="Service account email (optional)")
    parser.add_argument("--row-limit", type=int, default=50000)
    parser.add_argument("--target-col", default="fare")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--pipeline-yaml", default="pipeline.yaml")
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Skip re-compilation (use existing YAML)",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Wait for the pipeline run to complete",
    )
    args = parser.parse_args()

    if not args.no_compile:
        print(f"Compiling pipeline to {args.pipeline_yaml} ...")
        compile_pipeline(args.pipeline_yaml)

    submit(
        project=args.project,
        region=args.region,
        pipeline_root=args.pipeline_root,
        service_account=args.service_account,
        row_limit=args.row_limit,
        target_col=args.target_col,
        test_size=args.test_size,
        pipeline_yaml=args.pipeline_yaml,
        sync=args.sync,
    )


if __name__ == "__main__":
    main()
