-- Question: What are the top 5 products with the highest total sales revenue?
SELECT 
    p.product_name,
    p.description,
    SUM(s.product_total_price) AS total_revenue
FROM 
    sales_fact_table s
JOIN 
    product_dimension p ON s.product_id = p.product_id
GROUP BY 
    p.product_name, p.description
ORDER BY 
    total_revenue DESC
LIMIT 5;

-- Question: Which customers have spent the most on purchases, and how much have they spent?
SELECT 
    u.first_name || ' ' || u.last_name AS customer_name,
    u.email,
    SUM(s.total_cart_price) AS total_spent
FROM 
    sales_fact_table s
JOIN 
    user_dimension u ON s.user_id = u.user_id
GROUP BY 
    u.first_name, u.last_name, u.email
ORDER BY 
    total_spent DESC;

-- Question: What is the total sales revenue for each product category?
SELECT 
    c.category_name,
    SUM(s.product_total_price) AS total_revenue
FROM 
    sales_fact_table s
JOIN 
    category_dimension c ON s.category_id = c.category_id
GROUP BY 
    c.category_name
ORDER BY 
    total_revenue DESC;
