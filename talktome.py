#/usr/bin/env python
import json
import os

import requests

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, make_response, Response
from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient
from zdesk import Zendesk

app = Flask(__name__)

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

# Helper for verifying that requests came from Slack
def verify_slack_token(request_token):
    if slack_verification_token != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
        return make_response("Request contains invalid Slack verification token", 403)

@app.route("/")
def hello():
    return "Go away!"

@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Verify that the request came from Slack
    verify_slack_token(form_json["token"])
    print(form_json["response_url"])
    r = requests.post(form_json["response_url"], json={'text': "Aaight",
        "token": form_json["token"], "channel": form_json["channel"]["id"],
        "replace_original": False}, headers={'Content-Type': 'application/json'})
    print(r.text)
    return make_response("", 200)

# Create an event listener for "reaction_added" events and print the emoji name
@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    emoji = event_data["event"]["reaction"]
    channel = event_data["event"]["item"]["channel"]
    slack_client.api_call("chat.postMessage", channel=channel, text="Cheers for {}".format(emoji))


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
                            "text": "Deny"
                        },
                        "value": "click_me_123"
                    }
                ]
            }
        ]
        slack_client.api_call("chat.postMessage", channel=channel, blocks=blocks)

# Scheduling
def update_zendesk():
    zenworker.update_tickets()

scheduler = BackgroundScheduler()
job = scheduler.add_job(update_zendesk, 'interval', minutes=1)
scheduler.start()

# Start the server on port 3000
if __name__ == "__main__":
    app.run(port=3000)
