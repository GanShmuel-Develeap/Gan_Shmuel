from flask import Blueprint, jsonify

bill_bp = Blueprint('bill', __name__)

@bill_bp.route("/provider")
def get_provider():
    return jsonify({"message": "Ok"}), 200

@bill_bp.route("/provider/<id>")
def get_provider_id(id):
    return jsonify({"message": "Ok"}), 200

@bill_bp.route("/health")
def get_health():
    return jsonify({"message": "Ok"}), 200