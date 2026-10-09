from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)
CORS(app)

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
# DATABASE CONNECTION & HELPER
# =========================================================

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def fetch_all(query, params=None):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

# =========================================================
# HOME & HEALTH CHECK
# =========================================================

@app.route("/")
def home():
    return jsonify({
        "message": "AI Sales Intelligence API",
        "status": "running"
    })

@app.route("/api/health")
def health():
    connection = None
    try:
        connection = get_connection()
        return jsonify({
            "status": "ok",
            "database": "connected"
        })
    except Exception as error:
        return jsonify({
            "status": "error",
            "database": "not connected",
            "message": str(error)
        }), 500
    finally:
        if connection is not None:
            connection.close()

# =========================================================
# DASHBOARD KPIs
# =========================================================

@app.route("/api/dashboard/kpis")
def dashboard_kpis():
    try:
        query = """
            SELECT
                ROUND(SUM(Sales), 2) AS total_sales,
                ROUND(SUM(Profit), 2) AS total_profit,
                SUM(Quantity) AS total_quantity,
                COUNT(DISTINCT OrderID) AS total_orders
            FROM order_details
        """
        rows = fetch_all(query)
        return jsonify(rows[0] if rows else {})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# SALES BY CATEGORY
# =========================================================

@app.route("/api/sales/category")
def sales_by_category():
    try:
        query = """
            SELECT
                c.CategoryName AS category,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit
            FROM order_details od
            INNER JOIN products p ON od.ProductKey = p.ProductKey
            INNER JOIN subcategories sc ON p.SubCategoryID = sc.SubCategoryID
            INNER JOIN categories c ON sc.CategoryID = c.CategoryID
            GROUP BY c.CategoryID, c.CategoryName
            ORDER BY sales DESC
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# SALES BY REGION
# =========================================================

@app.route("/api/sales/region")
def sales_by_region():
    try:
        query = """
            SELECT
                a.Region AS region,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit
            FROM order_details od
            INNER JOIN orders o ON od.OrderID = o.OrderID
            INNER JOIN addresses a ON o.AddressID = a.AddressID
            GROUP BY a.Region
            ORDER BY sales DESC
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# MONTHLY SALES
# =========================================================

@app.route("/api/sales/monthly")
def monthly_sales():
    try:
        query = """
            SELECT
                Month AS month,
                ROUND(TotalSales, 2) AS sales,
                ROUND(TotalProfit, 2) AS profit
            FROM monthly_sales_view
            ORDER BY Month
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# SALES BY YEAR
# =========================================================

@app.route("/api/sales/yearly")
def yearly_sales():
    try:
        query = """
            SELECT
                YEAR(o.OrderDate) AS year,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit
            FROM orders o
            INNER JOIN order_details od ON o.OrderID = od.OrderID
            GROUP BY YEAR(o.OrderDate)
            ORDER BY year
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# TOP PRODUCTS
# =========================================================

@app.route("/api/products/top")
def top_products():
    try:
        limit = request.args.get("limit", default=10, type=int)
        if limit < 1 or limit > 50:
            limit = 10

        query = f"""
            SELECT
                p.ProductName AS product,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit,
                SUM(od.Quantity) AS quantity
            FROM order_details od
            INNER JOIN products p ON od.ProductKey = p.ProductKey
            GROUP BY p.ProductKey, p.ProductName
            ORDER BY sales DESC
            LIMIT {limit}
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# TOP CUSTOMERS
# =========================================================

@app.route("/api/customers/top")
def top_customers():
    try:
        limit = request.args.get("limit", default=10, type=int)
        if limit < 1 or limit > 50:
            limit = 10

        query = f"""
            SELECT
                c.CustomerID AS customer_id,
                c.CustomerName AS customer,
                c.Segment AS customer_segment,
                COUNT(DISTINCT o.OrderID) AS orders,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit
            FROM customers c
            INNER JOIN orders o ON c.CustomerID = o.CustomerID
            INNER JOIN order_details od ON o.OrderID = od.OrderID
            GROUP BY c.CustomerID, c.CustomerName, c.Segment
            ORDER BY sales DESC
            LIMIT {limit}
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# CUSTOMER SEGMENTS
# =========================================================

