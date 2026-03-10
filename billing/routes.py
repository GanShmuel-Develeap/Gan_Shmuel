from flask import Blueprint, jsonify, request, send_file, send_from_directory
from utils import create_provider, update_provider, create_truck, update_truck, get_truck, health_check

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


@bill_bp.route("/truck", methods=["POST"])
def create_truck_route():
    data = request.get_json()
    provider_id = data.get("provider") if data else None
    truck_id = data.get("id") if data else None

    if not provider_id or not truck_id:
        return jsonify({"error": "id and provider required"}), 400

    success, err = create_truck(truck_id, provider_id)
    if err:
        status = 404 if "not found" in err else 409
        return jsonify({"error": err}), status

    return jsonify({"id": truck_id}), 201


@bill_bp.route("/truck/<string:id>", methods=["PUT"])
def update_truck_route(id):
    data = request.get_json()
    provider_id = data.get("provider") if data else None

    if not provider_id:
        return jsonify({"error": "provider required"}), 400

    success, err = update_truck(id, provider_id)
    if not success:
        status = 404 if "not found" in err else 409
        return jsonify({"error": err}), status

    return jsonify({"message": "updated"}), 200


@bill_bp.route("/truck/<string:id>", methods=["GET"])
def get_truck_route(id):
    from_dt = request.args.get("from")   # yyyymmddhhmmss, default: 1st of month
    to_dt = request.args.get("to")       # yyyymmddhhmmss, default: now

    truck, err = get_truck(id, from_dt, to_dt)
    if err:
        return jsonify({"error": err}), 404

    return jsonify(truck), 200

@bill_bp.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

