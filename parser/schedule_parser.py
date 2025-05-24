import re
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedSchedule:
    """structured peptide schedule data"""
    peptide_name: str
    dosage: str
    frequency: str
    cycle_duration_days: int
    rest_period_days: int
    notes: str = ""

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
        
    return total_days if total_days > 0 else 42  # default 6 weeks

def parse_schedule(text: str) -> Optional[ParsedSchedule]:
    """parse natural language into structured schedule data"""
    text = text.strip()
    logger.info(f"parsing schedule: {text}")
    
    # pattern: "peptide dosage frequency for duration"
    # examples: "GHK-Cu 1mg daily for 6 weeks"
    #          "BPC-157 500mcg twice weekly for 8 weeks"
    
    # basic pattern matching
    pattern = r'(\w+(?:-\w+)*)\s+([0-9.]+\s*(?:mg|mcg|μg))\s+(.*?)\s+for\s+(.+)'
    match = re.match(pattern, text, re.IGNORECASE)
    
    if not match:
        logger.warning(f"could not parse schedule: {text}")
        return None
    
    peptide_name = match.group(1).strip()
    dosage = match.group(2).strip()
    frequency = match.group(3).strip()
    duration = match.group(4).strip()
    
    # convert to days
    cycle_duration_days = parse_duration_to_days(duration)
    
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