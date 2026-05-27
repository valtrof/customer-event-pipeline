from kfp.dsl import component, Input, Output, Dataset, Model, Metrics


@component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "pandas>=2.2.0",
        "scikit-learn>=1.5.0",
        "joblib>=1.4.0",
    ],
)
def train_component(
    dataset: Input[Dataset],
    model_artifact: Output[Model],
    metrics_artifact: Output[Metrics],
    target_col: str = "fare",
    test_size: float = 0.2,
    random_state: int = 42,
) -> None:
    import json
    import joblib
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    import math

    df = pd.read_csv(dataset.path)

    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols].fillna(0)
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("regressor", LinearRegression()),
    ])
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"MAE={mae:.4f}  RMSE={rmse:.4f}  R2={r2:.4f}")

    metrics_artifact.log_metric("mae", mae)
    metrics_artifact.log_metric("rmse", rmse)
    metrics_artifact.log_metric("r2", r2)
    metrics_artifact.log_metric("train_rows", len(X_train))
    metrics_artifact.log_metric("test_rows", len(X_test))

    joblib.dump(pipe, model_artifact.path)

    model_artifact.metadata["framework"] = "scikit-learn"
    model_artifact.metadata["model_type"] = "LinearRegression"
    model_artifact.metadata["feature_columns"] = json.dumps(feature_cols)
    model_artifact.metadata["target_column"] = target_col
    model_artifact.metadata["mae"] = mae
    model_artifact.metadata["rmse"] = rmse
    model_artifact.metadata["r2"] = r2
