import os

settings = {
    "AUTH_URL": os.getenv("AUTH_URL", "https://salespro.hpe.com/oauth2/token.json"),
    "BASE_URL": os.getenv("BASE_URL", "https://salespro.hpe.com"),
    "API_UID": os.getenv("API_UID", ""),
    "PRIVATE_KEY_FILE": os.getenv("PRIVATE_KEY_FILE", "private_key.pem"),
}

if settings["API_UID"] == "":
    raise ValueError("API_UID is not set. Please set it in your environment variables or .env file.")

if __name__ == "__main__":
    apiuid = settings.get("API_UID")
    print(f"API_UID: {apiuid}")
