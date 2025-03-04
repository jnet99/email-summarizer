from pymongo import MongoClient
import re
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def clean_text(text):

    text = re.sub(r'^>.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\S+\.\w{3,4}', '', text)
    return " ".join(text.split())

def extract_summary(text, num_sentences=3):

    try:
        text = clean_text(text)
        if not text:
            return "No summary available (empty text)"
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.split()) > 1]
        
        if len(sentences) <= 1:
            return text
        
        try:
            vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
            tfidf_matrix = vectorizer.fit_transform(sentences)
            sentence_scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
        except ValueError:
            sentence_scores = np.array([len(s.split()) for s in sentences])
        
        top_indices = sentence_scores.argsort()[-num_sentences:][::-1]
        return " ".join([sentences[i] for i in sorted(top_indices)])
    except Exception as e:
        return f"Error: {str(e)}"

def test_clean_text():
    """Test text cleaning logic"""
    dirty_text = "> Quoted line\nHello team. Meeting at 2 PM."
    clean = clean_text(dirty_text)
    assert "Quoted line" not in clean, "Quoted text not removed"
    
    dirty_text = "Attachments: report.pdf and image.png"
    clean = clean_text(dirty_text)
    assert "report.pdf" not in clean, "Attachments not removed"
    
    dirty_text = "Too   many   spaces."
    clean = clean_text(dirty_text)
    assert "  " not in clean, "Extra spaces not collapsed"
    
    print(" Unit tests for clean_text() passed!")

def test_extract_summary():
    """Test summarization logic"""

    text = "Hello. We have a meeting at 2 PM. Please prepare slides. Thanks."
    summary = extract_summary(text)
    assert "meeting at 2 PM" in summary, "Key sentence missing"
    

    text = "See you tomorrow."
    summary = extract_summary(text)
    assert summary == text, "Short email not handled correctly"
    
    text = ""
    summary = extract_summary(text)
    assert "empty text" in summary, "Empty email not handled"
    
    print(" Unit tests for extract_summary() passed!")

def test_pipeline_integration():
    test_client = MongoClient("mongodb://localhost:27017/")
    test_db = test_client["test_enron"]
    test_collection = test_db["test_emails"]
    
    try:
        test_email = {
            "body": "> Quoted text\nHello team. Meeting at 3 PM. Bring laptops.",
            "file": "test_email_1"
        }
        test_collection.insert_one(test_email)
        
        def test_run_pipeline():
            total = test_collection.count_documents({"body": {"$exists": True}})
            processed = 0
            while processed < total:
                batch = list(test_collection.find().skip(processed).limit(1))
                for doc in batch:
                    summary = extract_summary(doc["body"])
                    test_collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"summary": summary}}
                    )
                processed += len(batch)
        
        test_run_pipeline()
        
        updated = test_collection.find_one()
        assert "summary" in updated, "Summary not added to MongoDB"
        assert "Meeting at 3 PM" in updated["summary"], "Bad summary"
        
        print(" Integration test passed!")
    finally:
        test_collection.drop()
        test_client.close()

def manual_verification(limit=5):
    client = MongoClient("mongodb://localhost:27017/")
    collection = client["enron"]["enronmails"]
    
    print("\nManual Verification:")
    emails = collection.aggregate([
        {"$match": {"summary": {"$exists": True}}},
        {"$sample": {"size": limit}}
    ])
    
    for email in emails:
        print(f"\nOriginal ({email['_id']}):")
        print(email["body"][:200], "...")
        print("\nSummary:")
        print(email["summary"])
        print("-" * 50)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_clean_text()
    test_extract_summary()
    test_pipeline_integration()
    
    manual_verification()