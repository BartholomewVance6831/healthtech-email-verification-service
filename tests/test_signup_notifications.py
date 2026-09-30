from healthtech_signup.signup_notifications import AppointmentSignupRequest, SignupVerificationService


class FakeInfraiClient:
    def __init__(self) -> None:
        self.sent_payloads = []

    def auth_email_verify(self, payload: dict) -> dict:
        return {"status": "verified", "email": payload["email"]}

    def email_send(self, payload: dict) -> dict:
        self.sent_payloads.append(payload)
        return {"message_id": "msg_123"}


class FakePendingInfraiClient:
    def __init__(self) -> None:
        self.sent_payloads = []

    def auth_email_verify(self, payload: dict) -> dict:
        return {"status": "pending", "email": payload["email"]}

    def email_send(self, payload: dict) -> dict:
        self.sent_payloads.append(payload)
        return {"message_id": "msg_should_not_send"}


def test_verified_signup_sends_patient_notification() -> None:
    client = FakeInfraiClient()
    service = SignupVerificationService(client)

    result = service.verify_and_notify(
        AppointmentSignupRequest(
            email="patient@example.com",
            name="Alex Doe",
            appointment_id="apt-100",
            verification_code="123456",
        )
    )

    assert result.status == "confirmed"
    assert result.notification_message_id == "msg_123"
    assert len(client.sent_payloads) == 1
    assert client.sent_payloads[0]["subject"] == "Appointment signup confirmed"
    assert client.sent_payloads[0]["to"] == ["patient@example.com"]


def test_unverified_signup_does_not_send_notification() -> None:
    client = FakePendingInfraiClient()
    service = SignupVerificationService(client)

    result = service.verify_and_notify(
        AppointmentSignupRequest(
            email="patient@example.com",
            name="Alex Doe",
            appointment_id="apt-100",
            verification_code="000000",
        )
    )

    assert result.status == "verification_pending"
    assert result.notification_message_id is None
    assert client.sent_payloads == []
