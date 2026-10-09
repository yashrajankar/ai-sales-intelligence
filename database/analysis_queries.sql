
USE sales_intelligence;



SELECT *
FROM customers
LIMIT 10;



SELECT
    CustomerID,
    CustomerName,
    Segment
FROM customers
WHERE Segment = 'Consumer';



SELECT
    CustomerID,
    CustomerName,
    Segment
FROM customers
ORDER BY CustomerName ASC;



-- Total Sales

SELECT
    SUM(Sales) AS TotalSales
FROM order_details;


-- Total Profit

SELECT
    SUM(Profit) AS TotalProfit
FROM order_details;


-- Total Quantity

SELECT
    SUM(Quantity) AS TotalQuantity
FROM order_details;


-- Average Sales

SELECT
    AVG(Sales) AS AverageSales
FROM order_details;



SELECT
    MIN(Sales) AS MinimumSale,
    MAX(Sales) AS MaximumSale
FROM order_details;




SELECT
    COUNT(*) AS TotalOrders
FROM orders;




SELECT
    COUNT(*) AS TotalCustomers
FROM customers;




SELECT
    c.CategoryName,
    SUM(od.Sales) AS TotalSales
FROM order_details od
JOIN products p
    ON od.ProductKey = p.ProductKey
JOIN subcategories sc
    ON p.SubCategoryID = sc.SubCategoryID
JOIN categories c
    ON sc.CategoryID = c.CategoryID
GROUP BY c.CategoryName
ORDER BY TotalSales DESC;




SELECT
    c.CategoryName,
    SUM(od.Profit) AS TotalProfit
FROM order_details od
JOIN products p
    ON od.ProductKey = p.ProductKey
JOIN subcategories sc
    ON p.SubCategoryID = sc.SubCategoryID
JOIN categories c
    ON sc.CategoryID = c.CategoryID
GROUP BY c.CategoryName
ORDER BY TotalProfit DESC;



SELECT
    a.Region,
    SUM(od.Sales) AS TotalSales
FROM orders o
JOIN addresses a
    ON o.AddressID = a.AddressID
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY a.Region
ORDER BY TotalSales DESC;




SELECT
    a.Region,
    SUM(od.Profit) AS TotalProfit
FROM orders o
JOIN addresses a
    ON o.AddressID = a.AddressID
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY a.Region
ORDER BY TotalProfit DESC;




SELECT
    c.Segment,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit
FROM customers c
JOIN orders o
    ON c.CustomerID = o.CustomerID
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY c.Segment
ORDER BY TotalSales DESC;




SELECT
    sm.ShipModeName,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit
FROM ship_modes sm
JOIN orders o
    ON sm.ShipModeID = o.ShipModeID
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY sm.ShipModeName
ORDER BY TotalSales DESC;





SELECT
    sc.SubCategoryName,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit
FROM order_details od
JOIN products p
    ON od.ProductKey = p.ProductKey
JOIN subcategories sc
    ON p.SubCategoryID = sc.SubCategoryID
GROUP BY sc.SubCategoryName
ORDER BY TotalSales DESC;




SELECT
    p.ProductName,
    SUM(od.Sales) AS TotalSales
FROM products p
JOIN order_details od
    ON p.ProductKey = od.ProductKey
GROUP BY
    p.ProductKey,
    p.ProductName
ORDER BY TotalSales DESC
LIMIT 10;




SELECT
    p.ProductName,
    SUM(od.Profit) AS TotalProfit
FROM products p
JOIN order_details od
    ON p.ProductKey = od.ProductKey
GROUP BY
    p.ProductKey,
    p.ProductName
ORDER BY TotalProfit DESC
LIMIT 10;




SELECT
    sc.SubCategoryName,
    SUM(od.Sales) AS TotalSales
FROM order_details od
JOIN products p
    ON od.ProductKey = p.ProductKey
JOIN subcategories sc
    ON p.SubCategoryID = sc.SubCategoryID
GROUP BY sc.SubCategoryName
HAVING SUM(od.Sales) > 100000
ORDER BY TotalSales DESC;




