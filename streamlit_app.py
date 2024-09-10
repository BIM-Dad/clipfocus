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
        return vfx.crop(clip, width=min(clip.size), height=min(clip.size), x_center=clip.w // 2, y_center=clip.h // 2)
    elif aspect_ratio == "4:3":
        return vfx.crop(clip, width=int(clip.h * 4 / 3), height=clip.h, x_center=clip.w // 2, y_center=clip.h // 2)
    elif aspect_ratio == "16:9":
        return vfx.crop(clip, width=int(clip.h * 16 / 9), height=clip.h, x_center=clip.w // 2, y_center=clip.h // 2)
    elif aspect_ratio == "9:16":
        return vfx.crop(clip, width=clip.w, height=int(clip.w * 16 / 9), x_center=clip.w // 2, y_center=clip.h // 2)
    elif aspect_ratio == "3:4":
        return vfx.crop(clip, width=int(clip.h * 3 / 4), height=clip.h, x_center=clip.w // 2, y_center=clip.h // 2)
    else:
        return clip  # No cropping

# Define a function to add dynamic cursor highlight
def add_cursor_highlight(frame, t, cursor_color, radius, opacity, clip):
    overlay = frame.copy()

    # Simulating dynamic cursor movement
    height, width, _ = frame.shape
    cursor_x = int((t / clip.duration) * width)  # Simulate cursor movement from left to right
    cursor_y = int(height / 2)  # Keep it centered vertically

    # Draw the transparent circle for the cursor highlight
    circle_color = tuple(int(cursor_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    cv2.circle(overlay, (cursor_x, cursor_y), radius, circle_color, -1)
    
    # Apply the overlay with transparency
    cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
    
    return frame

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

    # Apply aspect ratio cropping
    clip = apply_aspect_ratio(clip, selected_ratio)

    # Define a function to process each frame with dynamic cursor highlight
    def add_cursor_highlight_to_frame(get_frame, t):
        frame = get_frame(t)
        return add_cursor_highlight(frame, t, cursor_color, radius, opacity, clip)

    # Apply cursor highlight frame-by-frame
    highlighted_clip = clip.fl(add_cursor_highlight_to_frame)

    # Save the processed video
    processed_video_path = os.path.join(tempfile.gettempdir(), "processed_video_with_audio.mp4")
    highlighted_clip.write_videofile(processed_video_path, codec="libx264", audio=True)

    # Display the video
    st.video(processed_video_path)

    # Add a download button for the processed video
    with open(processed_video_path, "rb") as f:
        st.download_button("Download Processed Video", f, "processed_video_with_audio.mp4", "video/mp4")
