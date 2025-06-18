import os
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
PRIVACY_STATUS = 'private' # Options: 'public', 'private', 'unlisted'

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

    def upload_video(title : str, description : str, file_path : str) -> bool:
        """Uploads a video to YouTube."""
        if not os.path.exists(file_path):
            print(f"Error: Video file not found at {file_path}")
            return

        # Create the video metadata (snippet and status)
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': TAGS,
                'categoryId': CATEGORY_ID
            },
            'status': {
                'privacyStatus': PRIVACY_STATUS
            }
        }

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
            return True

        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content.decode()}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")