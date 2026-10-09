from pathlib import Path

import joblib
import mysql.connector
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "outputs"
MODEL_DIR = BASE_DIR / "models"

OUTPUT_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)


# =========================================================
# MYSQL CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "sales_intelligence"
}


# =========================================================
# FEATURE COLUMNS
# =========================================================

FEATURE_COLUMNS = [
    "time_index",
    "year",
    "month",
    "quarter",
    "month_sin",
    "month_cos"
]


# =========================================================
# LOAD MONTHLY SALES
# =========================================================

def load_monthly_sales(connection):

    query = """
        SELECT
            Month,
            TotalSales
        FROM monthly_sales_view
        ORDER BY Month
    """

    cursor = connection.cursor(dictionary=True)

    cursor.execute(query)

    rows = cursor.fetchall()

    cursor.close()

    return pd.DataFrame(rows)


# =========================================================
# CREATE TIME FEATURES
# =========================================================

def create_features(df):

    df = df.copy()

    df["Month"] = pd.to_datetime(
        df["Month"]
    )

    df["TotalSales"] = pd.to_numeric(
        df["TotalSales"]
    )

    df = df.sort_values(
        "Month"
    ).reset_index(drop=True)

    # Sequential time number
    df["time_index"] = np.arange(
        len(df)
    )

    # Year
    df["year"] = (
        df["Month"].dt.year
    )

    # Month number
    df["month"] = (
        df["Month"].dt.month
    )

    # Quarter
    df["quarter"] = (
        df["Month"].dt.quarter
    )

    # Cyclic month features
    df["month_sin"] = np.sin(
        2 * np.pi * df["month"] / 12
    )

    df["month_cos"] = np.cos(
        2 * np.pi * df["month"] / 12
    )

    return df


# =========================================================
# CALCULATE MAE AND RMSE
# =========================================================

def calculate_metrics(actual, predicted):

    mae = mean_absolute_error(
        actual,
        predicted
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            predicted
        )
    )

    return mae, rmse


# =========================================================
# SAVE FORECAST TO MYSQL
# =========================================================

def save_forecast_to_database(
    connection,
    forecast_df
):

    cursor = connection.cursor()

    # -----------------------------------------------------
    # CREATE TABLE
    # -----------------------------------------------------

    create_table_query = """
        CREATE TABLE IF NOT EXISTS sales_forecasts (

            ForecastID INT AUTO_INCREMENT PRIMARY KEY,

            ForecastMonth DATE NOT NULL UNIQUE,

            PredictedSales DECIMAL(14,2) NOT NULL,

            ModelName VARCHAR(100) NOT NULL,

            CreatedAt TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP
        )
    """

    cursor.execute(
        create_table_query
    )

    # -----------------------------------------------------
    # CLEAR PREVIOUS FORECAST
    # -----------------------------------------------------

    cursor.execute(
        "DELETE FROM sales_forecasts"
    )

    # -----------------------------------------------------
    # INSERT NEW FORECAST
    # -----------------------------------------------------

    insert_query = """
        INSERT INTO sales_forecasts (
            ForecastMonth,
            PredictedSales,
            ModelName
        )
        VALUES (
            %s,
            %s,
            %s
        )
    """

    for _, row in forecast_df.iterrows():

        cursor.execute(
            insert_query,
            (
                row["ForecastMonth"].date(),
                float(row["PredictedSales"]),
                str(row["ModelName"])
            )
        )

    connection.commit()

    cursor.close()


# =========================================================
# CREATE FORECAST GRAPH
# =========================================================

