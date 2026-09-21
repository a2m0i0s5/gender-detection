import cv2
import argparse
import os
import sys

def highlightFace(net, frame, conf_threshold=0.7):
    try:
        frameOpencvDnn = frame.copy()
        frameHeight = frameOpencvDnn.shape[0]
        frameWidth = frameOpencvDnn.shape[1]
        blob = cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)

        net.setInput(blob)
        detections = net.forward()
        faceBoxes = []
        for i in range(detections.shape[2]):
            confidence = detections[0,0,i,2]
            if confidence > conf_threshold:
                x1 = int(detections[0,0,i,3]*frameWidth)
                y1 = int(detections[0,0,i,4]*frameHeight)
                x2 = int(detections[0,0,i,5]*frameWidth)
                y2 = int(detections[0,0,i,6]*frameHeight)
                faceBoxes.append([x1,y1,x2,y2])
                cv2.rectangle(frameOpencvDnn, (x1,y1), (x2,y2), (0,255,0), int(round(frameHeight/150)), 8)
        return frameOpencvDnn, faceBoxes
    except Exception as e:
        print(f"Error in highlightFace: {e}")
        return frame, []

# Parse arguments
parser = argparse.ArgumentParser(description="Gender and Age Detection using OpenCV and Caffe models")
parser.add_argument('--image', type=str, help='Path to input image file')
parser.add_argument('--video', type=str, help='Path to input video file')
parser.add_argument('--device', type=int, default=0, help='Camera device index (default: 0)')
parser.add_argument('--output', type=str, help='Path to save output image or video file')
parser.add_argument('--padding', type=int, default=20, help='Padding around the face for classification (default: 20)')
parser.add_argument('--conf', type=float, default=0.7, help='Confidence threshold for face detection (default: 0.7)')
parser.add_argument('--headless', action='store_true', help='Run in headless mode (no GUI windows)')
args = parser.parse_args()

script_dir = os.path.dirname(os.path.abspath(__file__))
faceProto = os.path.join(script_dir, "opencv_face_detector.pbtxt")
faceModel = os.path.join(script_dir, "opencv_face_detector_uint8.pb")
ageProto = os.path.join(script_dir, "age_deploy.prototxt")
ageModel = os.path.join(script_dir, "age_net.caffemodel")
genderProto = os.path.join(script_dir, "gender_deploy.prototxt")
genderModel = os.path.join(script_dir, "gender_net.caffemodel")

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
genderList = ['Male', 'Female']

# Load Models
try:
    faceNet = cv2.dnn.readNet(faceModel, faceProto)
    print("Face model loaded successfully")
except Exception as e:
    print(f"Error loading face model: {e}")
    sys.exit(1)

try:
    ageNet = cv2.dnn.readNet(ageModel, ageProto)
    print("Age model loaded successfully")
except Exception as e:
    print(f"Error loading age model: {e}")
    sys.exit(1)

try:
    genderNet = cv2.dnn.readNet(genderModel, genderProto)
    print("Gender model loaded successfully")
except Exception as e:
    print(f"Error loading gender model: {e}")
    sys.exit(1)

padding = args.padding
conf_threshold = args.conf

