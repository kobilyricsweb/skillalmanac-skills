-- notes without rls
create table public.notes (id int);
create table public.profiles (id uuid);
alter table public.profiles enable row level security;
create policy "anyone updates" on public.profiles for update using (true);
create table public.things (id int);
alter table public.things enable row level security;
grant all on public.notes to anon;
create function public.f() returns void security definer language sql as $$ select 1 $$;
