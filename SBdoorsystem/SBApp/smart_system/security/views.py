import re
import json
from datetime import timedelta
import cv2
from django.http import StreamingHttpResponse
import requests
import numpy as np
from django.http import StreamingHttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count
from django.http import StreamingHttpResponse, Http404
from twilio.rest import Client

from .models import AccessLog

User = get_user_model()

# ──────────────────────────────────────────────
#  WEBCAM STREAM PROXY (FIXED IP TO MATCH RESEAU)
# ──────────────────────────────────────────────
WEBCAM_BASE_URL = "http://192.168.1.3:8080"  # Fixed IP to match your HTML text fallback
WEBCAM_STREAM_PATH = "/shot.jpg"      
# ──────────────────────────────────────────────


def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        role = request.POST.get('role')

        user = authenticate(request, username=u, password=p)

        if user is not None:
            login(request, user)

            if role == 'security' and user.role == 'security':
                return redirect('sm_dashboard')
            elif role == 'employee' and user.role == 'employee':
                return redirect('employee_dashboard')
            else:
                messages.error(request, "Role mismatch.")
                return redirect('login')
        else:
            messages.error(request, 'ACCESS DENIED: Invalid username or password.')

    return render(request, 'security/login.html')


def register_view(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        user_id  = request.POST.get('user_id')
        email    = request.POST.get('email')
        phone    = request.POST.get('phone')
        u        = request.POST.get('username')
        p        = request.POST.get('password')
        birthday = request.POST.get('birthday')
        role     = request.POST.get('role')
        post     = request.POST.get('post')

        if role == 'security' and not re.match(r'^SM\d{4}$', user_id):
            messages.error(request, 'Security ID must match format: SMxxxx')
            return redirect('register')

        elif role == 'employee' and not re.match(r'^EM\d{4}$', user_id):
            messages.error(request, 'Employee ID must match format: EMxxxx')
            return redirect('register')

        if User.objects.filter(username=u).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')

        if User.objects.filter(user_id=user_id).exists():
            messages.error(request, 'ID already exists.')
            return redirect('register')

        user = User.objects.create_user(username=u, email=email, password=p)
        user.fullname = fullname
        user.user_id  = user_id
        user.phone    = phone
        user.role     = role
        user.birthday = birthday
        user.post     = post

        if role == 'security':
            user.is_security = True
        else:
            user.is_employee = True

        user.save()
        messages.success(request, "Account created successfully.")
        return redirect('login')

    return render(request, 'security/register.html')


def employee_dashboard_view(request):
    active_guards = User.objects.filter(role='security', is_active_guard=True)
    return render(request, 'security/employee.html', {'active_guards': active_guards})


def sm_dashboard_view(request):
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)

    logs = AccessLog.objects.order_by('-timestamp')[:30]

    today_entries = AccessLog.objects.filter(timestamp__date=today, action='ENTRY').count()
    today_exits   = AccessLog.objects.filter(timestamp__date=today, action='EXIT').count()

    daily_data = []
    for i in range(7):
        day     = seven_days_ago + timedelta(days=i)
        entries = AccessLog.objects.filter(timestamp__date=day, action='ENTRY').count()
        exits   = AccessLog.objects.filter(timestamp__date=day, action='EXIT').count()
        total   = entries + exits
        if total == 0:
            status = "Aucune activité"
            color  = "#555"
        elif total < 10:
            status = "Faible"
            color  = "#e67e22"
        elif total < 30:
            status = "Normal"
            color  = "#27ae60"
        else:
            status = "Élevé"
            color  = "#e74c3c"

        daily_data.append({
            'date':    day.strftime('%d/%m'),
            'entries': entries,
            'exits':   exits,
            'total':   total,
            'status':  status,
            'color':   color,
        })

    return render(request, 'security/sm.html', {
        'logs':          logs,
        'today_entries': today_entries,
        'today_exits':   today_exits,
        'daily_data':    json.dumps(daily_data),
        'webcam_url':    WEBCAM_BASE_URL + WEBCAM_STREAM_PATH,
    })


@login_required
def log_access_view(request):
    if request.method == 'POST' and request.user.role == 'security':
        action = request.POST.get('action')
        if action in ('ENTRY', 'EXIT'):
            AccessLog.objects.create(
                user=request.user,
                method='IP Camera',
                action=action,
            )
    return redirect('sm_dashboard')


# ──────────────────────────────────────────────
#  FIXED WEBCAM MJPEG PROXY
# ──────────────────────────────────────────────
def webcam_feed(request):
    # Base URL using the correct port we found in your browser screenshot!
    stream_url = "http://192.168.1.3:8080/video"
    snapshot_url = "http://192.168.1.3:8080/shot.jpg"

    def generate():
        # Option A: Try reading it as an explicit MJPEG stream via OpenCV
        cap = cv2.VideoCapture(stream_url)
        
        if cap.isOpened():
            try:
                while True:
                    success, frame = cap.read()
                    if not success:
                        break
                    ret, buffer = cv2.imencode('.jpg', frame)
                    if not ret:
                        continue
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            finally:
                cap.release()
        
        # Option B Fallback: If OpenCV fails to stream, pull fast snapshot frames directly via HTTP
        else:
            try:
                while True:
                    # Request a single high-speed frame from the phone
                    img_resp = requests.get(snapshot_url, timeout=2)
                    img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
                    frame = cv2.imdecode(img_arr, -1)
                    
                    if frame is not None:
                        ret, buffer = cv2.imencode('.jpg', frame)
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            except Exception:
                return # Triggers front-end offline layout cleanly

    return StreamingHttpResponse(
        generate(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


def trigger_emergency_alert(request):
    if request.method == 'POST':
        account_sid = 'ur_sid'
        auth_token  = 'ur_token'
        client      = Client(account_sid, auth_token)

        emp_name = request.user.fullname
        emp_post = request.user.post if request.user.post else "un emplacement inconnu"

        twiml_instruction = f"""
        <Response>
            <Say language="fr-FR" voice="Polly.Celine">
                Alerte de sécurité critique. L'employé {emp_name} demande une assistance
                immédiate au poste {emp_post}.
                Je répète. Urgence signalée par {emp_name} à {emp_post}. Veuillez intervenir.
            </Say>
        </Response>
        """

        client.calls.create(
            twiml=twiml_instruction,
            to='ur_number',
            from_='twilio_number'
        )

    messages.success(request, "🚨 APPEL LANCÉ ! La cabine de sécurité est contactée via Twilio.")
    return redirect('employee_dashboard')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def toggle_duty(request):
    if request.method == 'POST' and request.user.role == 'security':
        request.user.is_active_guard = not request.user.is_active_guard
        request.user.save()
    return redirect('sm_dashboard')