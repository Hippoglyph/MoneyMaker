import sqlite3
from datetime import datetime

from database.file_log_entry import FileLogEntry, ReviewStatus
from enum import StrEnum

# --- Configuration ---
DATABASE_NAME = 'file_records.db'

# --- Database Schema ---
# file_logs table:
# - id: INTEGER PRIMARY KEY AUTOINCREMENT (unique identifier for each log entry)
# - description: TEXT NOT NULL (the description of the file)
# - filename: TEXT NOT NULL (the name of the file)
# - creation_timestamp: TEXT NOT NULL (ISO 8601 formatted timestamp when the record was created)
# - uploaded_youtube: TEXT DEFAULT NULL (ISO 8601 formatted timestamp when uploaded to YouTube, or NULL if not yet)

class FileLogColumns(StrEnum):
    """Enum for column names in the 'file_logs' table."""
    ID = "id"
    DESCRIPTION = "description"
    FILENAME = "filename"
    CREATION_TIMESTAMP = "creation_timestamp"
    UPLOADED_YOUTUBE = "uploaded_youtube"
    REVIEWED = "reviewed"

class Database:

    @staticmethod
    def get_db_connection():
        """Establishes a connection to the SQLite database."""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            conn.row_factory = sqlite3.Row  # This allows accessing columns by name
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return None

    @staticmethod
    def create_table_if_not_exists():
        """Creates the file_logs table if it doesn't already exist, using StringEnum for column names."""
        conn = Database.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS file_logs (
                        {FileLogColumns.ID} INTEGER PRIMARY KEY AUTOINCREMENT,
                        {FileLogColumns.DESCRIPTION} TEXT NOT NULL,
                        {FileLogColumns.FILENAME} TEXT NOT NULL,
                        {FileLogColumns.CREATION_TIMESTAMP} TEXT NOT NULL,
                        {FileLogColumns.UPLOADED_YOUTUBE} TEXT DEFAULT NULL,
                        {FileLogColumns.REVIEWED} TEXT DEFAULT '{ReviewStatus.PENDING.value}'
                    )
                ''')
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error creating table: {e}")
            finally:
                conn.close()

    @staticmethod
    def log_file_upload_info(description: str, filename: str):
        """
        Logs file information (description, filename, creation timestamp) into the database.
        The 'uploaded_youtube' timestamp is set to NULL on creation.
        The 'reviewed' status is set to Pending on creation.
        Uses StringEnum for column names.

        Args:
            description (str): A description of the file/upload.
            filename (str): The name of the file being logged.
        """
        conn = Database.get_db_connection()
        if conn is None:
            return
        Database.create_table_if_not_exists()

        try:
            cursor = conn.cursor()
            current_timestamp = datetime.now().isoformat()  # ISO 8601 format

            # Use enum members for column names in the INSERT statement, including the new 'reviewed' column
            cursor.execute(
                f'''
                INSERT INTO file_logs (
                    {FileLogColumns.DESCRIPTION},
                    {FileLogColumns.FILENAME},
                    {FileLogColumns.CREATION_TIMESTAMP},
                    {FileLogColumns.UPLOADED_YOUTUBE},
                    {FileLogColumns.REVIEWED}
                )
                VALUES (?, ?, ?, ?, ?)
                ''',
                (description, filename, current_timestamp, None, ReviewStatus.PENDING.value) # uploaded_youtube is initially NULL, reviewed is 'Pending'
            )
            conn.commit()
            print(f"Successfully logged: Description='{description}', Filename='{filename}'")
        except sqlite3.Error as e:
            print(f"Error logging file info: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            conn.close()

    @staticmethod
    def mark_youtube_uploaded(log_id: int, datetime : datetime):
        """
        Updates the 'uploaded_youtube' timestamp for a specific log entry by its ID.
        Uses StringEnum for column names.

        Args:
            log_id (int): The ID of the log entry to update.
        """
        conn = Database.get_db_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            timestamp = datetime.isoformat() # Current time when marked as uploaded

            # Use enum members for column names in the UPDATE statement
            cursor.execute(
                f'''
                UPDATE file_logs
                SET {FileLogColumns.UPLOADED_YOUTUBE} = ?
                WHERE {FileLogColumns.ID} = ?
                ''',
                (timestamp, log_id)
            )
            conn.commit()

            if cursor.rowcount > 0:
                print(f"Successfully marked log ID {log_id} as uploaded to YouTube at {timestamp}.")
            else:
                print(f"No log entry found with ID {log_id}.")

        except sqlite3.Error as e:
            print(f"Error updating log ID {log_id}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            conn.close()

    @staticmethod
    def mark_reviewed(log_id: int, reviewed_status: ReviewStatus):
        """
        Updates the 'reviewed' status for a specific log entry by its ID.
        Uses StringEnum for column names.

        Args:
            log_id (int): The ID of the log entry to update.
            reviewed_status (bool): The new reviewed status (True or False).
        """
        conn = Database.get_db_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()

            cursor.execute(
                f'''
                UPDATE file_logs
                SET {FileLogColumns.REVIEWED} = ?
                WHERE {FileLogColumns.ID} = ?
                ''',
                 (reviewed_status.value, log_id)
            )
            conn.commit()

            if cursor.rowcount > 0:
                print(f"Successfully set 'reviewed' status for log ID {log_id} to {reviewed_status}.")
            else:
                print(f"No log entry found with ID {log_id}.")

        except sqlite3.Error as e:
            print(f"Error updating 'reviewed' status for log ID {log_id}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            conn.close()


    @staticmethod
    def view_all_logs():
        """Retrieves and prints all entries from the file_logs table, using StringEnum for column names."""
        conn = Database.get_db_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            # Use enum members for all column names in the SELECT statement
            select_columns = ", ".join([
                FileLogColumns.ID,
                FileLogColumns.DESCRIPTION,
                FileLogColumns.FILENAME,
                FileLogColumns.CREATION_TIMESTAMP,
                FileLogColumns.UPLOADED_YOUTUBE,
                FileLogColumns.REVIEWED
            ])
            cursor.execute(f"SELECT {select_columns} FROM file_logs ORDER BY {FileLogColumns.CREATION_TIMESTAMP} DESC")
            rows = cursor.fetchall()

            if not rows:
                print("\nNo log entries found in the database.")
                return

            print("\n--- All File Logs ---")
            for row in rows:
                # Create a FileLogEntry object from the row
                log_entry = FileLogEntry(**row)

                youtube_upload_status = log_entry.get_uploaded_youtube() if log_entry.is_youtube_uploaded() else "N/A (Not yet uploaded)"
                reviewed_status_display = log_entry.get_review_status().value

                print(f"ID: {log_entry.get_id()}")
                print(f"  Description: '{log_entry.get_description()}'")
                print(f"  Filename:    '{log_entry.get_filename()}'")
                print(f"  Created:     {log_entry.get_creation_timestamp()}")
                print(f"  YT Uploaded: {youtube_upload_status}")
                print(f"  Reviewed:    {reviewed_status_display}")
                print("-" * 30)
            print("---------------------\n")

        except sqlite3.Error as e:
            print(f"Error retrieving logs: {e}")
        finally:
            conn.close()

    @staticmethod
    def count_future_youtube_uploads() -> int:
        """
        Counts the number of log entries that are considered 'future' YouTube uploads.
        This includes:
        1. Entries where 'uploaded_youtube' timestamp is in the future relative to the current time (scheduled uploads).
        2. Entries where 'uploaded_youtube' is NULL and the 'reviewed' status is either PENDING or ACCEPTED
           (meaning they are awaiting upload and review approval).

        Returns:
            int: The count of entries meeting the criteria.
                 Returns 0 if no such entries are found or an error occurs.
        """
        conn = Database.get_db_connection()
        count = 0
        if conn is None:
            return count

        try:
            cursor = conn.cursor()
            current_timestamp = datetime.now().isoformat()
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM file_logs
                WHERE
                    ({FileLogColumns.UPLOADED_YOUTUBE} IS NOT NULL AND {FileLogColumns.UPLOADED_YOUTUBE} > ?)
                    OR
                    ({FileLogColumns.UPLOADED_YOUTUBE} IS NULL AND ({FileLogColumns.REVIEWED} = ? OR {FileLogColumns.REVIEWED} = ?))
                """,
                (current_timestamp, ReviewStatus.PENDING.value, ReviewStatus.ACCEPTED.value)
            )
            count = cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error counting future YouTube uploads: {e}")
        finally:
            conn.close()
        return count
    
    @staticmethod
    def get_pending_review_entries() -> list[FileLogEntry]:
        """
        Retrieves all log entries that currently have a 'PENDING' review status,
        returned as a list of FileLogEntry objects. Uses StringEnum for column names.

        Returns:
            list[FileLogEntry]: A list of FileLogEntry objects, where each object
                                represents a log entry with a 'PENDING' review status.
                                Returns an empty list if no such entries are found
                                or an error occurs.
        """
        conn = Database.get_db_connection()
        pending_entries = []
        if conn is None:
            return pending_entries

        try:
            cursor = conn.cursor()
            select_columns = ", ".join([
                FileLogColumns.ID,
                FileLogColumns.DESCRIPTION,
                FileLogColumns.FILENAME,
                FileLogColumns.CREATION_TIMESTAMP,
                FileLogColumns.UPLOADED_YOUTUBE,
                FileLogColumns.REVIEWED
            ])
            cursor.execute(f"""
                    SELECT {select_columns}
                    FROM file_logs
                    WHERE {FileLogColumns.REVIEWED} = ?
                    ORDER BY {FileLogColumns.CREATION_TIMESTAMP} ASC
                """, (ReviewStatus.PENDING.value,))
            rows = cursor.fetchall()

            for row in rows:
                # Instantiate FileLogEntry object directly from the sqlite3.Row object
                pending_entries.append(FileLogEntry(**row))

        except sqlite3.Error as e:
            print(f"Error retrieving pending review entries: {e}")
        finally:
            conn.close()
        return pending_entries
    
    @staticmethod
    def get_latest_youtube_upload_timestamp() -> datetime | None:
        """
        Retrieves the datetime object of the most recent log entry
        that has been marked as uploaded to YouTube.

        Returns:
            datetime | None: The datetime object of the latest YouTube upload,
                             or None if no entries have been uploaded to YouTube.
        """
        conn = Database.get_db_connection()
        latest_datetime = None 
        if conn is None:
            return latest_datetime

        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {FileLogColumns.UPLOADED_YOUTUBE}
                FROM file_logs
                WHERE {FileLogColumns.UPLOADED_YOUTUBE} IS NOT NULL
                ORDER BY {FileLogColumns.UPLOADED_YOUTUBE} DESC
                LIMIT 1
            """)
            result = cursor.fetchone()

            if result:
                timestamp_str = result[FileLogColumns.UPLOADED_YOUTUBE]
                # Convert the ISO 8601 string to a datetime object
                latest_datetime = datetime.fromisoformat(timestamp_str)

        except sqlite3.Error as e:
            print(f"Error retrieving latest YouTube upload timestamp: {e}")
        except ValueError as e:
            # Handle cases where the timestamp string might be malformed
            print(f"Error parsing timestamp from database: {e}")
            latest_datetime = None
        finally:
            conn.close()
        return latest_datetime
    
    @staticmethod
    def get_approved_but_not_youtube_uploaded_entries() -> list[FileLogEntry]:
        """
        Retrieves all log entries that have been 'ACCEPTED' for review
        but have not yet been marked as uploaded to YouTube (uploaded_youtube IS NULL).

        Returns:
            list[FileLogEntry]: A list of FileLogEntry objects matching the criteria.
                                Returns an empty list if no such entries are found
                                or an error occurs.
        """
        conn = Database.get_db_connection()
        approved_not_uploaded_entries = []
        if conn is None:
            return approved_not_uploaded_entries

        try:
            cursor = conn.cursor()
            select_columns = ", ".join([
                FileLogColumns.ID,
                FileLogColumns.DESCRIPTION,
                FileLogColumns.FILENAME,
                FileLogColumns.CREATION_TIMESTAMP,
                FileLogColumns.UPLOADED_YOUTUBE,
                FileLogColumns.REVIEWED
            ])
            cursor.execute(f"""
                    SELECT {select_columns}
                    FROM file_logs
                    WHERE {FileLogColumns.UPLOADED_YOUTUBE} IS NULL
                      AND {FileLogColumns.REVIEWED} = ?
                    ORDER BY {FileLogColumns.CREATION_TIMESTAMP} ASC
                """, (ReviewStatus.ACCEPTED.value,)) # Pass the value for 'Accepted' status
            rows = cursor.fetchall()

            for row in rows:
                # Instantiate FileLogEntry object directly from the sqlite3.Row object
                approved_not_uploaded_entries.append(FileLogEntry(**row))

        except sqlite3.Error as e:
            print(f"Error retrieving approved but not uploaded entries: {e}")
        finally:
            conn.close()
        return approved_not_uploaded_entries