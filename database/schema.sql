CREATE DATABASE IF NOT EXISTS sales_intelligence;

USE sales_intelligence;

CREATE TABLE customers (
    CustomerID VARCHAR(20) PRIMARY KEY,
    CustomerName VARCHAR(100) NOT NULL,
    Segment VARCHAR(30) NOT NULL
);

CREATE TABLE addresses (
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
);

CREATE TABLE categories (
    CategoryID INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE subcategories (
    SubCategoryID INT AUTO_INCREMENT PRIMARY KEY,
    SubCategoryName VARCHAR(100) NOT NULL,
    CategoryID INT NOT NULL,

    FOREIGN KEY (CategoryID)
        REFERENCES categories(CategoryID),

    UNIQUE (
        SubCategoryName,
        CategoryID
    )
);

CREATE TABLE products (
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
);

CREATE TABLE ship_modes (
    ShipModeID INT AUTO_INCREMENT PRIMARY KEY,
    ShipModeName VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE orders (
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
);

CREATE TABLE order_details (
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
);

CREATE INDEX idx_orders_customer
ON orders(CustomerID);

CREATE INDEX idx_orders_date
ON orders(OrderDate);

CREATE INDEX idx_order_details_order
ON order_details(OrderID);

CREATE INDEX idx_order_details_product
ON order_details(ProductKey);