# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Measures

### Input Validation
- All user inputs are sanitized to prevent SQL injection
- Peptide names are validated against a whitelist pattern
- Maximum input lengths are enforced
- Special characters are stripped from inputs

### Database Security
- Using SQLAlchemy ORM to prevent SQL injection
- Parameterized queries only
- No raw SQL execution from user input

### API Security
- Telegram Bot Token must be kept secret
- Token is loaded from environment variables only
- No hardcoded credentials in code

### Data Privacy
- No personal health information is logged
- User data is isolated by telegram_id
- No data sharing between users

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **DO NOT** open a public issue
2. Email the maintainer directly with details
3. Allow reasonable time for a fix before disclosure

## Best Practices for Deployment

1. **Environment Variables**
   - Never commit `.env` files
   - Use secure secret management in production
   - Rotate bot tokens regularly

2. **Database**
   - Use encrypted storage in production
   - Regular backups
   - Limit database access

3. **Monitoring**
   - Monitor for unusual bot activity
   - Set up alerts for errors
   - Review logs regularly

## Known Limitations

- SQLite database is not encrypted by default
- Bot messages are not end-to-end encrypted
- Reminder times are in UTC (no timezone support yet) 