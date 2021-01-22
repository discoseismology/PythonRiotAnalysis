import io
import cv2
from glob import glob
import json
import time
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

"""
Simple script to go through images directory and submit each photo to the Azure Face API which gives you the *estimated*
probability of several emotions being shown by the face. It then keeps track of the # of "likely" emotions (>50%) encountered.

It also currently calculates the average *estimated* age of the riot, as well as how many glasses it encounters and
how many people with facial hair it detects (gives probabilities, so take >50% again).
"""

if __name__ == "__main__":
    # Azure Set-up
    key = 'YourAzureKeyHere'
    endpoint = 'YourAzureEndpointHere'
    region = 'YourAzureRegionHere'
    face_client = FaceClient(endpoint, CognitiveServicesCredentials(key))

    # Get image file paths
    images = glob('./images/*')
    images.sort()

    # Create dict that will map # of emotions detected (and supported) by Azure
    emotions = {'anger': 0, 'contempt': 0, 'disgust': 0, 'fear': 0, 'happiness': 0, 'neutral': 0, 'sadness': 0, 'surprise': 0}
    glassesCount = 0
    facialHairCount = 0
    totalAge = 0

    # For average age
    counter = 0

    # Dict holding data points that will save on completion
    results = {}

    for imgName in images:
        print(imgName)

        # Load image from actual file path
        img = cv2.imread(imgName)

        # Get image ready for transmission to Azure
        ret, buf = cv2.imencode('.jpg', img)
        stream = io.BytesIO(buf)

        # Try and get face data from Azure
        try:
            detected_face = face_client.face.detect_with_stream(
                stream,
                return_face_id=False,
                return_face_attributes=['age', 'gender', 'emotion', 'facialHair', 'glasses'])

        # Should (Hopefully) only get this on Rate Limit blocking by Azure...
        except Exception as e:
            print("ERROR")
            print(e)
            print(imgName)
            time.sleep(60)
            continue

        # If it can't detect a face (some of the images aren't great), it returns None
        if not detected_face:
            continue

        counter += 1

        # Extract data returned from Azure
        faceAttr = detected_face[0].face_attributes.as_dict()
        faceEmotion = faceAttr['emotion']
        faceAge = faceAttr['age']
        faceGender = faceAttr['gender']
        facialHair = faceAttr['facial_hair']
        faceGlasses = faceAttr['glasses']

        if faceGlasses != 'noGlasses':
            glassesCount += 1

        # Given as "hair": {"moustache": 0.05, "beard": 0.40, "sideburns": 0.25}"
        # There's for sure way better ways to do this but...
        if sum(facialHair.values()) > 0.5:
            facialHairCount += 1

        if faceAge is not None:
            totalAge += faceAge

        # Get highest probability
        maxP = 0
        maxK = None
        for k, p in faceEmotion.items():
            if p > maxP:
                maxK = k
                maxP = p

        # Record results
        if maxP > 0.5:
            emotions[maxK] += 1
            results[imgName] = {'emotion': faceEmotion, 'age': faceAge, 'gender': faceGender, 'hair': facialHair, 'glasses': faceGlasses}

        print(f'Emotions: {emotions}\tAvg Age: {totalAge / counter}\tGlasses Seen: {glassesCount}\tFH: {facialHairCount}')
        print()

        # Stick to 20 calls/min max for free tier
        #time.sleep(4)

        # Paid allows 10 TPS
        time.sleep(0.15)

    # Write all data to .json
    with open('./results.json', 'w') as file:
        file.write(json.dumps(results, indent=4))