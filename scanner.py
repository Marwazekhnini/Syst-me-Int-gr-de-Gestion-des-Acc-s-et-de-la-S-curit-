import cv2
import requests
import numpy as np
import paho.mqtt.client as mqtt
from pyzbar.pyzbar import decode
import face_recognition
import pytesseract  
import time
from twilio.rest import Client as TwilioClient # Import Twilio

# --- CONFIGURATION TWILIO ---
account_sid = 'urs'
auth_token  = 'urs'
twilio_number = 'twilios'
security_guard_number = 'urs'

twilio_client = TwilioClient(account_sid, auth_token)

# --- CONFIGURATION GENERALE ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
CAMERA_URL = "http://192.168.1.17:8080/shot.jpg" 
MQTT_BROKER = "127.0.0.1" 
MQTT_TOPIC_APPROVED = "security/camera/approved"
MQTT_TOPIC_ALERT = "security/camera/alert"

AUTHORIZED_QR_CODES = ["SM2611", "still"]
AUTHORIZED_CIN = ["FA207406", "B98765"]

# Paramètres Mouvement
MIN_MOTION_AREA = 8000
MOTION_COOLDOWN = 30 # Augmenté à 30s pour éviter de téléphoner trop souvent
last_alert_time = 0
previous_frame = None

# --- MQTT SETUP ---
client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)

# --- FACE RECOGNITION SETUP ---
print("Chargement des visages connus...")
image1 = face_recognition.load_image_file("face1.jpg")
encoding1 = face_recognition.face_encodings(image1)[0]
known_face_encodings = [encoding1]
known_face_names = ["Agent Administratif"]

print("Système SIGAS prêt (avec alertes Twilio)...")

while True:
    try:
        img_resp = requests.get(CAMERA_URL)
        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, -1)

        # ----------------------------------------
        # 1. DÉTECTION DE MOUVEMENT + APPEL TWILIO
        # ----------------------------------------
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if previous_frame is None:
            previous_frame = gray
            continue
            
        frame_delta = cv2.absdiff(previous_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if cv2.contourArea(contour) > MIN_MOTION_AREA:
                current_time = time.time()
                if current_time - last_alert_time > MOTION_COOLDOWN:
                    print("🚨 Alerte! mouvement suspet - Déclenchement de l'appel...")
                    
                    # 1. Envoi MQTT
                    client.publish(MQTT_TOPIC_ALERT, "Alerte! mouvement suspet")
                    
                    # 2. Déclenchement de l'appel Twilio
                    try:
                        call = twilio_client.calls.create(
                            twiml='<Response><Say language="fr-FR">Alerte! Un mouvement suspect a été détecté dans la zone administrative. Vérifiez la caméra immédiatement.</Say></Response>',
                            to=security_guard_number,
                            from_=twilio_number
                        )
                        print(f"Appel lancé avec succès (SID: {call.sid})")
                    except Exception as e_twilio:
                        print(f"Erreur Twilio: {e_twilio}")

                    last_alert_time = current_time
                    
        previous_frame = gray

        # ----------------------------------------
        # 2. SCAN CIN (OCR)
        # ----------------------------------------
        text_on_card = pytesseract.image_to_string(gray)
        for cin in AUTHORIZED_CIN:
            if cin in text_on_card:
                print(f"Accès par CIN : {cin}")
                cv2.imwrite("C:/Users/HP/Desktop/Pythonpartstage/snapshot.jpg", frame)
                client.publish(MQTT_TOPIC_APPROVED, f"Accès par CIN : {cin}")
                time.sleep(5)

        # ----------------------------------------
        # 3. SCAN QR CODES
        # ----------------------------------------
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8").strip()
            if qr_data in AUTHORIZED_QR_CODES:
                print(f"Accès par QR : {qr_data}")
                cv2.imwrite("C:/Users/HP/Desktop/Pythonpartstage/snapshot.jpg", frame)
                client.publish(MQTT_TOPIC_APPROVED, f"Accès par QR : {qr_data}")
                time.sleep(5)

        # ----------------------------------------
        # 4. RECONNAISSANCE FACIALE
        # ----------------------------------------
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            if True in matches:
                name = known_face_names[matches.index(True)]
                print(f"Accès par CIN (Visage reconnu : {name})")
                cv2.imwrite("C:/Users/HP/Desktop/Pythonpartstage/snapshot.jpg", frame)
                client.publish(MQTT_TOPIC_APPROVED, f"Accès par CIN (Visage : {name})")
                time.sleep(5)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
    time.sleep(0.1)