SELECT
    OrderDetailID,
    Sales,
    Profit,

    CASE
        WHEN Profit > 0 THEN 'Profitable'
        WHEN Profit < 0 THEN 'Loss'
        ELSE 'No Profit'
    END AS ProfitStatus

FROM order_details
LIMIT 20;



SELECT
    OrderDetailID,
    Discount,

    CASE
        WHEN Discount = 0 THEN 'No Discount'
        WHEN Discount <= 0.20 THEN 'Low Discount'
        WHEN Discount <= 0.40 THEN 'Medium Discount'
        ELSE 'High Discount'
    END AS DiscountLevel

FROM order_details
LIMIT 20;




SELECT
    YEAR(o.OrderDate) AS SalesYear,
    SUM(od.Sales) AS TotalSales
FROM orders o
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY YEAR(o.OrderDate)
ORDER BY SalesYear;



SELECT
    YEAR(o.OrderDate) AS SalesYear,
    MONTH(o.OrderDate) AS SalesMonth,
    SUM(od.Sales) AS TotalSales
FROM orders o
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY
    YEAR(o.OrderDate),
    MONTH(o.OrderDate)
ORDER BY
    SalesYear,
    SalesMonth;




SELECT
    YEAR(o.OrderDate) AS SalesYear,
    MONTH(o.OrderDate) AS SalesMonth,
    MONTHNAME(o.OrderDate) AS MonthName,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit
FROM orders o
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY
    YEAR(o.OrderDate),
    MONTH(o.OrderDate),
    MONTHNAME(o.OrderDate)
ORDER BY
    SalesYear,
    SalesMonth;



SELECT
    AVG(DATEDIFF(ShipDate, OrderDate)) AS AverageShippingDays
FROM orders;



SELECT
    sm.ShipModeName,
    AVG(DATEDIFF(o.ShipDate, o.OrderDate)) AS AverageShippingDays
FROM orders o
JOIN ship_modes sm
    ON o.ShipModeID = sm.ShipModeID
GROUP BY sm.ShipModeName
ORDER BY AverageShippingDays;




SELECT
    c.CustomerID,
    c.CustomerName,
    c.Segment,
    COUNT(DISTINCT o.OrderID) AS TotalOrders,
    SUM(od.Quantity) AS TotalQuantity,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit
FROM customers c
JOIN orders o
    ON c.CustomerID = o.CustomerID
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY
    c.CustomerID,
    c.CustomerName,
    c.Segment
ORDER BY TotalSales DESC;




SELECT
    c.CustomerID,
    c.CustomerName,
    c.Segment,
    SUM(od.Sales) AS TotalSales
FROM customers c
JOIN orders o
    ON c.CustomerID = o.CustomerID
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY
    c.CustomerID,
    c.CustomerName,
    c.Segment
ORDER BY TotalSales DESC
LIMIT 10;




SELECT
    c.CustomerID,
    c.CustomerName,
    c.Segment,
    SUM(od.Profit) AS TotalProfit
FROM customers c
JOIN orders o
    ON c.CustomerID = o.CustomerID
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY
    c.CustomerID,
    c.CustomerName,
    c.Segment
ORDER BY TotalProfit DESC
LIMIT 10;




SELECT
    p.ProductName,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit
FROM products p
JOIN order_details od
    ON p.ProductKey = od.ProductKey
GROUP BY
    p.ProductKey,
    p.ProductName
HAVING SUM(od.Profit) < 0
ORDER BY TotalProfit ASC;



SELECT
    sc.SubCategoryName,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit
FROM subcategories sc
JOIN products p
    ON sc.SubCategoryID = p.SubCategoryID
JOIN order_details od
    ON p.ProductKey = od.ProductKey
GROUP BY sc.SubCategoryName
HAVING SUM(od.Profit) < 0
ORDER BY TotalProfit ASC;




SELECT
    c.CustomerID,
    c.CustomerName,
    SUM(od.Sales) AS TotalSales
FROM customers c
JOIN orders o
    ON c.CustomerID = o.CustomerID
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY
    c.CustomerID,
    c.CustomerName
