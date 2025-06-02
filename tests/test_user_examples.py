import pytest
from parser.schedule_parser import parse_schedule

class TestUserExamples:
    """test the specific schedule formats provided by the user"""
    
    def test_user_provided_schedules(self):
        """test all schedules from user's examples"""
        test_cases = [
            # (input, expected_peptide, expected_dosage, expected_frequency, expected_days)
            ("GHK-Cu 1.5mg daily for 5 weeks", "GHK-Cu", "1.5mg", "daily", 35),
            ("Thymosin 1.2mg twice weekly for 10 weeks", "Thymosin", "1.2mg", "twice weekly", 70),
            ("Epithalon 2mg daily for 3 weeks", "Epithalon", "2mg", "daily", 21),
            ("BPC-157 500mcg daily for 7 weeks", "BPC-157", "500mcg", "daily", 49),
            ("TB-500 2mg weekly for 10 weeks", "TB-500", "2mg", "weekly", 70),
        ]
        
        for text, expected_peptide, expected_dosage, expected_freq, expected_days in test_cases:
            result = parse_schedule(text)
            assert result is not None, f"Failed to parse: {text}"
            assert result.peptide_name == expected_peptide, f"Wrong peptide for: {text}"
            assert result.dosage == expected_dosage, f"Wrong dosage for: {text}"
            assert result.frequency == expected_freq, f"Wrong frequency for: {text}"
            assert result.cycle_duration_days == expected_days, f"Wrong duration for: {text}"
            
            # verify rest periods are set appropriately
            if "epithalon" in expected_peptide.lower():
                assert result.rest_period_days == 180  # 6 months for Epithalon
            elif "tb-500" in expected_peptide.lower():
                assert result.rest_period_days == 60   # 2-3 months for TB-500
            else:
                assert result.rest_period_days == expected_days  # default: same as cycle
    
    def test_decimal_dosages(self):
        """test that decimal dosages work correctly"""
        decimal_cases = [
            "Peptide 0.5mg daily for 4 weeks",
            "Test 1.25mg weekly for 8 weeks",
            "Sample 2.75mg EOD for 6 weeks",
        ]
        
        for text in decimal_cases:
            result = parse_schedule(text)
            assert result is not None, f"Failed to parse decimal dosage: {text}"
            assert "." in result.dosage, f"Decimal not preserved in: {text}"
    
    def test_frequency_variations(self):
        """test different frequency formats"""
        frequency_cases = [
            ("Test 1mg daily for 4 weeks", 1),          # daily = 1 day
            ("Test 1mg weekly for 4 weeks", 7),         # weekly = 7 days
            ("Test 1mg twice weekly for 4 weeks", 3),   # twice weekly ≈ 3 days
            ("Test 1mg EOD for 4 weeks", 2),            # EOD = 2 days
            ("Test 1mg every other day for 4 weeks", 2), # every other day = 2 days
        ]
        
        for text, expected_freq_days in frequency_cases:
            result = parse_schedule(text)
            assert result is not None, f"Failed to parse: {text}"
            # check that frequency is parsed correctly
            from parser.schedule_parser import parse_frequency_to_days
            freq_days = parse_frequency_to_days(result.frequency)
            assert freq_days == expected_freq_days, f"Wrong frequency days for: {text}" 