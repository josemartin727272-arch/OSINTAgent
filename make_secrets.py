from dotenv import load_dotenv
import os
load_dotenv()
v = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON','')
output = f'''GOOGLE_SHEETS_CREDENTIALS_JSON = """{v}"""
SPREADSHEET_ID = "1LP4rVIihIe0tpusUU8uEW-pVb2wLqiF7lG84ihMkTck"
ALERT_EMAIL_FROM = "Josemartin7272272@gmail.com"
ALERT_EMAIL_TO = "Josemartin7272272@gmail.com"
ALERT_EMAIL_PASSWORD = "ckmb eksb uudu egav"'''
with open(os.path.expanduser('~/Desktop/secrets.txt'), 'w') as f:
    f.write(output)
print("Done! File saved to Desktop/secrets.txt")
