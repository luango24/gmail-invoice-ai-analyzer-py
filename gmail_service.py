import os
import base64
from config import CONFIG

# Gmail Imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Warning: Google API libraries not installed. Gmail download will fail if enabled.")
    print("Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

# --- GMAIL FUNCTIONS ---
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def download_gmail_attachments():
    print("Checking Gmail for new invoices...")
    creds = None
    token_path = 'token.json'
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret_file = CONFIG.get("SecretJsonFile")
            if not secret_file or not os.path.exists(secret_file):
                print(f"Error: SecretJsonFile not found at '{secret_file}'. Cannot authenticate.")
                return
            
            flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Query for PDF attachments
        default_query = 'has:attachment filename:pdf'
        query = CONFIG.get("QueryString", default_query)
        
        print(f"Using Gmail query: {query}")
        # Optional: Add sender filter if configured (Legacy, prefer QueryString)
        # if "GmailSender" in CONFIG: query += f' from:{CONFIG["GmailSender"]}'
        
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("No emails found with PDF attachments.")
            return

        print(f"Found {len(messages)} emails. Checking attachments...")
        
        pdf_dir = CONFIG["pdf_directory"]
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            # print(f"Inspecting message ID: {message['id']}") # Excessive output
            
            payload = msg.get('payload', {})
            parts = payload.get('parts', [])
            
            # DFS function to find parts
            def find_pdf_parts(parts_list):
                 pdf_parts = []
                 for p in parts_list:
                     if p.get('mimeType') == 'application/pdf' or (p.get('filename') and p['filename'].lower().endswith('.pdf')):
                         pdf_parts.append(p)
                     if 'parts' in p:
                         pdf_parts.extend(find_pdf_parts(p['parts']))
                 return pdf_parts

            target_parts = find_pdf_parts(parts)
            if not target_parts and 'filename' in payload and payload['filename'].lower().endswith('.pdf'):
                 # The message itself might be the attachment (unlikely for gmail but possible in structure)
                 target_parts.append(payload)

            if not target_parts:
                # print(f"No PDF parts found in message {message['id']}")
                pass

            for part in target_parts:
                if part['filename'] and part['filename'].lower().endswith('.pdf'):
                    if 'data' in part['body']:
                        data = part['body']['data']
                    else:
                        att_id = part['body']['attachmentId']
                        att = service.users().messages().attachments().get(userId='me', messageId=message['id'], id=att_id).execute()
                        data = att['data']
                    
                    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                    path = os.path.join(pdf_dir, part['filename'])
                    
                    # Avoid overwriting or re-downloading existing? 
                    # For now, simple check.
                    if not os.path.exists(path):
                        with open(path, 'wb') as f:
                            f.write(file_data)
                        print(f"Downloaded: {part['filename']}")
                    else:
                        print(f"Skipped (Exists): {part['filename']}")

    except Exception as e:
        print(f"An error occurred during Gmail download: {e}")
