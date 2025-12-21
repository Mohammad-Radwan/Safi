from typing import Optional

from app.events.signals import (
    confirmation_requested,
    expense_created,
    invite_sent,
    transaction_confirmed,
)
from app.models import Expense, GroupSchema, NotificationSchema, Transaction, User
from app.repositories import NotificationRepository


def handle_involved_users(sender, expense: Expense, **extra):
    notify_repo = NotificationRepository()

    for shared_expense in expense.splits:
        if shared_expense.participant.user_id != expense.payer.user_id:
            message = (
                f"<b>{expense.payer.name}</b> has paid a new expense of <b>{expense.total_amount}EGP</b> "
                f"in <b>{expense.group.group_name}</b>.<br>"
                f"Description: {expense.description}.<br>"
                f"You should participate with <b>{shared_expense.amount}EGP</b> in this expense."
            )
            notification = NotificationSchema(
                user_id=shared_expense.participant.user_id,
                message=message,
                timestamp=expense.date,
            )
            notify_repo.add(notification)


def handle_User_invite(sender, group_schema: GroupSchema, user: User, **extra):
    notify_repo = NotificationRepository()

    notification = NotificationSchema(
        user_id=user.user_id,
        message=f"You have been invited to join group: {group_schema.group_name}",
        type="invite",
        payload={
            "group_id": group_schema.group_id,
            "group_name": group_schema.group_name,
            "first_member": group_schema.first_member_id,
        },
    )
    notify_repo.add(notification)


def handle_confirmation_requested(sender, transaction: Transaction, **extra):
    notify_repo = NotificationRepository()

    message = (
        f"{transaction.payer.name} has made a transaction of {transaction.amount}EGP."
        f"Did you receive it?"
    )

    notification = NotificationSchema(
        user_id=transaction.receiver.user_id,
        message=message,
        type="confirmation",
        payload={"transaction_id": transaction.transaction_id},
    )
    notify_repo.add(notification)


def update_notification_status(
    transaction: Transaction, status: str, notification_id: Optional[str] = None
):
    notify_repo = NotificationRepository()

    if notification_id:
        # Direct update (robust)
        notification = notify_repo.get_by_id(notification_id)
        if notification:
            new_payload = notification.payload.copy()
            new_payload["status"] = status
            updated_notif = notification.model_copy(
                update={"payload": new_payload, "is_read": True}
            )
            notify_repo.update(notification_id, updated_notif)
        return

    # Fallback to searching by user and logic (less robust)
    notifications = notify_repo.get_all_by_user(transaction.receiver.user_id)
    for notif in notifications:
        if (
            notif.type == "confirmation"
            and notif.payload
            and notif.payload.get("transaction_id") == transaction.transaction_id
        ):

            # Update payload
            new_payload = notif.payload.copy()
            new_payload["status"] = status

            updated_notif = notif.model_copy(
                update={"payload": new_payload, "is_read": True}
            )
            notify_repo.update(notif.notification_id, updated_notif)
            break


def handle_transaction_confirmed(
    sender, transaction: Transaction, notification_id: Optional[str] = None, **extra
):
    notify_repo = NotificationRepository()

    # Update existing notification for the receiver
    update_notification_status(transaction, "confirmed", notification_id)

    message = f"Your transaction of {transaction.amount}EGP to {transaction.receiver.name} has been confirmed."

    notification = NotificationSchema(
        user_id=transaction.payer.user_id,
        message=message,
        payload={"transaction_id": transaction.transaction_id},
    )
    notify_repo.add(notification)


def handle_transaction_rejected(
    sender, transaction: Transaction, notification_id: Optional[str] = None, **extra
):
    # Update existing notification for the receiver
    update_notification_status(transaction, "rejected", notification_id)

    # Optionally notify the payer as well? Maybe "Your settlement request was rejected."
    notify_repo = NotificationRepository()
    message = f"Your transaction of {transaction.amount}EGP to {transaction.receiver.name} has been rejected."
    notification = NotificationSchema(
        user_id=transaction.payer.user_id,
        message=message,
        payload={"transaction_id": transaction.transaction_id},
    )
    notify_repo.add(notification)


def enable_notifications(app):
    expense_created.connect(handle_involved_users)
    invite_sent.connect(handle_User_invite)
    confirmation_requested.connect(handle_confirmation_requested)
    transaction_confirmed.connect(handle_transaction_confirmed)
    from app.events.signals import transaction_rejected

    transaction_rejected.connect(handle_transaction_rejected)
