import streamlit as st
import cv2
import numpy as np
import tempfile

st.title("ClipFocus")

# Allow the user to upload a video
uploaded_video = st.file_uploader("Upload your tutorial video", type=["mp4", "mov"])

if uploaded_video:
    # Save the uploaded file temporarily
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_video.read())

    # Open the video with OpenCV
    cap = cv2.VideoCapture(tfile.name)

    # Check if the video was successfully opened
    if not cap.isOpened():
        st.error("Error: Could not open the video file.")
    else:
        st.text("Video uploaded and ready for processing")

        def highlight_cursor(frame):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                cv2.circle(frame, (x + w // 2, y + h // 2), 20, (0, 0, 255), 3)

            return frame

        # Display the processed video
        stframe = st.empty()  # This is where the processed video will be displayed

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Apply cursor highlighting to the frame
            highlighted_frame = highlight_cursor(frame)

            # Convert the image color format from OpenCV to display in Streamlit
            highlighted_frame = cv2.cvtColor(highlighted_frame, cv2.COLOR_BGR2RGB)
            stframe.image(highlighted_frame, channels="RGB")

        cap.release()

else:
    st.info("Please upload a video to begin processing.")
