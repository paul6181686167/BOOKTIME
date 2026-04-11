"""
Script admin : réinitialiser le mot de passe d'un utilisateur directement en base.
Usage : python reset_password_admin.py
"""
import os
import sys
import getpass
import bcrypt
from pymongo import MongoClient

MONGO_URL = (
    "mongodb+srv://berruyerpaul222_db_user:TggFAId06ZwWKEPC"
    "@booktime-prod.wnnbmls.mongodb.net/"
    "?retryWrites=true&w=majority"
)

def main():
    print("=== Réinitialisation de mot de passe (admin) ===\n")
    email = input("Email du compte : ").strip().lower()
    if not email:
        print("Email vide. Abandon.")
        sys.exit(1)

    new_password = getpass.getpass("Nouveau mot de passe (invisible) : ")
    if len(new_password) < 6:
        print("Mot de passe trop court (minimum 6 caractères). Abandon.")
        sys.exit(1)

    confirm = getpass.getpass("Confirmer le mot de passe : ")
    if new_password != confirm:
        print("Les mots de passe ne correspondent pas. Abandon.")
        sys.exit(1)

    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)
    db = client["booktime"]
    users = db["users"]

    user = users.find_one({"email": email})
    if not user:
        print(f"Aucun compte trouvé pour '{email}'.")
        sys.exit(1)

    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    result = users.update_one(
        {"email": email},
        {"$set": {"password_hash": new_hash}, "$unset": {"reset_token": "", "reset_token_expires": ""}}
    )

    if result.modified_count == 1:
        print(f"\n✅ Mot de passe mis à jour pour '{email}'.")
    else:
        print("❌ Mise à jour échouée.")

if __name__ == "__main__":
    main()
