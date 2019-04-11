#/usr/bin/env python
import json
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, make_response, Response
from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient
from zdesk import Zendesk

from lib import zendesk, messaging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_client = SlackClient(slack_bot_token)

slack_verification_token = os.environ["SLACK_VERIFICATION_TOKEN"]

class ZenWorker(object):
    def __init__(self):
        self.zendesk = Zendesk(os.environ["ZENDESK_URL"], zdesk_email=os.environ["ZENDESK_EMAIL"],
                               zdesk_api=os.environ["ZENDESK_API"])
        self.tickets = {}

    def update_tickets(self):
        self.tickets = self.zendesk.tickets_list()


zenworker = ZenWorker()
zenworker2 = zendesk.ZenWorker(os.environ["ZENDESK_URL"], os.environ["ZENDESK_EMAIL"],
                               os.environ["ZENDESK_API"])

slack_worker = messaging.SlackWorker(slack_bot_token, slack_verification_token,
                                     os.environ['DOMAIN'])

# keep
# Helper for verifying that requests came from Slack
def verify_slack_token(request_token):
    if slack_verification_token != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
        return make_response("Request contains invalid Slack verification token", 403)

# keep
@app.route("/")
def hello():
    return "Go away!"

# keep
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])
    # Verify that the request came from Slack
    verify_slack_token(form_json["token"])
    # Get the response message
    slack_worker.generate_response(form_json)
    return make_response("", 200)

# Create an event listener for "reaction_added" events and print the emoji name
@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    emoji = event_data["event"]["reaction"]
    channel = event_data["event"]["item"]["channel"]
    slack_client.api_call("chat.postMessage", channel=channel, text="Cheers for {}".format(emoji))

blocks = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "You have a new request:\n*<fakeLink.toEmployeeProfile.com|Fred Enriquez - New device request>*"
        }
    },
    {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": "*Type:*\nComputer (laptop)"
            }
        ]
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "Approve"
                },
                "value": "click_me_124"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "Deny!!!"
                },
                "value": "click_me_123"
            }
        ]
    },
    {
        "type": "context",
        "elements": [{"type": "plain_text", "text": "some context"}],
        "block_id": "ticket_id",
    }
]

@slack_events_adapter.on("app_mention")
def app_mention(event_data):
    verify_slack_token(event_data["token"])
    text = event_data["event"]["text"]
    channel = event_data["event"]["channel"]
    if "tell me a joke" in text:
        slack_client.api_call("chat.postMessage", channel=channel,
            text="He was so narrow-minded he could see through a keyhole with both eyes.")
    if "zendesk" in text:
        slack_client.api_call("chat.postMessage", channel=channel,
            text=("Last I checked, there were {} tickets in the"
                  " queue.".format(zenworker.tickets.get("count", 0))))
    if "secret" in text:
        slack_client.api_call("chat.postMessage", channel=channel, blocks=blocks)



@slack_events_adapter.on("message")
def app_home(event_data):
    print(event_data)
    verify_slack_token(event_data["token"])
    if not "text" in event_data["event"]:
        print("couldn't find text")
        return
    text = event_data["event"]["text"]
    channel = event_data["event"]["channel"]
    if text == "secret":
        slack_client.api_call("chat.postMessage", channel=channel, blocks=blocks)

# Scheduling
def update_zendesk():
    zenworker.update_tickets()

def update_zendesk_new():
    tickets = zenworker2.run()
    print(tickets)
    slack_worker.process_tickets(tickets)

scheduler = BackgroundScheduler()
#scheduler.add_job(update_zendesk, 'interval', minutes=1)
#scheduler.add_job(update_zendesk_new, 'interval', minutes=1)
scheduler.start()

# Start the server on port 3000
if __name__ == "__main__":
    app.run(port=3000)
