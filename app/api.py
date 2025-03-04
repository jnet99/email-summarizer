from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from bson import ObjectId
from .summarization import extract_summary
from fastapi import HTTPException
import logging

app = FastAPI()

client = MongoClient("mongodb://localhost:27017/")
db = client["enron"]

templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize/")
async def summarize_email(request: Request, email_id: str = Form(...)):
    """Summarize an email by its MongoDB ID from the UI."""
    try:
        logger.info(f"Received email_id: {email_id}")

        email_id = ObjectId(email_id)

        email = db.enronmails.find_one({"_id": email_id})
        if not email:
            logger.error(f"Email not found for ID: {email_id}")
            return templates.TemplateResponse("index.html", {
                "request": request, "error": "Email not found"
            })

        summary = extract_summary(email["body"])

        return templates.TemplateResponse("index.html", {
            "request": request, "summary": summary
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return templates.TemplateResponse("index.html", {
            "request": request, "error": str(e)
        })



@app.post("/summarize_text/")
async def summarize_user_email(request: Request, email_text: str = Form(...)):
    """Summarize user-provided email text."""
    try:
        if not email_text.strip():
            raise HTTPException(status_code=400, detail="Email text cannot be empty")
        if len(email_text) > 10000:  # Example limit
            raise HTTPException(status_code=400, detail="Email text is too long")

        summary = extract_summary(email_text)

        return templates.TemplateResponse("index.html", {
            "request": request, "summary": summary
        })
    except HTTPException as e:
        return templates.TemplateResponse("index.html", {
            "request": request, "error": e.detail
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return templates.TemplateResponse("index.html", {
            "request": request, "error": str(e)
        })
