from flask import Blueprint

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.get("/")
def list_users():
    return {"message": "list all users"}
