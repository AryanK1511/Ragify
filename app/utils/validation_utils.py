import re

import requests


class ValidationUtils:
    @staticmethod
    def is_url_valid(url: str, timeout: int = 5) -> bool:
        url_regex = re.compile(
            r"^(https?:\/\/)?" r"(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})" r"(\/\S*)?$"
        )

        if not url_regex.match(url):
            return False

        if not url.startswith("http"):
            url = "http://" + url

        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
        except requests.RequestException:
            return False
