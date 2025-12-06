from functools import wraps

from flask import jsonify, request
from pydantic import ValidationError


def validate_json(schema_model):
    """
    Decorator to validate JSON request body against a Pydantic model.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not request.is_json:
                    return (
                        jsonify(
                            {
                                "msg": "Request must be JSON (Content-Type: application/json)"
                            }
                        ),
                        400,
                    )

                data = schema_model.model_validate(request.get_json())

                return f(validated_data=data, *args, **kwargs)

            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = " -> ".join(str(loc) for loc in error["loc"])
                    msg = error["msg"]
                    errors.append({"field": field, "message": msg})
                return jsonify({"msg": "Validation error", "errors": errors}), 422

        return decorated_function

    return decorator
