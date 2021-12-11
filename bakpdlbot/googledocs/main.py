from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Location of token file
tokenfile=os.path.join(os.path.dirname(__file__),'token.json')

def MakeSheetConnection():
    """
        Connect with google api
    :return: service - google service
    """
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(tokenfile):
        creds = Credentials.from_authorized_user_file(tokenfile, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(os.path.dirname(__file__),'credentials.json'), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenfile, 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
    return service


def GoogleSheetValues(spreadsheetid=None,range=None):
    """
        Returns values of spreadsheetid in range
    """

    service = MakeSheetConnection()
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheetid,range=range).execute()
    values = result.get('values', [])
    return values


