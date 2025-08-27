import cv2
import datetime
import os
import smtplib, ssl
from email.message import EmailMessage

# ============ EMAIL CONFIG ============
EMAIL_SENDER = "obsidiannix572@gmail.com"
EMAIL_PASSWORD = "cdnm lyeu dmyu ffys"   # use Gmail app password, not your real password
EMAIL_RECEIVER = "primo.1000max@gmail.com"


def send_email_alert(snapshot_path, timestamp):
    """Send an email with a snapshot when motion is detected."""
    msg = EmailMessage()
    msg["Subject"] = f"🚨 Motion Detected! ({timestamp})"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content(f"Motion detected at {timestamp}. See attached snapshot.")

    # attach snapshot file
    with open(snapshot_path, "rb") as f:
        msg.add_attachment(f.read(),
                           maintype="image",
                           subtype="jpeg",
                           filename=os.path.basename(snapshot_path))

    # send via Gmail SMTP
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

    print(f"📧 Email alert sent with snapshot {snapshot_path}")


# ============ MOTION DETECTION ============
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

previous_frame = None
recording = False
video_writer = None
output_dir = "recordings"
os.makedirs(output_dir, exist_ok=True)

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Camera not available")
        break

    # convert frame → grayscale & blur to reduce noise
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if previous_frame is None:
        previous_frame = gray
        continue

    # frame difference → threshold
    frame_diff = cv2.absdiff(previous_frame, gray)
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    # find contours (motion areas)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    motion_detected = False

    for contour in contours:
        if cv2.contourArea(contour) < 1000:
            continue
        motion_detected = True
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # status text + timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    cv2.putText(frame, "Motion Detected" if motion_detected else "No Motion",
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255) if motion_detected else (0, 255, 0), 2)
    cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    # ================== ALERT & RECORDING ==================
    if motion_detected:
        if not recording:
            # start new recording file
            video_filename = os.path.join(output_dir, f"motion_{timestamp}.avi")
            video_writer = cv2.VideoWriter(video_filename,
                                           cv2.VideoWriter_fourcc(*"XVID"),
                                           20, (frame.shape[1], frame.shape[0]))
            recording = True

            # save snapshot
            snapshot_filename = os.path.join(output_dir, f"snapshot_{timestamp}.jpg")
            cv2.imwrite(snapshot_filename, frame)

            # send email with snapshot
            try:
                send_email_alert(snapshot_filename, timestamp)
            except Exception as e:
                print("❌ Failed to send email:", e)

        video_writer.write(frame)  # keep recording

    else:
        if recording:
            # stop recording when motion ends
            video_writer.release()
            recording = False

    # ================== SHOW WINDOWS ==================
    cv2.imshow("Security Camera", frame)
    cv2.imshow("Threshold", thresh)

    previous_frame = gray

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# cleanup
if recording:
    video_writer.release()
cap.release()
cv2.destroyAllWindows()
