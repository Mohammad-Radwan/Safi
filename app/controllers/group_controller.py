from flask import flash, redirect, render_template, request, session, url_for
from flask_classful import route

from app.controllers.base_controller import BaseController
from app.models.group import GroupCreationRequest
from app.services import ExpenseService, GroupService, TransactionService
from app.utils.decorators import require_group_admin
from app.utils.exceptions import CreationError, ResourceAlreadyExists, ResourceNotFound


class GroupController(BaseController):
    route_prefix = "/groups"

    def __init__(self):
        super().__init__()
        self.group_service = GroupService()
        self.expense_service = ExpenseService()
        self.transaction_service = TransactionService()

    @route("/create", methods=["POST"])
    def create_group(self):
        group_request = GroupCreationRequest(**request.form.to_dict())
        new_group = self.group_service.create_new_group(
            group_request, first_member_id=self.current_user.user_id
        )
        self.group_service.save_new_group(new_group)

        flash("Group created successfully!", "success")
        return redirect(url_for("GroupController:list_groups"))

    @route("/join", methods=["POST"])
    def join_group(self):
        invite_code = request.form.get("invite_code")
        try:
            self.group_service.join_group_by_code(
                self.current_user.user_id, invite_code
            )
            flash("Joined group successfully!", "success")
        except (ResourceNotFound, CreationError, ResourceAlreadyExists) as e:
            flash(e.message, "error")

        return redirect(url_for("GroupController:list_groups"))

    @route("/<group_id>/invite", methods=["POST"])
    @require_group_admin
    def invite_member(self, group_id):
        email = request.form.get("email")
        try:
            self.group_service.invite_member(self.current_user.user_id, group_id, email)
            flash("Invitation sent successfully!", "success")
        except (ResourceNotFound, CreationError, ResourceAlreadyExists) as e:
            flash(e.message, "error")
        return redirect(url_for("GroupController:get_group_details", group_id=group_id))

    @route("/<group_id>/respond", methods=["POST"])
    def respond_to_invite(self, group_id):
        is_json = request.is_json or request.content_type == "application/json"

        action = request.form.get("action")
        notification_id = request.form.get("notification_id")

        if is_json:
            data = request.get_json()
            action = data.get("action")
            notification_id = data.get("notification_id")

        try:
            self.group_service.respond_to_invite(
                self.current_user.user_id, group_id, action, notification_id
            )
            if is_json:
                return {"status": "success", "message": f"Invitation {action}ed!"}, 200

            flash(f"Invitation {action}ed!", "success")
        except (ResourceNotFound, ValueError) as e:
            message = getattr(e, "message", str(e))
            if is_json:
                return {"status": "error", "message": message}, 400
            flash(message, "error")

        return redirect(url_for("GroupController:list_groups"))

    @route("/<group_id>/invite/refresh", methods=["POST"])
    @require_group_admin
    def refresh_invite_code(self, group_id):
        try:
            self.group_service.refresh_invite_code(self.current_user.user_id, group_id)
            flash("Invite code regenerated successfully!", "success")
        except (ResourceNotFound, CreationError) as e:
            flash(e.message, "error")
        return redirect(url_for("GroupController:get_group_details", group_id=group_id))

    @route("/<group_id>/leave", methods=["POST"])
    def leave_group(self, group_id):
        successor_id = request.form.get("successor_id")
        try:
            self.group_service.leave_group(
                self.current_user.user_id, group_id, successor_id
            )
            flash("You have left the group.", "success")
        except (ResourceNotFound, CreationError) as e:
            flash(e.message, "error")
            return redirect(
                url_for("GroupController:get_group_details", group_id=group_id)
            )
        return redirect(url_for("GroupController:list_groups"))

    @route("/<group_id>/update", methods=["POST"])
    @require_group_admin
    def update_group(self, group_id):
        new_name = request.form.get("new_group_name")
        new_description = request.form.get("new_group_description")
        try:
            self.group_service.update_group_info(group_id, new_name, new_description)
            flash("Group updated successfully!", "success")
        except (ResourceNotFound, CreationError) as e:
            flash(e.message, "error")
        return redirect(url_for("GroupController:get_group_details", group_id=group_id))

    @route("/<group_id>/members/remove", methods=["POST"])
    @require_group_admin
    def remove_member(self, group_id):
        member_id = request.form.get("member_id")

        if not self._is_user_settled(group_id, member_id):
            flash(
                "Cannot remove member. They must be fully settled with all group members first.",
                "error",
            )
            return redirect(
                url_for("GroupController:get_group_details", group_id=group_id)
            )

        try:
            self.group_service.remove_member(group_id, member_id)
            flash("Member removed successfully!", "success")
        except (ResourceNotFound, CreationError) as e:
            flash(e.message, "error")
        return redirect(url_for("GroupController:get_group_details", group_id=group_id))

    def _is_user_settled(self, group_id: str, user_id: str) -> bool:
        """
        Check if a user has settled all debts within the group.
        This checks bilateral balances with ALL other group members.
        """
        expenses = self.expense_service.get_group_expenses(group_id)
        transactions = self.transaction_service.get_group_transactions(group_id)
        group = self.group_service.get_group(group_id)

        # Map: other_user_id -> balance (positive means user_id is owed, negative means user_id owes)
        balances = {m.user_id: 0.0 for m in group.members if m.user_id != user_id}

        # 1. Process Expenses
        for expense in expenses:
            payer_id = expense.payer.user_id
            for split in expense.splits:
                participant_id = split.participant.user_id
                amount = split.amount

                # If user paid for other -> user is owed (positive)
                if payer_id == user_id and participant_id in balances:
                    balances[participant_id] += amount

                # If other paid for user -> user owes (negative)
                elif participant_id == user_id and payer_id in balances:
                    balances[payer_id] -= amount

        # 2. Process Transactions (Settlements)
        for trans in transactions:
            payer_id = trans.payer.user_id
            receiver_id = trans.receiver.user_id
            amount = trans.amount

            # If user paid other -> user reduces debt to other OR creates credit (positive impact for user)
            # e.g A owes B 50. A pays B 50. A's balance with B goes -50 + 50 = 0.
            if payer_id == user_id and receiver_id in balances:
                balances[receiver_id] += amount

            # If other paid user -> user's credit from other is satisfied OR debt created (negative impact for user)
            # e.g A is owed 50 by B. B pays A 50. A's balance with B goes +50 - 50 = 0.
            elif receiver_id == user_id and payer_id in balances:
                balances[payer_id] -= amount

        # Check if all balances are effectively zero
        for bal in balances.values():
            if abs(bal) > 0.01:  # Allow small floating point epsilon
                return False

        return True

    @route("/<group_id>/assign_admin", methods=["POST"])
    @require_group_admin
    def assign_admin(self, group_id):
        new_admin_id = request.form.get("new_admin_id")
        try:
            self.group_service.assign_new_first_member(
                self.current_user.user_id, group_id, new_admin_id
            )
            flash("Admin privileges transferred successfully!", "success")
        except (ResourceNotFound, CreationError) as e:
            flash(e.message, "error")
        return redirect(url_for("GroupController:get_group_details", group_id=group_id))

    @route("/<string:group_id>/details", methods=["GET"])
    def get_group_details(self, group_id: str):
        group = self.group_service.get_group(group_id)
        expenses = self.expense_service.get_group_expenses(group_id)

        user_shares = []
        for expense in expenses:
            involved_users = [split.participant.user_id for split in expense.splits]
            if self.current_user.user_id not in involved_users:
                user_shares.append(0.0)
                continue

            share = -expense.total_amount / len(expense.splits)
            if expense.payer.user_id == self.current_user.user_id:
                share += expense.total_amount
            user_shares.append(round(share, 2))

        # Calculate balance per member relative to current user
        member_balances = {member.user_id: 0.0 for member in group.members}

        for expense in expenses:
            payer_id = expense.payer.user_id
            for split in expense.splits:
                participant_id = split.participant.user_id
                amount = split.amount

                # Case 1: Current user paid for someone else -> They owe current user (+)
                if (
                    payer_id == self.current_user.user_id
                    and participant_id != self.current_user.user_id
                ):
                    if participant_id in member_balances:
                        member_balances[participant_id] += amount

                # Case 2: Someone else paid for current user -> Current user owes them (-)
                elif (
                    participant_id == self.current_user.user_id
                    and payer_id != self.current_user.user_id
                ):
                    if payer_id in member_balances:
                        member_balances[payer_id] -= amount

        # Round balances
        for uid in member_balances:
            member_balances[uid] = round(member_balances[uid], 2)

        is_admin = False
        if group.first_member.user_id == self.current_user.user_id:
            self.group_service.refresh_invite_code(self.current_user.user_id, group_id)
            is_admin = True

        # determining back endpoint logic
        # if the user came from dashboard or groups list, store that preference
        if request.referrer:
            if "dashboard" in request.referrer:
                session[f"return_to_{group_id}"] = "dashboard.dashboard_index"
            elif "groups/list" in request.referrer:
                session[f"return_to_{group_id}"] = "GroupController:list_groups"

        # default to groups list if nothing stored or known
        back_endpoint = session.get(
            f"return_to_{group_id}", "GroupController:list_groups"
        )

        return render_template(
            "group_details.html",
            group=group,
            expenses=list(zip(expenses, user_shares)),
            your_balance=round(sum(user_shares), 2),
            member_balances=member_balances,
            current_user=self.current_user,
            is_admin=is_admin,
            back_endpoint=back_endpoint,
        )

    @route("/list", methods=["GET"])
    def list_groups(self):
        user_id = self.current_user.user_id
        # Always fetch all groups for client-side filtering
        groups = self.group_service.get_user_groups(user_id, status="all")
        groups = [group for group in groups]

        # sort groups by active first then alphabetically
        groups.sort(key=lambda group: (not group.is_active, group.group_name))

        return render_template(
            "groups.html",
            groups=groups,
            current_user=self.current_user,
        )

    @route("/<group_id>/members", methods=["GET"])
    def get_group_members(self, group_id):
        group = self.group_service.get_group(group_id)
        if not group:
            raise ResourceNotFound("Group not found.")

        members = [
            {"user_id": member.user_id, "name": member.name} for member in group.members
        ]
        return {"members": members}

    @require_group_admin
    @route("/<group_id>/delete", methods=["POST"])
    def delete_group(self, group_id: str):
        try:
            self.group_service.delete_group(group_id)
            flash("Group deleted successfully!", "success")
        except (ResourceNotFound, CreationError) as e:
            flash(e.message, "error")
            return redirect(
                url_for("GroupController:get_group_details", group_id=group_id)
            )
        return redirect(url_for("GroupController:list_groups"))

    @require_group_admin
    @route("/<group_id>/restore", methods=["POST"])
    def restore_group(self, group_id: str):
        try:
            self.group_service.restore_group(self.current_user.user_id, group_id)
            flash("Group restored successfully!", "success")
        except (ResourceNotFound, CreationError) as e:
            flash(e.message, "error")
        return redirect(url_for("GroupController:get_group_details", group_id=group_id))
