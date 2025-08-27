import cv2
import datetime
import os

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

previous_frame = None
recording = False
out = None

# Create folders for logs
if not os.path.exists("recordings"):
    os.makedirs("recordings")
if not os.path.exists("snapshots"):
    os.makedirs("snapshots")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if previous_frame is None:
        previous_frame = gray
        continue

    frame_diff = cv2.absdiff(previous_frame, gray)
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    motion_detected = False

    for contour in contours:
        if cv2.contourArea(contour) < 1000:
            continue
        motion_detected = True
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Overlay text
    status_text = "Recording..." if recording else "No Motion"
    cv2.putText(frame, status_text, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if recording else (0, 255, 0), 2)
    cv2.putText(frame, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow("Security Camera", frame)

    # Start recording + snapshot
    if motion_detected and not recording:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_filename = f"recordings/{timestamp}.avi"
        snapshot_filename = f"snapshots/{timestamp}.jpg"

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(video_filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]))
        recording = True

        cv2.imwrite(snapshot_filename, frame)
        print(f"🎥 Recording started: {video_filename}")
        print(f"📸 Snapshot saved: {snapshot_filename}")

    # Stop recording when motion ends
    elif not motion_detected and recording:
        recording = False
        out.release()
        out = None
        print("🛑 Recording stopped")

    # Write frames if recording
    if recording and out is not None:
        out.write(frame)

    previous_frame = gray

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if out is not None:
    out.release()
cv2.destroyAllWindows()
