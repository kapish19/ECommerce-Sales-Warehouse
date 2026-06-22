-- Create staging table for Categories
CREATE TABLE staging_categories (
    category VARCHAR(255) NOT NULL
);

-- Create staging table for Products
CREATE TABLE staging_products (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL,
    description TEXT,
    category VARCHAR(255) NOT NULL,
    image VARCHAR(255),
    rate FLOAT,
    count INT
);

-- Create staging table for Users
CREATE TABLE staging_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    password VARCHAR(255),
    phone VARCHAR(255),
    firstname VARCHAR(255),
    lastname VARCHAR(255),
    city VARCHAR(255),
    street VARCHAR(255),
    number INT,
    zipcode VARCHAR(20),
    latitude FLOAT,
    longitude FLOAT
);

-- Create staging table for Carts
CREATE TABLE staging_carts (
    id SERIAL PRIMARY KEY,
    userId INT NOT NULL,
    date TIMESTAMP NOT NULL,
    productId INT NOT NULL,
    quantity INT NOT NULL
);