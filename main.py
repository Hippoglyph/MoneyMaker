from dotenv import load_dotenv
load_dotenv(override=True)
from uploaders.youtube_uploader import YoutubeUploader
from pipelines.pipeline import Pipeline


#YoutubeUploader._get_authenticated_service()
Pipeline.run()
