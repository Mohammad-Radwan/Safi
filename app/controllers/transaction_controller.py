from flask import flash, redirect, render_template, request, url_for
from flask_classful import route

from app.controllers.base_controller import BaseController
from app.services import GroupService
from app.services.transaction import TransactionService
from app.utils.exceptions import ResourceNotFound


class TransactionController(BaseController):
    route_prefix = "/transactions"

    def __init__(self):
        super().__init__()
        self.transaction_service = TransactionService()
        self.group_service = GroupService()

    @route("/activity", methods=["GET"])
    def index(self):
        transactions = self.transaction_service.get_user_transactions(
            self.current_user.user_id
        )
        return render_template(
            "activity.html", transactions=transactions, current_user=self.current_user
        )

    @route("/settle", methods=["POST"])
    def settle_up(self):
        pay_to_id = request.form.get("pay_to")
        amount_str = request.form.get("amount", "0")
        group_id = request.form.get("group_id")

        if not group_id or not pay_to_id:
            flash("Invalid settlement details. Missing group or user.", "error")
            return redirect(request.referrer or url_for("dashboard.dashboard_index"))

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive.")

            self.transaction_service.create_settlement(
                payer_id=self.current_user.user_id,
                receiver_id=pay_to_id,
                amount=amount,
                group_id=group_id,
            )
            flash("Settlement request sent! Waiting for confirmation.", "success")
        except ResourceNotFound as e:
            flash(str(e), "error")
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(f"An error occurred during settlement: {str(e)}", "error")

        return redirect(url_for("GroupController:get_group_details", group_id=group_id))

    @route("/<transaction_id>/confirm", methods=["POST"])
    def confirm(self, transaction_id):
        try:
            notification_id = None
            if request.is_json:
                notification_id = request.json.get("notification_id")

            self.transaction_service.confirm_transaction(
                transaction_id, notification_id
            )
            if request.is_json:
                return {"status": "success", "message": "Transaction confirmed!"}, 200

            # Form submission fallback (if any)
            flash("Transaction confirmed.", "success")
        except ResourceNotFound as e:
            if request.is_json:
                return {"status": "error", "message": str(e)}, 404
            flash(str(e), "error")
        except Exception as e:
            if request.is_json:
                return {"status": "error", "message": f"Internal error: {str(e)}"}, 500
            flash(f"An error occurred: {str(e)}", "error")

        return redirect(request.referrer or url_for("dashboard.activity"))

    @route("/<transaction_id>/reject", methods=["POST"])
    def reject(self, transaction_id):
        try:
            notification_id = None
            if request.is_json:
                notification_id = request.json.get("notification_id")

            self.transaction_service.reject_transaction(transaction_id, notification_id)
            if request.is_json:
                return {"status": "success", "message": "Transaction rejected!"}, 200
            flash("Transaction rejected.", "success")
        except ResourceNotFound as e:
            if request.is_json:
                return {"status": "error", "message": str(e)}, 404
            flash(str(e), "error")
        except Exception as e:
            if request.is_json:
                return {"status": "error", "message": f"Internal error: {str(e)}"}, 500
            flash(f"An error occurred: {str(e)}", "error")

        return redirect(request.referrer or url_for("dashboard.activity"))
