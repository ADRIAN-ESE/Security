import cv2
import numpy as np

# Initialize camera
cap = cv2.VideoCapture(0)

previous_frame = None

while True:
    ret, current_frame = cap.read()
    gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    if previous_frame is None:
        previous_frame = gray
        continue
    frame_diff = cv2.absdiff(previous_frame, gray)
    previous_frame = gray
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if cv2.contourArea(contour) < 1000:
            continue
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(current_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.imshow('Security Camera', current_frame)
        # Send alert
        print("Motion detected!")
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break