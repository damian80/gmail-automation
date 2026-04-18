from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import anthropic
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def classify_email(client, sender, subject):
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"Is this email an IT support request? Answer only YES or NO, then one short reason.\n\nFrom: {sender}\nSubject: {subject}"
        }]
    )
    return message.content[0].text

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['UNREAD'], maxResults=10).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No unread messages.')
        return

    claude = anthropic.Anthropic()

    for msg in messages:
        message = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        classification = classify_email(claude, sender, subject)
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"IT Support?: {classification}")
        print("---")

if __name__ == '__main__':
    main()
