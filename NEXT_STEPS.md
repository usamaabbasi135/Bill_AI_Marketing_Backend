# Next Steps - OAuth Email Integration

## ✅ Completed

All code implementation is complete:
- ✅ UserEmailProvider model created
- ✅ Database migration file created (`a1b2c3d4e5f7_add_user_email_providers_table.py`)
- ✅ OAuth services implemented (Microsoft & Google)
- ✅ API endpoints created
- ✅ Email sender updated with OAuth support
- ✅ All files integrated into the application

## 🔄 Immediate Next Steps

### 1. Run Database Migration

Once your database is available, run:

```bash
flask db upgrade
```

This will create the `user_email_providers` table.

**To verify migration:**
```bash
flask db current  # Check current migration version
flask db history # View migration history
```

### 2. Set Environment Variables

Add these to your `.env` file or deployment environment:

```env
# Microsoft OAuth
MICROSOFT_CLIENT_ID=your_client_id_here
MICROSOFT_CLIENT_SECRET=your_client_secret_here
MICROSOFT_REDIRECT_URI=http://localhost:5000/api/auth/oauth/microsoft/callback

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/oauth/google/callback
```

### 3. Create OAuth Applications

Follow the detailed instructions in `OAUTH_SETUP_GUIDE.md`:
- **Microsoft**: Azure Portal → App Registrations
- **Google**: Google Cloud Console → OAuth 2.0 Client IDs

### 4. Test the Implementation

#### Test OAuth Connection:
```bash
# 1. Get authorization URL (requires JWT token)
GET /api/auth/oauth/microsoft/authorize
# or
GET /api/auth/oauth/google/authorize

# 2. Open the URL in browser and complete OAuth flow

# 3. Verify connection
GET /api/auth/oauth/providers
```

#### Test Email Sending:
```bash
# Send email (will use OAuth if available, SES as fallback)
POST /api/emails/<email_id>/send
```

## 📋 Checklist

- [ ] Database migration run successfully
- [ ] Environment variables set
- [ ] Microsoft OAuth app created and configured
- [ ] Google OAuth app created and configured
- [ ] Redirect URIs match in OAuth providers
- [ ] Test Microsoft OAuth flow
- [ ] Test Google OAuth flow
- [ ] Test email sending with OAuth
- [ ] Verify fallback to SES works

## 🔒 Production Considerations

Before deploying to production:

1. **Token Encryption**: Replace base64 encoding with proper encryption (see `OAUTH_SETUP_GUIDE.md`)
2. **State Storage**: Move from in-memory to Redis/database
3. **Update Redirect URIs**: Use production URLs in OAuth provider settings
4. **Monitoring**: Set up logging and alerts for OAuth operations
5. **Rate Limits**: Be aware of Microsoft/Google API rate limits

## 📚 Documentation

- **Setup Guide**: See `OAUTH_SETUP_GUIDE.md` for detailed instructions
- **API Endpoints**: All endpoints are documented in the code
- **Error Handling**: Comprehensive error handling and logging implemented

## 🐛 Troubleshooting

If you encounter issues:

1. **Database Connection**: Ensure PostgreSQL is running and `DATABASE_URL` is set
2. **OAuth Errors**: Check redirect URIs match exactly (case-sensitive, no trailing slashes)
3. **Token Issues**: Verify tokens are being stored and refreshed correctly
4. **Email Sending**: Check logs to see if OAuth or SES was used

## 📞 Need Help?

- Check application logs for detailed error messages
- Verify all environment variables are correctly set
- Test in development environment first
- Review `OAUTH_SETUP_GUIDE.md` for detailed troubleshooting

