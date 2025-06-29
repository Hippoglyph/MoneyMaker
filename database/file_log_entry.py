from enum import StrEnum

class ReviewStatus(StrEnum):
     """Enum for the possible review statuses."""
     PENDING = "Pending"
     DENIED = "Denied"
     ACCEPTED = "Accepted"

class FileLogEntry:
    """
    Represents a single entry from the 'file_logs' database table.
    Provides getter methods for each column.
    """
    def __init__(self, id: int, description: str, filename: str,
                 creation_timestamp: str, uploaded_youtube: str | None,
                 reviewed: str):
        self._id = id
        self._description = description
        self._filename = filename
        self._creation_timestamp = creation_timestamp
        self._uploaded_youtube = uploaded_youtube
        self._reviewed = ReviewStatus(reviewed)

    def get_id(self) -> int:
        """Returns the ID of the log entry."""
        return self._id

    def get_description(self) -> str:
        """Returns the description of the file."""
        return self._description

    def get_filename(self) -> str:
        """Returns the filename."""
        return self._filename

    def get_creation_timestamp(self) -> str:
        """Returns the timestamp when the entry was created (ISO 8601 format)."""
        return self._creation_timestamp

    def get_uploaded_youtube(self) -> str | None:
        """
        Returns the timestamp when the file was marked as uploaded to YouTube
        (ISO 8601 format), or None if not yet uploaded.
        """
        return self._uploaded_youtube

    def is_youtube_uploaded(self) -> bool:
        """Returns True if the file has been marked as uploaded to YouTube, False otherwise."""
        return self._uploaded_youtube is not None

    def get_review_status(self) -> ReviewStatus:
        """Returns the review status as a ReviewStatus enum member."""
        return self._reviewed

    def __repr__(self):
        """Provides a string representation for debugging."""
        return (f"FileLogEntry(id={self._id}, description='{self._description}', "
                f"filename='{self._filename}', created='{self._creation_timestamp}', "
                f"uploaded_youtube='{self._uploaded_youtube}', reviewed={self._reviewed.value})")