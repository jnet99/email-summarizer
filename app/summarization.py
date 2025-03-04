from pymongo import MongoClient
import re
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["enron"]
collection = db["enronmails"]

def clean_text(text):

    text = re.sub(r'\n>.*', '', text)  
    text = re.sub(r'\S+\.\w{3,4}', '', text)  
    return " ".join(text.split())

def extract_summary(text, num_sentences=3):

    try:
        logger.info("Cleaning text...")
        text = clean_text(text)
        if not text:
            logger.warning("Empty text after cleaning")
            return "No summary available (empty text)"
        

        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.split()) > 1]
        
        if len(sentences) <= 1:
            logger.warning(f"Only {len(sentences)} sentences found. Returning full text.")
            return text
        

        logger.info("Creating TF-IDF matrix...")
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(sentences)
        similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        logger.info("Calculating TextRank scores...")
        scores = np.ones(len(sentences)) 
        damping = 0.85  
        for _ in range(20): 
            prev_scores = np.copy(scores)
            for i in range(len(sentences)):
                sum_score = 0
                for j in range(len(sentences)):
                    if i != j:
                        sum_score += similarity_matrix[i][j] * prev_scores[j]
                scores[i] = (1 - damping) + damping * sum_score
        

        top_indices = scores.argsort()[-num_sentences:][::-1]
        ordered_indices = sorted(top_indices)
        summary = " ".join([sentences[i] for i in ordered_indices])
        
        logger.info(f"Summary generated: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error in extract_summary: {str(e)}")
        return f"Error: {str(e)}"
    
    
def process_batch(batch):

    updates = []
    for doc in batch:
        if "body" in doc and doc["body"].strip():
            summary = extract_summary(doc["body"])
            updates.append({
                "_id": doc["_id"],
                "summary": summary
            })
    return updates

def run_pipeline(batch_size=1000):

    total_docs = collection.count_documents({"body": {"$exists": True}})
    processed = 0

    while processed < total_docs:
        batch = list(collection.find({"body": {"$exists": True}})
                    .skip(processed)
                    .limit(batch_size))
        
        updates = process_batch(batch)
        
        for update in updates:
            collection.update_one(
                {"_id": update["_id"]},
                {"$set": {"summary": update["summary"]}}
            )
        

        processed += len(batch)
        logger.info(f"Processed {processed}/{total_docs} emails")
    
    logger.info("Pipeline complete!")

if __name__ == "__main__":
    run_pipeline()

   