def create_forecast_plot(
    monthly,
    test_predictions,
    future_forecast,
    best_model_name
):

    plt.figure(
        figsize=(12, 6)
    )

    # -----------------------------------------------------
    # ACTUAL SALES
    # -----------------------------------------------------

    plt.plot(
        monthly["Month"],
        monthly["TotalSales"],
        marker="o",
        label="Actual Sales"
    )

    # -----------------------------------------------------
    # TEST PREDICTIONS
    # -----------------------------------------------------

    plt.plot(
        test_predictions["Month"],
        test_predictions[best_model_name],
        marker="o",
        label=f"{best_model_name} Test Prediction"
    )

    # -----------------------------------------------------
    # FUTURE FORECAST
    # -----------------------------------------------------

    plt.plot(
        future_forecast["ForecastMonth"],
        future_forecast["PredictedSales"],
        marker="o",
        linestyle="--",
        label="Future Forecast"
    )

    plt.title(
        "Monthly Sales Forecast"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Sales"
    )

    plt.legend()

    plt.grid(
        True
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "sales_forecast.png",
        dpi=150
    )

    plt.close()


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print("=" * 60)
    print("SALES FORECASTING")
    print("=" * 60)

    connection = None

    try:

        # -------------------------------------------------
        # CONNECT TO MYSQL
        # -------------------------------------------------

        print(
            "\nConnecting to MySQL..."
        )

        connection = mysql.connector.connect(
            **DB_CONFIG
        )

        print(
            "Connected successfully."
        )

        # -------------------------------------------------
        # LOAD MONTHLY SALES
        # -------------------------------------------------

        print(
            "\nLoading monthly sales..."
        )

        monthly = load_monthly_sales(
            connection
        )

        if monthly.empty:

            print(
                "No monthly sales data found."
            )

            return

        print(
            f"Months available: {len(monthly)}"
        )

        if len(monthly) < 12:

            print(
                "At least 12 months of data "
                "are required for forecasting."
            )

            return

        # -------------------------------------------------
        # CREATE FEATURES
        # -------------------------------------------------

        print(
            "\nCreating time-based features..."
        )

        monthly = create_features(
            monthly
        )

        # -------------------------------------------------
        # INPUT AND TARGET
        # -------------------------------------------------

        X = monthly[
            FEATURE_COLUMNS
        ]

        y = monthly[
            "TotalSales"
        ]

        # -------------------------------------------------
        # CHRONOLOGICAL TRAIN/TEST SPLIT
        # -------------------------------------------------

        train_size = int(
            len(monthly) * 0.80
        )

        train = monthly.iloc[
            :train_size
        ]

        test = monthly.iloc[
            train_size:
        ]

        X_train = train[
            FEATURE_COLUMNS
        ]

        y_train = train[
            "TotalSales"
        ]

        X_test = test[
            FEATURE_COLUMNS
        ]

        y_test = test[
            "TotalSales"
        ]

        print(
            f"\nTraining months: {len(train)}"
        )

        print(
            f"Testing months: {len(test)}"
        )

        # =================================================
        # BASELINE
        # =================================================

        print(
            "\nCalculating previous-month baseline..."
        )

        baseline_predictions = (
            monthly["TotalSales"]
            .shift(1)
            .iloc[train_size:]
            .values
        )

        baseline_mae, baseline_rmse = (
            calculate_metrics(
                y_test,
                baseline_predictions
            )
        )

        # =================================================
        # LINEAR REGRESSION
        # =================================================

        print(
            "\nTraining Linear Regression..."
        )

        linear_model = LinearRegression()

        linear_model.fit(
            X_train,
            y_train
        )

        linear_predictions = (
            linear_model.predict(
                X_test
            )
        )

        # Sales cannot be negative
        linear_predictions = np.maximum(
            linear_predictions,
            0
        )

        linear_mae, linear_rmse = (
            calculate_metrics(
                y_test,
                linear_predictions
            )
        )

        # =================================================
        # RANDOM FOREST
        # =================================================

        print(
            "\nTraining Random Forest..."
        )

        random_forest = RandomForestRegressor(
            n_estimators=300,
            random_state=42,
            min_samples_leaf=2,
            n_jobs=-1
        )

        random_forest.fit(
            X_train,
            y_train
        )

        rf_predictions = (
            random_forest.predict(
                X_test
            )
        )

        # Sales cannot be negative
        rf_predictions = np.maximum(
            rf_predictions,
            0
        )

        rf_mae, rf_rmse = (
            calculate_metrics(
                y_test,
                rf_predictions
            )
        )

        # =================================================
        # MODEL COMPARISON
        # =================================================

        metrics = pd.DataFrame([

            {
                "Model": "Baseline",
                "MAE": round(
                    baseline_mae,
                    2
                ),
                "RMSE": round(
                    baseline_rmse,
                    2
                )
            },

            {
                "Model": "Linear Regression",
                "MAE": round(
                    linear_mae,
                    2
                ),
                "RMSE": round(
                    linear_rmse,
                    2
                )
            },

            {
                "Model": "Random Forest",
                "MAE": round(
                    rf_mae,
                    2
                ),
                "RMSE": round(
                    rf_rmse,
                    2
                )
            }
        ])

        print(
            "\nModel Evaluation:"
        )

        print(
            metrics.to_string(
                index=False
            )
        )

        # Save metrics
        metrics.to_csv(
            OUTPUT_DIR / "forecast_metrics.csv",
            index=False
        )

        # =================================================
        # SELECT MODEL
        # =================================================

        model_scores = {

            "Linear Regression":
                linear_rmse,

            "Random Forest":
                rf_rmse
        }

        best_model_name = min(
            model_scores,
            key=model_scores.get
        )

        if best_model_name == "Linear Regression":

            best_model = linear_model

        else:

            best_model = random_forest

        print(
            f"\nSelected forecasting model: "
            f"{best_model_name}"
        )

        # =================================================
        # TEST PREDICTIONS
        # =================================================

        test_predictions = pd.DataFrame({

            "Month":
                test["Month"].values,

            "ActualSales":
                y_test.values,

            "Baseline":
                baseline_predictions,

            "Linear Regression":
                linear_predictions,

            "Random Forest":
                rf_predictions
        })

        test_predictions.to_csv(
            OUTPUT_DIR / "test_predictions.csv",
            index=False
        )

        # =================================================
        # TRAIN SELECTED MODEL ON ALL DATA
        # =================================================

        print(
            "\nTraining selected model "
            "using complete historical data..."
        )

        best_model.fit(
            X,
            y
        )

        # =================================================
        # CREATE FUTURE MONTHS
        # =================================================

        last_month = monthly[
            "Month"
        ].max()

        future_dates = pd.date_range(

            start=(
                last_month
                + pd.offsets.MonthBegin(1)
            ),

            periods=6,

            freq="MS"
        )

        future = pd.DataFrame({

            "Month":
                future_dates
        })

        # -------------------------------------------------
        # FUTURE FEATURES
        # -------------------------------------------------

        future["time_index"] = np.arange(

            len(monthly),

            len(monthly) + len(future)
        )

        future["year"] = (
            future["Month"].dt.year
        )

        future["month"] = (
            future["Month"].dt.month
        )

        future["quarter"] = (
            future["Month"].dt.quarter
        )

        future["month_sin"] = np.sin(
            2
            * np.pi
            * future["month"]
            / 12
        )

        future["month_cos"] = np.cos(
            2
            * np.pi
            * future["month"]
            / 12
        )

        # -------------------------------------------------
        # PREDICT FUTURE SALES
        # -------------------------------------------------

        future_predictions = (
            best_model.predict(
                future[FEATURE_COLUMNS]
            )
        )

        future_predictions = np.maximum(
            future_predictions,
            0
        )

        future_forecast = pd.DataFrame({

            "ForecastMonth":
                future["Month"],

            "PredictedSales":
                future_predictions,

            "ModelName":
                best_model_name
        })

        # =================================================
        # SAVE FUTURE FORECAST
        # =================================================

        future_forecast.to_csv(
            OUTPUT_DIR / "future_sales_forecast.csv",
            index=False
        )

        # =================================================
        # SAVE MODEL
        # =================================================

        model_data = {

            "model":
                best_model,

            "feature_columns":
                FEATURE_COLUMNS,

            "model_name":
                best_model_name
        }

        joblib.dump(
            model_data,
            MODEL_DIR / "sales_forecasting_model.joblib"
        )

        # =================================================
        # SAVE FORECAST TO MYSQL
        # =================================================

        print(
            "\nSaving forecast to MySQL..."
        )

        save_forecast_to_database(
            connection,
            future_forecast
        )

        # =================================================
        # CREATE GRAPH
        # =================================================

        create_forecast_plot(

            monthly,

            test_predictions,

            future_forecast,

            best_model_name
        )

        # =================================================
        # DISPLAY FUTURE FORECAST
        # =================================================

        print(
            "\nFuture Sales Forecast:"
        )

        print(
            future_forecast.to_string(
                index=False
            )
        )

        # =================================================
        # OUTPUT FILES
        # =================================================

        print(
            "\nFiles created:"
        )

        print(
            " - ml/outputs/forecast_metrics.csv"
        )

        print(
            " - ml/outputs/test_predictions.csv"
        )

        print(
            " - ml/outputs/future_sales_forecast.csv"
        )

        print(
            " - ml/outputs/sales_forecast.png"
        )

        print(
            " - ml/models/sales_forecasting_model.joblib"
        )

        print(
            "\nSales forecasting completed successfully."
        )

    except mysql.connector.Error as error:

        print(
            "\nMySQL ERROR:"
        )

        print(error)

    except Exception as error:

        print(
            "\nERROR:"
        )

        print(error)

    finally:

        if (
            connection is not None
            and connection.is_connected()
        ):

            connection.close()

            print(
                "\nMySQL connection closed."
            )


# =========================================================
# PROGRAM START
# =========================================================

if __name__ == "__main__":
    main()