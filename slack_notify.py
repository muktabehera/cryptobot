import requests
import json


slack_headers = {
    "Content-Type": "application/json"
}

notifi_apca_paper_uri = 'https://hooks.slack.com/services/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'

data = {"text":"Hello, World!"}

notifi_response = requests.post(url=notifi_apca_paper_uri, headers=slack_headers,
                                data=str(data))

print(notifi_response.text)