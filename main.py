import cv2
import pickle
import cvzone
import numpy as np
import serial
import time

# Video feed
cap = cv2.VideoCapture(1)

# Set camera capture width and height
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Load the position list
with open('carParkPos', 'rb') as f:
    posList = pickle.load(f)

# Define width and height for the rectangles
width, height = 250, 300

# Initialize serial communication with Arduino
arduino = serial.Serial(port='COM3', baudrate=9600, timeout=1)  # Change 'COM3' to your Arduino port
time.sleep(2)  # Give some time for the Arduino to initialize

# Function to check parking space
def checkParkingSpace(imgPro):
    
    spaceCounter = 0
    for pos in posList:
        x, y = pos

        imgCrop = imgPro[y:y+height, x:x+width]
        
        count = cv2.countNonZero(imgCrop)
        cvzone.putTextRect(img, str(count), (x, y+height - 3), scale=1, thickness=2, offset=0, colorR=(0, 0, 255))
        
        if count < 500:
            color = (0, 255, 0)
            thickness = 5
            spaceCounter += 1
        else:
            color = (0, 0, 255)
            thickness = 2
        
        cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20, colorR=(0, 200, 0))
    
    return spaceCounter

while True:
    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    success, img = cap.read()
    
    if not success:
        break

    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
    imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
    imgMedian = cv2.medianBlur(imgThreshold, 5)
    kernel = np.ones((3, 3), np.uint8)
    imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)

    # Pass the processed image to the function
    freeSpaces = checkParkingSpace(imgDilate)
        
    # Send the number of free spaces to Arduino
    arduino.write(f"{freeSpaces}\n".encode())
    
    # Display images
    cv2.imshow("Image", img)
    cv2.imshow("ImageBlur", imgBlur)
    cv2.imshow("ImageThres", imgThreshold)
    cv2.imshow("ImageMedi", imgMedian)
    
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
