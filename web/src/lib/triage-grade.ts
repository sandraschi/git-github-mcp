/**
 * Rule-based triage grading for GitHub issues and PRs.
 *
 * Pure functions, no network, no LLM - deterministic first pass so the
 * triage page works with zero local model configured. An LLM re-grade can
 * layer on top later; the grade contract (A/B/C/D + plan + reply) stays.
 *
 * Scale:
 *   A - detailed report (repro + env + logs, sometimes root cause + fix)
 *   B - usable report (real problem, something missing)
 *   C - thin report (a sentence, no repro, no env)
 *   D - this stinks (spam, empty, or abusive - close, no engagement)
 */

export type TriageGrade = "A" | "B" | "C" | "D";

export interface TriageAssessment {
  grade: TriageGrade;
  gradeLabel: string;
  signals: string[];
  plan: string;
  suggestedReply: string;
}

export type TriageBucket = "needs_reply" | "stale";

const ABUSIVE = [
  "fuck yourself",
  "piece of shit",
  "fucking fake",
  "fuck you",
  "moron",
  "idiot",
  "retard",
  "kill yourself",
];

const REPRO_RE =
  /reproduc|steps to reproduce|expected behavior|actual behavior|steps:/i;
const ENV_RE =
  /\b(windows|linux|macos|ubuntu|debian|arch)\b|\bpython\s?3\b|\bv?\d+\.\d+(\.\d+)?\b|environment|installed via|fresh clone/i;
const LOG_RE =
  /traceback|```|error:|exception|stderr|warning:|failed to|exit code|^\s*at\s+\S+\s*\(/im;
const CAUSE_RE =
  /root cause|suggested fix|workaround|caused by|because |the problem is/i;
const TITLE_ONLY_NOISE_RE = /^(test|asdf|xxx+|hi+|hello+|help+!?|\?+|\.+)$/i;

export const GRADE_LABEL: Record<TriageGrade, string> = {
  A: "Detailed report",
  B: "Usable report",
  C: "Thin report",
  D: "This stinks",
};

export function gradeBody(
  title: string,
  body: string,
): {
  grade: TriageGrade;
  signals: string[];
} {
  const text = `${title}\n${body}`;
  const lower = text.toLowerCase();
  const trimmed = body.trim();
  const signals: string[] = [];

  if (ABUSIVE.some((w) => lower.includes(w))) {
    signals.push("abusive language");
    return { grade: "D", signals };
  }
  if (trimmed.length < 30 || TITLE_ONLY_NOISE_RE.test(title.trim())) {
    signals.push(trimmed.length === 0 ? "empty body" : "near-empty body");
    return { grade: "D", signals };
  }

  if (REPRO_RE.test(text)) signals.push("repro steps");
  if (ENV_RE.test(text)) signals.push("env/version info");
  if (LOG_RE.test(text)) signals.push("logs or code");
  if (CAUSE_RE.test(text)) signals.push("cause/fix analysis");

  const substantive = trimmed.length >= 300;
  if (substantive) signals.push("substantive write-up");

  const rich =
    signals.includes("logs or code") &&
    (signals.includes("env/version info") || signals.includes("repro steps"));
  if (substantive && rich) return { grade: "A", signals };
  if (signals.length >= 2 || substantive) return { grade: "B", signals };
  if (signals.length >= 1 || trimmed.length >= 100)
    return { grade: "B", signals };
  return { grade: "C", signals: ["no repro, no env, no logs"] };
}

const ACK_A = (slug: string, n: number) =>
  `Thanks for the report - and sorry for the slow reply.\n\nI've read it properly now. The detail (repro + env + analysis) is exactly what makes this actionable. I'm triaging it to a fix in ${slug} and will update #${n} once it's on master.`;

const ACK_ASK_INFO = (slug: string, n: number) =>
  `Thanks for reporting this - and sorry for the slow reply.\n\nThis looks real, but I'm missing what I need to reproduce it in ${slug}. Could you add:\n1. Minimal repro steps (commands or clicks, in order)\n2. Environment (OS, relevant versions)\n3. The exact error text or log tail\n\nI'll pick #${n} back up as soon as that's here.`;

const CLOSE_SUPERSEDED = (slug: string, n: number) =>
  `Sorry for the very late response - this sat far too long without a maintainer reply, that's on us.\n\nI checked current master of ${slug} and this no longer applies as filed. Closing #${n} as superseded. If you still reproduce on a current checkout, please reopen with version + logs and I'll pick it up promptly.`;

const CLOSE_NOISE = (n: number) =>
  `Closing #${n}: no actionable content. If you have a concrete repro (steps + environment + error text), please open a fresh issue and I'll look at it.`;

const ACK_PR = (slug: string, n: number) =>
  `Thanks for the PR - and sorry for the slow review. I maintain ${slug} in spare time and don't always see notifications quickly.\n\nI've read #${n} and will review properly within the next few days; I'll comment here if I need changes.`;

export function planFor(
  bucket: TriageBucket,
  kind: "issue" | "pr",
  grade: TriageGrade,
  slug: string,
  n: number,
): { plan: string; suggestedReply: string } {
  if (grade === "D") {
    return {
      plan: "Close with the noise template, no engagement.",
      suggestedReply: CLOSE_NOISE(n),
    };
  }
  if (bucket === "stale") {
    return {
      plan: "Verify on master first; close as superseded with apology if fixed, else re-triage.",
      suggestedReply: CLOSE_SUPERSEDED(slug, n),
    };
  }
  if (kind === "pr") {
    return {
      plan: "Ack today, review within days.",
      suggestedReply: ACK_PR(slug, n),
    };
  }
  if (grade === "A") {
    return {
      plan: "Ack today, triage to fix.",
      suggestedReply: ACK_A(slug, n),
    };
  }
  return {
    plan: "Ack + ask for missing repro/env.",
    suggestedReply: ACK_ASK_INFO(slug, n),
  };
}

export function assess(
  bucket: TriageBucket,
  kind: "issue" | "pr",
  title: string,
  body: string,
  slug: string,
  n: number,
): TriageAssessment {
  const { grade, signals } = gradeBody(title, body);
  const { plan, suggestedReply } = planFor(bucket, kind, grade, slug, n);
  return {
    grade,
    gradeLabel: GRADE_LABEL[grade],
    signals,
    plan,
    suggestedReply,
  };
}
