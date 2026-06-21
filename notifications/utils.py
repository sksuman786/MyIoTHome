from django.conf import settings
from django.utils.timezone import now


def send_device_status_notification(user, device, new_status):
    """Create an in-app Notification and send an FCM push via HTTP v1 API.

    Sends to topic `user_{user.id}` so client apps can subscribe per-user.
    This function is best-effort: if Firebase libs or network fail, it
    still creates the in-app Notification record and returns quietly.
    """
    try:
        from notifications.models import Notification
    except Exception:
        Notification = None

    # Create an in-app notification first (if model available)
    title = f"{device.device_name} is {new_status.title()}"
    message = f"Device {device.device_name} ({device.device_id}) changed status to {new_status}."
    try:
        if Notification is not None:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type='device_online' if new_status == 'online' else 'device_offline',
                device=device
            )
    except Exception:
        # don't block sending push if DB write fails
        pass

    # Try to send FCM push to topic user_{user.id}
    sa_file = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_FILE', None)
    project_id = getattr(settings, 'FIREBASE_PROJECT_ID', None)
    if not sa_file or not project_id:
        return

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as GoogleRequest
        import requests
    except Exception:
        # Missing google-auth or requests
        return

    try:
        scopes = ['https://www.googleapis.com/auth/firebase.messaging']
        creds = service_account.Credentials.from_service_account_file(str(sa_file), scopes=scopes)
        creds.refresh(GoogleRequest())
        access_token = creds.token

        url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        topic = f"user_{user.id}"

        payload = {
            'message': {
                'topic': topic,
                'notification': {
                    'title': title,
                    'body': message,
                },
                'data': {
                    'device_id': device.device_id,
                    'device_name': device.device_name,
                    'status': new_status,
                    'timestamp': now().isoformat(),
                }
            }
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; UTF-8'
        }

        #requests.post(url, json=payload, headers=headers, timeout=10)
        resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
       )
        print("FCM STATUS:", resp.status_code)
        print("FCM RESPONSE:", resp.text)
    except Exception:
        # Best-effort: ignore failures silently
        return