@app.route("/api/customers/segments")
def customer_segments():
    try:
        query = """
            SELECT
                SegmentName AS segment,
                COUNT(*) AS customers
            FROM customer_segments
            GROUP BY SegmentName
            ORDER BY customers DESC
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/customers/segments/details")
def customer_segment_details():
    try:
        query = """
            SELECT
                CustomerID AS customer_id,
                Recency AS recency,
                Frequency AS frequency,
                Monetary AS monetary,
                RFMScore AS rfm_score,
                ClusterID AS cluster_id,
                SegmentName AS segment
            FROM customer_segments
            ORDER BY RFMScore DESC
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/customers/segments/summary")
def customer_segment_summary():
    try:
        query = """
            SELECT
                SegmentName AS segment,
                COUNT(*) AS customers,
                
                -- Round days to whole integer (0 decimals)
                ROUND(AVG(Recency), 0) AS avg_recency,
                
                -- Round order frequency to 1 decimal place
                ROUND(AVG(Frequency), 1) AS avg_frequency,
                
                ROUND(AVG(Monetary), 2) AS avg_monetary
            FROM customer_segments
            GROUP BY SegmentName
            ORDER BY customers DESC
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# SALES FORECAST
# =========================================================

@app.route("/api/forecast")
def sales_forecast():
    try:
        query = """
            SELECT
                ForecastMonth AS month,
                ROUND(PredictedSales, 2) AS predicted_sales,
                ModelName AS model
            FROM sales_forecasts
            ORDER BY ForecastMonth
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/forecast/metrics")
def forecast_metrics():
    return jsonify({
        "message": "Forecast metrics are available in ml/outputs/forecast_metrics.csv",
        "status": "available"
    })

# =========================================================
# CATEGORY PERFORMANCE
# =========================================================

@app.route("/api/category/performance")
def category_performance():
    try:
        query = """
            SELECT
                c.CategoryName AS category,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit,
                ROUND((SUM(od.Profit) / NULLIF(SUM(od.Sales), 0)) * 100, 2) AS profit_margin
            FROM order_details od
            INNER JOIN products p ON od.ProductKey = p.ProductKey
            INNER JOIN subcategories sc ON p.SubCategoryID = sc.SubCategoryID
            INNER JOIN categories c ON sc.CategoryID = c.CategoryID
            GROUP BY c.CategoryID, c.CategoryName
            ORDER BY sales DESC
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# SHIP MODE ANALYSIS
# =========================================================

@app.route("/api/shipping")
def shipping_analysis():
    try:
        query = """
            SELECT
                sm.ShipModeName AS ship_mode,
                COUNT(DISTINCT o.OrderID) AS orders,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit
            FROM ship_modes sm
            INNER JOIN orders o ON sm.ShipModeID = o.ShipModeID
            INNER JOIN order_details od ON o.OrderID = od.OrderID
            GROUP BY sm.ShipModeID, sm.ShipModeName
            ORDER BY sales DESC
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# PRODUCT SUBCATEGORY ANALYSIS
# =========================================================

@app.route("/api/subcategories")
def subcategory_analysis():
    try:
        query = """
            SELECT
                sc.SubCategoryName AS subcategory,
                c.CategoryName AS category,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit
            FROM order_details od
            INNER JOIN products p ON od.ProductKey = p.ProductKey
            INNER JOIN subcategories sc ON p.SubCategoryID = sc.SubCategoryID
            INNER JOIN categories c ON sc.CategoryID = c.CategoryID
            GROUP BY sc.SubCategoryID, sc.SubCategoryName, c.CategoryName
            ORDER BY sales DESC
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# LOSS-MAKING PRODUCTS
# =========================================================

@app.route("/api/products/loss-making")
def loss_making_products():
    try:
        query = """
            SELECT
                p.ProductName AS product,
                ROUND(SUM(od.Sales), 2) AS sales,
                ROUND(SUM(od.Profit), 2) AS profit
            FROM order_details od
            INNER JOIN products p ON od.ProductKey = p.ProductKey
            GROUP BY p.ProductKey, p.ProductName
            HAVING SUM(od.Profit) < 0
            ORDER BY profit ASC
            LIMIT 20
        """
        rows = fetch_all(query)
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# RUN FLASK
# =========================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )