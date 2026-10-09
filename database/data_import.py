import os
import sys
import pandas as pd
import mysql.connector
from mysql.connector import Error


# ============================================================
# CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root"
}

DATABASE_NAME = "sales_intelligence"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_PATH = os.path.join(
    BASE_DIR,
    "data",
    "Sample - Superstore.csv"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def create_database():
    """Create the database if it does not exist."""

    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )

        cursor = connection.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}"
        )

        connection.commit()

        print(f"Database checked: {DATABASE_NAME}")

    except Error as error:
        print(f"Database creation error: {error}")
        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


def connect_database():
    """Connect to the sales intelligence database."""

    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DATABASE_NAME
        )

        if connection.is_connected():
            print("Connected successfully.")

        return connection

    except Error as error:
        print(f"Database connection error: {error}")
        raise


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables(connection):
    """Create all project tables."""

    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # CUSTOMERS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                CustomerID VARCHAR(20) PRIMARY KEY,
                CustomerName VARCHAR(100) NOT NULL,
                Segment VARCHAR(30) NOT NULL
            )
        """)

        # ----------------------------------------------------
        # ADDRESSES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                AddressID INT AUTO_INCREMENT PRIMARY KEY,
                Country VARCHAR(100) NOT NULL,
                City VARCHAR(100) NOT NULL,
                State VARCHAR(100) NOT NULL,
                PostalCode VARCHAR(20) NOT NULL,
                Region VARCHAR(50) NOT NULL,
                UNIQUE (
                    Country,
                    City,
                    State,
                    PostalCode,
                    Region
                )
            )
        """)

        # ----------------------------------------------------
        # CATEGORIES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                CategoryID INT AUTO_INCREMENT PRIMARY KEY,
                CategoryName VARCHAR(50) NOT NULL UNIQUE
            )
        """)

        # ----------------------------------------------------
        # SUBCATEGORIES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subcategories (
                SubCategoryID INT AUTO_INCREMENT PRIMARY KEY,
                SubCategoryName VARCHAR(100) NOT NULL,
                CategoryID INT NOT NULL,

                FOREIGN KEY (CategoryID)
                REFERENCES categories(CategoryID),

                UNIQUE (
                    SubCategoryName,
                    CategoryID
                )
            )
        """)

        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                ProductKey INT AUTO_INCREMENT PRIMARY KEY,
                SourceProductID VARCHAR(30) NOT NULL,
                ProductName VARCHAR(255) NOT NULL,
                SubCategoryID INT NOT NULL,

                FOREIGN KEY (SubCategoryID)
                REFERENCES subcategories(SubCategoryID),

                UNIQUE (
                    SourceProductID,
                    ProductName
                )
            )
        """)

        # ----------------------------------------------------
        # SHIPPING MODES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ship_modes (
                ShipModeID INT AUTO_INCREMENT PRIMARY KEY,
                ShipModeName VARCHAR(50) NOT NULL UNIQUE
            )
        """)

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                OrderID VARCHAR(30) PRIMARY KEY,
                OrderDate DATE NOT NULL,
                ShipDate DATE NOT NULL,
                CustomerID VARCHAR(20) NOT NULL,
                AddressID INT NOT NULL,
                ShipModeID INT NOT NULL,

                FOREIGN KEY (CustomerID)
                REFERENCES customers(CustomerID),

                FOREIGN KEY (AddressID)
                REFERENCES addresses(AddressID),

                FOREIGN KEY (ShipModeID)
                REFERENCES ship_modes(ShipModeID)
            )
        """)

        # ----------------------------------------------------
        # ORDER DETAILS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_details (
                OrderDetailID INT PRIMARY KEY,
                OrderID VARCHAR(30) NOT NULL,
                ProductKey INT NOT NULL,
                Quantity INT NOT NULL,
                Sales DECIMAL(12,2) NOT NULL,
                Discount DECIMAL(5,4) NOT NULL,
                Profit DECIMAL(12,2) NOT NULL,

                FOREIGN KEY (OrderID)
                REFERENCES orders(OrderID),

                FOREIGN KEY (ProductKey)
                REFERENCES products(ProductKey)
            )
        """)

        connection.commit()

        # ----------------------------------------------------
        # INDEXES
        #
        # MySQL version may not support:
        # CREATE INDEX IF NOT EXISTS
        #
        # So we create them normally and ignore
        # error 1061 if the index already exists.
        # ----------------------------------------------------

        indexes = [
            (
                "idx_orders_customer",
                """
                CREATE INDEX idx_orders_customer
                ON orders(CustomerID)
                """
            ),
            (
                "idx_orders_date",
                """
                CREATE INDEX idx_orders_date
                ON orders(OrderDate)
                """
            ),
            (
                "idx_order_details_order",
                """
                CREATE INDEX idx_order_details_order
                ON order_details(OrderID)
                """
            ),
            (
                "idx_order_details_product",
                """
                CREATE INDEX idx_order_details_product
                ON order_details(ProductKey)
                """
            )
        ]

        for index_name, index_query in indexes:

            try:
                cursor.execute(index_query)
                print(f"Index created: {index_name}")

            except Error as error:

                # MySQL error 1061 =
                # Duplicate key name
                if error.errno == 1061:
                    print(
                        f"Index already exists - skipped: {index_name}"
                    )
                else:
                    raise

        connection.commit()

        print("Tables checked/created successfully.")

    except Error as error:
        connection.rollback()
        print(f"Table creation error: {error}")
        raise

    finally:
        cursor.close()


# ============================================================
# CLEAR EXISTING DATA
# ============================================================

def clear_existing_data(connection):
    """Clear old imported data safely."""

    cursor = connection.cursor()

    try:

        print("Clearing existing tables...")

        # ----------------------------------------------------
        # ML OUTPUT TABLES
        # ----------------------------------------------------

        optional_tables = [
            "customer_segments",
            "sales_forecasts"
        ]

        for table in optional_tables:

            try:
                cursor.execute(
                    f"DELETE FROM {table}"
                )

            except Error as error:

                # 1146 = table doesn't exist
                if error.errno == 1146:
                    connection.rollback()
                else:
                    raise

        # ----------------------------------------------------
        # CHILD TABLE FIRST
        # ----------------------------------------------------

        cursor.execute(
            "DELETE FROM order_details"
        )

        cursor.execute(
            "DELETE FROM orders"
        )

        cursor.execute(
            "DELETE FROM products"
        )

        cursor.execute(
            "DELETE FROM subcategories"
        )

        cursor.execute(
            "DELETE FROM categories"
        )

        cursor.execute(
            "DELETE FROM ship_modes"
        )

        cursor.execute(
            "DELETE FROM customers"
        )

        cursor.execute(
            "DELETE FROM addresses"
        )

        connection.commit()

        print("Existing data cleared.")

    except Error as error:

        connection.rollback()

        print(
            f"Error while clearing existing data: {error}"
        )

        raise

    finally:
        cursor.close()


# ============================================================
# LOAD CSV
# ============================================================

def load_dataset():
    """Load and preprocess the Superstore CSV."""

    print("Loading dataset...")

    if not os.path.exists(CSV_PATH):

        raise FileNotFoundError(
            f"\nCSV file not found:\n{CSV_PATH}\n\n"
            "Make sure the file is inside the data folder "
            "and named:\nSample - Superstore.csv"
        )

    df = pd.read_csv(
    CSV_PATH,
    encoding="latin1"
)

    print(f"Rows loaded: {len(df)}")

    # --------------------------------------------------------
    # CHECK REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "Order ID",
        "Order Date",
        "Ship Date",
        "Customer ID",
        "Customer Name",
        "Segment",
        "Country",
        "City",
        "State",
        "Region",
        "Ship Mode",
        "Product ID",
        "Product Name",
        "Category",
        "Sub-Category",
        "Quantity",
        "Sales",
        "Discount",
        "Profit"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "The CSV is missing required columns:\n"
            + "\n".join(
                f"- {column}"
                for column in missing_columns
            )
        )

    # --------------------------------------------------------
    # DATE CLEANING
    # --------------------------------------------------------

    df["Order Date"] = pd.to_datetime(
        df["Order Date"],
        errors="coerce"
    )

    df["Ship Date"] = pd.to_datetime(
        df["Ship Date"],
        errors="coerce"
    )

    # Remove rows with invalid dates
    df = df.dropna(
        subset=[
            "Order Date",
            "Ship Date"
        ]
    )

    # --------------------------------------------------------
    # POSTAL CODE
    #
    # Extended dataset has missing postal codes.
    # Database requires PostalCode NOT NULL.
    # --------------------------------------------------------

    if "Postal Code" not in df.columns:

        df["Postal Code"] = "UNKNOWN"

    else:

        df["Postal Code"] = (
            df["Postal Code"]
            .fillna("UNKNOWN")
            .astype(str)
        )

        # Convert values such as 43055.0 -> 43055
        df["Postal Code"] = df["Postal Code"].apply(
            lambda value:
                value[:-2]
                if value.endswith(".0")
                else value
        )

        df["Postal Code"] = df["Postal Code"].replace(
            {
                "nan": "UNKNOWN",
                "NaN": "UNKNOWN",
                "": "UNKNOWN"
            }
        )

    # --------------------------------------------------------
    # NUMERIC COLUMNS
    # --------------------------------------------------------

    numeric_columns = [
        "Quantity",
        "Sales",
        "Discount",
        "Profit"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=numeric_columns
    )

    # --------------------------------------------------------
    # STRING CLEANING
    # --------------------------------------------------------

    string_columns = [
        "Order ID",
        "Customer ID",
        "Customer Name",
        "Segment",
        "Country",
        "City",
        "State",
        "Region",
        "Ship Mode",
        "Product ID",
        "Product Name",
        "Category",
        "Sub-Category"
    ]

    for column in string_columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    print("Data preprocessing completed.")

    return df


# ============================================================
# IMPORT CUSTOMERS
# ============================================================

def import_customers(connection, df):
    """Import customer records."""

    cursor = connection.cursor()

    print("Importing customers...")

    customers = (
        df[
            [
                "Customer ID",
                "Customer Name",
                "Segment"
            ]
        ]
        .drop_duplicates(
            subset=["Customer ID"]
        )
    )

    query = """
        INSERT INTO customers
        (
            CustomerID,
            CustomerName,
            Segment
        )
        VALUES (%s, %s, %s)
    """

    values = [
        (
            row["Customer ID"],
            row["Customer Name"],
            row["Segment"]
        )
        for _, row in customers.iterrows()
    ]

    cursor.executemany(query, values)

    connection.commit()

    print(
        f"Customers inserted: {len(values)}"
    )

    cursor.close()


# ============================================================
# IMPORT ADDRESSES
# ============================================================

