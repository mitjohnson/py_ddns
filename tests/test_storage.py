from pyddns.storage import Storage


def test_storage_singleton():
    storage1 = Storage(filename="py_ddns.db")
    storage2 = Storage(filename="py_ddns.db")
    assert storage1 is storage2, "Storage is not a singleton!"


def test_storage_create_tables():
    storage = Storage(filename="py_ddns.db")
    assert storage.cursor is not None, "Cursor is not initialized!"


def test_storage_add_and_retrieve():
    storage = Storage(filename="py_ddns.db")
    storage.add_service("TestService", "test.example.com", "127.0.0.1")
    record = storage.retrieve_record("test.example.com")
    assert record is not None, "Failed to retrieve the record!"
    assert record[0] == "127.0.0.1", "Retrieved IP does not match!"


def test_storage_update_ip():
    storage = Storage(filename="py_ddns.db")
    storage.add_service("TestService2", "test2.example.com", "127.0.0.1")
    storage.update_ip("TestService2", "test2.example.com", "127.0.0.2")
    record = storage.retrieve_record("test2.example.com")
    assert record[0] == "127.0.0.2", "IP address was not updated!"
