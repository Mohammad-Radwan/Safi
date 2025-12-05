from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/")
def list_users():
    return {"message": "User authentication endpoint"}
