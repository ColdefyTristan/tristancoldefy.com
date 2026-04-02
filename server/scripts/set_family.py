"""
Usage:
  python -m scripts.set_family <identifier> [--revoke]

<identifier> peut être un id (entier), un username ou une adresse email.
Par défaut, passe is_family à True. Avec --revoke, passe à False.
"""

import argparse
import sys

from sqlmodel import Session, select

from app.db import engine
from app.models.tables import User, UserEmailAddress


def find_user(session: Session, identifier: str) -> User | None:
    # Try numeric id
    if identifier.isdigit():
        return session.get(User, int(identifier))

    # Try username
    user = session.exec(select(User).where(User.username == identifier)).first()
    if user:
        return user

    # Try email
    email_row = session.exec(
        select(UserEmailAddress).where(UserEmailAddress.email == identifier)
    ).first()
    if email_row:
        return session.get(User, email_row.user_id)

    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Gérer le flag is_family d'un utilisateur.")
    parser.add_argument("identifier", help="id, username ou email de l'utilisateur")
    parser.add_argument("--revoke", action="store_true", help="Passe is_family à False")
    args = parser.parse_args()

    value = not args.revoke

    with Session(engine) as session:
        user = find_user(session, args.identifier)
        if user is None:
            print(f"Utilisateur introuvable : {args.identifier!r}", file=sys.stderr)
            sys.exit(1)

        user.is_family = value
        session.add(user)
        session.commit()

        status = "activé" if value else "désactivé"
        print(f"is_family {status} pour {user.username!r} (id={user.id})")


if __name__ == "__main__":
    main()
