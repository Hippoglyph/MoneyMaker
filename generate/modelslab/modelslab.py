import json
import os
import time

import requests

from generate.video_generator import VideoGenerator


class ModelSlab(VideoGenerator):

    def generate(prompt : str) -> str:
        payload = ModelSlab._get_payload(prompt)
        response = requests.request("POST", "https://modelslab.com/api/v6/video/text2video_ultra", headers={'Content-Type': 'application/json'}, data=payload)
        if response.status_code == 200:
            dict_response = json.loads(response.text)
            dict_response = ModelSlab._wait_until_done(dict_response)
            if dict_response["status"] == "success":
                return ModelSlab._handle_success_response(dict_response)
        else:
            raise RuntimeError(response)
            
    def _wait_until_done(response : dict) -> dict:
        while response["status"] == "processing":
            print(f"Debug: Sleeping for {response["eta"]} seconds")
            time.sleep(response["eta"])
            check_response = requests.request("POST", response["fetch_result"], headers={'Content-Type': 'application/json'}, data=json.dumps({"key": os.getenv("MODELSLAB_KEY")}))
            dict_check_response = json.loads(check_response.text)
            if dict_check_response["status"] == "success":
                response["status"] = "success"
                response["output"] = dict_check_response["output"]
            elif dict_check_response["status"] == "error":
                raise RuntimeError(dict_check_response)
        return response
            

    def _handle_success_response(response : dict) -> str:
        url = response["output"][0]
        file_name = response["meta"]["file_prefix"] + "." + response["meta"]["output_type"]
        with requests.get(url, stream=True) as file_object:
            file_object.raise_for_status()
            with open(VideoGenerator.get_clip_folder() + file_name, 'wb') as f:
                # Download the file in chunks of 8KB
                for chunk in file_object.iter_content(chunk_size=8192):
                    f.write(chunk)
        return file_name

    def _get_payload(prompt : str) -> str:
        return json.dumps({
            "key": os.getenv("MODELSLAB_KEY"),
            "prompt": prompt,
            #"blurry, low quality, pixelated, deformed, mutated, disfigured, bad anatomy, extra limbs, missing limbs, unrealistic motion, glitch, noisy, oversaturated, underexposed, overexposed, poor lighting, low contrast, unnatural colors, jpeg artifacts, watermark, text, signature, cut off, cropped, stretched, distorted face, bad proportions, duplicated limbs, broken body, grain, flickering, frame skipping, motion blur, unrealistic shadows, low detail, low resolution, compression artifacts, out of frame"
            "negative_prompt": None,
            "fps": 24,
            "guidance_scale": 5,
            "num_frames": 129,
            "num_inference_steps": 30,
            "resolution": 480,
            "sample_shift": 5,
            "portrait": True,
            "webhook": None,
            "track_id": None,
            "temp": True
        })