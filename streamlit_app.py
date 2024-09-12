import streamlit as st
import cv2
import numpy as np
import tempfile
import os
from moviepy.editor import VideoFileClip
import moviepy.video.fx.all as vfx

# Custom CSS for the UI layout
st.markdown("""
    <style>
    .reportview-container .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .stExpander {
        width: 100%;
    }
    .ratio-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin-bottom: 1rem;
        width: 100%;
    }
    .ratio-box {
        display: flex;
        justify-content: center;
        align-items: center;
        border: 2px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        cursor: pointer;
        transition: border-color 0.3s;
        text-align: center;
    }
    .ratio-box.selected {
        border-color: #FF4B4B;
    }
    .box-portrait-9-16, .box-portrait-3-4 {
        width: 40px;
        height: 70px;
    }
    .box-square {
        width: 60px;
        height: 60px;
    }
    .box-landscape-small {
        width: 80px;
        height: 60px;
    }
    .box-landscape-large {
        width: 100px;
        height: 56px;
    }
    .stButton button {
        width: 100%;
        height: 45px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("ClipFocus")

# Function to apply dynamic aspect ratio cropping around the cursor
def dynamic_crop(frame, cursor_x, cursor_y, aspect_ratio, frame_width, frame_height):
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

# Function to convert hex color to BGR format for OpenCV
def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return rgb[::-1]  # Reverse to get BGR

# Define a function to detect the cursor and add dynamic highlight
def detect_cursor(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_frame, 240, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        return x + w // 2, y + h // 2  # Return cursor center
    return None, None

# Upload video
uploaded_video = st.file_uploader("Upload your tutorial video", type=["mp4", "mov"])

# Create columns for the expandable section and the Focus button
col1, col2 = st.columns([6, 1])

with col1:
    # Expandable "More Settings" section
    with st.expander("More Settings"):
        st.subheader("Image Size")
        
        # Aspect Ratio Selection
        selected_ratio = st.radio(
            "Aspect Ratio",
            options=["Portrait (9:16)", "Portrait (3:4)", "Square (1:1)", "Landscape (4:3)", "Landscape (16:9)"],
            index=2,
            horizontal=True
        )

        # Cursor highlight settings below aspect ratio
        st.subheader("Cursor Highlight Settings")
        cursor_color = st.color_picker("Pick a cursor highlight color", "#FF0000")
        opacity = st.slider("Select opacity for the highlight", min_value=0.1, max_value=1.0, value=0.5)
        radius = st.slider("Select the radius for the highlight", min_value=10, max_value=100, value=20)

with col2:
    # "Focus" button to trigger processing
    focus_button = st.button("Focus")

# Process the video and display the preview
if uploaded_video and focus_button:
    st.subheader("Processing Video")

    # Save uploaded video temporarily
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_video.read())
    tfile.flush()

    # Load video with MoviePy
    clip = VideoFileClip(tfile.name)

    # Get frame dimensions
    frame_width, frame_height = clip.size

    # Define a function to process each frame, detect cursor, and crop dynamically
    def add_cursor_highlight_to_frame(get_frame, t):
        frame = get_frame(t)

        # Detect cursor position
        cursor_x, cursor_y = detect_cursor(frame)

        if cursor_x is not None and cursor_y is not None:
            # Apply dynamic cropping
            frame = dynamic_crop(frame, cursor_x, cursor_y, selected_ratio, frame_width, frame_height)

            # Highlight the cursor
            overlay = frame.copy()
            bgr_color = hex_to_bgr(cursor_color)
            cv2.circle(overlay, (cursor_x, cursor_y), radius, bgr_color, -1)
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

        return frame

    # Apply cursor detection and highlight frame-by-frame
    highlighted_clip = clip.fl(add_cursor_highlight_to_frame)

    # Save the processed video
    processed_video_path = os.path.join(tempfile.gettempdir(), "processed_video_with_audio.mp4")
    highlighted_clip.write_videofile(processed_video_path, codec="libx264", audio=True)

    # Display the video
    st.video(processed_video_path)

    # Add a download button for the processed video
    with open(processed_video_path, "rb") as f:
        st.download_button("Download Processed Video", f, "processed_video_with_audio.mp4", "video/mp4")
