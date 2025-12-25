import pytest
from parser.schedule_parser import parse_schedule, days_to_readable

class TestUserExamples:
    """test the specific schedule formats for new semicolon format"""
    
    def test_user_provided_schedules(self):
        """test all common schedule patterns"""
        test_cases = [
            # (input, peptide, dosage, days_of_week, weeks)
            ("GHK-Cu; 1.5mg; 1-7; 5", "GHK-Cu", "1.5mg", "1,2,3,4,5,6,7", 5),
            ("Thymosin; 1.2mg; 1,4; 10", "Thymosin", "1.2mg", "1,4", 10),
            ("Epithalon; 2mg; 1-7; 3", "Epithalon", "2mg", "1,2,3,4,5,6,7", 3),
            ("BPC-157; 500mcg; 1,3,5; 7", "BPC-157", "500mcg", "1,3,5", 7),
            ("TB-500; 2mg; 1; 10", "TB-500", "2mg", "1", 10),
        ]
        
        for text, expected_peptide, expected_dosage, expected_days, expected_weeks in test_cases:
            result = parse_schedule(text)
            assert result is not None, f"Failed to parse: {text}"
            assert result.peptide_name == expected_peptide, f"Wrong peptide for: {text}"
            assert result.dosage == expected_dosage, f"Wrong dosage for: {text}"
            assert result.days_of_week == expected_days, f"Wrong days for: {text}"
            assert result.weeks == expected_weeks, f"Wrong weeks for: {text}"
            
            # verify rest periods are set appropriately
            if "epithalon" in expected_peptide.lower():
                assert result.rest_period_days == 180  # 6 months for Epithalon
            elif "tb-500" in expected_peptide.lower():
                assert result.rest_period_days == 60   # 2-3 months for TB-500
            else:
                assert result.rest_period_days == expected_weeks * 7  # default: same as cycle
    
    def test_decimal_dosages(self):
        """test that decimal dosages work correctly"""
        decimal_cases = [
            "Peptide; 0.5mg; 1-7; 4",
            "Test; 1.25mg; 1; 8",
            "Sample; 2.75mg; 1,3,5,7; 6",
        ]
        
        for text in decimal_cases:
            result = parse_schedule(text)
            assert result is not None, f"Failed to parse decimal dosage: {text}"
            assert "." in result.dosage, f"Decimal not preserved in: {text}"
    
    def test_days_patterns(self):
        """test different days patterns"""
        pattern_cases = [
            ("Test; 1mg; 1-7; 4", "daily"),           # every day
            ("Test; 1mg; 1-5; 4", "weekdays"),        # weekdays
            ("Test; 1mg; 6,7; 4", "weekends"),        # weekends
            ("Test; 1mg; 1,3,5; 4", "Mon/Wed/Fri"),   # MWF
            ("Test; 1mg; 2,4; 4", "Tue/Thu"),         # TuTh
            ("Test; 1mg; 1; 4", "Mon"),               # Monday only
        ]
        
        for text, expected_readable in pattern_cases:
            result = parse_schedule(text)
            assert result is not None, f"Failed to parse: {text}"
            readable = days_to_readable(result.days_of_week)
            assert readable == expected_readable, f"Wrong readable for: {text}"
