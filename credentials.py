import os
from pathlib import Path


def get_secret(secret_name):
    env_var_name = f"SECRET_{secret_name.upper().replace('-', '_')}"
    if env_var_name in os.environ:
        return os.environ[env_var_name]
    secrets_directory = os.environ.get('CREDENTIALS_DIRECTORY', '.')
    secrets_directory = Path(secrets_directory)

    secret_file = secrets_directory / secret_name

    with open(secret_file, "r") as file:
        secret = file.read()
    return secret.strip()

