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

# Updated function to correctly apply aspect ratio
def apply_aspect_ratio(clip, aspect_ratio):
    clip_width, clip_height = clip.size

    st.write(f"Original Clip Dimensions: {clip_width}x{clip_height}")  # Print clip size for debugging

    if aspect_ratio == "Square (1:1)":
        crop_size = min(clip_width, clip_height)
        st.write(f"Cropping to 1:1 with size: {crop_size}")
        return vfx.crop(clip, width=crop_size, height=crop_size, x_center=clip_width // 2, y_center=clip_height // 2)
    elif aspect_ratio == "Landscape (4:3)":
        new_width = int(clip_height * 4 / 3)
        st.write(f"Cropping to 4:3 with new width: {new_width}")
        return vfx.crop(clip, width=new_width, height=clip_height, x_center=clip_width // 2, y_center=clip_height // 2)
    elif aspect_ratio == "Landscape (16:9)":
        new_width = int(clip_height * 16 / 9)
        st.write(f"Cropping to 16:9 with new width: {new_width}")
        return vfx.crop(clip, width=new_width, height=clip_height, x_center=clip_width // 2, y_center=clip_height // 2)
    elif aspect_ratio == "Portrait (9:16)":
        new_height = int(clip_width * 16 / 9)
        st.write(f"Cropping to 9:16 with new height: {new_height}")
        return vfx.crop(clip, width=clip_width, height=new_height, x_center=clip_width // 2, y_center=clip_height // 2)
    elif aspect_ratio == "Portrait (3:4)":
        new_height = int(clip_width * 4 / 3)
        st.write(f"Cropping to 3:4 with new height: {new_height}")
        return vfx.crop(clip, width=clip_width, height=new_height, x_center=clip_width // 2, y_center=clip_height // 2)
    else:
        st.write("No cropping applied.")
        return clip

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

    # Apply aspect ratio cropping
    clip = apply_aspect_ratio(clip, selected_ratio)

    # Progress bar
    progress_bar = st.progress(0)
    n_frames = clip.reader.nframes
    current_frame = 0

    # Define a function to update progress as frames are processed
    def update_progress(get_frame, t):
        global current_frame
        frame = get_frame(t)
        current_frame += 1
        progress_bar.progress(min(current_frame / n_frames, 1.0))
        return frame

    # Apply frame processing with progress tracking
    processed_clip = clip.fl(update_progress)

    # Save the processed video
    processed_video_path = os.path.join(tempfile.gettempdir(), "processed_video_with_audio.mp4")
    processed_clip.write_videofile(processed_video_path, codec="libx264", audio=True)

    # Display the video
    st.video(processed_video_path)

    # Add a download button for the processed video
    with open(processed_video_path, "rb") as f:
        st.download_button("Download Processed Video", f, "processed_video_with_audio.mp4", "video/mp4")
