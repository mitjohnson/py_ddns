"""
Storage Module

This module provides a class for managing SQLite database operations specifically
for Dynamic DNS (DDNS) services. The `Storage` class handles the creation,
updating, and retrieval of domain records in a SQLite database.
"""
import sqlite3
import logging
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
        """ Decorator utilized to handle all errors invlovling the SQLite Database."""
        def wrapper(*args, **kwargs) -> Any:

            try:

                return func(*args, **kwargs)

            except sqlite3.Error as err:
                logging.error("SQLite Error: %s", err)
                raise
            except sqlite3.DatabaseError as err:
                logging.error("SQLite Database Error: %s", err)
                raise
            except sqlite3.DataError as err:
                logging.error("SQLite Data Error: %s", err)
                raise
            except sqlite3.IntegrityError as err:
                logging.error("SQLite Integrity Error: %s", err)
                raise
        return wrapper

    @handle_sqlite_error
    def create_tables(self) -> None:
        """ Method to create all SQLite tables utilized by pyddns """

        sql = """
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            domain_name TEXT NOT NULL UNIQUE,
            record_id TEXT DEFAULT NULL,
            current_ip TEXT NOT NULL,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(service, domain_name)
        )
        """
        self.cursor.execute(sql)
        self.connection.commit()
        logging.debug("SQLite: Successfully verified that the domains table is present.")

    @handle_sqlite_error
    def drop_tables(self) -> None:
        """ Method to drop all SQLite tables utilized by pyddns """

        logging.warning("one or more database tables have been requested to be dropped.")

        sql = """
        DROP TABLE IF EXISTS domains;
        """
        self.cursor.execute(sql)
        self.connection.commit()

        logging.info("domains table has sucessfully been dropped.")

    @handle_sqlite_error
    def add_service(
        self, service_name: str, domain_name: str, current_ip: str, record_id: Optional[str] = None
        ) -> None:
        """ Adds a service to the SQLite database and sets a created_at timestamp """

        sql = """
        INSERT INTO domains(service, domain_name, current_ip, record_id)
        VALUES(?, ?, ?, ?)
        """
        self.cursor.execute(sql, (service_name, domain_name, current_ip, record_id))
        self.connection.commit()
        logging.debug(
            "SQLite: Adding service: %s, Domain: %s, IP: %s", service_name, domain_name, current_ip
        )
        logging.info("SQLite: Sucessfully added %s to database.", service_name)

    @handle_sqlite_error
    def update_ip(self, service_name: str, domain_name: str, current_ip: str) -> None:
        """ Updated the domain name's IP address in the SQLite database. """

        sql = """
        UPDATE domains
        SET service = COALESCE(?, service),
            current_ip = COALESCE(?, current_ip),
            last_updated = CURRENT_TIMESTAMP
         WHERE domain_name = ? 
        """
        self.cursor.execute(sql, (service_name, current_ip, domain_name))
        self.connection.commit()
        logging.info("SQLite: Updated %s on %s to %s", domain_name, service_name, current_ip)

    @handle_sqlite_error
    def retrieve_record(self, domain_name: str) -> Optional[Tuple[str, datetime, str]]:
        """ Retrieves IP adress, last_updated, and record_id from SQLite databse if present. """

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
