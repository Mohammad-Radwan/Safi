from dataclasses import dataclass
from typing import List


@dataclass
class User:
    user_id: str
    name: str


@dataclass
class SharedExpense:
    participant: User
    amount: float


@dataclass
class Expense:
    payer: User
    total_amount: float
    splits: List[SharedExpense]


def calculate_balances(
    current_user: User, expenses: List[Expense], group_members: List[User]
):
    member_balances = {member.user_id: 0.0 for member in group_members}

    for expense in expenses:
        payer = expense.payer
        for split in expense.splits:
            participant = split.participant
            amount = split.amount

            # If current user paid, participant owes current user (positive balance for participant)
            if (
                payer.user_id == current_user.user_id
                and participant.user_id != current_user.user_id
            ):
                member_balances[participant.user_id] += amount

            # If current user participated but didn't pay, current user owes payer (negative balance for payer)
            elif (
                participant.user_id == current_user.user_id
                and payer.user_id != current_user.user_id
            ):
                member_balances[payer.user_id] -= amount

    return member_balances


# Test Data
me = User("me", "Me")
alice = User("alice", "Alice")
bob = User("bob", "Bob")

# Case 1: I paid 300, splits 100 each. Alice owes me 100, Bob owes me 100.
e1 = Expense(
    payer=me,
    total_amount=300,
    splits=[SharedExpense(me, 100), SharedExpense(alice, 100), SharedExpense(bob, 100)],
)

# Case 2: Alice paid 90, we split 3 ways (30 each). I owe Alice 30. Bob owes Alice 30 (irrelevant to me).
e2 = Expense(
    payer=alice,
    total_amount=90,
    splits=[SharedExpense(me, 30), SharedExpense(alice, 30), SharedExpense(bob, 30)],
)

expenses = [e1, e2]
group_members = [me, alice, bob]

balances = calculate_balances(me, expenses, group_members)

print("Balances:")
for uid, bal in balances.items():
    if uid == me.user_id:
        continue
    print(f"{uid}: {bal}")

# Expectation:
# Alice: +100 (from e1) - 30 (from e2) = +70
# Bob: +100 (from e1) = +100
assert balances["alice"] == 70.0
assert balances["bob"] == 100.0
print("Verification Success!")
