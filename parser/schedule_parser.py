import re
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# security constants
MAX_PEPTIDE_NAME_LENGTH = 100
MAX_DOSAGE_LENGTH = 50
MAX_NOTES_LENGTH = 500
MAX_CYCLE_DAYS = 365
MIN_CYCLE_DAYS = 1

@dataclass
class ParsedSchedule:
    """structured peptide schedule data"""
    peptide_name: str
    dosage: str
    frequency: str
    cycle_duration_days: int
    rest_period_days: int
    notes: str = ""

def sanitize_input(text: str) -> str:
    """sanitize user input to prevent injection attacks"""
    # remove any potential SQL injection characters
    text = re.sub(r'[;<>\"\'\\]', '', text)
    # normalize whitespace
    text = ' '.join(text.split())
    return text.strip()

def validate_peptide_name(name: str) -> bool:
    """validate peptide name format"""
    # allow letters, numbers, hyphens, and spaces
    if not re.match(r'^[a-zA-Z0-9\-\s]+$', name):
        return False
    if len(name) > MAX_PEPTIDE_NAME_LENGTH:
        return False
    return True

def validate_dosage(dosage: str) -> bool:
    """validate dosage format"""
    # allow numbers, units, and common dosage formats
    if not re.match(r'^[\d\.\s]+(mg|mcg|iu|ml|cc)$', dosage.lower()):
        return False
    if len(dosage) > MAX_DOSAGE_LENGTH:
        return False
    return True

def parse_frequency_to_days(frequency: str) -> int:
    """convert frequency text to days between doses"""
    frequency = frequency.lower().strip()
    
    if "daily" in frequency or "every day" in frequency:
        return 1
    elif "twice weekly" in frequency or "2x weekly" in frequency:
        return 3  # approximately every 3-4 days
    elif "once weekly" in frequency or "weekly" in frequency:
        return 7
    elif "every other day" in frequency or "eod" in frequency:
        return 2
    elif "3x weekly" in frequency or "three times weekly" in frequency:
        return 2  # approximately every 2-3 days
    else:
        return 1  # default to daily

def parse_duration_to_days(duration_text: str) -> int:
    """convert duration text to days"""
    duration_text = duration_text.lower().strip()
    
    # extract numbers and units
    weeks_match = re.search(r'(\d+)\s*week', duration_text)
    days_match = re.search(r'(\d+)\s*day', duration_text)
    months_match = re.search(r'(\d+)\s*month', duration_text)
    
    total_days = 0
    if weeks_match:
        total_days += int(weeks_match.group(1)) * 7
    if days_match:
        total_days += int(days_match.group(1))
    if months_match:
        total_days += int(months_match.group(1)) * 30
    
    # handle "0 days" case
    if total_days == 0 and re.search(r'0\s*day', duration_text):
        return 0  # explicitly return 0 for invalid duration
        
    return total_days if total_days > 0 else 42  # default 6 weeks

def parse_schedule(text: str) -> Optional[ParsedSchedule]:
    """
    Parse natural language peptide schedule.
    
    Security: All inputs are sanitized and validated
    """
    if not text or len(text) > 500:  # max input length
        return None
        
    # sanitize input
    text = sanitize_input(text)
    text_lower = text.lower()
    
    # pattern: "peptide dosage frequency for duration"
    # examples: "GHK-Cu 1mg daily for 6 weeks"
    #          "BPC-157 500mcg twice weekly for 8 weeks"
    
    # first find the dosage to know where peptide name ends
    dosage_match = re.search(r'(\d+\.?\d*)\s*(mg|mcg|iu|ml|cc|μg|ug)', text_lower)
    if not dosage_match:
        return None
    
    dosage_start = dosage_match.start()
    dosage_value = dosage_match.group(1)
    dosage_unit = dosage_match.group(2)
    
    # handle unicode μ
    if dosage_unit in ['μg', 'ug']:
        dosage_unit = 'mcg'
    
    dosage = f"{dosage_value}{dosage_unit}"
    if not validate_dosage(dosage):
        logger.warning(f"invalid dosage: {dosage}")
        return None
    
    # peptide name is everything before the dosage
    peptide_name = text[:dosage_start].strip()
    if not peptide_name or not validate_peptide_name(peptide_name):
        logger.warning(f"invalid peptide name: {peptide_name}")
        return None
    
    # extract the rest after dosage
    rest_of_text = text[dosage_match.end():].strip()
    
    # look for "for" to separate frequency from duration
    for_match = re.search(r'\s+for\s+', rest_of_text, re.IGNORECASE)
    if not for_match:
        return None
    
    frequency = rest_of_text[:for_match.start()].strip()
    duration_text = rest_of_text[for_match.end():].strip()
    
    if not frequency:
        frequency = "daily"  # default frequency
    
    # parse duration
    cycle_duration_days = parse_duration_to_days(duration_text)
    
    # validate cycle duration
    if cycle_duration_days < MIN_CYCLE_DAYS or cycle_duration_days > MAX_CYCLE_DAYS:
        logger.warning(f"invalid cycle duration: {cycle_duration_days}")
        return None
    
    # default rest periods based on common peptide protocols
    rest_period_days = cycle_duration_days  # equal rest to cycle duration
    
    # special cases for known peptides
    peptide_lower = peptide_name.lower()
    if "foxo4" in peptide_lower:
        rest_period_days = 120  # 4+ months rest for FOXO4-DRI
    elif "epithalon" in peptide_lower:
        rest_period_days = 180  # 6 months rest for Epithalon
    elif "tb-500" in peptide_lower:
        rest_period_days = 60   # 2-3 months rest for TB-500
    
    return ParsedSchedule(
        peptide_name=peptide_name,
        dosage=dosage,
        frequency=frequency,
        cycle_duration_days=cycle_duration_days,
        rest_period_days=rest_period_days,
        notes=f"Parsed from: {text}"
    ) 