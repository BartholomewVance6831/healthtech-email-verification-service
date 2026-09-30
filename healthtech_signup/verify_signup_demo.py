import argparse
import json

from .signup_notifications import AppointmentSignupRequest, build_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a patient signup email and send an appointment-ready notification.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--appointment-id", required=True)
    parser.add_argument("--verification-code", required=True)
    args = parser.parse_args()

    service = build_service()
    result = service.verify_and_notify(
        AppointmentSignupRequest(
            email=args.email,
            name=args.name,
            appointment_id=args.appointment_id,
            verification_code=args.verification_code,
        )
    )
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
