import credentials
import os
from tempfile import TemporaryDirectory


def test_get_secret():
    with TemporaryDirectory() as tmpdir:
        os.environ["CREDENTIALS_DIRECTORY"] = tmpdir
        secret_name = "my-secret"
        secret_value = "password123"
        with open(os.path.join(tmpdir, secret_name), "w") as f:
            f.write(secret_value)
        assert credentials.get_secret(secret_name) == secret_value
