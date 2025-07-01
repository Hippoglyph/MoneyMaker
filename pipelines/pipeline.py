from datetime import datetime, timedelta, timezone
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
        current_timestamp = datetime.now(timezone.utc)
        latest_timestamp = Database.get_latest_youtube_upload_timestamp() 
        if latest_timestamp and latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.astimezone(timezone.utc)
        upload_time_for_first_video_in_batch = None
        if latest_timestamp is None: # FIRST EVER UPLOAD
            upload_time_for_first_video_in_batch = current_timestamp + timedelta(hours=6)
        else:
            earliest_next_upload_slot = latest_timestamp + timedelta(hours=Pipeline.UPLOAD_COOLDOWN)

            if current_timestamp < earliest_next_upload_slot:
                upload_time_for_first_video_in_batch = earliest_next_upload_slot
            else:
                upload_time_for_first_video_in_batch = current_timestamp + timedelta(hours=6)
                
        current_scheduled_upload_time = upload_time_for_first_video_in_batch

        for entry in pending_entries:
            if current_scheduled_upload_time < current_timestamp:
                print(f"Warning: Calculated upload time for {entry.get_id()} ({current_scheduled_upload_time}) is in the past. Adjusting to now + 1 minute.")
                current_scheduled_upload_time = current_timestamp + timedelta(hour=6)

            print(f"Attempting to upload video '{entry.get_description()}' (ID: {entry.get_id()}) scheduled for {current_scheduled_upload_time.isoformat()}")

            if YoutubeUploader.upload_video(
                entry.get_description(), 
                entry.get_description(), 
                VideoGenerator.get_clip_folder() + entry.get_filename(), 
                current_scheduled_upload_time
            ):
                Database.mark_youtube_uploaded(entry.get_id())
                print(f"Successfully uploaded and marked entry {entry.get_id()}")
            else:
                print(f"Failed to upload {entry.get_id()}")
            
            current_scheduled_upload_time += timedelta(hours=Pipeline.UPLOAD_COOLDOWN)

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
