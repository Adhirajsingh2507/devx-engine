-- ORBIT-TRUST 0005 — lock down RPC execute grants (doc 19 security acceptance).
--
-- WHY: 0003 revoked the write RPCs FROM public, but Supabase's default
-- privileges grant EXECUTE directly to the `anon` and `authenticated` roles.
-- `REVOKE ... FROM public` does not remove role-specific grants, so an
-- authenticated (incl. anonymous) browser user could call these SECURITY
-- DEFINER functions directly over PostgREST — forging p_actor and bypassing
-- RLS. The N2 acceptance harness caught this (SEC-9/SEC-10). Fix: revoke
-- EXECUTE from anon + authenticated explicitly. service_role keeps its grant
-- (the FastAPI path), which is the only role that should call these.

revoke execute on function _require_member(uuid, uuid, text)                    from anon, authenticated;
revoke execute on function create_demo_workspace(uuid, text, text)             from anon, authenticated;
revoke execute on function import_commit(uuid, uuid, bigint, jsonb, jsonb)     from anon, authenticated;
revoke execute on function save_review_action(uuid, uuid, uuid, bigint, text, text, uuid) from anon, authenticated;
revoke execute on function advance_demo_clock(uuid, uuid, timestamptz)         from anon, authenticated;

-- is_member(uuid) is the RLS read helper and MUST remain executable by
-- authenticated (RLS policies call it). Left intact on purpose.
