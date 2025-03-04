import requests

email_id = "67aa610fbe8052c3ef7179db"  # MongoDB ObjectId
url = f"http://127.0.0.1:8000/summarize/{email_id}"

response = requests.post(url)

if response.status_code == 200:
    print("Response JSON:", response.json()) 
else:
    print(f"Error {response.status_code}: {response.text}") 
