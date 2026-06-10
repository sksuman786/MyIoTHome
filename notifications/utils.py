def send_device_status_notification(user, device, new_status):


    '''
    """Send a device status notification.

    This creates an in-app Notification record and attempts to send a
    Firebase Cloud Messaging (FCM) push to a topic for the user
    (topic name: `user_{user.id}`) using the HTTP v1 API.

    Requirements (optional):
    - Django settings `FIREBASE_SERVICE_ACCOUNT_FILE` (path to service account JSON)
    - Django settings `FIREBASE_PROJECT_ID` (Firebase project id)

    If those settings are not present or google-auth isn't installed,
    the function will still create an in-app Notification and return.
    """
    from django.conf import settings
    from django.utils.timezone import now
    from notifications.models import Notification

    # Create an in-app notification first
    title = f"{device.device_name} is {new_status.title()}"
    message = f"Device {device.device_name} ({device.device_id}) changed status to {new_status}."
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type='device_online' if new_status == 'online' else 'device_offline',
        device=device
    )

    # Try to send FCM push to topic user_{user.id}
    sa_file = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_FILE', None)
    project_id = getattr(settings, 'FIREBASE_PROJECT_ID', None)
    if not sa_file or not project_id:
        return

    try:
        # google-auth libraries
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as GoogleRequest
        import requests
    except Exception:
        return

    try:
        scopes = ['https://www.googleapis.com/auth/firebase.messaging']
        creds = service_account.Credentials.from_service_account_file(sa_file, scopes=scopes)
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

        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        # ignore response but could be logged if needed
    except Exception:
        return
    '''
    pass
