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

# Function to apply aspect ratio
def apply_aspect_ratio(clip, aspect_ratio):
    if aspect_ratio == "1:1":
        side = min(clip.size)
        return vfx.crop(clip, width=side, height=side, x_center=clip.w // 2, y_center=clip.h // 2)
    elif aspect_ratio == "4:3":
        width = int(clip.h * 4 / 3)
        return vfx.crop(clip, width=width, height=clip.h, x_center=clip.w // 2, y_center=clip.h // 2)
    elif aspect_ratio == "16:9":
        width = int(clip.h * 16 / 9)
        return vfx.crop(clip, width=width, height=clip.h, x_center=clip.w // 2, y_center=clip.h // 2)
    elif aspect_ratio == "9:16":  # Flipping the dimensions for portrait
        height = int(clip.w * 16 / 9)
        return vfx.crop(clip, width=clip.w, height=height, x_center=clip.w // 2, y_center=clip.h // 2)
    elif aspect_ratio == "3:4":
        height = int(clip.w * 4 / 3)
        return vfx.crop(clip, width=clip.w, height=height, x_center=clip.w // 2, y_center=clip.h // 2)
    else:
        return clip  # No cropping if aspect ratio is not matched


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

        # Display boxes based on the selected aspect ratio
        st.markdown('<div class="ratio-container">', unsafe_allow_html=True)
        if selected_ratio == "Portrait (9:16)":
            st.markdown('<div class="ratio-box box-portrait-9-16 selected">9:16</div>', unsafe_allow_html=True)
        elif selected_ratio == "Portrait (3:4)":
            st.markdown('<div class="ratio-box box-portrait-3-4 selected">3:4</div>', unsafe_allow_html=True)
        elif selected_ratio == "Square (1:1)":
            st.markdown('<div class="ratio-box box-square selected">1:1</div>', unsafe_allow_html=True)
        elif selected_ratio == "Landscape (4:3)":
            st.markdown('<div class="ratio-box box-landscape-small selected">4:3</div>', unsafe_allow_html=True)
        elif selected_ratio == "Landscape (16:9)":
            st.markdown('<div class="ratio-box box-landscape-large selected">16:9</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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

    # Apply aspect ratio cropping - this step must happen before any other processing
    cropped_clip = apply_aspect_ratio(clip, selected_ratio)

    # Define a function to process each frame (if any other processing is needed later)
    def process_frame(get_frame, t):
        frame = get_frame(t)
        return frame  # Here you can modify or process the frame further if needed

    # Apply any further frame-by-frame processing (if required, but skipping for now)
    final_clip = cropped_clip.fl(process_frame)

    # Save the processed video
    processed_video_path = os.path.join(tempfile.gettempdir(), "processed_video_with_audio.mp4")
    final_clip.write_videofile(processed_video_path, codec="libx264", audio=True)

    # Show the video preview
    st.video(processed_video_path)

    # Add a download button for the processed video
    with open(processed_video_path, "rb") as f:
        st.download_button("Download Processed Video", f, "processed_video_with_audio.mp4", "video/mp4")
