import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Connect to Google Sheets
def get_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Load credentials
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    
    # Open your sheet by name 
    workbook = client.open("Student Information")
    sheet = workbook.sheet1  
    return sheet
