import os
import pytest


@pytest.fixture(autouse=True)
def setup_and_teardown_per_test():
    """Setup and teardown logic for each test run."""
    with open("py_ddns.ini", "w") as f:
        f.write("""[Client_settings]\nlogging_level=info\n""")

    yield  # This allows each test to run before cleanup

    files = ["py_ddns.ini", "py_ddns.db", "py_ddns.log"]
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"Error occurred while trying to remove {file}: {e}")
