import streamlit as st
import cv2
import tempfile
import numpy as np
from moviepy.editor import VideoFileClip
import os

# Function to convert hex color to BGR format for OpenCV
def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return rgb[::-1]  # Reverse to get BGR

# Function to dynamically crop the frame around the cursor
def dynamic_crop(frame, cursor_x, cursor_y, aspect_ratio, frame_width, frame_height):
    crop_width, crop_height = frame_width, frame_height  # Initialize to frame size
    
    if aspect_ratio == "1:1":
        crop_width = crop_height = min(frame_width, frame_height)
    elif aspect_ratio == "4:3":
        crop_width = int(frame_height * 4 / 3)
        crop_height = frame_height
    elif aspect_ratio == "16:9":
        crop_width = int(frame_height * 16 / 9)
        crop_height = frame_height
    elif aspect_ratio == "9:16":
        crop_height = int(frame_width * 16 / 9)
        crop_width = frame_width
    elif aspect_ratio == "3:4":
        crop_height = frame_height
        crop_width = int(frame_height * 3 / 4)

    # Ensure cropping doesn't go out of bounds
    x_min = max(0, cursor_x - crop_width // 2)
    y_min = max(0, cursor_y - crop_height // 2)
    x_max = min(frame_width, x_min + crop_width)
    y_max = min(frame_height, y_min + crop_height)
    
    return frame[y_min:y_max, x_min:x_max]

# Function to detect cursor
def detect_cursor(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_frame, 240, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        return x + w // 2, y + h // 2  # Return cursor center
    return None, None

# Add cursor highlight with cropping
def add_cursor_highlight_to_frame(get_frame, t):
    frame = get_frame(t).copy()  # Copy the frame to make it writable
    cursor_x, cursor_y = detect_cursor(frame)

    if cursor_x is not None and cursor_y is not None:
        frame = dynamic_crop(frame, cursor_x, cursor_y, selected_ratio, frame.shape[1], frame.shape[0])
        overlay = frame.copy()
        bgr_color = hex_to_bgr(cursor_color)
        cv2.circle(overlay, (cursor_x, cursor_y), radius, bgr_color, -1)
        cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

    return frame

# Streamlit app UI
st.title("ClipFocus: Cursor Highlighting and Cropping Tool")

# Upload video
uploaded_video = st.file_uploader("Upload your tutorial video", type=["mp4", "avi", "mov"])

# Expandable settings for aspect ratio, highlight color, etc.
with st.expander("More Settings"):
    st.subheader("Image Size")
    selected_ratio = st.radio(
        "Aspect Ratio",
        options=["16:9", "9:16", "4:3", "1:1", "3:4"],
        index=0,
        horizontal=True
    )

    st.subheader("Cursor Highlight Settings")
    cursor_color = st.color_picker("Pick cursor highlight color", "#FF0000")
    radius = st.slider("Cursor highlight size (px)", 5, 50, 15)
    opacity = st.slider("Cursor highlight opacity", 0.1, 1.0, 0.5)

# Process video when "Focus" button is pressed
if uploaded_video:
    focus_button = st.button("Focus")
    if focus_button:
        st.subheader("Processing Video")
        
        # Save uploaded video temporarily
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_video.read())
        
        # Load video
        video_clip = VideoFileClip(tfile.name)

        # Apply cursor highlighting and cropping
        highlighted_clip = video_clip.fl_image(lambda frame: add_cursor_highlight_to_frame(lambda t: frame, 0))

        # Save the processed video
        processed_video_path = os.path.join(tempfile.gettempdir(), "processed_video_with_audio.mp4")
        highlighted_clip.write_videofile(processed_video_path, codec="libx264", audio_codec="aac")
        
        # Display the video
        st.video(processed_video_path)
        
        # Add a download button for the processed video
        with open(processed_video_path, "rb") as f:
            st.download_button("Download Processed Video", f, "processed_video_with_audio.mp4")

