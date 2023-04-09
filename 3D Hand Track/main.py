import cv2
from cvzone.HandTrackingModule import HandDetector
import socket
import math
import numpy as np

def calculateDistance(hand):

    if hand["bbox"] == -1:
        return [-1, -1]

    lmList = hand['lmList']
    x, y, w, h = hand['bbox']
    x1, y1 = lmList[5][:2]
    x2, y2 = lmList[17][:2]

    distance = int(math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2))
    A, B, C = coff
    distanceCM = int(A * distance ** 2 + B * distance + C)

    distanceArr = [distance, distanceCM]
    return distanceArr

# Parameters
width, height = 1280, 720

# Webcam
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# Hand Detector
detector = HandDetector(maxHands=2, detectionCon=0.8)

# Find function
# x is the raw distance, y is the value in cm
x = [300, 245, 200, 170, 145, 130, 112, 103, 93, 87, 80, 75, 70, 67, 62, 59, 57]
y = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
coff = np.polyfit(x, y, 2)  # y = Ax^2 + Bx + C

# Communication
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverAddressPort = ("127.0.0.1", 8888)

formatter = "{0:.2f}"

while True:

    # Get frame from webcam
    success, img = cap.read()
    # Hands
    hands, img = detector.findHands(img)

    # Flip image (frame)
    img = cv2.flip(img, 1)

    if hands:

        # If there is two hands in cam
        if len(hands) == 2:
            leftHand = hands[0] if hands[0]["type"] == "Left" else hands[1]
            rightHand = hands[0] if hands[0]["type"] == "Right" else hands[1]
        else:
            leftHand = hands[0] if hands[0]["type"] == "Left" else {
                "lmList": [], "bbox": -1}
            rightHand = hands[0] if hands[0]["type"] == "Right" else {
                "lmList": [], "bbox": -1}

        leftLmList = leftHand["lmList"]
        rightLmList = rightHand["lmList"]
        leftData, rightData = [], []

        # Calculate distances
        rightHandDistance = calculateDistance(rightHand)
        leftHandDistance = calculateDistance(leftHand)



        # Add datas to lists
        for lm in rightLmList:
            rightData.extend(
                [lm[0], height - lm[1], lm[2], rightHandDistance[0]])
        for lm in leftLmList:
            leftData.extend(
                [lm[0], height - lm[1], lm[2], leftHandDistance[0]])

        # RIGHT POSES + ? + LEFT POSES + ? + RIGHT DIST + ? + LEFT DIST
        socketStr = str(rightData) + "?" + str(leftData) + "?" + str(rightHandDistance[1]) + "?" + str(leftHandDistance[1])

        # Socket communication
        sock.sendto(str.encode(str(socketStr)), serverAddressPort)
        # print(socketStr)
    else:
        sock.sendto(str.encode(str("")), serverAddressPort)

    # Flip image (frame)
    img = cv2.flip(img, 1)

    img = cv2.resize(img, (0, 0), None, 0.5, 0.5)
    cv2.imshow("Image", img)
    cv2.waitKey(1)
