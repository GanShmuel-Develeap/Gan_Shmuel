from flask import Blueprint, jsonify, request,send_file
from utils import create_provider, update_provider, upload_rates, get_rates_file_path
bill_bp = Blueprint('bill', __name__)

@bill_bp.route("/health", methods=["GET"])
def get_health():
    return jsonify({"message": "Ok"}), 200

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






