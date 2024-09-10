import streamlit as st
import cv2
import numpy as np
import tempfile

# Custom CSS to style the aspect ratio boxes and ensure full-width expander
st.markdown("""
    <style>
    .reportview-container .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .stExpander {
        width: 100%;  /* Make the expander full width */
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
        width: 100%;  /* Make the Focus button full width */
        height: 45px; /* Ensure the button height is consistent */
    }
    </style>
    """, unsafe_allow_html=True)

st.title("ClipFocus")

# Define a function to draw a transparent circle at the cursor location
def highlight_cursor(frame, cursor_color=(255, 0, 0), opacity=0.5, radius=20):
    overlay = frame.copy()  # Create a copy of the frame to apply the overlay
    height, width, _ = frame.shape
    # Calculate the center of the frame as the location for the circle
    center_x, center_y = width // 2, height // 2
    # Draw a filled circle on the overlay
    cv2.circle(overlay, (center_x, center_y), radius, cursor_color, -1)
    # Apply the overlay with transparency (using the specified opacity)
    cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
    return frame

def crop_to_ratio(frame, aspect_ratio):
    h, w, _ = frame.shape
    if aspect_ratio == "1:1":  # Square
        target_width = min(h, w)
        start_x = (w - target_width) // 2
        start_y = (h - target_width) // 2
        return frame[start_y:start_y + target_width, start_x:start_x + target_width]
    elif aspect_ratio == "4:3":
        target_width = int(h * 4 / 3)
    elif aspect_ratio == "16:9":
        target_width = int(h * 16 / 9)
    elif aspect_ratio == "9:16":
        target_width = int(h * 9 / 16)
    elif aspect_ratio == "3:4":  # Added Portrait 3:4
        target_width = int(h * 3 / 4)
    else:
        return frame  # No cropping if no valid ratio is selected
    
    # Crop to center of the frame
    start_x = (w - target_width) // 2
    return frame[:, start_x:start_x + target_width]

# Upload area
st.subheader("Upload your tutorial video")
uploaded_video = st.file_uploader("Drag and drop file here", type=["mp4", "mov"])

# Cursor highlight settings
st.subheader("Cursor Highlight Settings")
cursor_color = st.color_picker("Pick a cursor highlight color", "#FF0000")  # Default red
opacity = st.slider("Select opacity for the highlight", min_value=0.1, max_value=1.0, value=0.5)
radius = st.slider("Select the radius for the highlight", min_value=10, max_value=100, value=20)

# Create columns for the expandable section and the Focus button to stay aligned
col1, col2 = st.columns([6, 1])  # Increased width of the expandable area

with col1:
    # Expandable "More Settings" section for Image Size selection
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
    # "Focus" button to trigger the processing, aligned to the right
    focus_button = st.button("Focus")

# Process the video and display the preview below the drag-and-drop area
if uploaded_video and focus_button:
    st.subheader("Video Preview")
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
        
        # Set up the progress bar and placeholder for displaying the video
        progress_bar = st.progress(0)
        stframe = st.empty()  # This is where the processed video will be displayed
        progress_text = st.empty()  # For displaying the current frame number

        current_frame = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Crop the frame to the selected aspect ratio
            cropped_frame = crop_to_ratio(frame, selected_ratio)

            # Apply cursor highlighting (add a transparent circle)
            highlight_color = tuple(int(cursor_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))  # Convert hex to BGR
            highlighted_frame = highlight_cursor(cropped_frame, cursor_color=highlight_color, opacity=opacity, radius=radius)

            # Convert and display the current frame in the stream
            highlighted_frame_rgb = cv2.cvtColor(highlighted_frame, cv2.COLOR_BGR2RGB)
            stframe.image(highlighted_frame_rgb, caption=f"Frame {current_frame + 1}/{total_frames}", channels="RGB")

            # Update the progress bar and text
            current_frame += 1
            progress_percentage = int((current_frame / total_frames) * 100)
            progress_bar.progress(progress_percentage)
            progress_text.text(f"Processing frame {current_frame} of {total_frames}")

        cap.release()
        st.success("Video processing complete!")
