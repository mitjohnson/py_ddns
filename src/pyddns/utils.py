from pyddns.config import Config
from pyddns.cache import Storage

root_config = Config()

def _get_config() -> Config:
    return root_config

root_storage = Storage()

def _get_storage() -> Storage:
    return root_storage