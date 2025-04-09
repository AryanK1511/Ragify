# app/utils/validation_utils.py

import re


class ValidationUtils:
    @staticmethod
    def is_url_valid(url: str, timeout: int = 5) -> bool:
        url_regex = re.compile(
            r"^(https?:\/\/)?" r"(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})" r"(\/\S*)?$"
        )

        if not url_regex.match(url):
            return False

        return True
