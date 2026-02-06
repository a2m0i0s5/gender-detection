
import cv2
import argparse
import os

def highlightFace(net, frame, conf_threshold=0.7):
    try:
        frameOpencvDnn=frame.copy()
        frameHeight=frameOpencvDnn.shape[0]
        frameWidth=frameOpencvDnn.shape[1]
        blob=cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)

        net.setInput(blob)
        detections=net.forward()
        faceBoxes=[]
        for i in range(detections.shape[2]):
            confidence=detections[0,0,i,2]
            if confidence>conf_threshold:
                x1=int(detections[0,0,i,3]*frameWidth)
                y1=int(detections[0,0,i,4]*frameHeight)
                x2=int(detections[0,0,i,5]*frameWidth)
                y2=int(detections[0,0,i,6]*frameHeight)
                faceBoxes.append([x1,y1,x2,y2])
                cv2.rectangle(frameOpencvDnn, (x1,y1), (x2,y2), (0,255,0), int(round(frameHeight/150)), 8)
        return frameOpencvDnn,faceBoxes
    except Exception as e:
        print(f"Error in highlightFace: {e}")
        return frame, []

parser=argparse.ArgumentParser()
parser.add_argument('--image')

args=parser.parse_args()

script_dir = os.path.dirname(os.path.abspath(__file__))
faceProto=os.path.join(script_dir, "opencv_face_detector.pbtxt")
faceModel=os.path.join(script_dir, "opencv_face_detector_uint8.pb")
ageProto=os.path.join(script_dir, "age_deploy.prototxt")
ageModel=os.path.join(script_dir, "age_net.caffemodel")
genderProto=os.path.join(script_dir, "gender_deploy.prototxt")
genderModel=os.path.join(script_dir, "gender_net.caffemodel")

MODEL_MEAN_VALUES=(78.4263377603, 87.7689143744, 114.895847746)
ageList=['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
genderList=['Male','Female']

try:
    faceNet=cv2.dnn.readNet(faceModel,faceProto)
    print("Face model loaded successfully")
except Exception as e:
    print(f"Error loading face model: {e}")
    exit(1)

try:
    ageNet=cv2.dnn.readNet(ageModel,ageProto)
    print("Age model loaded successfully")
except Exception as e:
    print(f"Error loading age model: {e}")
    exit(1)

try:
    genderNet=cv2.dnn.readNet(genderModel,genderProto)
    print("Gender model loaded successfully")
except Exception as e:
    print(f"Error loading gender model: {e}")
    exit(1)

padding=20

if args.image:
    image_path = os.path.join(script_dir, args.image)
    frame = cv2.imread(image_path)
    if frame is None:
        print("Error: Could not load image")
        exit(1)
    print("Processing image")
    resultImg, faceBoxes = highlightFace(faceNet, frame)
    if not faceBoxes:
        print("No face detected")
        cv2.putText(resultImg, "No face detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2, cv2.LINE_AA)
    else:
        print(f"Detected {len(faceBoxes)} face(s)")
        for faceBox in faceBoxes:
            face = frame[max(0, faceBox[1]-padding):min(faceBox[3]+padding, frame.shape[0]-1), max(0, faceBox[0]-padding):min(faceBox[2]+padding, frame.shape[1]-1)]
            blob = cv2.dnn.blobFromImage(face, 1.0, (227,227), MODEL_MEAN_VALUES, swapRB=False)
            try:
                genderNet.setInput(blob)
                genderPreds = genderNet.forward()
                gender = genderList[genderPreds[0].argmax()]
                print(f'Gender: {gender}')
            except Exception as e:
                print(f"Error in gender prediction: {e}")
                gender = "Unknown"
            try:
                ageNet.setInput(blob)
                agePreds = ageNet.forward()
                age = ageList[agePreds[0].argmax()]
                print(f'Age: {age[1:-1]} years')
            except Exception as e:
                print(f"Error in age prediction: {e}")
                age = "(Unknown)"
            cv2.putText(resultImg, f'{gender}, {age}', (faceBox[0], faceBox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2, cv2.LINE_AA)
    cv2.imshow("Detecting age and gender", resultImg)
    cv2.waitKey(0)
else:
    video = cv2.VideoCapture(0)
    if not video.isOpened():
        print("Error: Could not open video capture")
        exit(1)
    padding = 20
    while cv2.waitKey(1) < 0:
        hasFrame, frame = video.read()
        if not hasFrame:
            print("No frame read, breaking")
            cv2.waitKey()
            break
        print("Processing frame")
        resultImg, faceBoxes = highlightFace(faceNet, frame)
        if not faceBoxes:
            print("No face detected")
            cv2.putText(resultImg, "No face detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2, cv2.LINE_AA)
        else:
            print(f"Detected {len(faceBoxes)} face(s)")
            for faceBox in faceBoxes:
                face = frame[max(0, faceBox[1]-padding):min(faceBox[3]+padding, frame.shape[0]-1), max(0, faceBox[0]-padding):min(faceBox[2]+padding, frame.shape[1]-1)]
                blob = cv2.dnn.blobFromImage(face, 1.0, (227,227), MODEL_MEAN_VALUES, swapRB=False)
                try:
                    genderNet.setInput(blob)
                    genderPreds = genderNet.forward()
                    gender = genderList[genderPreds[0].argmax()]
                    print(f'Gender: {gender}')
                except Exception as e:
                    print(f"Error in gender prediction: {e}")
                    gender = "Unknown"
                try:
                    ageNet.setInput(blob)
                    agePreds = ageNet.forward()
                    age = ageList[agePreds[0].argmax()]
                    print(f'Age: {age[1:-1]} years')
                except Exception as e:
                    print(f"Error in age prediction: {e}")
                    age = "(Unknown)"
                cv2.putText(resultImg, f'{gender}, {age}', (faceBox[0], faceBox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2, cv2.LINE_AA)
        cv2.imshow("Detecting age and gender", resultImg)
