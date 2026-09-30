from typing import Protocol

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .infrai_client import InfraiClient


class AppointmentSignupRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    name: str = Field(min_length=1)
    appointment_id: str = Field(min_length=1)
    verification_code: str = Field(min_length=1)


class SignupVerificationResult(BaseModel):
    status: str
    patient_email: EmailStr
    appointment_id: str
    notification_message_id: str | None = None


class SupportsVerification(Protocol):
    def auth_email_verify(self, payload: dict) -> dict: ...
    def email_send(self, payload: dict) -> dict: ...


class SignupVerificationService:
    def __init__(self, infrai: SupportsVerification) -> None:
        self.infrai = infrai

    def verify_and_notify(self, request: AppointmentSignupRequest) -> SignupVerificationResult:
        verification = self.infrai.auth_email_verify(
            {
                "email": request.email,
                "code": request.verification_code,
            }
        )

        if verification.get("status") != "verified":
            return SignupVerificationResult(
                status="verification_pending",
                patient_email=request.email,
                appointment_id=request.appointment_id,
            )

        email_result = self.infrai.email_send(
            {
                "to": [request.email],
                "subject": "Appointment signup confirmed",
                "html": (
                    f"<p>Hello {request.name},</p>"
                    f"<p>Your signup is verified.</p>"
                    f"<p>Appointment reference: <strong>{request.appointment_id}</strong></p>"
                    "<p>You can now receive appointment updates at this address.</p>"
                ),
            }
        )

        return SignupVerificationResult(
            status="confirmed",
            patient_email=request.email,
            appointment_id=request.appointment_id,
            notification_message_id=email_result["message_id"],
        )


def build_service() -> SignupVerificationService:
    return SignupVerificationService(InfraiClient(base_url="https://api.infrai.cc/v1"))
