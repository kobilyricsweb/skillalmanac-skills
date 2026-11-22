import {
  useEffect,
  useId,
  useRef,
  useState,
  type ClipboardEvent,
  type FormEvent,
  type KeyboardEvent,
} from "react";

export interface PendingInvite {
  id: string;
  email: string;
  sentAt: string;
}

export interface InviteMembersProps {
  teamId: string;
}

type LoadStatus = "loading" | "ready" | "error";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_EMAIL_LENGTH = 254;

function normalizeEmail(value: string): string {
  return value.trim().toLowerCase();
}

function isValidEmail(value: string): boolean {
  return value.length <= MAX_EMAIL_LENGTH && EMAIL_PATTERN.test(value);
}

function splitTokens(raw: string): string[] {
  return raw.split(/[\s,;]+/).filter((token) => token.length > 0);
}

interface BatchResult {
  valid: string[];
  invalid: string[];
  duplicates: string[];
}

/** Splits raw input into new valid emails, invalid tokens and duplicates. */
function parseBatch(raw: string, chips: string[], invites: PendingInvite[]): BatchResult {
  const seen = new Set<string>([
    ...chips,
    ...invites.map((invite) => normalizeEmail(invite.email)),
  ]);
  const result: BatchResult = { valid: [], invalid: [], duplicates: [] };

  for (const token of splitTokens(raw)) {
    const email = normalizeEmail(token);
    if (!isValidEmail(email)) {
      result.invalid.push(token);
    } else if (seen.has(email)) {
      result.duplicates.push(email);
    } else {
      seen.add(email);
      result.valid.push(email);
    }
  }
  return result;
}

function describeProblems({ invalid, duplicates }: BatchResult): string | null {
  const parts: string[] = [];
  if (invalid.length > 0) {
    parts.push(`Not valid email addresses: ${invalid.join(", ")}.`);
  }
  if (duplicates.length > 0) {
    parts.push(`Already added or invited: ${duplicates.join(", ")}.`);
  }
  return parts.length > 0 ? parts.join(" ") : null;
}

function formatSentAt(sentAt: string): string {
  const date = new Date(sentAt);
  return Number.isNaN(date.getTime()) ? sentAt : date.toLocaleString();
}

function messageOf(err: unknown): string {
  if (err instanceof Error && err.name !== "AbortError" && err.message) {
    return err.message;
  }
  return "Something went wrong. Please try again.";
}

