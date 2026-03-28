from datetime import datetime

from flask import jsonify


def serialize_document(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_document(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_document(item) for key, item in value.items()}
    return value


def success_response(data=None, message: str = "OK", status: int = 200):
    payload = {
        "message": message,
        "data": serialize_document(data),
    }
    return jsonify(payload), status


def error_response(message: str, status: int, details=None):
    payload = {
        "message": message,
        "errors": serialize_document(details or {}),
    }
    return jsonify(payload), status