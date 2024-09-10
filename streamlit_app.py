import streamlit as st
import cv2
import numpy as np
import tempfile

st.title("ClipFocus")

def crop_to_vertical(frame):
    h, w, _ = frame.shape
    # Calculate the width for a 9:16 ratio
    target_width = int(h * 9 / 16)
    
    # Crop the frame to the center
    start_x = w // 2 - target_width // 2
    return frame[:, start_x:start_x+target_width]

def highlight_cursor(frame, color=(0, 0, 255), radius=20):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        cv2.circle(frame, (x + w // 2, y + h // 2), radius, color, 3)
    
    return frame

# Allow the user to upload a video
uploaded_video = st.file_uploader("Upload your tutorial video", type=["mp4", "mov"])

if uploaded_video:
    # Save the uploaded file temporarily
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_video.read())

    # Open the video with OpenCV
    cap = cv2.VideoCapture(tfile.name)

    if not cap.isOpened():
        st.error("Error: Could not open the video file.")
    else:
        st.text("Video uploaded and ready for processing")

        # Get the total number of frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Set up the progress bar
        progress_bar = st.progress(0)
        progress_text = st.empty()  # For displaying the current frame number

        stframe = st.empty()  # This is where the processed video will be displayed
        
        current_frame = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Crop the frame to vertical format
            cropped_frame = crop_to_vertical(frame)

            # Apply cursor highlighting to the cropped frame
            highlighted_frame = highlight_cursor(cropped_frame)

            # Convert and display
            highlighted_frame = cv2.cvtColor(highlighted_frame, cv2.COLOR_BGR2RGB)
            stframe.image(highlighted_frame, channels="RGB")
            
            # Update the progress bar and text
            current_frame += 1
            progress_percentage = int((current_frame / total_frames) * 100)
            progress_bar.progress(progress_percentage)
            progress_text.text(f"Processing frame {current_frame} of {total_frames}")

        cap.release()
        st.success("Video processing complete!")