async function fetchInvites(teamId: string, signal: AbortSignal): Promise<PendingInvite[]> {
  const res = await fetch(`/api/invites?team=${encodeURIComponent(teamId)}`, {
    signal,
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Could not load pending invites (status ${res.status}).`);
  }
  const data: unknown = await res.json();
  if (!Array.isArray(data)) {
    throw new Error("Unexpected response from the server.");
  }
  return data as PendingInvite[];
}

export default function InviteMembers({ teamId }: InviteMembersProps) {
  const uid = useId();
  const headingId = `${uid}-heading`;
  const formHeadingId = `${uid}-form-heading`;
  const inputId = `${uid}-email`;
  const hintId = `${uid}-hint`;
  const errorId = `${uid}-error`;

  const [invites, setInvites] = useState<PendingInvite[]>([]);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const [draft, setDraft] = useState("");
  const [chips, setChips] = useState<string[]>([]);
  const [inputError, setInputError] = useState<string | null>(null);

  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // Latest teamId, so async results from a previous team are ignored.
  const teamRef = useRef(teamId);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    teamRef.current = teamId;
  }, [teamId]);

  // Switching team clears everything that belonged to the previous team.
  useEffect(() => {
    setInvites([]);
    setChips([]);
    setDraft("");
    setInputError(null);
    setSendError(null);
    setNotice(null);
    setSending(false);
    setLoadError(null);
  }, [teamId]);

  // Load pending invites; aborted when the team changes or the effect re-runs.
  useEffect(() => {
    const controller = new AbortController();
    setLoadStatus("loading");
    setLoadError(null);

    fetchInvites(teamId, controller.signal)
      .then((list) => {
        if (controller.signal.aborted) return;
        setInvites(list);
        setLoadStatus("ready");
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setLoadError(messageOf(err));
        setLoadStatus("error");
      });

    return () => controller.abort();
  }, [teamId, reloadKey]);

  function applyAdd(raw: string) {
    const result = parseBatch(raw, chips, invites);
    if (result.valid.length > 0) {
      setChips((prev) => [...prev, ...result.valid]);
    }
    // Invalid tokens stay in the input so the user can correct them.
    setDraft(result.invalid.join(", "));
    setInputError(describeProblems(result));
    setNotice(null);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.nativeEvent.isComposing) return;
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      applyAdd(draft);
    } else if (event.key === "Backspace" && draft === "" && chips.length > 0) {
      setChips((prev) => prev.slice(0, -1));
    }
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    const text = event.clipboardData.getData("text");
    if (/[\s,;]/.test(text.trim())) {
      event.preventDefault();
      applyAdd(`${draft} ${text}`);
    }
  }

  function removeChip(email: string) {
    setChips((prev) => prev.filter((chip) => chip !== email));
    inputRef.current?.focus();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sending) return;

    const result = parseBatch(draft, chips, invites);
    const emails = [...chips, ...result.valid];
    const problems = describeProblems(result);

    if (result.valid.length > 0) setChips(emails);
    setDraft(result.invalid.join(", "));
    setNotice(null);

    if (result.invalid.length > 0) {
      setInputError(problems);
      return;
    }
    if (emails.length === 0) {
      setInputError(problems ?? "Add at least one email address before sending.");
      return;
    }
    setInputError(problems);

    const team = teamId;
    setSending(true);
    setSendError(null);
    try {
      const res = await fetch("/api/invites", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ teamId: team, emails }),
      });
      if (!res.ok) {
        throw new Error(`Could not send invites (status ${res.status}). Please try again.`);
      }
      if (teamRef.current !== team) return;
      setChips([]);
      setDraft("");
      setInputError(null);
      setNotice(`Invitations sent to ${emails.length} ${emails.length === 1 ? "person" : "people"}.`);
      setReloadKey((key) => key + 1);
    } catch (err) {
      if (teamRef.current !== team) return;
      setSendError(messageOf(err));
    } finally {
      if (teamRef.current === team) setSending(false);
    }
  }

  const inputDescribedBy = [hintId, inputError ? errorId : null].filter(Boolean).join(" ");

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId}>Team invites</h2>

      <h3>Pending invites</h3>
      {loadStatus === "error" && (
        <div role="alert">
          <p>{loadError}</p>
          <button type="button" onClick={() => setReloadKey((key) => key + 1)}>
            Try again
          </button>
        </div>
      )}
      {loadStatus === "loading" && invites.length === 0 && (
        <p role="status">Loading pending invites...</p>
      )}
      {loadStatus === "ready" && invites.length === 0 && (
        <p>No pending invites for this team.</p>
      )}
      {invites.length > 0 && (
        <ul aria-label="Pending invites">
          {invites.map((invite) => (
            <li key={invite.id}>
              <span>{invite.email}</span>{" "}
              <time dateTime={invite.sentAt}>Sent {formatSentAt(invite.sentAt)}</time>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} noValidate aria-labelledby={formHeadingId}>
        <h3 id={formHeadingId}>Invite new members</h3>

        <label htmlFor={inputId}>Email addresses</label>
        <p id={hintId}>
          Press Enter, a comma, or paste a list to add an address. Addresses can be separated by
          commas, spaces or new lines.
        </p>

        {chips.length > 0 && (
          <ul aria-label="Addresses to invite">
            {chips.map((email) => (
              <li key={email}>
                <span>{email}</span>{" "}
                <button
                  type="button"
                  onClick={() => removeChip(email)}
                  disabled={sending}
                  aria-label={`Remove ${email}`}
                >
                  <span aria-hidden="true">×</span>
                </button>
              </li>
            ))}
          </ul>
        )}

        <div>
          <input
            ref={inputRef}
            id={inputId}
            type="text"
            inputMode="email"
            autoComplete="off"
            spellCheck={false}
            value={draft}
            disabled={sending}
            aria-invalid={inputError ? true : undefined}
            aria-describedby={inputDescribedBy}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
          />{" "}
          <button
            type="button"
            onClick={() => applyAdd(draft)}
            disabled={sending || draft.trim() === ""}
          >
            Add
          </button>
        </div>

        {inputError && (
          <p id={errorId} role="alert">
            {inputError}
          </p>
        )}

        <button type="submit" disabled={sending || (chips.length === 0 && draft.trim() === "")}>
          {sending ? "Sending..." : "Send invites"}
        </button>

        <p role="status" aria-live="polite">
          {notice}
        </p>
        {sendError && <p role="alert">{sendError}</p>}
      </form>
    </section>
  );
}
