# upload_test.py
import requests
from pathlib import Path

# CONFIG — change these before running
BASE_URL = "http://127.0.0.1:8000"                # change for PythonAnywhere
ENDPOINT = "/api/registrations/"
URL = BASE_URL.rstrip("/") + ENDPOINT
FILE_PATH = Path(r"C:\Users\019301.MAA019301A\Desktop\finger.jpg")
TIMEOUT = 30  # seconds

# form fields
data = {
    "name": "Ravi Kumar",
    "age": "30",
    "event": "ID Check",
    "phone_no": "9876543210",
    "member_id": "M-2001",
}

def main():
    # check if file exists
    if not FILE_PATH.exists():
        print(f"❌ ERROR: File not found: {FILE_PATH}")
        return

    # send upload request
    with FILE_PATH.open("rb") as f:
        files = {"document": (FILE_PATH.name, f, "image/jpeg")}
        try:
            resp = requests.post(URL, data=data, files=files, timeout=TIMEOUT)
        except requests.RequestException as e:
            print("❌ ERROR: Connection failed.")
            print("Details:", e)
            return

    # Check status code
    if resp.status_code in (200, 201):
        print("✅ Upload successful!")
        print("Server response:")
        print(resp.json())
    else:
        print("❌ Upload failed!")
        print("Status code:", resp.status_code)
        # try to show JSON error
        try:
            print("Error details:", resp.json())
        except ValueError:
            print("Server response:", resp.text)

if __name__ == "__main__":
    main()
