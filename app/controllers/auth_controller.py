from flask import Blueprint, jsonify

from app.models.user import LoginUser, RegisterUser
from app.services.auth_service import AuthService
from app.utilities.validators import validate_json

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


class AuthController:

    def __init__(self):
        self.auth_service = AuthService()

    @auth_bp.route("/register", methods=["POST"])
    @validate_json(RegisterUser)
    def register(self, validated_data: RegisterUser):
        user, error = self.auth_service.register_user(
            name=validated_data.name,
            username=validated_data.username,
            email=validated_data.email,
            password=validated_data.password,
            phone_number=validated_data.phone_number,
        )

        if error:
            return jsonify({"msg": error}), 409

        return (
            jsonify(
                {
                    "msg": "User created",
                    "user": user.model_dump(exclude={"password_hash"}),
                }
            ),
            201,
        )

    @auth_bp.route("/login", methods=["POST"])
    @validate_json(LoginUser)
    def login(self, validated_data: LoginUser):
        result, error = self.auth_service.authenticate_user(
            email=validated_data.email, password=validated_data.password
        )

        if error:
            return jsonify({"msg": error}), 401

        return jsonify(result), 200
