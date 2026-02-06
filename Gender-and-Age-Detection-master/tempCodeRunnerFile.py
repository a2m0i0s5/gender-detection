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