import pandas as pd
import re

def clean_email(text):
    text = re.sub(r'\n>.*', '', text)  # Remove quoted replies
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    return ' '.join(text.split())      # Trim whitespace

raw_df = pd.read_csv('emails.csv', encoding='latin-1')

raw_df = raw_df.dropna(subset=['body'])
raw_df['clean_body'] = raw_df['body'].apply(clean_email)
clean_df = raw_df[['date', 'from', 'to', 'subject', 'clean_body']]

clean_df.to_csv('cleaned_enron_emails.csv', index=False)