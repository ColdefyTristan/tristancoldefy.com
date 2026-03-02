from app.models.tables import UserEmailAddress


class EmailSender:

    def send_verification_email(user_email: UserEmailAddress, token=str):

        r = EmailSender.send()  # noqa: F841

        return {"ok": True}

    def send():

        return {"ok": True}
