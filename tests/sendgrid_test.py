# sendgrid_test.py

from prefect.blocks.notifications import SendgridEmail

# Load your existing block (name must match the one you created in Prefect UI)
block = SendgridEmail.load("sendgrid-dhaka-city-precipitation-forecast")

# Send a test notification
block.notify("✅ Test message from Prefect 🤖")