def import_addresses(connection, df):
    """Import unique address records."""

    cursor = connection.cursor()

    print("Importing addresses...")

    addresses = (
        df[
            [
                "Country",
                "City",
                "State",
                "Postal Code",
                "Region"
            ]
        ]
        .drop_duplicates()
    )

    query = """
        INSERT INTO addresses
        (
            Country,
            City,
            State,
            PostalCode,
            Region
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    values = [
        (
            row["Country"],
            row["City"],
            row["State"],
            row["Postal Code"],
            row["Region"]
        )
        for _, row in addresses.iterrows()
    ]

    cursor.executemany(query, values)

    connection.commit()

    print(
        f"Addresses inserted: {len(values)}"
    )

    cursor.close()


# ============================================================
# IMPORT CATEGORIES
# ============================================================

def import_categories(connection, df):
    """Import categories."""

    cursor = connection.cursor()

    print("Importing categories...")

    categories = (
        df["Category"]
        .drop_duplicates()
        .tolist()
    )

    query = """
        INSERT INTO categories
        (CategoryName)
        VALUES (%s)
    """

    values = [
        (category,)
        for category in categories
    ]

    cursor.executemany(query, values)

    connection.commit()

    print(
        f"Categories inserted: {len(values)}"
    )

    cursor.close()


# ============================================================
# IMPORT SUBCATEGORIES
# ============================================================

def import_subcategories(connection, df):
    """Import subcategories."""

    cursor = connection.cursor()

    print("Importing subcategories...")

    category_map = {}

    cursor.execute("""
        SELECT
            CategoryID,
            CategoryName
        FROM categories
    """)

    for category_id, category_name in cursor.fetchall():

        category_map[category_name] = category_id

    subcategories = (
        df[
            [
                "Sub-Category",
                "Category"
            ]
        ]
        .drop_duplicates()
    )

    query = """
        INSERT INTO subcategories
        (
            SubCategoryName,
            CategoryID
        )
        VALUES (%s, %s)
    """

    values = []

    for _, row in subcategories.iterrows():

        category_id = category_map[
            row["Category"]
        ]

        values.append(
            (
                row["Sub-Category"],
                category_id
            )
        )

    cursor.executemany(
        query,
        values
    )

    connection.commit()

    print(
        f"Subcategories inserted: {len(values)}"
    )

    cursor.close()


# ============================================================
# IMPORT PRODUCTS
# ============================================================

def import_products(connection, df):
    """Import products."""

    cursor = connection.cursor()

    print("Importing products...")

    # Get subcategory IDs
    subcategory_map = {}

    cursor.execute("""
        SELECT
            sc.SubCategoryID,
            sc.SubCategoryName,
            c.CategoryName
        FROM subcategories sc
        INNER JOIN categories c
            ON sc.CategoryID = c.CategoryID
    """)

    for (
        subcategory_id,
        subcategory_name,
        category_name
    ) in cursor.fetchall():

        subcategory_map[
            (
                subcategory_name,
                category_name
            )
        ] = subcategory_id

    products = (
        df[
            [
                "Product ID",
                "Product Name",
                "Sub-Category",
                "Category"
            ]
        ]
        .drop_duplicates(
            subset=[
                "Product ID",
                "Product Name"
            ]
        )
    )

    query = """
        INSERT INTO products
        (
            SourceProductID,
            ProductName,
            SubCategoryID
        )
        VALUES (%s, %s, %s)
    """

    values = []

    for _, row in products.iterrows():

        key = (
            row["Sub-Category"],
            row["Category"]
        )

        subcategory_id = subcategory_map[key]

        values.append(
            (
                row["Product ID"],
                row["Product Name"],
                subcategory_id
            )
        )

    cursor.executemany(
        query,
        values
    )

    connection.commit()

    print(
        f"Products inserted: {len(values)}"
    )

    cursor.close()


# ============================================================
# IMPORT SHIPPING MODES
# ============================================================

def import_shipping_modes(connection, df):
    """Import shipping modes."""

    cursor = connection.cursor()

    print("Importing shipping modes...")

    shipping_modes = (
        df["Ship Mode"]
        .drop_duplicates()
        .tolist()
    )

    query = """
        INSERT INTO ship_modes
        (ShipModeName)
        VALUES (%s)
    """

    values = [
        (mode,)
        for mode in shipping_modes
    ]

    cursor.executemany(
        query,
        values
    )

    connection.commit()

    print(
        f"Ship modes inserted: {len(values)}"
    )

    cursor.close()


# ============================================================
# BUILD DATABASE MAPS
# ============================================================

def build_database_maps(connection):
    """
    Build lookup dictionaries needed for orders
    and order details.
    """

    cursor = connection.cursor()

    # --------------------------------------------------------
    # ADDRESS MAP
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            AddressID,
            Country,
            City,
            State,
            PostalCode,
            Region
        FROM addresses
    """)

    address_map = {}

    for row in cursor.fetchall():

        address_id = row[0]

        key = (
            row[1],
            row[2],
            row[3],
            row[4],
            row[5]
        )

        address_map[key] = address_id

    # --------------------------------------------------------
    # SHIP MODE MAP
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            ShipModeID,
            ShipModeName
        FROM ship_modes
    """)

    ship_mode_map = {}

    for row in cursor.fetchall():

        ship_mode_map[row[1]] = row[0]

    # --------------------------------------------------------
    # PRODUCT MAP
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            ProductKey,
            SourceProductID,
            ProductName
        FROM products
    """)

    product_map = {}

    for row in cursor.fetchall():

        product_map[
            (
                row[1],
                row[2]
            )
        ] = row[0]

    cursor.close()

    return (
        address_map,
        ship_mode_map,
        product_map
    )


