from dotenv import load_dotenv
from generate.modelslab.modelslab import ModelSlab
from generate.video_generator import VideoGenerator
from prompt.prompt_generator import PromptGenerator
from uploaders.youtube_uploader import YoutubeUploader

load_dotenv(override=True)
from pipelines.pipeline import Pipeline
from database.database import Database

#YoutubeUploader._get_authenticated_service()
#Pipeline.run()
# for entry in Database.get_pending_youtube_uploads():
#     if YoutubeUploader.upload_video(entry.get_description(), entry.get_description(), VideoGenerator.get_clip_folder() + entry.get_filename()):
#         Database.mark_youtube_uploaded(entry.get_id())

Pipeline.run()
#YoutubeUploader._get_authenticated_service()
#Database.view_all_logs()