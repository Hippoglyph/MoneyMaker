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

if Database.count_future_youtube_uploads() < 10:
    input("Need to generate 10 videos. Procceed?")
    load_dotenv(override=True)
    for _ in range(10):
        prompt = PromptGenerator.generate()
        file_name = ModelSlab.generate(prompt)
        Database.log_file_upload_info(prompt, file_name)