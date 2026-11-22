Postgres has one password per role, so changing `app_user` in place breaks new connections mid-rollout. Rotate via a second role, then retire the old one.

1. Generate the new password and store it in your secret manager.
```bash
NEWPW=$(openssl rand -base64 32 | tr -d '/+=')
```
2. Create a twin role that inherits `app_user` privileges.
```sql
CREATE ROLE app_user_v2 LOGIN PASSWORD '<NEWPW>' IN ROLE app_user INHERIT;
```
3. Point `DATABASE_URL` at `app_user_v2` with the new password. Roll one server at a time: drain from the load balancer, restart, confirm healthy, re-add, next.
4. Check that no session still uses the old role.
```sql
SELECT count(*) FROM pg_stat_activity WHERE usename = 'app_user';
```
Warning: step 5 invalidates the old password, so run it only after the count above is 0 on all three servers and the app is healthy.

5. Set a new random password on the old role.
```sql
ALTER ROLE app_user PASSWORD '<RANDOM_UNUSED>';
```

Warning: objects created by `app_user_v2` are owned by `app_user_v2`; if the app runs migrations or creates tables, run `ALTER DEFAULT PRIVILEGES` or `SET ROLE app_user` first so ownership stays consistent.

Check:
```sql
SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;
```
Only `app_user_v2` should appear for the app.