# ============================================================
# IMPORT ORDERS
# ============================================================

def import_orders(
    connection,
    df,
    address_map,
    ship_mode_map
):
    """Import unique orders."""

    cursor = connection.cursor()

    print("Importing orders...")

    # --------------------------------------------------------
    # Keep one row for each Order ID.
    # --------------------------------------------------------

    orders = (
        df[
            [
                "Order ID",
                "Order Date",
                "Ship Date",
                "Customer ID",
                "Country",
                "City",
                "State",
                "Postal Code",
                "Region",
                "Ship Mode"
            ]
        ]
        .drop_duplicates(
            subset=["Order ID"]
        )
    )

    query = """
        INSERT INTO orders
        (
            OrderID,
            OrderDate,
            ShipDate,
            CustomerID,
            AddressID,
            ShipModeID
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = []

    for _, row in orders.iterrows():

        address_key = (
            row["Country"],
            row["City"],
            row["State"],
            row["Postal Code"],
            row["Region"]
        )

        address_id = address_map[address_key]

        ship_mode_id = ship_mode_map[
            row["Ship Mode"]
        ]

        values.append(
            (
                row["Order ID"],
                row["Order Date"].date(),
                row["Ship Date"].date(),
                row["Customer ID"],
                address_id,
                ship_mode_id
            )
        )

    cursor.executemany(
        query,
        values
    )

    connection.commit()

    print(
        f"Orders inserted: {len(values)}"
    )

    cursor.close()


# ============================================================
# IMPORT ORDER DETAILS
# ============================================================

def import_order_details(
    connection,
    df,
    product_map
):
    """
    Import order detail records.

    IMPORTANT:
    The extended CSV does not contain Row ID.
    Therefore OrderDetailID is generated sequentially.
    """

    cursor = connection.cursor()

    print("Importing order details...")

    query = """
        INSERT INTO order_details
        (
            OrderDetailID,
            OrderID,
            ProductKey,
            Quantity,
            Sales,
            Discount,
            Profit
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = []

    # --------------------------------------------------------
    # Generate OrderDetailID ourselves.
    # --------------------------------------------------------

    order_detail_id = 1

    for _, row in df.iterrows():

        product_key = product_map[
            (
                row["Product ID"],
                row["Product Name"]
            )
        ]

        values.append(
            (
                order_detail_id,
                row["Order ID"],
                product_key,
                int(row["Quantity"]),
                float(row["Sales"]),
                float(row["Discount"]),
                float(row["Profit"])
            )
        )

        order_detail_id += 1

    # --------------------------------------------------------
    # Insert in batches.
    #
    # This is safer for the larger 18,994-row dataset.
    # --------------------------------------------------------

    batch_size = 1000

    for start in range(
        0,
        len(values),
        batch_size
    ):

        batch = values[
            start:start + batch_size
        ]

        cursor.executemany(
            query,
            batch
        )

        connection.commit()

        print(
            f"Inserted order details: "
            f"{min(start + batch_size, len(values))}"
            f"/{len(values)}"
        )

    print(
        f"Order details inserted: {len(values)}"
    )

    cursor.close()


# ============================================================
# VERIFY IMPORT
# ============================================================

def verify_import(connection):
    """Verify imported database records."""

    cursor = connection.cursor()

    print()
    print("===================================")
    print("IMPORT VERIFICATION")
    print("===================================")

    # --------------------------------------------------------
    # COUNTS
    # --------------------------------------------------------

    tables = [
        "customers",
        "addresses",
        "categories",
        "subcategories",
        "products",
        "ship_modes",
        "orders",
        "order_details"
    ]

    for table in tables:

        cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        )

        count = cursor.fetchone()[0]

        print(
            f"{table}: {count}"
        )

    # --------------------------------------------------------
    # TOTAL SALES
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            ROUND(SUM(Sales), 2),
            ROUND(SUM(Profit), 2),
            SUM(Quantity)
        FROM order_details
    """)

    sales, profit, quantity = cursor.fetchone()

    print()
    print(
        f"Total Sales: {sales}"
    )

    print(
        f"Total Profit: {profit}"
    )

    print(
        f"Total Quantity: {quantity}"
    )

    # --------------------------------------------------------
    # DATE RANGE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            MIN(OrderDate),
            MAX(OrderDate)
        FROM orders
    """)

    start_date, end_date = cursor.fetchone()

    print(
        f"Order Date Range: "
        f"{start_date} to {end_date}"
    )

    print("===================================")

    cursor.close()


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    connection = None

    print()
    print("===================================")
    print("AI SALES INTELLIGENCE")
    print("EXTENDED SUPERSTORE DATA IMPORT")
    print("===================================")
    print()

    try:

        # ----------------------------------------------------
        # STEP 1
        # ----------------------------------------------------

        create_database()

        # ----------------------------------------------------
        # STEP 2
        # ----------------------------------------------------

        df = load_dataset()

        # ----------------------------------------------------
        # STEP 3
        # ----------------------------------------------------

        print("Connecting to MySQL...")

        connection = connect_database()

        # ----------------------------------------------------
        # STEP 4
        # ----------------------------------------------------

        create_tables(connection)

        # ----------------------------------------------------
        # STEP 5
        # ----------------------------------------------------

        clear_existing_data(connection)

        # ----------------------------------------------------
        # STEP 6
        # ----------------------------------------------------

        import_customers(
            connection,
            df
        )

        # ----------------------------------------------------
        # STEP 7
        # ----------------------------------------------------

        import_addresses(
            connection,
            df
        )

        # ----------------------------------------------------
        # STEP 8
        # ----------------------------------------------------

        import_categories(
            connection,
            df
        )

        # ----------------------------------------------------
        # STEP 9
        # ----------------------------------------------------

        import_subcategories(
            connection,
            df
        )

        # ----------------------------------------------------
        # STEP 10
        # ----------------------------------------------------

        import_products(
            connection,
            df
        )

        # ----------------------------------------------------
        # STEP 11
        # ----------------------------------------------------

        import_shipping_modes(
            connection,
            df
        )

        # ----------------------------------------------------
        # STEP 12
        # ----------------------------------------------------

        (
            address_map,
            ship_mode_map,
            product_map
        ) = build_database_maps(connection)

        # ----------------------------------------------------
        # STEP 13
        # ----------------------------------------------------

        import_orders(
            connection,
            df,
            address_map,
            ship_mode_map
        )

        # ----------------------------------------------------
        # STEP 14
        # ----------------------------------------------------

        import_order_details(
            connection,
            df,
            product_map
        )

        # ----------------------------------------------------
        # STEP 15
        # ----------------------------------------------------

        verify_import(connection)

        print()
        print("===================================")
        print("DATA IMPORT COMPLETED SUCCESSFULLY")
        print("===================================")

    except Exception as error:

        print()
        print("===================================")
        print("IMPORT FAILED")
        print("===================================")

        print(
            f"Error: {error}"
        )

        # Print full traceback for debugging
        import traceback
        traceback.print_exc()

    finally:

        if connection and connection.is_connected():

            connection.close()

            print(
                "MySQL connection closed."
            )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()