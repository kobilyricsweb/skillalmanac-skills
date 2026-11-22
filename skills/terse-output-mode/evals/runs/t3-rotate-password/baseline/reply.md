One role means a plain `ALTER ROLE` breaks any server still on the old password. Use a second role instead.

1. Create a twin role with the new password and the same privileges:
   `CREATE ROLE app_user_b LOGIN PASSWORD '<new>' IN ROLE app_user;`
   (or copy the grants explicitly)
   Also copy the role's settings with `ALTER ROLE ... SET`.
   Check that `app_user` owns no objects. If it does, run `SET ROLE app_user` after connecting, or use `ALTER DEFAULT PRIVILEGES`.
2. Check connection limits and `pg_hba.conf`. Make sure `app_user_b` is allowed from the app servers, and that `max_connections` has headroom for the overlap.
3. Test it: `psql "postgresql://app_user_b:<new>@host/db" -c 'select 1'`.
4. Update the secret store, then roll out `DATABASE_URL` with the new user and password one server at a time:
   - Take the server out of the load balancer (drain it).
   - Restart it with the new env.
   - Check its health and logs, then put it back in.
   - Repeat for the other two servers.
5. Confirm nothing still uses the old role:
   `select usename, count(*) from pg_stat_activity group by 1;`
   `app_user` should show 0 connections.
6. Retire the old role: `ALTER ROLE app_user NOLOGIN;` (or change its password). Watch for errors for a day or so.
7. Optional: to get back to the original name, repeat steps 1-6 in the other direction.

Rollback: until step 6, point `DATABASE_URL` back at `app_user`. Don't drop the old role until you're sure.
