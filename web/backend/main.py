import os
import cv2
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random
from typing import List
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(
    title="Dataset Editor API",
    description="API for splitting video files into frames for further processing.",
    version="1.0.0",
    contact={
        "name": "febri dwi putro",
        "email": "putrodwifebri@gmail.com",
    },
    license_info={
        "name": "MIT License",
    }
)

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as necessary for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy Data for Dataset Split Features
menu_data =  {
  "menu": [
    {
      "name": "Video Editor",
      "description": "Process videos such as splitting into frames, resizing, compressing, etc.",
      "sub_features": [
        {
          "name": "Split Video",
          "description": "Split videos into frames based on the number of images or duration.",
          "points": [
            {
              "name": "Split by Number of Images"
            },
            {
              "name": "Split by Duration"
            },
            {
              "name": "Split by Frame Rate"
            }
          ]
        }
      ]
    },
    {
      "name": "Dataset Split",
      "description": "Split datasets for model training.",
      "sub_features": [
        {
          "name": "Audio Dataset Split",
          "description": "Split audio files based on duration, silence detection, or custom segments.",
          "points": [
            {
              "name": "Split by Duration"
            },
            {
              "name": "Split by Number of Segments"
            },
            {
              "name": "Split by Silence Detection"
            },
            {
              "name": "Balanced Audio Split"
            },
            {
              "name": "Batch Audio Split"
            }
          ]
        },
        {
          "name": "Text Dataset Split",
          "description": "Split text files for NLP models by sentence, word count, or paragraph.",
          "points": [
            {
              "name": "Split by Sentence/Paragraph"
            },
            {
              "name": "Split by Word Count"
            },
            {
              "name": "Split by Character Count"
            },
            {
              "name": "Random Text Split"
            },
            {
              "name": "Stratified Text Split"
            },
            {
              "name": "Split by Chapter/Section"
            }
          ]
        },
        {
          "name": "Image Dataset Split",
          "description": "Split image datasets based on number of images or stratified categories.",
          "points": [
            {
              "name": "Split by Number of Images"
            },
            {
              "name": "Split by Image Size"
            },
            {
              "name": "Random Image Split"
            },
            {
              "name": "Stratified Image Split"
            },
            {
              "name": "Class-based Split"
            },
            {
              "name": "Aspect Ratio Split"
            }
          ]
        }
      ]
    }
  ]
}

@app.get("/menu")
async def get_menu():
    """
    Returns the dataset split and video editor features menu.
    """
    return menu_data


app.mount("/output", StaticFiles(directory="output"), name="output")

progress_status = {}

@app.post("/split-video", summary="Split Video into Frames", description="Endpoint to upload a video and split it into a specified number of frames.")
async def split_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...), 
    num_images: int = Form(...)
):
    """
    Upload a video file and specify the number of images to extract from the video.
    
    Parameters:
    - **video**: Video file (MP4)
    - **num_images**: Number of frames to extract from the video
    """
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)        

    video_id = random.randint(1000, 9999)  # Generate a unique ID for the video
    video_path = f"./{video.filename}"
    
    # Save the video file
    with open(video_path, "wb") as f:
        f.write(await video.read())

    # Start the background task to process the video
    progress_status[video_id] = 0 
    background_tasks.add_task(process_video, video_id, video_path, num_images, output_dir)

    return {"message": "Video processing started", "video_id": video_id}


def process_video(video_id, video_path, num_images, output_dir):
    """
    Function to process the video in the background and split it into frames.
    This is executed in the background and does not block the API.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        progress_status[video_id] = -1 
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = total_frames // num_images

    count = 0
    frame_idx = 0
    image_list = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0 and count < num_images:
            timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            filename = f"char-{timestamp}-{random.randint(0, 1000)}.png"
            output_path = os.path.join(output_dir, filename)

            cv2.imwrite(output_path, frame)
            image_list.append(output_path)
            count += 1

            # Update progress
            progress_status[video_id] = (count / num_images) * 100

        frame_idx += 1

    cap.release()
    os.remove(video_path) 
    progress_status[video_id] = 100 

@app.get("/progress/{video_id}", summary="Check video processing progress")
async def check_progress(video_id: int):
    """
    Endpoint to check the progress of a video splitting task.
    """
    progress = progress_status.get(video_id, -1)
    if progress == -1:
        return {"status": "error", "message": "Invalid video ID"}
    return {"status": "processing", "progress": progress}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)