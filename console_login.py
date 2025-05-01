import pyotp
import qrcode
import os
import json
import time

SECRET_FILE = 'secret.json'
LOCK_FILE = 'lock.json'
MAX_ATTEMPTS = 5
LOCK_DURATION = 120  # 2 minutes in seconds
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
            lock_data = json.load(f)
            # Auto-delete expired lock
            if time.time() > lock_data.get('lock_until', 0):
                reset_lock_info()
                return {'attempts': 0, 'lock_until': 0, 'email': ''}
            return lock_data
    except (FileNotFoundError, json.JSONDecodeError):
        return {'attempts': 0, 'lock_until': 0, 'email': ''}

def save_lock_info(attempts, lock_until, email):
    with open(LOCK_FILE, 'w') as f:
        json.dump({
            'attempts': attempts,
            'lock_until': lock_until,
            'email': email
        }, f)

def reset_lock_info():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def check_user_lock(email):
    lock_info = load_lock_info()
    now = time.time()
    
    if lock_info['email'] == email and now < lock_info['lock_until']:
        remaining = int(lock_info['lock_until'] - now)
        print(f"\n======Too many failed attempts for {email}. Try again in {remaining} seconds.======")
        return True
    return False

def setup_2fa():
    if load_secret():
        print("\n======2FA is already set up. No need to scan a new QR code.======")
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
        print("\n======Invalid code. Setup failed.======")
        return False

def login_with_authenticator(email):
    if check_user_lock(email):
        return False

    secret = load_secret()
    if not secret:
        print("\n======No 2FA setup found. Setting up now...======")
        if not setup_2fa():
            return False
        secret = load_secret()

    lock_info = load_lock_info()
    attempts = 0
    
    while attempts < MAX_ATTEMPTS:
        code = input("Enter the 6-digit code from Microsoft Authenticator: ")
        if pyotp.TOTP(secret).verify(code):
            print("Code verified — you are logged in.")
            reset_lock_info()
            return True
        else:
            attempts += 1
            remaining_attempts = MAX_ATTEMPTS - attempts
            print(f"\n======Invalid code. {remaining_attempts} attempts remaining.======")

    save_lock_info(attempts, time.time() + LOCK_DURATION, email)
    print(f"\n======Too many failed attempts for {email}. Locked for {LOCK_DURATION} seconds.======")
    return False

def login_with_email_password():
    email = input("Enter email: ")
    if email != EMAIL:
        print("\n======Email not recognized.======")
        return False

    if check_user_lock(email):
        return False

    lock_info = load_lock_info()
    attempts = 0
    
    while attempts < 3:
        password = input("Enter password: ")
        if password == PASSWORD:
            print("Login successful with email and password.")
            reset_lock_info()
            return True
        else:
            attempts += 1
            remaining_attempts = 3 - attempts
            print(f"Invalid password. {remaining_attempts} attempts remaining.")

    print("\n======Too many failed password attempts.======")
    if load_secret():
        print("Please enter the 6-digit code from Microsoft Authenticator.")
        return login_with_authenticator(email)
    else:
        save_lock_info(attempts, time.time() + LOCK_DURATION, email)
        print("2FA is not set up for this account. Access denied.")
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
                if email == EMAIL:
                    is_logged_in = login_with_authenticator(email)
                else:
                    print("\n======Email not recognized.======")
            elif choice == "3":
                print("Exiting.")
                break
            else:
                print("\n======Invalid selection.======")
        else:
            print("\n======You are logged in.======")
            if not load_secret():
                print("1. Set up 2FA")
                print("2. Logout")
            else:
                print("1. Logout")

            choice = input("Enter your choice: ")

            if choice == "1" and not load_secret():
                setup_2fa()
            elif choice in ("1", "2"):
                is_logged_in = False
                print("\n======You have been logged out.======")
            else:
                print("\n======Invalid choice.======")

if __name__ == "__main__":
    main()