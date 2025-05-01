import pyotp
import qrcode
import os
import json
import time

SECRET_FILE = 'secret.json'
LOCK_FILE = 'lock.json'
MAX_ATTEMPTS = 5
LOCK_DURATION = 60
EMAIL = "saly@example.com"
PASSWORD = "saly"  

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

def load_lock_info():
    try:
        with open(LOCK_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'attempts': 0, 'lock_until': 0}

def save_lock_info(attempts, lock_until):
    with open(LOCK_FILE, 'w') as f:
        json.dump({'attempts': attempts, 'lock_until': lock_until}, f)

def reset_lock_info():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def setup_2fa():
    if load_secret():
        print("2FA is already set up. No need to scan a new QR code.")
        return True

    secret = pyotp.random_base32()
    save_secret(secret)
    print(f"Secret key (save this securely): {secret}")

    uri = pyotp.TOTP(secret).provisioning_uri(
        name=EMAIL,
        issuer_name="MyConsoleApp"
    )

    print("\nSteps to Set Up 2FA with Microsoft Authenticator:")
    print("1. Open Microsoft Authenticator on your phone and tap 'Scan a QR code'")
    print("2. Scan the QR code displayed on your PC screen")
    print("3. Enter the 6-digit code shown in the app into the console")

    qrcode.make(uri).show()

    code = input("\nEnter the 6-digit code from Microsoft Authenticator to verify setup: ")
    if pyotp.TOTP(secret).verify(code):
        print("Code verified — 2FA setup complete.")
        return True
    else:
        print("Invalid code. Setup failed.")
        return False

def login_with_authenticator():
    lock_info = load_lock_info()
    now = time.time()

    if now < lock_info['lock_until']:
        remaining = int(lock_info['lock_until'] - now)
        print(f"\n======Too many failed attempts. Please try again in {remaining} seconds.======")
        return False

    secret = load_secret()
    if not secret:
        print("\n======No 2FA setup found. Setting up now...======")
        if not setup_2fa():
            return False
        secret = load_secret()

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        code = input("Enter the 6-digit code from Microsoft Authenticator: ")
        if pyotp.TOTP(secret).verify(code):
            print("Code verified — you are logged in.")
            reset_lock_info()
            return True
        else:
            attempts += 1
            print(f"\n======Invalid code. Attempt {attempts} of {MAX_ATTEMPTS}.======")

    lock_until = time.time() + LOCK_DURATION
    save_lock_info(attempts, lock_until)
    print(f"\n======Too many failed attempts. You are locked out for {LOCK_DURATION} seconds.======")
    return False

def login_with_email_password():
    email = input("Enter email: ")
    password = input("Enter password: ")

    if email == EMAIL and password == PASSWORD:
        print("Login successful with email and password.")
        return True
    else:
        print("Invalid email or password.")
        return False

def main():
    is_logged_in = False

    while True:
        if not is_logged_in:
            print("\nWelcome. Choose a login method:")
            print("1. Login with email and password")
            print("2. Login with Authenticator (email only)")
            print("3. Exit")

            choice = input("Enter 1, 2, or 3: ")

            if choice == "1":
                is_logged_in = login_with_email_password()
            elif choice == "2":
                email = input("Enter email: ")
                secret = load_secret()
                if email == EMAIL:
                    if secret:
                        is_logged_in = login_with_authenticator()
                    else:
                        print("\n======2FA is not set up for this account.======")
                else:
                    print("\n======Email not recognized.======")
            elif choice == "3":
                print("Exiting.")
                break
            else:
                print("\n======Invalid selection.======")
        else:
            print("\n======You are logged in.======")
            secret = load_secret()
            if not secret:
                # print("\n======Note: 2FA is not enabled.======")
                print("1. Set up 2FA")
                print("2. Logout")
            else:
                print("1. Logout")

            choice = input("Enter your choice: ")

            if choice == "1" and not secret:
                setup_2fa()
            elif (choice == "1" and secret) or (choice == "2" and not secret):
                is_logged_in = False
                print("\n======You have been logged out.======")
            else:
                print("\n======Invalid choice.======")

if __name__ == "__main__":
    main()
