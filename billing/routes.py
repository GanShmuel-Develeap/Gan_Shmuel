from flask import Blueprint, jsonify, request,send_file
from utils import create_provider, update_provider, upload_rates, get_rates_file_path,health_check
from utils import get_truck, create_truck, update_truck
import mysql.connector
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

@bill_bp.route("/rates", methods=["POST"])
def post_rates():
    data = request.get_json(silent=True)
    filename = data.get("file") if data else None
    if not filename:
        return jsonify({"error": "file parameter required"}), 400

    try:
        rows_updated, err = upload_rates(filename)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except mysql.connector.IntegrityError as e:
        return jsonify({"error": f"Invalid provider_id in XL file"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    if err:
        status = 404 if "not found" in err.lower() else 400
        return jsonify({"error": err}), status

    return jsonify({"message": "rates updated", "rows_processed": rows_updated}), 200


@bill_bp.route("/rates", methods=["GET"])
def get_rates():
    path, err = get_rates_file_path()
    if err:
        return jsonify({"error": err}), 404

    return send_file(
        path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="rates.xlsx"
    )



# ---------------- Create Truck ----------------
@bill_bp.route("/truck", methods=["POST"])
def create_truck_route():
    data = request.get_json()
    truck_id = data.get("id") if data else None
    provider_id = data.get("provider") if data else None

    if not truck_id or not provider_id:
        return jsonify({"error": "truck id and provider id required"}), 400

    success, err = create_truck(truck_id, provider_id)
    if not success:
        return jsonify({"error": err}), 409
    return jsonify({"message": "Truck created successfully"}), 201

# ---------------- Update Truck ----------------
@bill_bp.route("/truck/<string:truck_id>", methods=["PUT"])
def update_truck_route(truck_id):

    data = request.get_json()
    provider_id = data.get("provider") if data else None

    if not provider_id:
        return jsonify({"error": "provider id required"}), 400

    success, err = update_truck(truck_id, provider_id)
    if not success:
        return jsonify({"error": err}), 404

    return jsonify({"id": truck_id, "provider": provider_id}), 200

# ---------------- Get Truck ----------------
@bill_bp.route("/truck/<string:truck_id>", methods=["GET"])
def get_truck_route(truck_id):

    from_dt = request.args.get("from")
    to_dt = request.args.get("to")

    truck_data, err = get_truck(truck_id, from_dt=from_dt, to_dt=to_dt)
    if err:
        return jsonify({"error": err}), 404

    return jsonify(truck_data), 200

