-- Drop tables if they exist, taking dependencies into account
DROP TABLE IF EXISTS sales_fact_table CASCADE;
DROP TABLE IF EXISTS product_dimension CASCADE;
DROP TABLE IF EXISTS category_dimension CASCADE;
DROP TABLE IF EXISTS user_dimension CASCADE;
DROP TABLE IF EXISTS cart_dimension CASCADE;

-- Category Dimension
CREATE TABLE category_dimension (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL
);

-- Product Dimension
CREATE TABLE product_dimension (
    product_id SERIAL PRIMARY KEY,
    price DECIMAL(10, 2) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url TEXT
);

-- User Dimension
CREATE TABLE user_dimension (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(50) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone_num VARCHAR(15),
    street VARCHAR(255),
    city VARCHAR(100),
    zip_code VARCHAR(20),
    long DECIMAL(9, 6),
    lat DECIMAL(9, 6)
);

-- Cart Dimension
CREATE TABLE cart_dimension (
    cart_id SERIAL PRIMARY KEY,
    cart_date TIMESTAMP NOT NULL
);

-- Sales Fact Table
CREATE TABLE sales_fact_table (
    sales_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    category_id INT NOT NULL,
    cart_id INT NOT NULL,
    user_id INT NOT NULL,
    quantity_purchased INT NOT NULL,
    product_total_price DECIMAL(10, 2) NOT NULL,
    rating_count INT,
    rating_rate DECIMAL(3, 2),
    total_cart_price DECIMAL(10, 2),
    distinct_products_in_cart INT,
    FOREIGN KEY (product_id) REFERENCES product_dimension (product_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES category_dimension (category_id) ON DELETE CASCADE,
    FOREIGN KEY (cart_id) REFERENCES cart_dimension (cart_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user_dimension (user_id) ON DELETE CASCADE
);
