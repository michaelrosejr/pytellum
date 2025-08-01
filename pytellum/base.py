import json
import pathlib
from datetime import datetime
from time import time
from urllib.parse import urlparse

import jwt
import requests
from utils import console_logger, to_obj

# logger = console_logger("intellim", level="WARNING")


class IntellimConn:
    def __init__(self, api_uid, private_key_file, url, base_url=None, logger=None):
        self.api_uid = api_uid
        self.private_key_file = private_key_file
        self.url = url
        self.logger = logger or console_logger("intellim", level="DEBUG")
        self.base_url = base_url if base_url is None else "https://salespro.hpe.com"
        self.uri = urlparse(self.url)
        self.get_token()

    # private_key_f = open(PRIVATE_KEY_FILE, 'r')
    # private_key = private_key_f.read()
    # private_key_f.close()

    def get_token(self, save=False):
        """Get an access token using the private key and API UID."""
        """Retrieve an access token, either from a saved file or by requesting a new one."""
        now = int(datetime.now().replace(microsecond=0).timestamp())
        try:
            with open("access_token.json") as f:
                self.token = json.load(f)
                self.access_token = self.token.get("access_token")
                self.expires_in = self.token.get("expires_in")
                self.token_type = self.token.get("token_type")
                self.scope = self.token.get("scope")
                self.expires_at = self.token.get("created_at") + self.expires_in
                self.logger.info("Access token loaded from file.")
        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.info("No valid access token found, requesting a new one.")
            self.request_token(save_token_to_file=save)

        if not hasattr(self, "access_token"):
            self.request_token(save_token_to_file=save)

        # If token expires soon, request a new one
        if now >= self.expires_at - 60:  # 60 seconds buffer
            self.logger.info("Access token expired, requesting a new one.")
            self.request_token(save_token_to_file=save)

        return self.access_token

    def request_token(self, save_token_to_file=False):
        """Retrieve an access token using the private key and API UID.
        This method reads the private key from a file, constructs a JWT claim set,
        encodes it, and sends a request to the OAuth2 token endpoint to obtain an access token.
        """
        private_key = pathlib.Path(self.private_key_file).read_text()
        claim_set = {
            "iss": self.api_uid,
            "aud": f"{self.uri.scheme}://{self.uri.hostname}",
            "scope": "admin_read",
            "exp": time() + 60,
            "iat": time(),
        }

        encoded_jwt = jwt.encode(claim_set, private_key, algorithm="RS256")

        self.token = requests.post(
            self.url, data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": encoded_jwt}
        ).json()

        self.access_token = self.token.get("access_token")
        self.expires_in = self.token.get("expires_in")
        self.token_type = self.token.get("token_type")
        self.scope = self.token.get("scope")
        self.expires_at = time() + self.expires_in

        if save_token_to_file:
            self.logger.info("Saving access token to file.")
            self.save_token()

        return self.access_token

    def save_token(self):
        """Save the access token to a file."""
        with open("access_token.json", "w") as f:
            # f.write(self.token)
            json.dump(self.token, f, indent=4)

    def command(self, apiPath, method="GET", params=None, data=None):
        """Send a command to the API."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if params is None:
            params = {}
        if data is None:
            data = {}
        url = f"{self.base_url}/{apiPath}"

        if method == "GET":
            response = requests.get(url, headers=headers, params=params, data=data)

        # if 200 convert response to dataclass
        if response.status_code == 200:
            return to_obj(response.json())

        self.logger.error(f"{response.status_code} - {response.text}")
