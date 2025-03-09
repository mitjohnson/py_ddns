import sqlite3, logging
from typing import Optional, Callable, Any, Tuple
from datetime import datetime

class Storage:
    """
    A class to manage SQLite database operations for DDNS services.

    This class handles the creation, updating, and retrieval of domain records
    in a SQLite database.
    """

    def __init__(self, filename: str='py_ddns.db'):
        self.connection = sqlite3.connect(filename)
        self.cursor = self.connection.cursor()

        self.create_tables()

    @staticmethod
    def handle_sqlite_error(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            
            try:

                return func(*args, **kwargs)
            
            except sqlite3.Error as err:
                logging.error(f"SQLite Error: {err}")
                raise
            except sqlite3.DatabaseError as err:
                logging.error(f"SQLite Database Error: {err}")
                raise
            except sqlite3.DataError as err:
                logging.error(f"SQLite Data Error: {err}")
                raise
            except sqlite3.IntegrityError as err:
                logging.error(f"SQLite Integrity Error: {err}")
                raise

        return wrapper
        
    @handle_sqlite_error
    def create_tables(self) -> None:
        
        sql = """
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            domain_name TEXT NOT NULL UNIQUE,
            record_id TEXT DEFAULT NULL,
            current_ip TEXT NOT NULL,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(service, domain_name)
        )
        """
        self.cursor.execute(sql)
        self.connection.commit()
        logging.debug(f"SQLite: Successfully verified that the domains table is present.")

    @handle_sqlite_error
    def drop_tables(self) -> None:

        logging.warning(f"one or more database tables have been requested to be dropped.")

        sql = """
        DROP TABLE IF EXISTS domains;
        """
        self.cursor.execute(sql)
        self.connection.commit()
        
        logging.info("domains table has sucessfully been dropped.")

    @handle_sqlite_error
    def add_service(self, service_name: str, domain_name: str, current_ip: str, record_id: Optional[str] = None) -> None:
        
        sql = """
        INSERT INTO domains(service, domain_name, current_ip, record_id)
        VALUES(?, ?, ?, ?)
        """
        self.cursor.execute(sql, (service_name, domain_name, current_ip, record_id))
        self.connection.commit()
        logging.debug(f"SQLite: Adding service: {service_name}, Domain: {domain_name}, IP: {current_ip}")
        logging.info(f"SQLite: Sucessfully added {service_name} to database.")

    @handle_sqlite_error
    def update_ip(self, service_name: str, domain_name: str, current_ip: str) -> None:

        sql = """
        UPDATE domains
        SET service = COALESCE(?, service),
            current_ip = COALESCE(?, current_ip),
            last_updated = CURRENT_TIMESTAMP
         WHERE domain_name = ? 
        """
        self.cursor.execute(sql, (service_name, current_ip, domain_name))
        self.connection.commit()
        logging.info(f"SQLite: Updated {domain_name} on {service_name} to {current_ip}")

    @handle_sqlite_error
    def retrieve_record(self, domain_name: str) -> Optional[Tuple[str, datetime, str]]:

        sql = """
        SELECT current_ip, last_updated, record_id FROM domains
        WHERE domain_name = ?
        """
        self.cursor.execute(sql, (domain_name,))
        response = self.cursor.fetchone()

        if not response:
            return None

        ip: str = response[0]
        last_updated: datetime = response[1]
        record_id: str = response[2]

        return (ip, last_updated, record_id)
