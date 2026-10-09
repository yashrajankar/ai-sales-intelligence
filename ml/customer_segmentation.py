from pathlib import Path

import joblib
import mysql.connector
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


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
# GET CUSTOMER RFM DATA
# =========================================================

def get_customer_rfm(connection):

    query = """
        SELECT
            c.CustomerID,
            c.CustomerName,
            c.Segment,

            DATEDIFF(
                (
                    SELECT
                        DATE_ADD(MAX(OrderDate), INTERVAL 1 DAY)
                    FROM orders
                ),
                MAX(o.OrderDate)
            ) AS Recency,

            COUNT(DISTINCT o.OrderID) AS Frequency,

            ROUND(SUM(od.Sales), 2) AS Monetary

        FROM customers c

        INNER JOIN orders o
            ON c.CustomerID = o.CustomerID

        INNER JOIN order_details od
            ON o.OrderID = od.OrderID

        GROUP BY
            c.CustomerID,
            c.CustomerName,
            c.Segment

        ORDER BY
            c.CustomerID
    """

    cursor = connection.cursor(dictionary=True)

    cursor.execute(query)

    rows = cursor.fetchall()

    cursor.close()

    return pd.DataFrame(rows)


# =========================================================
# CREATE RFM SCORES
# =========================================================

def create_rfm_scores(df):

    # Recency:
    # Lower number of days is better.
    # Therefore the score is reversed.

    df["RecencyScore"] = pd.qcut(
        df["Recency"].rank(method="first"),
        5,
        labels=[5, 4, 3, 2, 1]
    ).astype(int)

    # Frequency:
    # Higher number of orders is better.

    df["FrequencyScore"] = pd.qcut(
        df["Frequency"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    # Monetary:
    # Higher total sales is better.

    df["MonetaryScore"] = pd.qcut(
        df["Monetary"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    # Overall RFM score

    df["RFMScore"] = (
        df["RecencyScore"]
        + df["FrequencyScore"]
        + df["MonetaryScore"]
    )

    return df


# =========================================================
# CREATE CUSTOMER SEGMENT NAMES
# =========================================================

def create_segment_names(df):

    def get_segment(score):

        if score >= 13:
            return "Champions"

        elif score >= 10:
            return "Loyal Customers"

        elif score >= 7:
            return "Potential Customers"

        else:
            return "Needs Attention"

    df["SegmentName"] = df["RFMScore"].apply(
        get_segment
    )

    return df


# =========================================================
# FIND BEST NUMBER OF CLUSTERS
# =========================================================

def find_best_k(scaled_data, max_k=6):

    results = []

    max_allowed_k = min(
        max_k,
        len(scaled_data) - 1
    )

    for k in range(
        2,
        max_allowed_k + 1
    ):

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )

        labels = model.fit_predict(
            scaled_data
        )

        score = silhouette_score(
            scaled_data,
            labels
        )

        results.append({
            "K": k,
            "SilhouetteScore": round(
                score,
                4
            )
        })

        print(
            f"K = {k} | "
            f"Silhouette Score = {score:.4f}"
        )

    result_df = pd.DataFrame(
        results
    )

    best_row = result_df.loc[
        result_df["SilhouetteScore"].idxmax()
    ]

    best_k = int(
        best_row["K"]
    )

    return best_k, result_df


# =========================================================
# SAVE CUSTOMER SEGMENTS TO MYSQL
# =========================================================

def save_segments_to_database(
    connection,
    df
):

    cursor = connection.cursor()

    # -----------------------------------------------------
    # CREATE TABLE
    # -----------------------------------------------------

    create_table = """
        CREATE TABLE IF NOT EXISTS customer_segments (

            CustomerID VARCHAR(20) PRIMARY KEY,

            Recency INT NOT NULL,

            Frequency INT NOT NULL,

            Monetary DECIMAL(12,2) NOT NULL,

            RecencyScore INT NOT NULL,

            FrequencyScore INT NOT NULL,

            MonetaryScore INT NOT NULL,

            RFMScore INT NOT NULL,

            ClusterID INT NOT NULL,

            SegmentName VARCHAR(50) NOT NULL,

            UpdatedAt TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,

            FOREIGN KEY (CustomerID)
                REFERENCES customers(CustomerID)
        )
    """

    cursor.execute(
        create_table
    )

    # -----------------------------------------------------
    # REMOVE OLD RESULTS
    # -----------------------------------------------------

    cursor.execute(
        "DELETE FROM customer_segments"
    )

    # -----------------------------------------------------
    # INSERT NEW RESULTS
    # -----------------------------------------------------

    insert_query = """
        INSERT INTO customer_segments (

            CustomerID,
            Recency,
            Frequency,
            Monetary,
            RecencyScore,
            FrequencyScore,
            MonetaryScore,
            RFMScore,
            ClusterID,
            SegmentName

        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """

    for _, row in df.iterrows():

        values = (

            str(row["CustomerID"]),

            int(row["Recency"]),

            int(row["Frequency"]),

            float(row["Monetary"]),

            int(row["RecencyScore"]),

            int(row["FrequencyScore"]),

            int(row["MonetaryScore"]),

            int(row["RFMScore"]),

            int(row["ClusterID"]),

            str(row["SegmentName"])
        )

        cursor.execute(
            insert_query,
            values
        )

    connection.commit()

    cursor.close()


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print("=" * 60)
    print("CUSTOMER INTELLIGENCE - RFM + K-MEANS")
    print("=" * 60)

    connection = None

    try:

        # -------------------------------------------------
        # CONNECT TO MYSQL
        # -------------------------------------------------

        print("\nConnecting to MySQL...")

        connection = mysql.connector.connect(
            **DB_CONFIG
        )

        print(
            "Connected successfully."
        )

        # -------------------------------------------------
        # LOAD CUSTOMER DATA
        # -------------------------------------------------

        print(
            "\nLoading customer transaction data..."
        )

        df = get_customer_rfm(
            connection
        )

        if df.empty:

            print(
                "No customer data found."
            )

            return

        print(
            f"Customers loaded: {len(df)}"
        )

        # -------------------------------------------------
        # DATA TYPE CONVERSION
        # -------------------------------------------------

        df["Recency"] = pd.to_numeric(
            df["Recency"]
        )

        df["Frequency"] = pd.to_numeric(
            df["Frequency"]
        )

        df["Monetary"] = pd.to_numeric(
            df["Monetary"]
        )

        # -------------------------------------------------
        # CREATE RFM SCORES
        # -------------------------------------------------

        print(
            "\nCreating RFM scores..."
        )

        df = create_rfm_scores(
            df
        )

        # -------------------------------------------------
        # CREATE PRESENTATION SEGMENTS
        # -------------------------------------------------

        df = create_segment_names(
            df
        )

        # -------------------------------------------------
        # PREPARE DATA FOR K-MEANS
        # -------------------------------------------------

        rfm_columns = [
            "Recency",
            "Frequency",
            "Monetary"
        ]

        rfm_data = df[
            rfm_columns
        ].copy()

        print(
            "\nScaling RFM data..."
        )

        scaler = StandardScaler()

        scaled_data = scaler.fit_transform(
            rfm_data
        )

        # -------------------------------------------------
        # FIND BEST K
        # -------------------------------------------------

        print(
            "\nFinding suitable number of clusters..."
        )

        best_k, silhouette_results = find_best_k(
            scaled_data
        )

        print(
            f"\nSelected K = {best_k}"
        )

        # -------------------------------------------------
        # SAVE SILHOUETTE SCORES
        # -------------------------------------------------

        silhouette_results.to_csv(
            OUTPUT_DIR / "silhouette_scores.csv",
            index=False
        )

        # -------------------------------------------------
        # TRAIN FINAL K-MEANS
        # -------------------------------------------------

        print(
            "\nTraining K-Means model..."
        )

        kmeans = KMeans(
            n_clusters=best_k,
            random_state=42,
            n_init=10
        )

        df["ClusterID"] = kmeans.fit_predict(
            scaled_data
        )

        # -------------------------------------------------
        # CREATE CLUSTER SUMMARY
        # -------------------------------------------------

        cluster_summary = (
            df.groupby("ClusterID")
            .agg(
                Customers=(
                    "CustomerID",
                    "count"
                ),

                AvgRecency=(
                    "Recency",
                    "mean"
                ),

                AvgFrequency=(
                    "Frequency",
                    "mean"
                ),

                AvgMonetary=(
                    "Monetary",
                    "mean"
                )
            )
            .reset_index()
        )

        cluster_summary[
            [
                "AvgRecency",
                "AvgFrequency",
                "AvgMonetary"
            ]
        ] = cluster_summary[
            [
                "AvgRecency",
                "AvgFrequency",
                "AvgMonetary"
            ]
        ].round(2)

        # -------------------------------------------------
        # SAVE CUSTOMER RESULTS
        # -------------------------------------------------

        df.to_csv(
            OUTPUT_DIR / "customer_segments.csv",
            index=False
        )

        cluster_summary.to_csv(
            OUTPUT_DIR / "cluster_summary.csv",
            index=False
        )

        # -------------------------------------------------
        # SAVE ML MODEL
        # -------------------------------------------------

        model_data = {

            "scaler": scaler,

            "kmeans": kmeans,

            "rfm_columns": rfm_columns,

            "best_k": best_k
        }

        joblib.dump(
            model_data,
            MODEL_DIR
            / "customer_segmentation_model.joblib"
        )

        # -------------------------------------------------
        # SAVE RESULTS TO MYSQL
        # -------------------------------------------------

        print(
            "\nSaving customer segments to MySQL..."
        )

        save_segments_to_database(
            connection,
            df
        )

        # -------------------------------------------------
        # DISPLAY CLUSTER SUMMARY
        # -------------------------------------------------

        print(
            "\nCluster Summary:"
        )

        print(
            cluster_summary.to_string(
                index=False
            )
        )

        # -------------------------------------------------
        # DISPLAY RFM SEGMENT SUMMARY
        # -------------------------------------------------

        print(
            "\nRFM Segment Summary:"
        )

        segment_summary = (
            df["SegmentName"]
            .value_counts()
            .reset_index()
        )

        segment_summary.columns = [
            "SegmentName",
            "Customers"
        ]

        print(
            segment_summary.to_string(
                index=False
            )
        )

        # -------------------------------------------------
        # OUTPUT FILES
        # -------------------------------------------------

        print(
            "\nFiles created:"
        )

        print(
            " - ml/outputs/customer_segments.csv"
        )

        print(
            " - ml/outputs/cluster_summary.csv"
        )

        print(
            " - ml/outputs/silhouette_scores.csv"
        )

        print(
            " - ml/models/customer_segmentation_model.joblib"
        )

        print(
            "\nCustomer segmentation completed successfully."
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