from parser.schedule_parser import (
    days_to_readable,
    parse_days_pattern,
    parse_schedule,
    sanitize_input,
    validate_dosage,
    validate_peptide_name,
)


class TestScheduleParser:
    """test schedule parsing functionality"""

    def test_valid_schedules(self):
        """test parsing of valid schedule formats"""
        test_cases = [
            # (input, peptide, dosage, days_of_week, weeks)
            ("GHK-Cu; 1mg; 1-7; 6", "GHK-Cu", "1mg", "1,2,3,4,5,6,7", 6),
            ("BPC-157; 500mcg; 1,3,5; 8", "BPC-157", "500mcg", "1,3,5", 8),
            ("TB-500; 2mg; 1; 4", "TB-500", "2mg", "1", 4),
            ("Ipamorelin; 200mcg; 1-5; 12", "Ipamorelin", "200mcg", "1,2,3,4,5", 12),
        ]

        for text, expected_peptide, expected_dosage, expected_days, expected_weeks in test_cases:
            result = parse_schedule(text)
            assert result is not None, f"Failed to parse: {text}"
            assert result.peptide_name == expected_peptide
            assert result.dosage == expected_dosage
            assert result.days_of_week == expected_days
            assert result.weeks == expected_weeks

    def test_invalid_schedules(self):
        """test rejection of invalid schedules"""
        invalid_cases = [
            "",  # empty
            "just some random text",  # no structure
            "GHK-Cu; 1mg; 1-7",  # missing weeks
            "GHK-Cu; 1mg",  # missing days and weeks
            "GHK-Cu",  # only name
            "A" * 201,  # too long
            "GHK-Cu; 1mg; 8-9; 6",  # invalid day range
            "GHK-Cu; 1mg; 1-7; 0",  # zero weeks
            "GHK-Cu; 1mg; 1-7; 53",  # too many weeks
        ]

        for text in invalid_cases:
            result = parse_schedule(text)
            assert result is None, f"Should not parse: {text}"

    def test_security_injection_attempts(self):
        """test SQL injection and XSS prevention"""
        malicious_inputs = [
            "GHK-Cu'; DROP TABLE users; --; 1mg; 1-7; 6",
            "<script>alert('xss')</script>; 1mg; 1-7; 6",
        ]

        for text in malicious_inputs:
            result = parse_schedule(text)
            if result:
                assert "<" not in result.peptide_name
                assert ">" not in result.peptide_name
                assert '"' not in result.peptide_name
                assert "\\" not in result.peptide_name


class TestDaysPattern:
    """test days pattern parsing"""

    def test_range_patterns(self):
        """test range format parsing"""
        assert parse_days_pattern("1-7") == "1,2,3,4,5,6,7"
        assert parse_days_pattern("1-5") == "1,2,3,4,5"
        assert parse_days_pattern("6-7") == "6,7"
        assert parse_days_pattern("1-1") == "1"

    def test_list_patterns(self):
        """test list format parsing"""
        assert parse_days_pattern("1,3,5") == "1,3,5"
        assert parse_days_pattern("2,4") == "2,4"
        assert parse_days_pattern("1") == "1"
        assert parse_days_pattern("7") == "7"

    def test_invalid_patterns(self):
        """test rejection of invalid patterns"""
        assert parse_days_pattern("0-7") is None  # day 0 invalid
        assert parse_days_pattern("1-8") is None  # day 8 invalid
        assert parse_days_pattern("5-3") is None  # reversed range
        assert parse_days_pattern("abc") is None  # non-numeric
        assert parse_days_pattern("1,8") is None  # day 8 invalid

    def test_days_to_readable(self):
        """test conversion to readable format"""
        assert days_to_readable("1,2,3,4,5,6,7") == "daily"
        assert days_to_readable("1,2,3,4,5") == "weekdays"
        assert days_to_readable("6,7") == "weekends"
        assert days_to_readable("1,3,5") == "Mon/Wed/Fri"
        assert days_to_readable("2,4") == "Tue/Thu"


class TestInputValidation:
    """test input validation functions"""

    def test_sanitize_input(self):
        """test input sanitization"""
        assert sanitize_input("normal text") == "normal text"
        assert sanitize_input("text<script>") == "textscript"
        assert sanitize_input("text   with   spaces") == "text with spaces"
        # semicolons now allowed for parsing
        assert ";" in sanitize_input("text;with;semicolons")

    def test_validate_peptide_name(self):
        """test peptide name validation"""
        # valid names
        assert validate_peptide_name("GHK-Cu")
        assert validate_peptide_name("BPC-157")
        assert validate_peptide_name("TB 500")

        # invalid names
        assert not validate_peptide_name("GHK-Cu!")  # special char
        assert not validate_peptide_name("A" * 101)  # too long

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


class TestEdgeCases:
    """test edge cases and boundary conditions"""

    def test_weeks_limits(self):
        """test weeks validation"""
        # valid: 1-52 weeks
        result = parse_schedule("GHK-Cu; 1mg; 1-7; 1")
        assert result is not None
        assert result.weeks == 1

        result = parse_schedule("GHK-Cu; 1mg; 1-7; 52")
        assert result is not None
        assert result.weeks == 52

        # invalid: 0 weeks
        result = parse_schedule("GHK-Cu; 1mg; 1-7; 0")
        assert result is None

        # invalid: > 52 weeks
        result = parse_schedule("GHK-Cu; 1mg; 1-7; 53")
        assert result is None

    def test_unicode_handling(self):
        """test unicode character handling"""
        result = parse_schedule("GHK-Cu; 1μg; 1-7; 6")
        assert result is not None
        assert result.dosage == "1mcg"  # μg converted to mcg

    def test_whitespace_handling(self):
        """test handling of extra whitespace"""
        result = parse_schedule("  GHK-Cu ;  1mg ;  1-7 ;  6  ")
        assert result is not None
        assert result.peptide_name == "GHK-Cu"
        assert result.weeks == 6
