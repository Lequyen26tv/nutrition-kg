import os
import time
import logging

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable, SessionExpired, TransientError


logging.getLogger("neo4j").setLevel(logging.CRITICAL)
logging.getLogger("neo4j.io").setLevel(logging.CRITICAL)
logging.getLogger("neo4j.pool").setLevel(logging.CRITICAL)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
ENV_PATH = os.path.join(BACKEND_DIR, ".env")

print("\n==================================================")
print("Dang tim file .env tai:")
print(ENV_PATH)

if os.path.exists(ENV_PATH):
    print("Da tim thay file .env")
    load_dotenv(ENV_PATH)
else:
    print("Khong tim thay file .env")
print("==================================================\n")


class Neo4jManager:
    def __init__(self):
        self.driver = None
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")

        print("========== THONG TIN KET NOI ==========")
        print("URI      :", self.uri)
        print("USER     :", self.user)
        print("PASSWORD :", "*" * len(self.password) if self.password else "None")
        print("=======================================\n")

        if not self.uri:
            raise ValueError("Thieu NEO4J_URI trong file .env")
        if not self.user:
            raise ValueError("Thieu NEO4J_USER trong file .env")
        if not self.password:
            raise ValueError("Thieu NEO4J_PASSWORD trong file .env")

        self._connect()

    def _connect(self):
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                connection_timeout=30,
                max_connection_lifetime=300,
                keep_alive=True,
            )
            self.driver.verify_connectivity()
            print("Ket noi Neo4j Aura thanh cong!")

        except AuthError:
            raise Exception("Sai username hoac password Neo4j Aura.")

        except ServiceUnavailable as e:
            raise Exception(
                "Khong the ket noi Neo4j Aura.\n"
                f"Chi tiet: {e}\n\n"
                "Hay kiem tra:\n"
                "1. Database Aura co dang RUNNING khong.\n"
                "2. URI co dung dang neo4j+s://xxxxx.databases.neo4j.io khong.\n"
                "3. May co Internet khong."
            )

    def _is_retryable_error(self, error):
        message = str(error).lower()
        retry_markers = (
            "failed to write data",
            "failed to read from defunct connection",
            "connection reset",
            "connection refused",
            "broken pipe",
            "defunct connection",
            "unable to retrieve routing information",
            "service unavailable",
        )
        return isinstance(error, (ServiceUnavailable, SessionExpired, TransientError, OSError)) or any(
            marker in message for marker in retry_markers
        )

    def reconnect(self):
        try:
            if self.driver:
                self.driver.close()
        except Exception:
            pass

        print("Neo4j connection stale. Reconnecting to Aura...")
        self._connect()
        return self.driver

    def get_driver(self):
        if self.driver is None:
            self.reconnect()
        return self.driver

    def get_session(self):
        return self.get_driver().session()

    def run_query(self, query, parameters=None, max_retries=3):
        parameters = parameters or {}

        for attempt in range(1, max_retries + 1):
            try:
                with self.get_session() as session:
                    return session.run(query, parameters).data()
            except Exception as e:
                if attempt >= max_retries or not self._is_retryable_error(e):
                    raise

                print(f"Neo4j query failed on attempt {attempt}/{max_retries}: {e}")
                time.sleep(min(attempt, 3))
                self.reconnect()

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None


neo4j_db = Neo4jManager()
