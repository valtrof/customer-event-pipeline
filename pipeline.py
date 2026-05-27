"""Compile the customer-event pipeline to YAML."""
import argparse

import kfp
from kfp import dsl
from kfp.compiler import Compiler

from components.extract_component import extract_component
from components.transform_component import transform_component
from components.train_component import train_component


@dsl.pipeline(
    name="customer-event-pipeline",
    description="Extract Chicago taxi data -> feature engineering -> LinearRegression training",
)
def customer_event_pipeline(
    project: str,
    row_limit: int = 50000,
    target_col: str = "fare",
    test_size: float = 0.2,
):
    extract_task = extract_component(
        project=project,
        row_limit=row_limit,
    )
    extract_task.set_display_name("Extract from BigQuery")

    transform_task = transform_component(
        input_csv=extract_task.outputs["output_csv"],
    )
    transform_task.set_display_name("Transform & Feature Engineering")
    transform_task.after(extract_task)

    train_task = train_component(
        dataset=transform_task.outputs["output_dataset"],
        target_col=target_col,
        test_size=test_size,
    )
    train_task.set_display_name("Train LinearRegression")
    train_task.after(transform_task)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile KFP pipeline to YAML")
    parser.add_argument("--output", default="pipeline.yaml", help="Output YAML path")
    args = parser.parse_args()

    Compiler().compile(
        pipeline_func=customer_event_pipeline,
        package_path=args.output,
    )
    print(f"Pipeline compiled to {args.output}")