# Helper to process a face crop and return gender, age
def process_face(face_crop):
    if face_crop is None or face_crop.size == 0:
        return "Unknown", "(Unknown)", 0.0, 0.0
    blob = cv2.dnn.blobFromImage(face_crop, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
    
    # Predict gender
    gender = "Unknown"
    gender_conf = 0.0
    try:
        genderNet.setInput(blob)
        genderPreds = genderNet.forward()
        gender_idx = genderPreds[0].argmax()
        gender = genderList[gender_idx]
        gender_conf = genderPreds[0][gender_idx]
    except Exception as e:
        print(f"Error in gender prediction: {e}")
        
    # Predict age
    age = "(Unknown)"
    age_conf = 0.0
    try:
        ageNet.setInput(blob)
        agePreds = ageNet.forward()
        age_idx = agePreds[0].argmax()
        age = ageList[age_idx]
        age_conf = agePreds[0][age_idx]
    except Exception as e:
        print(f"Error in age prediction: {e}")
        
    return gender, age, gender_conf, age_conf

# Show helper that handles headless environment gracefully
show_window_failed = False
def display_frame(window_name, frame):
    global show_window_failed
    if args.headless or show_window_failed:
        return False
    try:
        cv2.imshow(window_name, frame)
        return True
    except Exception:
        show_window_failed = True
        print("Note: Running in headless mode or display unavailable. GUI window disabled.")
        return False

# Mode 1: Single Image
if args.image:
    # Read the image. Check both absolute paths and paths relative to working directory / script directory
    frame = cv2.imread(args.image)
    if frame is None:
        # Try relative to script directory as fallback
        fallback_path = os.path.join(script_dir, args.image)
        frame = cv2.imread(fallback_path)
        
    if frame is None:
        print(f"Error: Could not load image from '{args.image}'")
        sys.exit(1)
        
    print("Processing image...")
    resultImg, faceBoxes = highlightFace(faceNet, frame, conf_threshold)
    if not faceBoxes:
        print("No face detected")
        cv2.putText(resultImg, "No face detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
    else:
        print(f"Detected {len(faceBoxes)} face(s)")
        h, w, _ = frame.shape
        for faceBox in faceBoxes:
            x1_c = max(0, faceBox[0] - padding)
            y1_c = max(0, faceBox[1] - padding)
            x2_c = min(w, faceBox[2] + padding)
            y2_c = min(h, faceBox[3] + padding)
            face = frame[y1_c:y2_c, x1_c:x2_c]
            
            gender, age, g_conf, a_conf = process_face(face)
            print(f'Detected: Gender={gender} ({g_conf:.2%}), Age={age[1:-1]} years ({a_conf:.2%})')
            
            # Draw label - adjust position if face is at the very top edge of the image
            label = f'{gender}, {age}'
            label_y = faceBox[1] - 10 if faceBox[1] - 10 > 20 else faceBox[3] + 25
            cv2.putText(resultImg, label, (faceBox[0], label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            
    # Show output if GUI is supported
    display_frame("Detecting age and gender", resultImg)
    
    # Save output if requested
    if args.output:
        cv2.imwrite(args.output, resultImg)
        print(f"Result saved to {args.output}")
    elif show_window_failed or args.headless:
        # Automatically save to default file if GUI is unsupported/headless and no output path was given
        default_out = "output_result.jpg"
        cv2.imwrite(default_out, resultImg)
        print(f"Running headless. Output automatically saved to {default_out}")
        
    if not args.headless and not show_window_failed:
        cv2.waitKey(0)
    cv2.destroyAllWindows()

# Mode 2: Video File or Webcam
else:
    source = args.video if args.video else args.device
    source_type = "video file" if args.video else "webcam"
    print(f"Opening {source_type}: {source}")
    
    video = cv2.VideoCapture(source)
    if not video.isOpened():
        print(f"Error: Could not open {source_type}")
        sys.exit(1)
        
    # Get video properties
    frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 100:
        fps = 30.0
        
    # Video Writer setup if output requested
    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(args.output, fourcc, fps, (frame_width, frame_height))
        print(f"Writing output video to {args.output}")
        
    # Buffer to prevent box flickering when face detection temporarily fails for a few frames
    history_faces = []
    history_decay = 0
    
    print("Press 'q' or 'ESC' in the window to exit.")
    while True:
        hasFrame, frame = video.read()
        if not hasFrame:
            print("Finished processing video or no frame read.")
            break
            
        resultImg, faceBoxes = highlightFace(faceNet, frame, conf_threshold)
        
        # Flickering protection
        if faceBoxes:
            history_faces = faceBoxes
            history_decay = 5  # Persist detection boxes for 5 frames
        else:
            if history_decay > 0:
                history_decay -= 1
                # Use history faces
                faceBoxes = history_faces
                # Redraw rectangles for history faces on resultImg
                for box in faceBoxes:
                    cv2.rectangle(resultImg, (box[0], box[1]), (box[2], box[3]), (0, 165, 255), int(round(frame_height/150)), 8)
                    
        if not faceBoxes:
            cv2.putText(resultImg, "No face detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            h, w, _ = frame.shape
            for faceBox in faceBoxes:
                x1_c = max(0, faceBox[0] - padding)
                y1_c = max(0, faceBox[1] - padding)
                x2_c = min(w, faceBox[2] + padding)
                y2_c = min(h, faceBox[3] + padding)
                face = frame[y1_c:y2_c, x1_c:x2_c]
                
                gender, age, g_conf, a_conf = process_face(face)
                
                # Draw label
                label = f'{gender}, {age}'
                label_y = faceBox[1] - 10 if faceBox[1] - 10 > 20 else faceBox[3] + 25
                cv2.putText(resultImg, label, (faceBox[0], label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                
        # Save frame to output video file
        if writer:
            writer.write(resultImg)
            
        # Display frame
        display_success = display_frame("Detecting age and gender", resultImg)
        
        # In webcam/video mode, if we are in headless mode and not writing to a file, warn user
        if (args.headless or show_window_failed) and not writer:
            print("Warning: Running headless but no output file specified. Saving current frame to output_result.jpg and exiting.")
            cv2.imwrite("output_result.jpg", resultImg)
            break
            
        # Wait key to allow rendering and checking for user exit
        wait_time = int(1000 / fps) if args.video else 1
        key = cv2.waitKey(wait_time) & 0xFF
        if key in [27, ord('q'), ord('Q')]:
            break
            
    # Cleanup
    video.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    print("Done processing video.")
