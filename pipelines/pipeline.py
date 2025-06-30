from datetime import datetime, timedelta
from dotenv import load_dotenv
from database.database import Database
from database.file_log_entry import ReviewStatus
from generate.modelslab.modelslab import ModelSlab
from generate.video_generator import VideoGenerator
from prompt.prompt_generator import PromptGenerator
from uploaders.youtube_uploader import YoutubeUploader


class Pipeline:

    GENERATION_BATCH_SIZE = 10
    QUEUE_SIZE = 10
    UPLOAD_COOLDOWN = 24 #h

    def review() -> None:
        pending_reviews = Database.get_pending_review_entries()
        while len(pending_reviews) > 0:
            rev = pending_reviews.pop()
            print(rev.get_description())
            print(rev.get_filename())
            approved = None
            while approved is None:
                approve_str = input("Approve (Y/N)?")
                if approve_str == "Y":
                    approved = True
                elif approve_str == "N":
                    approved = False
            Database.mark_reviewed(rev.get_id(), ReviewStatus.ACCEPTED if approved else ReviewStatus.DENIED)

    def upload_youtube() -> None:
        pending_entries = Database.get_approved_but_not_youtube_uploaded_entries()
        current_timestamp = datetime.now()
        latest_timestamp = Database.get_latest_youtube_upload_timestamp()
        upload_time = None
        if latest_timestamp is None: # FIRST
            upload_time = current_timestamp + timedelta(hours=1)
        elif (current_timestamp - latest_timestamp) < timedelta(hours=Pipeline.UPLOAD_COOLDOWN):
            upload_time = latest_timestamp + timedelta(hours=Pipeline.UPLOAD_COOLDOWN)
        for entry in pending_entries:
            if YoutubeUploader.upload_video(entry.get_description(), entry.get_description(), VideoGenerator.get_clip_folder() + entry.get_filename(), upload_time):
                Database.mark_youtube_uploaded(entry.get_id())
            else:
                print(f"Failed yo upload {entry.get_id()}")
            upload_time =+ timedelta(hours=Pipeline.UPLOAD_COOLDOWN)

    def run() -> None:
        Pipeline.review()

        if Database.count_future_youtube_uploads() < Pipeline.QUEUE_SIZE:
            input(f"Need to generate {Pipeline.GENERATION_BATCH_SIZE} videos. Proceed?")
            load_dotenv(override=True)
            for _ in range(Pipeline.GENERATION_BATCH_SIZE):
                prompt = PromptGenerator.generate()
                file_name = ModelSlab.generate(prompt)
                Database.log_file_upload_info(prompt, file_name)
        
            Pipeline.review()

        Pipeline.upload_youtube()
