import os
import datetime # Import datetime module
from typing import Optional # Import Optional for type hints

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# The CLIENT_SECRETS_FILE is the JSON file you downloaded from the Google Cloud Console.
CLIENT_SECRETS_FILE = "client_secrets.json"

# This scope allows full write access to the authenticated user's YouTube account,
# including the ability to upload videos.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# This enables resumable uploads, which is important for large files.
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# --- VIDEO METADATA (Customize these!) ---
TAGS = ['GoodVibes', 'Pets', 'Dog', 'FeelGood', 'Shorts']
CATEGORY_ID = '24'  # '22' is "People & Blogs". Common IDs: 1 (Film), 2 (Autos), 10 (Music), 15 (Pets), 17 (Sports), 19 (Travel), 20 (Gaming), 22 (People & Blogs), 23 (Comedy), 24 (Entertainment), 25 (News & Politics), 26 (Howto & Style), 27 (Education), 28 (Science & Technology), 29 (Nonprofits & Activism)
DEFAULT_PRIVACY_STATUS = 'private' # Renamed for clarity: Use a default, but it can be overridden by scheduling.

# --- Hardcoded Fields ---
INTENDED_FOR_CHILDREN = False # Sets "Intended for children" (Made for Kids) to False
MODIFIED_CONTENT_AI = True   # Sets "Altered or synthetic content" to True

class YoutubeUploader:

    def _get_authenticated_service():
        """Authenticates the user and returns the YouTube API service object."""
        credentials = None

        # Check if a cached token exists
        if os.path.exists('token.json'):
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_file('token.json', SCOPES)

        # If no valid token, or token expired/needs refresh, initiate flow
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(google.auth.transport.requests.Request())
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE, SCOPES)
                credentials = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(credentials.to_json())

        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)

    def upload_video(title : str, description : str, file_path : str,
                     schedule_datetime: Optional[datetime.datetime] = None) -> bool:
        """
        Uploads a video to YouTube.

        Args:
            title (str): The title of the video.
            description (str): The description of the video.
            file_path (str): The path to the video file.
            schedule_datetime (Optional[datetime.datetime]): Optional datetime object
                to schedule the video's publication. If provided, the video's
                privacy status will be set to 'private' until the scheduled time,
                regardless of DEFAULT_PRIVACY_STATUS. The datetime should be
                timezone-aware (UTC recommended) or will be treated as local.
        Returns:
            bool: True if upload was successful, False otherwise.
        """
        if not os.path.exists(file_path):
            print(f"Error: Video file not found at {file_path}")
            return False

        effective_privacy_status = DEFAULT_PRIVACY_STATUS
        publish_at_str = None

        if schedule_datetime:
            # Ensure the datetime is timezone-aware and convert to UTC for consistent API behavior
            if schedule_datetime.tzinfo is None:
                # Assume naive datetime is local time, convert to UTC
                schedule_datetime = schedule_datetime.astimezone(datetime.timezone.utc)
            else:
                # Already timezone-aware, just convert to UTC
                schedule_datetime = schedule_datetime.astimezone(datetime.timezone.utc)

            # Check if the schedule date is in the past
            if schedule_datetime < datetime.datetime.now(datetime.timezone.utc):
                print("Warning: Schedule datetime is in the past. Video will likely publish immediately.")

            # Format to RFC 3339 string (e.g., 2024-01-25T10:00:00Z)
            publish_at_str = schedule_datetime.isoformat(timespec='seconds') + 'Z'

            # If scheduling, privacy status MUST be 'private' at upload time
            if effective_privacy_status != 'private':
                print(f"Info: Overriding privacyStatus from '{effective_privacy_status}' to 'private' for scheduling.")
            effective_privacy_status = 'private'


        # Create the video metadata (snippet, status, and contentDetails)
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': TAGS,
                'categoryId': CATEGORY_ID
            },
            'status': {
                'privacyStatus': effective_privacy_status, # Use the determined privacy status
                'selfDeclaredMadeForKids': INTENDED_FOR_CHILDREN
            },
            'contentDetails': {
                'altContent': MODIFIED_CONTENT_AI
            }
        }

        # Add publishAt to the status if a schedule_datetime was provided
        if publish_at_str:
            body['status']['publishAt'] = publish_at_str

        # Create a MediaFileUpload object for the video file
        media_body = MediaFileUpload(file_path, resumable=True)

        # Call the API's videos.insert method to upload the video.
        try:
            print(f"Uploading video: '{title}' from '{file_path}'...")
            youtube_service = YoutubeUploader._get_authenticated_service()
            insert_request = youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media_body
            )

            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%")

            print("\nUpload Complete!")
            print(f"Video ID: {response['id']}")
            print(f"Title: {response['snippet']['title']}")
            print(f"Privacy Status: {response['status']['privacyStatus']}")
            print(f"Made For Kids: {response['status'].get('selfDeclaredMadeForKids', 'N/A')}")
            print(f"Altered/Synthetic Content (AI): {response['contentDetails'].get('altContent', 'N/A')}")

            if 'publishAt' in response['status']:
                print(f"Scheduled for: {response['status']['publishAt']}")
            else:
                print("Video published immediately (not scheduled).")
            return True

        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content.decode()}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False