import pytest
from parser.schedule_parser import parse_schedule, sanitize_input, validate_peptide_name, validate_dosage

class TestScheduleParser:
    """test schedule parsing functionality"""
    
    def test_valid_schedules(self):
        """test parsing of valid schedule formats"""
        test_cases = [
            ("GHK-Cu 1mg daily for 6 weeks", "GHK-Cu", "1mg", "daily", 42),
            ("BPC-157 500mcg twice weekly for 8 weeks", "BPC-157", "500mcg", "twice weekly", 56),
            ("TB-500 2mg weekly for 4 weeks", "TB-500", "2mg", "weekly", 28),
            ("Ipamorelin 200mcg daily for 12 weeks", "Ipamorelin", "200mcg", "daily", 84),
        ]
        
        for text, expected_peptide, expected_dosage, expected_freq, expected_days in test_cases:
            result = parse_schedule(text)
            assert result is not None, f"Failed to parse: {text}"
            assert result.peptide_name == expected_peptide
            assert result.dosage == expected_dosage
            assert result.frequency == expected_freq
            assert result.cycle_duration_days == expected_days
    
    def test_invalid_schedules(self):
        """test rejection of invalid schedules"""
        invalid_cases = [
            "",  # empty
            "just some random text",  # no structure
            "GHK-Cu without dosage",  # missing dosage
            "1mg daily for 6 weeks",  # missing peptide
            "GHK-Cu 1mg",  # missing duration
            "A" * 501,  # too long
        ]
        
        for text in invalid_cases:
            result = parse_schedule(text)
            assert result is None, f"Should not parse: {text}"
    
    def test_security_injection_attempts(self):
        """test SQL injection and XSS prevention"""
        malicious_inputs = [
            "GHK-Cu'; DROP TABLE users; -- 1mg daily for 6 weeks",
            "<script>alert('xss')</script> 1mg daily for 6 weeks",
            "GHK-Cu\" OR \"1\"=\"1 1mg daily for 6 weeks",
            "GHK-Cu\\ 1mg daily for 6 weeks",
        ]
        
        for text in malicious_inputs:
            result = parse_schedule(text)
            # should either fail to parse or sanitize the input
            if result:
                assert ";" not in result.peptide_name
                assert "<" not in result.peptide_name
                assert ">" not in result.peptide_name
                assert "\"" not in result.peptide_name
                assert "\\" not in result.peptide_name

class TestInputValidation:
    """test input validation functions"""
    
    def test_sanitize_input(self):
        """test input sanitization"""
        assert sanitize_input("normal text") == "normal text"
        assert sanitize_input("text;with;semicolons") == "textwithsemicolons"
        assert sanitize_input("text<script>") == "textscript"
        assert sanitize_input("text   with   spaces") == "text with spaces"
    
    def test_validate_peptide_name(self):
        """test peptide name validation"""
        # valid names
        assert validate_peptide_name("GHK-Cu")
        assert validate_peptide_name("BPC-157")
        assert validate_peptide_name("TB 500")
        
        # invalid names
        assert not validate_peptide_name("GHK-Cu!")  # special char
        assert not validate_peptide_name("A" * 101)  # too long
        assert not validate_peptide_name("GHK;Cu")  # semicolon
    
    def test_validate_dosage(self):
        """test dosage validation"""
        # valid dosages
        assert validate_dosage("1mg")
        assert validate_dosage("500mcg")
        assert validate_dosage("2.5mg")
        assert validate_dosage("100 iu")
        
        # invalid dosages
        assert not validate_dosage("1")  # no unit
        assert not validate_dosage("mg")  # no number
        assert not validate_dosage("1kg")  # invalid unit
        assert not validate_dosage("1mg; DROP TABLE")  # injection

class TestEdgeCases:
    """test edge cases and boundary conditions"""
    
    def test_cycle_duration_limits(self):
        """test cycle duration validation"""
        # valid: 1-365 days
        result = parse_schedule("GHK-Cu 1mg daily for 1 day")
        assert result is not None
        assert result.cycle_duration_days == 1
        
        # invalid: 0 days
        result = parse_schedule("GHK-Cu 1mg daily for 0 days")
        assert result is None
        
        # invalid: > 365 days
        result = parse_schedule("GHK-Cu 1mg daily for 400 days")
        assert result is None
    
    def test_unicode_handling(self):
        """test unicode character handling"""
        result = parse_schedule("GHK-Cu 1μg daily for 6 weeks")
        # should handle μ (micro) symbol
        assert result is not None 