import re
from django.core.exceptions import ValidationError

def phone_validator(value):
    """
    Validates international phone numbers.
    Format: + followed by 8–15 digits
    Example: +971501234567
    """
    pattern = r'^\+\d{8,15}$'
    if not re.match(pattern, value):
        raise ValidationError(
            "Enter a valid phone  number with country code (e.g., +971501234567)"
        )