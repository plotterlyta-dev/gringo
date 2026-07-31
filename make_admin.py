"""
Usage: python make_admin.py user@example.com

Promotes an existing registered user to admin. Run this after registering
a normal account for yourself through the website — there's deliberately
no way to become an admin through the UI itself.
"""
import sys
import db

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    db.init_db()
    user = db.query_one("SELECT * FROM users WHERE email = ?", (email,))
    if not user:
        print(f"No user found with email {email}. Register an account on the site first.")
        sys.exit(1)

    db.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
    print(f"✅ {email} is now an admin. They can sign in at /admin/login with their normal password.")
