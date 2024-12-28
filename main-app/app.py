from flask import Flask, jsonify, render_template, request
import requests
from functools import lru_cache
import os

app = Flask(__name__)

product_service_host = "localhost" if os.getenv("HOSTNAME") is None else "product-service"
cart_service_host = "localhost" if os.getenv("HOSTNAME") is None else "cart-service"
review_service_host = "localhost" if os.getenv("HOSTNAME") is None else "review-service"


def get_products(product_id):
    try:
        response = requests.get(f'http://{product_service_host}:3000/products/{product_id}')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching product data: {e}")
        return {"error": "Failed to fetch product data"}
    
def get_sold_products(product_id):
    try:
        response = requests.get(f'http://{cart_service_host}:3002/cart/{product_id}')
        response.raise_for_status()
        data = response.json()

        if 'data' in data:
            cart_item = data['data'] 
            total_quantity = 0

            if isinstance(cart_item, dict) and 'product_id' in cart_item:
                if cart_item['product_id'] == product_id:
                    total_quantity = cart_item.get('quantity', 0)

            print(f"Total quantity for product_id {product_id}: {total_quantity}")
            return total_quantity
        else:
            print("Invalid data format:", data)
            return 0  
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sold product data: {e}")
        return {"error": "Failed to fetch sold product data"}
    
def get_reviews(product_id):
    try:
        response = requests.get(f'http://{review_service_host}:3003/products/{product_id}/reviews')
        response.raise_for_status()
        data = response.json()

        return data.get('data', {"reviews": [], "product": {}})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching review data: {e}")
        return {"error": "Failed to fetch review data"}
@app.route('/product/<int:product_id>')
def get_product_info(product_id):
    product = get_products(product_id)
    cart = get_sold_products(product_id)
    review = get_reviews(product_id)

    combined_response = {
        "product": product if "error" not in product else None,
        "cart": cart,
        "reviews": review.get("reviews", []) if isinstance(review, dict) and "error" not in review else review if isinstance(review, list) else []

    }

    if request.args.get('format') == 'json':
        return jsonify({
            "data": combined_response,
            "message": "Product data fetched successfully" if product else "Failed to fetch product data"
        })

    return render_template('product.html', **combined_response)

if __name__ == '__main__':
    app.run(debug=True, port=3005, host="0.0.0.0")