from kfp.dsl import component, Output, Dataset


@component(
    base_image="python:3.11-slim",
    packages_to_install=["google-cloud-bigquery[pandas]>=3.25.0", "pyarrow>=16.0.0"],
)
def extract_component(
    project: str,
    output_csv: Output[Dataset],
    row_limit: int = 50000,
) -> None:
    from google.cloud import bigquery

    client = bigquery.Client(project=project)

    query = f"""
        SELECT
            taxi_id,
            trip_seconds,
            trip_miles,
            fare,
            tips,
            tolls,
            extras,
            trip_total,
            pickup_community_area,
            dropoff_community_area
        FROM `bigquery-public-data.chicago_taxi_trips.taxi_trips`
        WHERE trip_seconds IS NOT NULL
          AND trip_miles IS NOT NULL
          AND fare IS NOT NULL
          AND fare > 0
          AND trip_seconds > 0
          AND trip_miles > 0
        LIMIT {row_limit}
    """

    df = client.query(query).to_dataframe()
    df.to_csv(output_csv.path, index=False)
    print(f"Extracted {len(df)} rows to {output_csv.path}")
