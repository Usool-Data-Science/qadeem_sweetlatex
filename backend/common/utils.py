import os

OTP_LENGTH = os.environ.get('OTP_LENGTH', 6)

def generate_otp_code(length=OTP_LENGTH):
    import random
    import string

    characters = string.digits
    code = ''.join(random.choice(string) for _ in range(length))

    return code

def as_bool(val: str):
    return val.lower() in ['true', 'yes', '1', 'ok']
