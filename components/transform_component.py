from kfp.dsl import component, Input, Output, Dataset


@component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas>=2.2.0"],
)
def transform_component(
    input_csv: Input[Dataset],
    output_dataset: Output[Dataset],
) -> None:
    import pandas as pd

    df = pd.read_csv(input_csv.path)

    df["trip_duration_min"] = df["trip_seconds"] / 60.0
    df["avg_fare_per_mile"] = df.apply(
        lambda r: r["fare"] / r["trip_miles"] if r["trip_miles"] > 0 else 0.0,
        axis=1,
    )
    df["avg_fare_per_min"] = df.apply(
        lambda r: r["fare"] / r["trip_duration_min"]
        if r["trip_duration_min"] > 0
        else 0.0,
        axis=1,
    )
    df["tip_rate"] = df.apply(
        lambda r: r["tips"] / r["fare"] if r["fare"] > 0 else 0.0, axis=1
    )

    df["pickup_community_area"] = df["pickup_community_area"].fillna(0)
    df["dropoff_community_area"] = df["dropoff_community_area"].fillna(0)

    feature_cols = [
        "trip_duration_min",
        "trip_miles",
        "avg_fare_per_mile",
        "avg_fare_per_min",
        "tip_rate",
        "pickup_community_area",
        "dropoff_community_area",
        "fare",
    ]
    df_out = df[feature_cols].dropna()

    # clip extreme outliers (top 1%)
    for col in ["trip_duration_min", "trip_miles", "avg_fare_per_mile", "avg_fare_per_min"]:
        upper = df_out[col].quantile(0.99)
        df_out = df_out[df_out[col] <= upper]

    df_out.to_csv(output_dataset.path, index=False)
    print(f"Transformed dataset: {len(df_out)} rows, columns: {list(df_out.columns)}")
