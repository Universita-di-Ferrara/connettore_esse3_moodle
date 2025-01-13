
from __future__ import print_function
from datetime import date, datetime

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import base64
from email.message import EmailMessage

from config import SAMPLE_SPREADSHEET_ID, SCOPES, ADMIN_EMAIL, USER_EMAIL

logger = logging.getLogger('log')


def invioEmail(errorbody, succesbody):
   
    creds = getCredentials()

    try:
        service = build('gmail', 'v1', credentials=creds, cache_discovery = False)
        message = EmailMessage()

        message['To'] = USER_EMAIL
       

        message['From'] = ADMIN_EMAIL
        #se ho errori allora mando una email di errore
        if (errorbody != []):
            message['Subject'] = 'Errore durante esecuzione connettore'
            messaggio = ""
            for line in errorbody:
                messaggio += line+"\n"
            message.set_content(messaggio)
        else:
        #altrimenti invio una email di successo
            message['Subject'] = 'Success!! Connettore ha creato gli esami'
            messaggio = ""
            for line in succesbody:
                messaggio += line+"\n"
            message.set_content(messaggio)

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        

        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message

def getListaAppelli():
    
    creds = getCredentials()

    try:
        service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
        # a seconda del token prendo fogli differenti
        
        SpreadSheet = "ListaAppelli"
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SpreadSheet).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return None
        else:

            return values
    except HttpError as err:
        print(err)
        return None
    
def getDatiEsse3():
    
    creds = getCredentials()

    try:
        service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
        # a seconda del token prendo fogli differenti
        
        SpreadSheet = "DatiEsse3"
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SpreadSheet).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return None
        else:

            return values
    except HttpError as err:
        print(err)
        return None

def getAppelliSpecialiFromSS():
    
    creds = getCredentials()

    try:
        service = build('sheets', 'v4', credentials=creds, cache_discovery = False)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range="AppelliSpeciali").execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return None
        else:

            return values
    except HttpError as err:
        print(err)
        return None
    
def lookup(row:list)->dict:
    columns = {}
    
    for index,el in enumerate(row):
        columns.update({el.lower():index})
    return columns
    
    
    
def insertValue(cellRange, values):
    creds = getCredentials()

    try:
        service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
        rangeName = f"{cellRange}"
        body = {"values":values}
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=rangeName,
            valueInputOption="RAW",
            body=body).execute()
        if not result:
            print('No data updated.')
            return None
        else:

            return result
    except HttpError as err:
        print(err)
        return None
    
def getValues(cellRange):
    creds = getCredentials()

    try:
        service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
        rangeName = f"ListaAppelli!{cellRange}"
       
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return None
        else:
            return values
    except HttpError as err:
        print(err)
        return None
    
def clearAppelli():
    listaAppelli = getListaAppelli()
    range = {}
    for index,row in enumerate(listaAppelli[1:],2):
        #3 index è la data appello
        if (date.today() > datetime.strptime(row[3], "%d/%m/%Y").date()):
            range = {
                "startRowIndex": 1,
                "endRowIndex": index,
                "startColumnIndex": 0,
                "endColumnIndex": 13
            }
        else :
            break
    if range:
        deleteRange(range)
            
def sortAppelli():
    creds = getCredentials()

    
    service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
    spreadsheet = service.spreadsheets().get(spreadsheetId=SAMPLE_SPREADSHEET_ID).execute()
    sheets = spreadsheet.get('sheets')
    sheetName = "ListaAppelli"
    for sheet in sheets:
        if sheet.get('properties').get('title') == sheetName:
            sheetId = sheet.get('properties').get('sheetId')
    
    sortRequest = {
        "sortRange":{
            "range":{
                "sheetId":sheetId,
                "startRowIndex":1
            },
            "sortSpecs":[
                {
                    "sortOrder":"ASCENDING",
                    "dimensionIndex": 3,
                }
            ]
        }
    }
    _batchRequest = {
        "requests":[
            sortRequest
        ]
    }
    service.spreadsheets().batchUpdate(spreadsheetId = SAMPLE_SPREADSHEET_ID , body = _batchRequest).execute()
    
def trovaInListaAppelli(_values, listaAppelli):
    for row in listaAppelli[1:]:
        if set(_values).issubset(set(row)):
            return True
    return False

