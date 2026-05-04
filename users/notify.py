from .models import Notification


def notify(user, title, body="", type="general"):
    Notification.objects.create(user=user, title=title, body=body, type=type)


def notify_many(users, title, body="", type="general"):
    Notification.objects.bulk_create([
        Notification(user=u, title=title, body=body, type=type)
        for u in users
    ])
