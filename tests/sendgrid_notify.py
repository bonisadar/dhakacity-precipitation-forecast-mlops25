import logging
from datetime import datetime

from prefect.blocks.notifications import SendgridEmail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_sendgrid_notification():
    try:
        sendgrid_block = SendgridEmail.load("send-grid-notification-test")

        message = "Test Email from Prefect"
        subject = (
            "This is a test email from your Prefect SendGrid block.\n\n"
            f"Timestamp: {datetime.now()}\n"
            "If you're seeing this, your notification setup is working perfectly.\n\n"
            "Tip: Customize your messages, add emojis, or even switch to HTML later!"
        )

        sendgrid_block.notify(subject, message)
        logger.info("Test email sent successfully via SendGrid!")

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")


if __name__ == "__main__":
    test_sendgrid_notification()
