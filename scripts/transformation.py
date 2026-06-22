import os
import json
import pandas as pd

# Define directories
RAW_DATA_PATH = "data/raw"
PROCESSED_DATA_PATH = "data/processed"

# Ensure the processed directory exists
os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)

# Helper function to load JSON files
def load_json(filename):
    with open(os.path.join(RAW_DATA_PATH, filename)) as f:
        return json.load(f)

# Helper function to save DataFrame to CSV with explicit casting
def save_to_csv(df, filename, dtypes):
    df = df.astype(dtypes)  # Explicit type casting
    df.to_csv(os.path.join(PROCESSED_DATA_PATH, filename), index=False)

# 1. Category Dimension
def process_category_dimension(categories):
    category_dimension = pd.DataFrame({
        "category_id": range(1, len(categories) + 1),
        "category_name": categories
    })
    dtypes = {
        "category_id": "int",
        "category_name": "str"
    }
    save_to_csv(category_dimension, "category_dimension.csv", dtypes)
    return dict(zip(categories, range(1, len(categories) + 1)))

# 2. Product Dimension
def process_product_dimension(products):
    product_dimension = pd.DataFrame(products).rename(columns={
        "id": "product_id",
        "title": "product_name",
        "price": "price",
        "description": "description",
        "image": "image_url"
    })[["product_id", "price", "product_name", "description", "image_url"]]
    dtypes = {
        "product_id": "int",
        "price": "float",
        "product_name": "str",
        "description": "str",
        "image_url": "str"
    }
    save_to_csv(product_dimension, "product_dimension.csv", dtypes)
    return product_dimension

# 3. User Dimension
def process_user_dimension(users):
    user_dimension = pd.DataFrame(users).rename(columns={
        "id": "user_id",
        "email": "email",
        "username": "username",
        "phone": "phone_num"
    })
    user_dimension["first_name"] = user_dimension["name"].apply(lambda x: x["firstname"])
    user_dimension["last_name"] = user_dimension["name"].apply(lambda x: x["lastname"])
    user_dimension["street"] = user_dimension["address"].apply(lambda x: x["street"])
    user_dimension["city"] = user_dimension["address"].apply(lambda x: x["city"])
    user_dimension["zip_code"] = user_dimension["address"].apply(lambda x: x["zipcode"])
    user_dimension["long"] = user_dimension["address"].apply(lambda x: x["geolocation"]["long"])
    user_dimension["lat"] = user_dimension["address"].apply(lambda x: x["geolocation"]["lat"])
    user_dimension = user_dimension[[
        "user_id", "email", "username", "first_name", "last_name", "phone_num",
        "street", "city", "zip_code", "long", "lat"
    ]]
    dtypes = {
        "user_id": "int",
        "email": "str",
        "username": "str",
        "first_name": "str",
        "last_name": "str",
        "phone_num": "str",
        "street": "str",
        "city": "str",
        "zip_code": "str",
        "long": "float",
        "lat": "float"
    }
    save_to_csv(user_dimension, "user_dimension.csv", dtypes)

# 4. Cart Dimension
def process_cart_dimension(carts):
    cart_dimension = pd.DataFrame(carts).rename(columns={"id": "cart_id", "date": "cart_date"})[["cart_id", "cart_date"]]
    cart_dimension["cart_date"] = pd.to_datetime(cart_dimension["cart_date"])  # Convert to datetime
    dtypes = {
        "cart_id": "int"
    }
    save_to_csv(cart_dimension, "cart_dimension.csv", dtypes)

# 5. Sales Fact Table
def process_sales_fact_table(carts, products, category_mapping, product_dimension):
    sales_fact_table = []
    cart_prices = {}
    cart_items = {}

    for cart in carts:
        cart_id = cart["id"]
        user_id = cart["userId"]
        cart_total_price = 0
        distinct_products_in_cart = len(cart["products"])
        for product in cart["products"]:
            product_id = product["productId"]
            quantity = product["quantity"]
            price = product_dimension.loc[product_dimension["product_id"] == product_id, "price"].values[0]
            product_total_price = price * quantity
            cart_total_price += product_total_price
            rating_count = products[product_id - 1]["rating"]["count"]
            rating_rate = products[product_id - 1]["rating"]["rate"]
            sales_fact_table.append({
                "sales_id": len(sales_fact_table) + 1,
                "product_id": product_id,
                "category_id": category_mapping[products[product_id - 1]["category"]],
                "cart_id": cart_id,
                "user_id": user_id,
                "quantity_purchased": quantity,
                "product_total_price": product_total_price,
                "rating_count": rating_count,
                "rating_rate": rating_rate,
                "total_cart_price": None,
                "distinct_products_in_cart": None
            })
        cart_prices[cart_id] = cart_total_price
        cart_items[cart_id] = distinct_products_in_cart

    for row in sales_fact_table:
        row["total_cart_price"] = cart_prices[row["cart_id"]]
        row["distinct_products_in_cart"] = cart_items[row["cart_id"]]

    sales_fact_table = pd.DataFrame(sales_fact_table)
    dtypes = {
        "sales_id": "int",
        "product_id": "int",
        "category_id": "int",
        "cart_id": "int",
        "user_id": "int",
        "quantity_purchased": "int",
        "product_total_price": "float",
        "rating_count": "int",
        "rating_rate": "float",
        "total_cart_price": "float",
        "distinct_products_in_cart": "int"
    }
    save_to_csv(sales_fact_table, "sales_fact_table.csv", dtypes)

# Main Script
def main():
    categories = load_json("categories.json")
    products = load_json("products.json")
    users = load_json("users.json")
    carts = load_json("carts.json")

    category_mapping = process_category_dimension(categories)
    product_dimension = process_product_dimension(products)
    process_user_dimension(users)
    process_cart_dimension(carts)
    process_sales_fact_table(carts, products, category_mapping, product_dimension)

    print("Data transformation complete. Files saved to 'data/processed'.")

if __name__ == "__main__":
    main()
