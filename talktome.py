#/usr/bin/env python
import json
import os

import requests

from flask import Flask, request, make_response, Response
from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient

app = Flask(__name__)

slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_client = SlackClient(slack_bot_token)

slack_verification_token = os.environ["SLACK_VERIFICATION_TOKEN"]

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
        "token": form_json["token"], "channel": form_json["channel"]["id"]},
                      headers={'Content-Type': 'application/json'})
    print(r.text)
    return make_response("", 200)

# Create an event listener for "reaction_added" events and print the emoji name
@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    emoji = event_data["event"]["reaction"]
    print(emoji)


@slack_events_adapter.on("app_mention")
def app_mention(event_data):
    print(event_data)
    text = event_data["event"]["text"]
    channel = event_data["event"]["channel"]
    if "tell me a joke" in text:
        slack_client.api_call("chat.postMessage", channel=channel,
            text="He was so narrow-minded he could see through a keyhole with both eyes.")


@slack_events_adapter.on("message")
def app_home(event_data):
    print(event_data)
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

# Start the server on port 3000
if __name__ == "__main__":
    app.run(port=3000)
