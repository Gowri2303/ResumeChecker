"""
Hugging Face model integration for semantic similarity comparison
between resume text and job description.

Uses the HuggingFace Inference API with an API key.
"""

import os
import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from utils import extract_skills_from_text, clean_text
from job_description import (
    JOB_DESCRIPTION, JOB_TITLE, REQUIRED_SKILLS, BONUS_SKILLS,
    MINIMUM_REQUIRED_MATCH_PERCENT
)

# Load environment variables from .env file (use explicit path)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# ─── HuggingFace API Config ───
HF_API_KEY = os.getenv("HF_API_KEY")  # <-- Your key goes in the .env file
HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Initialize the HuggingFace Inference Client
_client = None

def get_client():
    """Get or create the HuggingFace InferenceClient."""
    global _client
    if _client is None:
        if not HF_API_KEY:
            raise ValueError(
                "❌ HuggingFace API key not found!\n\n"
                "Please add your API key to the `.env` file:\n"
                "HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxx\n\n"
                "Get your free key at: https://huggingface.co/settings/tokens"
            )
        _client = InferenceClient(token=HF_API_KEY)
    return _client


def get_embedding(text: str) -> list:
    """
    Get embedding for a single text using HuggingFace Inference API.
    
    Args:
        text: String to embed
    
    Returns:
        Embedding vector as a list of floats
    """
    client = get_client()
    result = client.feature_extraction(
        text[:2000],  # Truncate to avoid token limits
        model=HF_MODEL
    )
    # Result can be nested — flatten to 1D by averaging token embeddings
    arr = np.array(result)
    if arr.ndim == 2:
        return arr.mean(axis=0).tolist()
    return arr.tolist()


def cosine_similarity(vec_a, vec_b) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compute_similarity(resume_text: str, jd_text: str) -> float:
    """
    Compute semantic similarity between resume and job description
    using HuggingFace Inference API (all-MiniLM-L6-v2 model).
    
    Args:
        resume_text: Cleaned resume text
        jd_text: Job description text
    
    Returns:
        Similarity score between 0 and 1
    """
    resume_embedding = get_embedding(resume_text)
    jd_embedding = get_embedding(jd_text)
    
    return cosine_similarity(resume_embedding, jd_embedding)


def analyze_resume(resume_text: str) -> dict:
    """
    Full analysis of a resume against the hardcoded job description.
    
    Args:
        resume_text: Raw extracted text from the resume PDF
    
    Returns:
        Dictionary containing analysis results
    """
    cleaned_resume = clean_text(resume_text)
    cleaned_jd = clean_text(JOB_DESCRIPTION)
    
    # --- 1. Semantic Similarity ---
    similarity_score = compute_similarity(cleaned_resume, cleaned_jd)
    similarity_percent = round(similarity_score * 100, 1)
    
    # --- 2. Keyword/Skill Matching ---
    matched_required = extract_skills_from_text(cleaned_resume, REQUIRED_SKILLS)
    matched_bonus = extract_skills_from_text(cleaned_resume, BONUS_SKILLS)
    
    missing_required = [s for s in REQUIRED_SKILLS if s.lower() not in [m.lower() for m in matched_required]]
    
    total_required = len(REQUIRED_SKILLS)
    matched_required_count = len(matched_required)
    match_percent = round((matched_required_count / total_required) * 100, 1) if total_required > 0 else 0
    
    # --- 3. Shortlist Decision ---
    # Shortlisted if: required skill match >= threshold AND similarity > 0.3
    is_shortlisted = (match_percent >= MINIMUM_REQUIRED_MATCH_PERCENT) and (similarity_percent >= 30)
    
    # --- 4. Build Reasoning ---
    if is_shortlisted:
        reasons = []
        reasons.append(f"Has {matched_required_count} out of {total_required} required skills")
        reasons.append("Resume content aligns well with the job description")
        if matched_required:
            reasons.append(f"Matched skills: {', '.join(sorted(set(matched_required)))}")
        if matched_bonus:
            reasons.append(f"Also has bonus skills: {', '.join(sorted(set(matched_bonus)))}")
        if missing_required:
            unique_missing = _deduplicate_skills(missing_required)
            reasons.append(f"Could improve on: {', '.join(sorted(unique_missing))}")
    else:
        reasons = []
        reasons.append(f"Only {matched_required_count} out of {total_required} required skills found")
        reasons.append("Resume content does not align well with the job description")
        if missing_required:
            unique_missing = _deduplicate_skills(missing_required)
            reasons.append(f"Missing skills: {', '.join(sorted(unique_missing))}")
        if matched_required:
            reasons.append(f"Has these skills: {', '.join(sorted(set(matched_required)))}")
        if matched_bonus:
            reasons.append(f"Also has bonus skills: {', '.join(sorted(set(matched_bonus)))}")
    
    return {
        "job_title": JOB_TITLE,
        "is_shortlisted": is_shortlisted,
        "similarity_percent": similarity_percent,
        "match_percent": match_percent,
        "matched_required_skills": sorted(set(matched_required)),
        "matched_bonus_skills": sorted(set(matched_bonus)),
        "missing_required_skills": sorted(set(missing_required)),
        "reasons": reasons,
        "total_required_skills": total_required,
        "matched_required_count": matched_required_count,
    }


def _deduplicate_skills(skills: list) -> list:
    """Remove synonym duplicates from skill list for cleaner display."""
    synonyms = {
        "nodejs": "node.js",
        "springboot": "spring boot",
        "fullstack": "full stack",
        "full-stack": "full stack",
        "cicd": "ci/cd",
        "restful": "rest/restful",
        "rest": "rest/restful",
        "nosql": "nosql",
        "vuejs": "vue",
        "nextjs": "next.js",
    }
    cleaned = set()
    for skill in skills:
        normalized = synonyms.get(skill.lower(), skill)
        cleaned.add(normalized)
    return list(cleaned)
