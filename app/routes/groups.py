from flask import Blueprint

groups_bp = Blueprint("groups", __name__, url_prefix="/groups")


@groups_bp.get("/")
def list_users():
    return {"message": "list all groups"}
