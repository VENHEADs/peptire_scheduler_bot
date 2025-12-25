import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# security constants
MAX_PEPTIDE_NAME_LENGTH = 100
MAX_DOSAGE_LENGTH = 50
MAX_WEEKS = 52
MIN_WEEKS = 1

@dataclass
class ParsedSchedule:
    """structured peptide schedule data"""
    peptide_name: str
    dosage: str
    days_of_week: str  # "1,2,3,4,5,6,7" format
    weeks: int
    rest_period_days: int
    notes: str = ""

def sanitize_input(text: str) -> str:
    """sanitize user input to prevent injection attacks"""
    # remove dangerous characters but keep semicolons for parsing
    text = re.sub(r'[<>\"\'\\]', '', text)
    # normalize whitespace
    text = ' '.join(text.split())
    return text.strip()

def validate_peptide_name(name: str) -> bool:
    """validate peptide name format"""
    if not re.match(r'^[a-zA-Z0-9\-\s]+$', name):
        return False
    if len(name) > MAX_PEPTIDE_NAME_LENGTH:
        return False
    return True

def validate_dosage(dosage: str) -> bool:
    """validate dosage format"""
    if not re.match(r'^[\d\.\s]+(mg|mcg|iu|ml|cc)$', dosage.lower()):
        return False
    if len(dosage) > MAX_DOSAGE_LENGTH:
        return False
    return True

def parse_days_pattern(pattern: str) -> str | None:
    """
    Parse days pattern and return normalized "1,2,3" format.
    
    Accepts:
    - "1-7" → "1,2,3,4,5,6,7" (range)
    - "1-5" → "1,2,3,4,5" (weekdays)
    - "1,3,5" → "1,3,5" (specific days)
    
    Returns None if invalid.
    """
    pattern = pattern.strip()
    
    # check for range format: "1-7" or "1-5"
    range_match = re.match(r'^(\d)-(\d)$', pattern)
    if range_match:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        if 1 <= start <= 7 and 1 <= end <= 7 and start <= end:
            return ','.join(str(d) for d in range(start, end + 1))
        return None
    
    # check for list format: "1,3,5"
    if re.match(r'^[\d,]+$', pattern):
        days = [d.strip() for d in pattern.split(',') if d.strip()]
        valid_days = []
        for d in days:
            if d.isdigit() and 1 <= int(d) <= 7:
                valid_days.append(d)
            else:
                return None
        if valid_days:
            return ','.join(sorted(set(valid_days), key=int))
    
    return None

def days_to_readable(days_of_week: str) -> str:
    """convert days_of_week to human readable format"""
    day_names = {
        '1': 'Mon', '2': 'Tue', '3': 'Wed', '4': 'Thu',
        '5': 'Fri', '6': 'Sat', '7': 'Sun'
    }
    days = days_of_week.split(',')
    
    if days == ['1', '2', '3', '4', '5', '6', '7']:
        return 'daily'
    elif days == ['1', '2', '3', '4', '5']:
        return 'weekdays'
    elif days == ['6', '7']:
        return 'weekends'
    else:
        return '/'.join(day_names.get(d, d) for d in days)

def parse_schedule(text: str) -> Optional[ParsedSchedule]:
    """
    Parse semicolon-separated peptide schedule.
    
    Format: peptide name; dosage; days; weeks
    Examples:
    - "GHK-Cu; 1mg; 1-7; 6" → daily for 6 weeks
    - "BPC-157; 500mcg; 1,3,5; 8" → Mon/Wed/Fri for 8 weeks
    """
    if not text or len(text) > 200:
        return None
    
    text = sanitize_input(text)
    parts = [p.strip() for p in text.split(';')]
    
    if len(parts) != 4:
        logger.warning(f"expected 4 parts, got {len(parts)}")
        return None
    
    peptide_name, dosage, days_pattern, weeks_str = parts
    
    # validate peptide name
    if not peptide_name or not validate_peptide_name(peptide_name):
        logger.warning(f"invalid peptide name: {peptide_name}")
        return None
    
    # validate and normalize dosage
    dosage = dosage.lower().replace(' ', '')
    # handle unicode μ
    dosage = dosage.replace('μg', 'mcg').replace('ug', 'mcg')
    if not validate_dosage(dosage):
        logger.warning(f"invalid dosage: {dosage}")
        return None
    
    # parse days pattern
    days_of_week = parse_days_pattern(days_pattern)
    if not days_of_week:
        logger.warning(f"invalid days pattern: {days_pattern}")
        return None
    
    # parse weeks
    try:
        weeks = int(weeks_str)
        if weeks < MIN_WEEKS or weeks > MAX_WEEKS:
            logger.warning(f"weeks out of range: {weeks}")
            return None
    except ValueError:
        logger.warning(f"invalid weeks value: {weeks_str}")
        return None
    
    # calculate rest period based on peptide
    rest_period_days = weeks * 7  # default: equal rest to cycle
    peptide_lower = peptide_name.lower()
    if "foxo4" in peptide_lower:
        rest_period_days = 120
    elif "epithalon" in peptide_lower:
        rest_period_days = 180
    elif "tb-500" in peptide_lower:
        rest_period_days = 60
    
    return ParsedSchedule(
        peptide_name=peptide_name,
        dosage=dosage,
        days_of_week=days_of_week,
        weeks=weeks,
        rest_period_days=rest_period_days,
        notes=f"Parsed from: {text}"
    )