HAVING SUM(od.Sales) >
(
    SELECT AVG(CustomerSales)
    FROM
    (
        SELECT
            o2.CustomerID,
            SUM(od2.Sales) AS CustomerSales
        FROM orders o2
        JOIN order_details od2
            ON o2.OrderID = od2.OrderID
        GROUP BY o2.CustomerID
    ) AS customer_totals
)
ORDER BY TotalSales DESC;




SELECT
    c.CustomerID,
    c.CustomerName,
    COUNT(DISTINCT o.OrderID) AS NumberOfOrders
FROM customers c
JOIN orders o
    ON c.CustomerID = o.CustomerID
GROUP BY
    c.CustomerID,
    c.CustomerName
ORDER BY NumberOfOrders DESC;




SELECT
    o.OrderID,
    o.OrderDate,
    c.CustomerName,
    od.Sales,
    od.Discount,
    od.Profit
FROM orders o
JOIN customers c
    ON o.CustomerID = c.CustomerID
JOIN order_details od
    ON o.OrderID = od.OrderID
WHERE od.Discount >= 0.40
ORDER BY od.Discount DESC;




SELECT
    c.CategoryName,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit,

    ROUND(
        (SUM(od.Profit) / NULLIF(SUM(od.Sales), 0)) * 100,
        2
    ) AS ProfitMarginPercentage

FROM order_details od
JOIN products p
    ON od.ProductKey = p.ProductKey
JOIN subcategories sc
    ON p.SubCategoryID = sc.SubCategoryID
JOIN categories c
    ON sc.CategoryID = c.CategoryID

GROUP BY c.CategoryName
ORDER BY ProfitMarginPercentage DESC;



SELECT
    a.Region,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit,

    ROUND(
        (SUM(od.Profit) / NULLIF(SUM(od.Sales), 0)) * 100,
        2
    ) AS ProfitMarginPercentage

FROM orders o
JOIN addresses a
    ON o.AddressID = a.AddressID
JOIN order_details od
    ON o.OrderID = od.OrderID

GROUP BY a.Region
ORDER BY TotalSales DESC;



SELECT
    o.OrderID,
    o.OrderDate,
    o.ShipDate,

    c.CustomerID,
    c.CustomerName,
    c.Segment,

    a.City,
    a.State,
    a.Region,

    sm.ShipModeName,

    p.ProductName,
    sc.SubCategoryName,
    cat.CategoryName,

    od.Quantity,
    od.Sales,
    od.Discount,
    od.Profit

FROM orders o

JOIN customers c
    ON o.CustomerID = c.CustomerID

JOIN addresses a
    ON o.AddressID = a.AddressID

JOIN ship_modes sm
    ON o.ShipModeID = sm.ShipModeID

JOIN order_details od
    ON o.OrderID = od.OrderID

JOIN products p
    ON od.ProductKey = p.ProductKey

JOIN subcategories sc
    ON p.SubCategoryID = sc.SubCategoryID

JOIN categories cat
    ON sc.CategoryID = cat.CategoryID

LIMIT 20;




SELECT

    (SELECT COUNT(*)
     FROM orders) AS TotalOrders,

    (SELECT COUNT(*)
     FROM customers) AS TotalCustomers,

    (SELECT SUM(Quantity)
     FROM order_details) AS TotalQuantity,

    (SELECT ROUND(SUM(Sales), 2)
     FROM order_details) AS TotalSales,

    (SELECT ROUND(SUM(Profit), 2)
     FROM order_details) AS TotalProfit;




SELECT
    DATE_FORMAT(o.OrderDate, '%Y-%m-01') AS Month,
    SUM(od.Sales) AS TotalSales
FROM orders o
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY
    DATE_FORMAT(o.OrderDate, '%Y-%m-01')
ORDER BY Month;




SELECT
    DATE_FORMAT(o.OrderDate, '%Y-%m-01') AS Month,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit,
    SUM(od.Quantity) AS TotalQuantity
FROM orders o
JOIN order_details od
    ON o.OrderID = od.OrderID
GROUP BY
    DATE_FORMAT(o.OrderDate, '%Y-%m-01')
ORDER BY Month;

