import imaplib
import email
from email.header import decode_header

def sort_emails(email_user, email_pass, imap_server, search_query, target_folder):
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Search for emails
        # Ensure search_query is properly formatted for IMAP
        # Example: '(SUBJECT "Invoice")'
        status, messages = mail.search(None, search_query)
        
        moved_count = 0
        if status == 'OK':
            # Loop through found emails and move them
            email_ids = messages[0].split()
            for num in email_ids:
                # Copy to target folder
                result = mail.copy(num, target_folder)
                if result[0] == 'OK':
                    # Mark as deleted in Inbox if copy was successful
                    mail.store(num, '+FLAGS', '\\Deleted')
                    moved_count += 1
        
        # Permanently remove deleted emails from Inbox
        mail.expunge()
        mail.logout()
        return f"Successfully moved {moved_count} emails to '{target_folder}' matching '{search_query}'."
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Example usage:
    # print(sort_emails("user@gmail.com", "pass", "imap.gmail.com", '(SUBJECT "Invoice")', "Invoices"))
    pass
