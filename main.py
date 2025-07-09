from dotenv import load_dotenv
load_dotenv(override=True)
from database.database import Database
from uploaders.youtube_uploader import YoutubeUploader
from pipelines.pipeline import Pipeline


#YoutubeUploader._get_authenticated_service()
Pipeline.run()
#Database.view_all_logs()