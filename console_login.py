import pyotp
import qrcode
import os
import json

def save_secret(secret):
    with open('secret.json', 'w') as f:
        json.dump({'secret': secret}, f)

def load_secret():
    try:
        with open('secret.json', 'r') as f:
            return json.load(f)['secret']
    except FileNotFoundError:
        return None

def delete_secret():
    if os.path.exists('secret.json'):
        os.remove('secret.json')

def setup_2fa():
    existing_secret = load_secret()
    if existing_secret:
        print("2FA is already set up. No need to scan a new QR code.")
        return True

    secret = pyotp.random_base32()
    save_secret(secret)
    print(f"Secret key (save this securely): {secret}")

    uri = pyotp.TOTP(secret).provisioning_uri(
        name="you@example.com",
        issuer_name="MyConsoleApp"
    )

    print("\n📷 Scan this QR code in Microsoft Authenticator:")
    qrcode.make(uri).show()

    totp = pyotp.TOTP(secret)
    code = input("\nEnter the 6-digit code from Microsoft Authenticator to verify setup: ")

    if totp.verify(code):
        print("Code verified — 2FA setup complete!")
        return True
    else:
        print("Invalid code. Setup failed.")
        delete_secret()
        return False


def login():
    secret = load_secret()
    if not secret:
        print("  No 2FA setup found. Please run setup first.")
        return False

    totp = pyotp.TOTP(secret)
    code = input("\nEnter the 6-digit code from Microsoft Authenticator: ")

    if totp.verify(code):
        print(" Code verified — you are logged in!")
        return True
    else:
        print(" Invalid code. Login failed.")
        return False

def main():
    is_logged_in = False
    
    while True:
        print("\n===  2FA Console App ===")
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
                print(" You have been logged out.")
            elif choice == "2":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
        else:
            if choice == "1":
                setup_2fa()
            elif choice == "2":
                if load_secret():
                    if login():
                        is_logged_in = True
                else:
                    print("Goodbye!")
                    break
            elif choice == "3" and load_secret():
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
