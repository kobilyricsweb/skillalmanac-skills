import { useEffect, useId, useRef, useState } from 'react';
import type { ClipboardEvent, FormEvent, KeyboardEvent } from 'react';

export interface InviteMembersProps {
  teamId: string;
}

export interface PendingInvite {
  id: string;
  email: string;
  sentAt: string;
}

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready' };

type SendState =
  | { status: 'idle' }
  | { status: 'sending' }
  | { status: 'sent'; count: number }
  | { status: 'error'; message: string };

interface ParseResult {
  valid: string[];
  invalid: string[];
  duplicate: string[];
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const SEPARATOR_PATTERN = /[\s,;]+/;
const SEPARATOR_KEYS = new Set([',', ';']);

export function isValidEmail(value: string): boolean {
  return value.length <= 254 && EMAIL_PATTERN.test(value);
}

function isPendingInviteList(value: unknown): value is PendingInvite[] {
  return (
    Array.isArray(value) &&
    value.every((item) => {
      if (typeof item !== 'object' || item === null) return false;
      const record = item as Record<string, unknown>;
      return (
        typeof record.id === 'string' &&
        typeof record.email === 'string' &&
        typeof record.sentAt === 'string'
      );
    })
  );
}

// Splits free text into addresses and sorts them. `known` holds lowercase
// addresses that are already chips or already invited; duplicates are compared
// case-insensitively and each address is counted once per call.
function parseCandidates(text: string, known: ReadonlySet<string>): ParseResult {
  const result: ParseResult = { valid: [], invalid: [], duplicate: [] };
  const seen = new Set(known);
  for (const token of text.split(SEPARATOR_PATTERN)) {
    if (token === '') continue;
    if (!isValidEmail(token)) {
      result.invalid.push(token);
      continue;
    }
    const key = token.toLowerCase();
    if (seen.has(key)) {
      result.duplicate.push(token);
      continue;
    }
    seen.add(key);
    result.valid.push(token);
  }
  return result;
}

function describeProblems(result: ParseResult): string | null {
  const parts: string[] = [];
  if (result.invalid.length > 0) {
    parts.push(`Not a valid email address: ${result.invalid.join(', ')}.`);
  }
  if (result.duplicate.length > 0) {
    parts.push(`Already added or invited: ${result.duplicate.join(', ')}.`);
  }
  return parts.length > 0 ? parts.join(' ') : null;
}

function formatSentAt(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleDateString(undefined, { dateStyle: 'medium' });
}

export function InviteMembers({ teamId }: InviteMembersProps) {
  // Keyed by teamId: a team change remounts the form, so chips, the draft,
  // status messages and in-flight requests from the old team are discarded.
  return <InviteMembersForTeam key={teamId} teamId={teamId} />;
}

function InviteMembersForTeam({ teamId }: InviteMembersProps) {
  const headingId = useId();
  const pendingHeadingId = useId();
  const inputId = useId();
  const hintId = useId();
  const errorId = useId();

  const inputRef = useRef<HTMLInputElement>(null);
  const sendControllerRef = useRef<AbortController | null>(null);

  const [invites, setInvites] = useState<PendingInvite[]>([]);
  const [loadState, setLoadState] = useState<LoadState>({ status: 'loading' });
  const [reloadToken, setReloadToken] = useState(0);
  const [chips, setChips] = useState<string[]>([]);
  const [draft, setDraft] = useState('');
  const [draftError, setDraftError] = useState<string | null>(null);
  const [sendState, setSendState] = useState<SendState>({ status: 'idle' });

  // Load pending invites. The controller aborts the request when teamId changes
  // (or on unmount), so an older response can never overwrite a newer one.
  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const res = await fetch(`/api/invites?team=${encodeURIComponent(teamId)}`, {
          headers: { Accept: 'application/json' },
          signal: controller.signal,
        });
        if (!res.ok) {
          throw new Error(`Could not load pending invites (HTTP ${res.status}).`);
        }
        const data: unknown = await res.json();
        if (!isPendingInviteList(data)) {
          throw new Error('Pending invites came back in an unexpected format.');
        }
        setInvites(data);
        setLoadState({ status: 'ready' });
      } catch (err) {
        if (controller.signal.aborted) return;
        setLoadState({
          status: 'error',
          message: err instanceof Error ? err.message : 'Could not load pending invites.',
        });
      }
    }

    void load();
    return () => controller.abort();
  }, [teamId, reloadToken]);

  // Abort a send that is still running when the component unmounts.
  useEffect(() => {
    return () => sendControllerRef.current?.abort();
  }, []);

  function startReload() {
    setLoadState({ status: 'loading' });
    setReloadToken((token) => token + 1);
  }

  function knownEmails(): Set<string> {
    return new Set(
      [...chips, ...invites.map((invite) => invite.email)].map((email) => email.toLowerCase()),
    );
  }

  function applyParsed(result: ParseResult) {
    if (result.valid.length > 0) {
      setChips((previous) => [...previous, ...result.valid]);
    }
    // Invalid addresses stay in the input so the user can correct them.
    setDraft(result.invalid.join(', '));
    setDraftError(describeProblems(result));
  }

  function commitText(text: string) {
    applyParsed(parseCandidates(text, knownEmails()));
  }

  function removeChip(email: string) {
    setChips((previous) => previous.filter((chip) => chip !== email));
    inputRef.current?.focus();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (SEPARATOR_KEYS.has(event.key) || (event.key === 'Enter' && draft.trim() !== '')) {
      // Enter with an empty draft is left alone so it submits the form.
      event.preventDefault();
      commitText(draft);
      return;
    }
    if (event.key === 'Backspace' && draft === '' && chips.length > 0) {
      setChips((previous) => previous.slice(0, -1));
    }
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    const pasted = event.clipboardData.getData('text');
    // A single address pastes into the draft normally; a list is split into chips.
    if (!SEPARATOR_PATTERN.test(pasted.trim())) return;
    event.preventDefault();
    commitText(`${draft} ${pasted}`);
  }

  function handleBlur() {
    if (draft.trim() !== '') commitText(draft);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sendState.status === 'sending') return;

    const parsed = parseCandidates(draft, knownEmails());
    if (parsed.invalid.length > 0 || parsed.duplicate.length > 0) {
      // Show the problems first; the user confirms the cleaned list by sending again.
      applyParsed(parsed);
      return;
    }

    const emails = [...chips, ...parsed.valid];
    if (emails.length === 0) {
      setDraftError('Add at least one email address.');
      inputRef.current?.focus();
      return;
    }

    setChips(emails);
    setDraft('');
    setDraftError(null);
    setSendState({ status: 'sending' });

    const controller = new AbortController();
    sendControllerRef.current?.abort();
    sendControllerRef.current = controller;

    try {
      const res = await fetch('/api/invites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ teamId, emails }),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setChips([]);
      setSendState({ status: 'sent', count: emails.length });
      startReload();
    } catch {
      if (controller.signal.aborted) return;
      // The addresses stay as chips so the user can retry without retyping.
      setSendState({
        status: 'error',
        message: 'Invites were not sent. Your addresses are still listed, so you can try again.',
      });
    }
  }

  const sending = sendState.status === 'sending';
  const draftIsEmpty = draft.trim() === '';

  return (
    <section aria-labelledby={headingId} className="invite-members">
      <h2 id={headingId}>Invite members</h2>

      <form onSubmit={handleSubmit} noValidate aria-busy={sending}>
        <label htmlFor={inputId}>Email addresses</label>
        <p id={hintId}>
          Press Enter or comma, or paste a list, to add an address. Use a Remove button to take one
          off the list.
        </p>

        {chips.length > 0 && (
          <ul aria-label="Addresses to invite" className="invite-chips">
            {chips.map((email) => (
              <li key={email} className="invite-chip">
                <span>{email}</span>
                <button
                  type="button"
                  onClick={() => removeChip(email)}
                  aria-label={`Remove ${email}`}
                  disabled={sending}
                >
                  <span aria-hidden="true">×</span>
                </button>
              </li>
            ))}
          </ul>
        )}

        <input
          id={inputId}
          ref={inputRef}
          type="text"
          inputMode="email"
          autoComplete="off"
          spellCheck={false}
          placeholder="name@example.com"
          value={draft}
          onChange={(event) => {
            setDraft(event.target.value);
            setDraftError(null);
          }}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          onBlur={handleBlur}
          disabled={sending}
          aria-invalid={draftError !== null}
          aria-describedby={draftError ? `${hintId} ${errorId}` : hintId}
        />
        {draftError && (
          <p id={errorId} role="alert">
            {draftError}
          </p>
        )}

        <button type="submit" disabled={sending || (chips.length === 0 && draftIsEmpty)}>
          {sending ? 'Sending invites…' : 'Send invites'}
        </button>

        <div role="status" aria-live="polite">
          {sendState.status === 'sent' &&
            `Sent ${sendState.count} ${sendState.count === 1 ? 'invite' : 'invites'}.`}
        </div>
        {sendState.status === 'error' && <p role="alert">{sendState.message}</p>}
      </form>

      <section aria-labelledby={pendingHeadingId}>
        <h3 id={pendingHeadingId}>Pending invites</h3>

        {loadState.status === 'loading' && <p role="status">Loading pending invites…</p>}

        {loadState.status === 'error' && (
          <div role="alert">
            <p>{loadState.message}</p>
            <button type="button" onClick={startReload}>
              Try again
            </button>
          </div>
        )}

        {loadState.status === 'ready' && invites.length === 0 && (
          <p>No invites are pending for this team.</p>
        )}

        {loadState.status === 'ready' && invites.length > 0 && (
          <ul>
            {invites.map((invite) => (
              <li key={invite.id}>
                <span>{invite.email}</span> <time dateTime={invite.sentAt}>sent {formatSentAt(invite.sentAt)}</time>
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
