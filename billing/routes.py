from flask import Blueprint, jsonify, request

bill_bp = Blueprint('bill', __name__)

@bill_bp.route("/provider", methods=["POST"])
def create_provider():
    data = request.get_json()
    name = data.get("name")
    if not name:
        return {"error": "name required"}, 400

@bill_bp.route("/provider/<id>")
def get_provider_id(id):
    return jsonify({"message": "Ok"}), 200

@bill_bp.route("/health", methods=["GET"])
def get_health():
    return jsonify({"message": "Ok"}), 200