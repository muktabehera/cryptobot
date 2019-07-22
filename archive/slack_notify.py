import requests
from archive import config

channel = "ERROR"

slack_headers = {
    "Content-Type": "application/json"
}

if config.slack_channel == 'LIVE':
    slack_url = "https://hooks.slack.com/services/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"  # ADD BEFORE RUNNLING LIVE!
else:  # config.slack_channel == 'PAPER':
    slack_url = "https://hooks.slack.com/services/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"

if channel == 'CHECK':
    slack_url = "https://hooks.slack.com/services/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"

if channel == 'ERROR':
    slack_url = "https://hooks.slack.com/services/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"

data = {"text":f"{slack_url}"}

notifi_response = requests.post(url=slack_url, headers=slack_headers,
                                data=str(data))

print(notifi_response.text)