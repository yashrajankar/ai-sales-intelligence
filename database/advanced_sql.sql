USE sales_intelligence;


DROP VIEW IF EXISTS sales_details_view;

CREATE VIEW sales_details_view AS
SELECT
    o.OrderID,
    o.OrderDate,
    o.ShipDate,

    c.CustomerID,
    c.CustomerName,
    c.Segment,

    a.Country,
    a.City,
    a.State,
    a.PostalCode,
    a.Region,

    sm.ShipModeName,

    p.ProductKey,
    p.SourceProductID,
    p.ProductName,

    sc.SubCategoryName,
    cat.CategoryName,

    od.OrderDetailID,
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
    ON sc.CategoryID = cat.CategoryID;



SELECT *
FROM sales_details_view
LIMIT 20;



DROP VIEW IF EXISTS monthly_sales_view;

CREATE VIEW monthly_sales_view AS
SELECT
    DATE_FORMAT(o.OrderDate, '%Y-%m-01') AS Month,
    SUM(od.Sales) AS TotalSales,
    SUM(od.Profit) AS TotalProfit,
    SUM(od.Quantity) AS TotalQuantity,
    COUNT(DISTINCT o.OrderID) AS TotalOrders

FROM orders o

JOIN order_details od
    ON o.OrderID = od.OrderID

GROUP BY
    DATE_FORMAT(o.OrderDate, '%Y-%m-01');


-- Test the view

SELECT *
FROM monthly_sales_view
ORDER BY Month;




DROP VIEW IF EXISTS customer_sales_view;

CREATE VIEW customer_sales_view AS
SELECT
    c.CustomerID,
    c.CustomerName,
    c.Segment,

    COUNT(DISTINCT o.OrderID) AS TotalOrders,

    SUM(od.Quantity) AS TotalQuantity,

    ROUND(SUM(od.Sales), 2) AS TotalSales,

    ROUND(SUM(od.Profit), 2) AS TotalProfit,

    MAX(o.OrderDate) AS LastOrderDate

FROM customers c

JOIN orders o
    ON c.CustomerID = o.CustomerID

JOIN order_details od
    ON o.OrderID = od.OrderID

GROUP BY
    c.CustomerID,
    c.CustomerName,
    c.Segment;


-- Test the view

SELECT *
FROM customer_sales_view
ORDER BY TotalSales DESC
LIMIT 20;




DROP VIEW IF EXISTS category_performance_view;

CREATE VIEW category_performance_view AS
SELECT
    cat.CategoryName,

    SUM(od.Sales) AS TotalSales,

    SUM(od.Profit) AS TotalProfit,

    SUM(od.Quantity) AS TotalQuantity,

    ROUND(
        (SUM(od.Profit) / NULLIF(SUM(od.Sales), 0)) * 100,
        2
    ) AS ProfitMarginPercentage

FROM order_details od

JOIN products p
    ON od.ProductKey = p.ProductKey

JOIN subcategories sc
    ON p.SubCategoryID = sc.SubCategoryID

JOIN categories cat
    ON sc.CategoryID = cat.CategoryID

GROUP BY
    cat.CategoryName;


-- Test the view

SELECT *
FROM category_performance_view
ORDER BY TotalSales DESC;




DROP PROCEDURE IF EXISTS GetSalesByDateRange;

DELIMITER $$

CREATE PROCEDURE GetSalesByDateRange(
    IN start_date DATE,
    IN end_date DATE
)
BEGIN

    SELECT
        DATE(o.OrderDate) AS OrderDate,
        COUNT(DISTINCT o.OrderID) AS TotalOrders,
        SUM(od.Quantity) AS TotalQuantity,
        ROUND(SUM(od.Sales), 2) AS TotalSales,
        ROUND(SUM(od.Profit), 2) AS TotalProfit

    FROM orders o

    JOIN order_details od
        ON o.OrderID = od.OrderID

    WHERE o.OrderDate BETWEEN start_date AND end_date

    GROUP BY
        DATE(o.OrderDate)

    ORDER BY
        OrderDate;

END$$

DELIMITER ;



CALL GetSalesByDateRange(
    '2017-01-01',
    '2017-12-31'
);



DROP PROCEDURE IF EXISTS GetCustomerSales;

DELIMITER $$

CREATE PROCEDURE GetCustomerSales(
    IN customer_id VARCHAR(20)
)
BEGIN

    SELECT
        c.CustomerID,
        c.CustomerName,
        c.Segment,

        COUNT(DISTINCT o.OrderID) AS TotalOrders,

        SUM(od.Quantity) AS TotalQuantity,

        ROUND(SUM(od.Sales), 2) AS TotalSales,

        ROUND(SUM(od.Profit), 2) AS TotalProfit,

        MIN(o.OrderDate) AS FirstOrderDate,

        MAX(o.OrderDate) AS LastOrderDate

    FROM customers c

    JOIN orders o
        ON c.CustomerID = o.CustomerID

    JOIN order_details od
        ON o.OrderID = od.OrderID

    WHERE c.CustomerID = customer_id

    GROUP BY
        c.CustomerID,
        c.CustomerName,
        c.Segment;

END$$

DELIMITER ;



CALL GetCustomerSales('CG-12520');




DROP FUNCTION IF EXISTS CalculateProfitMargin;

DELIMITER $$

CREATE FUNCTION CalculateProfitMargin(
    sales_amount DECIMAL(12,2),
    profit_amount DECIMAL(12,2)
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN

    IF sales_amount = 0 THEN
        RETURN 0;
    END IF;

    RETURN ROUND(
        (profit_amount / sales_amount) * 100,
        2
    );

END$$

DELIMITER ;



SELECT
    CalculateProfitMargin(1000, 200) AS ProfitMargin;




DROP FUNCTION IF EXISTS GetProfitStatus;

DELIMITER $$

CREATE FUNCTION GetProfitStatus(
    profit_amount DECIMAL(12,2)
)
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN

    IF profit_amount > 0 THEN
        RETURN 'Profitable';

    ELSEIF profit_amount < 0 THEN
        RETURN 'Loss';

    ELSE
        RETURN 'No Profit';

    END IF;

END$$

DELIMITER ;




SELECT
    OrderDetailID,
    Sales,
    Profit,
    GetProfitStatus(Profit) AS ProfitStatus
FROM order_details
LIMIT 20;


-- TRIGGER


DROP TRIGGER IF EXISTS before_order_detail_insert;

DELIMITER $$

CREATE TRIGGER before_order_detail_insert
BEFORE INSERT ON order_details
FOR EACH ROW
BEGIN

    IF NEW.Quantity <= 0 THEN

        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Quantity must be greater than zero';

    END IF;

END$$

DELIMITER ;


--  TRIGGER

DROP TRIGGER IF EXISTS before_order_detail_discount;

DELIMITER $$

CREATE TRIGGER before_order_detail_discount
BEFORE INSERT ON order_details
FOR EACH ROW
BEGIN

    IF NEW.Discount < 0 THEN

        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Discount cannot be negative';

    END IF;

END$$

DELIMITER ;




SHOW FULL TABLES
WHERE Table_type = 'VIEW';



SHOW PROCEDURE STATUS
WHERE Db = 'sales_intelligence';



SHOW FUNCTION STATUS
WHERE Db = 'sales_intelligence';




SHOW TRIGGERS
FROM sales_intelligence;

