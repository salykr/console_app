import pyotp
import qrcode
import os
import json
import tkinter as tk
from PIL import ImageTk, Image

SECRET_FILE = 'secret.json'

def save_secret(secret):
    with open(SECRET_FILE, 'w') as f:
        json.dump({'secret': secret}, f)

def load_secret():
    try:
        with open(SECRET_FILE, 'r') as f:
            return json.load(f)['secret']
    except FileNotFoundError:
        return None

def delete_secret():
    if os.path.exists(SECRET_FILE):
        os.remove(SECRET_FILE)


def setup_2fa():
    if load_secret():
        print("2FA is already set up. No need to scan a new QR code.")
        return True

    # generates a secure random key
    secret = pyotp.random_base32()
    save_secret(secret)
    print(f"Secret key (save this securely): {secret}")

    #creates a URI with: secret key, email, app name
    uri = pyotp.TOTP(secret).provisioning_uri(
        name="saly@example.com",
        issuer_name="MyConsoleApp"
    )

    print("\nScan this QR code in Microsoft Authenticator:")
    qrcode.make(uri).show()

    code = input("\nEnter the 6-digit code from Microsoft Authenticator to verify setup: ")
    if pyotp.TOTP(secret).verify(code):
        print("Code verified — 2FA setup complete.")
        return True
    else:
        print("Invalid code. Setup failed.")
        # delete_secret()
        return False

def login():
    secret = load_secret()
    if not secret:
        print("No 2FA setup found. Please run setup first.")
        return False

    code = input("\nEnter the 6-digit code from Microsoft Authenticator: ")
    if pyotp.TOTP(secret).verify(code):
        print("Code verified — you are logged in.")
        return True
    else:
        print("Invalid code. Login failed.")
        return False

def main():
    is_logged_in = False

    while True:
        print("\n=== 2FA Console App ===")
        if is_logged_in:
            print("1. Logout")
            print("2. Exit")
        else:
            print("1. Setup 2FA")
            if load_secret():
                print("2. Login")
                print("3. Exit")
            else:
                print("2. Exit")

        choice = input("\nEnter your choice: ")

        if is_logged_in:
            if choice == "1":
                is_logged_in = False
                print("You have been logged out.")
            elif choice == "2":
                print("Logged Out.")
                break
            else:
                print("Invalid choice. Please try again.")
        else:
            if choice == "1":
                setup_2fa()
            elif choice == "2" and load_secret():
                if login():
                    is_logged_in = True
            elif choice == "3" or (choice == "2" and not load_secret()):
                print("Logged Out.")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
