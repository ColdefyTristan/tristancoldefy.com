from app.models import UserEmailAddress


class EmailSender:

    def send_verification_email(user_email: UserEmailAddress, token=str):

        r = EmailSender.send()

        return {"ok": True}

    def send():

        return {"ok": True}
