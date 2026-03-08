from flask import Blueprint, jsonify, request
from utils import create_provider, update_provider, health_check
bill_bp = Blueprint('bill', __name__)

@bill_bp.route("/health", methods=["GET"])
def get_health():
    alive = health_check()
    if alive:
        return jsonify({"message": "Ok"}), 200
    else:
        return jsonify({"message": "Failure"}), 500

@bill_bp.route("/provider", methods=["POST"])
def create_provider_route():
    data = request.get_json()
    name = data.get("name") if data else None
    if not name:
        return jsonify({"error": "name required"}), 400

    provider_id, err = create_provider(name)
    if err:
        return jsonify({"error": err}), 409

    return jsonify({"id": str(provider_id)}), 201


@bill_bp.route("/provider/<int:id>", methods=["PUT"])
def update_provider_route(id):
    data = request.get_json()
    name = data.get("name") if data else None
    if not name:
        return jsonify({"error": "name required"}), 400

    success, err = update_provider(id, name)
    if not success:
        status = 404 if "not found" in err else 409
        return jsonify({"error": err}), status

    return jsonify({"message": "updated"}), 200