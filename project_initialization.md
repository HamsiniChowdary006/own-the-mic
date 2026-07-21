# OwnTheMic Backend Modernization - Initialization Steps

## Supabase Integration
1. **Set up Supabase Account:**
   - Create a new Supabase project
   - Get PostgreSQL connection string (DATABASE_URL)

2. **Environment Variables:**
   - Add to .env file:
   ```
   DATABASE_URL=your-supabase-postgresql-connection-string
   ```

3. **Update config.py:**
   - Successful modification as shown in the tool response

4. **Schema Migration:**
   - Run `alembic upgrade head` to apply existing migration
   - Add additional migrations for any schema changes

5. **Environment Setup:**
   - Verify connection with:
   ```python
   import psycopg2
   conn = psycopg2.connect(DATABASE_URL)
   conn.close()
   ```

## Next Steps
- Proceed with Phase 2 (Google OAuth) after Supabase integration verification