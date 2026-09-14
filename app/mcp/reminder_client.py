import os
import smtplib
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage

from icalendar import Calendar, Event


def _create_ics(summary: str, description: str, days_from_now: int,
                 duration_minutes: int, output_path: str) -> str:
    cal = Calendar()
    cal.add("prodid", "-//Personal Insight Agent//mxm.dk//")
    cal.add("version", "2.0")

    event = Event()
    event.add("summary", summary)
    event.add("description", description)
    start = datetime.utcnow() + timedelta(days=days_from_now)
    event.add("dtstart", start)
    event.add("dtend", start + timedelta(minutes=duration_minutes))
    event.add("dtstamp", datetime.utcnow())
    event["uid"] = str(uuid.uuid4())

    cal.add_component(event)

    with open(output_path, "wb") as f:
        f.write(cal.to_ical())

    return output_path


def _send_email_with_ics(subject: str, body: str, ics_path: str) -> None:
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("REMINDER_RECIPIENT", gmail_address)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = recipient
    msg.set_content(body)

    with open(ics_path, "rb") as f:
        msg.add_attachment(
            f.read(), maintype="text", subtype="calendar", filename="reminder.ics"
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(msg)


def schedule_reminder(summary: str, description: str, days_from_now: int = 3,
                       duration_minutes: int = 30) -> dict:
    ics_path = _create_ics(
        summary=summary,
        description=description,
        days_from_now=days_from_now,
        duration_minutes=duration_minutes,
        output_path=f"/tmp/{uuid.uuid4().hex}.ics" if os.name != "nt" else f"{uuid.uuid4().hex}.ics",
    )

    _send_email_with_ics(
        subject=f"Reminder: {summary}",
        body=description,
        ics_path=ics_path,
    )

    scheduled_for = (datetime.utcnow() + timedelta(days=days_from_now)).isoformat()

    return {
        "status": "reminder sent",
        "scheduled_for": scheduled_for,
        "note": "Calendar invite emailed. Open the attachment to add it to your calendar.",
    }