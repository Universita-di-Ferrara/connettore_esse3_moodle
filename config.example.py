
flag = "LOCALE"
#flag = "PREPRODUZIONE"
#flag = "PRODUZIONE"

GLOBAL_TOKEN = "token moodle" #token locale
BASIC_AUTH = "basic auth esse3"

GLOBAL_FORMAT = "&moodlewsrestformat=json"
GLOBAL_API = "your moodle/webservice/rest/server.php?"
LINK_CORSO_MOODLE = "your moodle/course/view.php?id="

ADMIN_EMAIL = "admin email"
USER_EMAIL = "user email who send email to"
GLOBAL_ESSE3 = "endpoint esse3/e3rest/api/"
ESSE3_TIMEOUT_SECONDS = (5, 30)  # (connessione, lettura)
ESSE3_RETRIES = 2
ESSE3_BACKOFF_FACTOR = 0.5
ESSE3_SLOW_REQUEST_SECONDS = 10
ESSE3_RETRY_STATUS_CODES = (429, 500, 502, 503, 504)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/gmail.send']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = 'id spreadsheet modello'
SAMPLE_RANGE_NAME = 'nome foglio'

if (flag=="PREPRODUZIONE"):

    GLOBAL_TOKEN = "" 
    GLOBAL_API = ""
    LINK_CORSO_MOODLE = ""
    
if (flag == "PRODUZIONE"):

    GLOBAL_TOKEN = ""
    LINK_CORSO_MOODLE = ""
    SAMPLE_RANGE_NAME = 'nome foglio'
