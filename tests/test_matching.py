import pytest
from src.matching import apply_mismatch_guard, SIMILARITY_THRESHOLD, MIN_CONFIDENCE

def test_category_mismatch_rejected():
    post = {"primary_subject": "fox"}
    wolf_candidate = {
        "primary_subject": "wolf",
        "confidence": 0.9,
        "similarity_score": 0.9,
    }
    approved, reason = apply_mismatch_guard(post, wolf_candidate)
    assert approved is False
    assert "category mismatch" in reason.lower()

def test_low_confidence_rejected():
    post = {"primary_subject": "fox"}
    low_conf_candidate = {
        "primary_subject": "fox",
        "confidence": 0.3,
        "similarity_score": 0.9,
    }
    approved, reason = apply_mismatch_guard(post, low_conf_candidate)
    assert approved is False
    assert "confidence" in reason.lower()

def test_low_similarity_rejected():
    post = {"primary_subject": "fox"}
    low_sim_candidate = {
        "primary_subject": "fox",
        "confidence": 0.9,
        "similarity_score": 0.1,
    }
    approved, reason = apply_mismatch_guard(post, low_sim_candidate)
    assert approved is False
    assert "similarity" in reason.lower()

def test_good_match_approved():
    post = {"primary_subject": "fox"}
    good_candidate = {
        "primary_subject": "fox",
        "confidence": 0.9,
        "similarity_score": 0.9,
    }
    approved, reason = apply_mismatch_guard(post, good_candidate)
    assert approved is True
    assert reason is None

def test_post_with_no_expected_subject_skips_category_check():
    post = {"primary_subject": None}
    candidate = {
        "primary_subject": "fox",
        "confidence": 0.9,
        "similarity_score": 0.9,
    }
    approved, reason = apply_mismatch_guard(post, candidate)
    assert approved is True