-- T70 manual hardening template. NOT applied by this repository.
-- Run only after approved migration to0003 using a reviewed migration owner.
-- Current eight private tables + migration marker; update after every new table.
-- Runtime backend still uses verified owner predicates; this is client deny-all,
-- not a claim of per-end-user RLS on privileged backend SQL connections.
BEGIN;
DO $vela$
DECLARE
  name text;
  expected text[] := ARRAY['demo_state','command_receipt','import_preview',
    'coordination_run','published_recommendation','private_original',
    'import_generation','import_job','alembic_version'];
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') OR
     NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
    RAISE EXCEPTION 'Expected Supabase client roles are absent';
  END IF;
  FOREACH name IN ARRAY expected LOOP
    IF to_regclass(format('public.%I',name)) IS NULL THEN
      RAISE EXCEPTION 'Expected Vela table is absent; review migration inventory';
    END IF;
  END LOOP;
  IF (SELECT array_agg(version_num::text) FROM public.alembic_version)
      IS DISTINCT FROM ARRAY['0003_import_jobs']::text[] THEN
    RAISE EXCEPTION 'Review this script against the actual migration head before use';
  END IF;
  FOREACH name IN ARRAY expected LOOP
    EXECUTE format('REVOKE ALL PRIVILEGES ON TABLE public.%I FROM PUBLIC, anon, authenticated',name);
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',name);
    IF has_table_privilege('anon',format('public.%I',name),'SELECT') OR
       has_table_privilege('anon',format('public.%I',name),'INSERT') OR
       has_table_privilege('anon',format('public.%I',name),'UPDATE') OR
       has_table_privilege('anon',format('public.%I',name),'DELETE') OR
       has_table_privilege('authenticated',format('public.%I',name),'SELECT') OR
       has_table_privilege('authenticated',format('public.%I',name),'INSERT') OR
       has_table_privilege('authenticated',format('public.%I',name),'UPDATE') OR
       has_table_privilege('authenticated',format('public.%I',name),'DELETE') THEN
      RAISE EXCEPTION 'Inherited client privileges remain; review role grants';
    END IF;
  END LOOP;
END;
$vela$;
COMMIT;
-- Do not grant anon/authenticated direct access or use service credentials in UI.
-- Existing security-definer RPCs/role inheritance require a separate live review.

