# example6


import os
import requests

API_URL = "https://dsa-staging.jnj.com/api/v1"

api_key = os.getenv("THEA_API_KEY", "").strip()

if not api_key:
    raise RuntimeError("THEA_API_KEY is not configured.")

session = requests.Session()

response = session.post(
    f"{API_URL}/api_key/token",
    params={
        "key": api_key,
        "duration": 0.04,
    },
    timeout=30,
)

response.raise_for_status()

data = response.json()

token = data.get("authToken", {}).get("token") or data.get("token")

if not token:
    raise RuntimeError(
        "Authentication succeeded, but no token was found."
    )

session.headers.update({"Girder-Token": token})

me = session.get(
    f"{API_URL}/user/me",
    timeout=30,
)

me.raise_for_status()

user = me.json()

print("Authentication successful!")
print("Username:", user.get("login", "Unknown"))
print("User ID:", user.get("_id", "Unknown"))

