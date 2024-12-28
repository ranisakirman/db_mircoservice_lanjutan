from flask import Flask, jsonify, request
from pymongo import MongoClient
from urllib.parse import quote_plus
import os
from bson  import ObjectId
import requests

# Membuat instance Flask
app = Flask(__name__)


# Konfigurasi kredensial MongoDB
username = os.getenv("MONGO_USER", "root")
password = os.getenv("MONGO_PASSWORD", "Dev@root23")

# Encode username dan password
encoded_username = quote_plus(username)
encoded_password = quote_plus(password)

# Konfigurasi URI berdasarkan *environment*
mongo_host = os.getenv("MONGO_HOST", "localhost" if os.getenv("HOSTNAME") is None else "review-db")
mongo_port = os.getenv("MONGO_PORT", "27017")
mongo_db = os.getenv("MONGO_DB", "review_service")
mongo_auth_source = os.getenv("MONGO_AUTH_SOURCE", "admin")

MONGO_URI = f"mongodb://{encoded_username}:{encoded_password}@{mongo_host}:{mongo_port}/{mongo_db}?authSource={mongo_auth_source}"

# Koneksi ke MongoDB
client = MongoClient(MONGO_URI)
db = client["review_service"]
reviews_collection = db["reviews"]

# URL Product Service
product_service_host = "localhost" if os.getenv("HOSTNAME") is None else "product-service"
PRODUCT_SERVICE_URL = f"http://{product_service_host}:3000/products/"

# Mengambil data produk dari Product Service
def get_product_data(product_id):
    try:
        response = requests.get(f'{PRODUCT_SERVICE_URL}{product_id}')
        print("Requesting : {PRODUCT_SERVICE_URL}{product_id}")
        if response.status_code == 200:
            return response.json().get("data")
        else:
            print("Error feacthing product data : {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching product data: {e}")
        return {"error": "failded to fetch product data"}

# Memformat ObjectId MongoDB menjadi string
def format_review_id(review):
    review["_id"] = str(review["_id"])
    return review

@app.route('/reviews', methods=['GET'])
def get_reviews():
    reviews = [format_review_id(review) for review in reviews_collection.find()]
    result = [
        {
            "id": review["_id"],
            "product_id": review["product_id"],
            "review": review["review"],
            "product": get_product_data(review["product_id"])
        }
        for review in reviews
    ]
    return jsonify({"message": "All reviews fetched successfully", "data": result}), 200


@app.route("/products/<int:product_id>/reviews", methods=["GET"])
def get_reviews_by_product(product_id):
    product_data = get_product_data(product_id)
    if not product_data:
        return jsonify({"message": "Product not found"}), 404

    reviews = [format_review_id(review) for review in reviews_collection.find({"product_id": product_id})]
    return jsonify({"message": "Reviews fetched successfully", "data": reviews}), 200

@app.route('/reviews', methods=['POST'])
def create_review():
    data = request.json
    product_id = data.get("product_id")
    ratings = data.get("ratings")
    comment = data.get("comment")

    if not product_id or not ratings or not comment:
        return jsonify({
            "message": "Missing product_id, ratings, or comment"
            }), 400

    product_data = get_product_data(product_id)
    if not product_data:
        return jsonify({"message": "Product not found"}), 404

    review = {
        "product_id": product_id,
        "review": {"ratings": ratings, "comment": comment}
    }

    result = reviews_collection.insert_one(review)
    return jsonify({"message": "Review created successfully", "id": str(result.inserted_id)}), 201


@app.route("/reviews/<string:review_id>", methods=["DELETE"])
def delete_review(review_id):
    result = reviews_collection.delete_one({"_id": ObjectId(review_id)})
    if result.deleted_count == 0:
        return jsonify({"message": "Review not found"}), 404
    return jsonify({"message": "Review deleted"}), 200

# Menjalankan aplikasi Flask pada port 3003
if __name__ == '__main__':
    app.run(debug=True, port=3003, host="0.0.0.0")