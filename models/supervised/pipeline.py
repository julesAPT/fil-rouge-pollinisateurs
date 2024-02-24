from typing import List

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.experimental import enable_iterative_imputer
from sklearn.feature_selection import SelectFromModel
from sklearn.impute import IterativeImputer, KNNImputer, SimpleImputer
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


class CustomPipeline:
    def __init__(
        self,
        numeric_features: List[str],
        categorical_features: List[str],
        ordinal_features: List[str],
        nominal_features: List[str],
        estimator=RandomForestRegressor(),
    ):
        """
        Initialize the class with the given estimator and feature lists.

        Args:
            numeric_features (List[str]): List of numeric feature names.
            categorical_features (List[str]): List of categorical feature names.
            ordinal_features (List[str]): List of ordinal feature names.
            nominal_features (List[str]): List of nominal feature names.
            estimator: The machine learning estimator to be used.
        """
        self.estimator = estimator
        self.numeric_features = numeric_features
        self.categorical_features = categorical_features
        self.ordinal_features = ordinal_features
        self.nominal_features = nominal_features
        self.pipeline = self._create_pipeline()

    def _create_pipeline(self) -> "Pipeline":
        numeric_pipeline = Pipeline(
            steps=[("scaler", StandardScaler()), ("imputer", KNNImputer(n_neighbors=5))]
        )

        ordinal_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OrdinalEncoder()),
            ]
        )
        nominal_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]
        )

        categorical_pipeline = ColumnTransformer(
            transformers=[
                ("ordinal", ordinal_pipeline, self.ordinal_features),
                ("nominal", nominal_pipeline, self.nominal_features),
            ],
            remainder="drop",
        )

        preprocessor = ColumnTransformer(
            transformers=[
                ("numerical", numeric_pipeline, self.numeric_features),
                ("categorical", categorical_pipeline, self.categorical_features),
            ],
            remainder="drop",
        )

        feature_selector = SelectFromModel(estimator=Ridge())

        estimator = self.estimator

        pipe = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("feature_selector", feature_selector),
                ("estimator", estimator),
            ]
        )
        return pipe

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "CustomPipeline":
        self.pipeline.fit(X, y)
        self.fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> "pd.Series":
        return self.pipeline.predict(X)

    def calculate_feature_importance(self) -> "pd.DataFrame":
        # check if the pipeline has been fitted
        if not (hasattr(self, "fitted")) or not (self.fitted):
            raise ValueError("The pipeline has not been fitted yet.")
        try:
            importance = self.pipeline.named_steps["estimator"].feature_importances_
            feature_names = self.pipeline.steps[0][1].get_feature_names_out()

            feature_importance = pd.DataFrame(
                {"feature": feature_names, "importance (%)": importance * 100}
            ).sort_values("importance (%)", ascending=False)
        except AttributeError:
            feature_importance = pd.DataFrame()
        return feature_importance

    def score(self, X: pd.DataFrame, y: pd.Series) -> float:
        return self.pipeline.score(X, y)

    def get_metrics(self, X: pd.DataFrame, y: pd.Series):
        # return R2, MSE, MAE metrics
        y_pred = self.predict(X)
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)

        print(f"R2: {r2}")
        print(f"MSE: {mse}")
        print(f"MAE: {mae}")

        return r2, mse, mae