def deleteRange(range):
    creds = getCredentials()

    
    service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
    spreadsheet = service.spreadsheets().get(spreadsheetId=SAMPLE_SPREADSHEET_ID).execute()
    sheets = spreadsheet.get('sheets')
    sheetName = "ListaAppelli"
    for sheet in sheets:
        if sheet.get('properties').get('title') == sheetName:
            sheetId = sheet.get('properties').get('sheetId')
    range['sheetId'] = sheetId
    deleteRangeRequest = { 
        "deleteRange":{
            "range":range,
            "shiftDimension":"ROWS"
        }
    }
    
    batchParams = {
        "requests": [
            deleteRangeRequest,
        ]
    }
    service.spreadsheets().batchUpdate(spreadsheetId = SAMPLE_SPREADSHEET_ID, body = batchParams).execute()
        
def resetValues(index):
    creds = getCredentials()

    try:
        service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
        rangeName = f"ListaAppelli!A{index}:I{index}"
        body = {"values":[["", "", "", "", "", "", "", ""]]}
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=rangeName,
            valueInputOption="RAW",
            body=body).execute()
        if not result:
            print('No data updated.')
            return None
        else:

            return result
    except HttpError as err:
        print(err)
        return None

def getSheetId(sheetName):
    creds = getCredentials()

    
    service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
    spreadsheet = service.spreadsheets().get(spreadsheetId=SAMPLE_SPREADSHEET_ID).execute()
    
    sheets = spreadsheet.get('sheets')
    
    for sheet in sheets:
        if sheet.get('properties').get('title') == sheetName:
            sheetId = sheet.get('properties').get('sheetId')
            return sheetId

def createBatchUpdates(_values, _batchRequest, sheetId):

    batchRequestRows = []
    for row in _values:
        valuesData = []
        for val in row:
            
            match val:
                case bool():
                    valuesData.append({
                        "userEnteredValue":{
                            "boolValue": val,
                        },
                        "dataValidation":{
                            "condition":{
                                "type":"BOOLEAN"
                            }
                        }
                    })
                case int():
                    valuesData.append({
                        "userEnteredValue":{
                            "numberValue": val,
                        }
                    })
                case str():
                    valuesData.append({
                        "userEnteredValue":{
                            "stringValue": val,
                        }
                    })
                case date():
                    temp = datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
                    delta = val - temp
                    sheetDate = float(delta.days) + (float(delta.seconds) / 86400)
                    valuesData.append({
                        "userEnteredValue":{
                            "numberValue": sheetDate,
                        },
                        "userEnteredFormat":{
                            "numberFormat": {
                                "type": "DATE",
                                "pattern":"dd/MM/yyyy"
                            }
                        }
                    })
        batchRequestRows.append({
            "values": valuesData
            })

        
    batchRequestAppendCells = {
                "appendCells": {
                    "sheetId": sheetId,
                    "rows": batchRequestRows,
                    "fields": "*"
                }   
            }
          

    _batchRequest['requests'].append(batchRequestAppendCells)
    
    #service.spreadsheets().batchUpdate(spreadsheetId = SAMPLE_SPREADSHEET_ID, body = batchRequest).execute()
    """    _values.append({
                "userEnteredValue":{
                    
                }
            })
        data = {"values":}
        
        batchRequest = {
            "requests":[
                {
                    "appendCells": {
                        "sheetId": sheetId,
                        "rows": 
                    }   
                },
            ] 
              
              }  
        
        
        result = sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=rangeName,
            valueInputOption="RAW",
            body=body).execute()
        if not result:
            print('No data updated.')
            return None
        else:

            return result
    except HttpError as err:
        print(err)
        return None
"""

def insertBatchUpdates(_batchRequest):
    try:
        creds = getCredentials()

        service = build('sheets', 'v4', credentials=creds, cache_discovery = False)
        service.spreadsheets().get(spreadsheetId=SAMPLE_SPREADSHEET_ID).execute()

        service.spreadsheets().batchUpdate(spreadsheetId = SAMPLE_SPREADSHEET_ID , body = _batchRequest).execute()
    except HttpError as httpError: 
        logger.error(f"Errore in insertBatchUpdates:{httpError}") 

    
def getCredentials():
    """Google Credentials.
    Retrieve Google Credentials.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(os.path.abspath('token/token.json')):
        creds = Credentials.from_authorized_user_file(os.path.abspath('token/token.json'), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.abspath('token/credentials.json'), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(os.path.abspath('token/token.json'), 'w') as token:
            token.write(creds.to_json())
    return creds