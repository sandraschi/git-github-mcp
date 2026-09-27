import {
  CheckCircle2,
  ExternalLink,
  Loader2,
  Lock,
  LockOpen,
  Megaphone,
  MessagesSquare,
  Plus,
  RefreshCw,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { githubOps } from "@/lib/api";

interface Category {
  id: string;
  name: string;
  slug: string;
  emoji: string;
  description?: string;
}

interface Discussion {
  number: number;
  title: string;
  url: string;
  createdAt: string;
  locked: boolean;
  isAnswered: boolean | null;
  upvotes: number;
  comments: number;
  category: string;
  author: string;
}

interface Comment {
  id: string;
  author: string;
  body: string;
  createdAt: string;
  isAnswer: boolean;
  upvotes: number;
}

interface DiscussionDetail extends Discussion {
  id: string;
  body: string;
  comments_total: number;
  comments_list: Comment[];
}

export function Discussions() {
  const [params] = useSearchParams();
  const [owner, setOwner] = useState(params.get("owner") ?? "sandraschi");
  const [repo, setRepo] = useState(params.get("repo") ?? "freecad-mcp");
  const [categories, setCategories] = useState<Category[]>([]);
  const [catFilter, setCatFilter] = useState<string>("");
  const [answeredOnly, setAnsweredOnly] = useState(false);
  const [discussions, setDiscussions] = useState<Discussion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<DiscussionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newCat, setNewCat] = useState("general");
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [commentBody, setCommentBody] = useState("");

  const fetchList = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.allSettled([
      (
        githubOps("discussion_categories", { owner, repo }) as Promise<{
          success: boolean;
          result?: { categories: Category[] };
        }>
      ).then((d) => {
        if (d.success) setCategories(d.result?.categories ?? []);
      }),
      (
        githubOps("discussion_list", {
          owner,
          repo,
          category: catFilter || undefined,
          answered_only: answeredOnly,
          limit: 30,
        }) as Promise<{
          success: boolean;
          result?: { discussions: Discussion[] };
          error?: string;
        }>
      ).then((d) => {
        if (d.success) setDiscussions(d.result?.discussions ?? []);
        else setError(d.error ?? "Failed");
      }),
    ])
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [owner, repo, catFilter, answeredOnly]);

  useEffect(fetchList, [fetchList]);

  const fetchDetail = useCallback(
    (num: number) => {
      setSelected(num);
      setDetailLoading(true);
      (
        githubOps("discussion_view", {
          owner,
          repo,
          discussion_number: num,
          limit: 50,
        }) as Promise<{
          success: boolean;
          result?: DiscussionDetail & { comments: Comment[] };
          error?: string;
        }>
      )
        .then((d) => {
          if (d.success && d.result) {
            setDetail({
              ...d.result,
              comments_list: d.result.comments ?? [],
            });
          } else setError(d.error ?? "Failed");
        })
        .catch((e) => setError(String(e)))
        .finally(() => setDetailLoading(false));
    },
    [owner, repo],
  );

  const createDiscussion = async () => {
    if (!newTitle.trim() || !newBody.trim()) return;
    setCreating(false);
    await githubOps("discussion_create", {
      owner,
      repo,
      category: newCat,
      title: newTitle,
      body: newBody,
    });
    setNewTitle("");
    setNewBody("");
    fetchList();
  };

  const postComment = async () => {
    if (!selected || !commentBody.trim()) return;
    await githubOps("discussion_comment", {
      owner,
      repo,
      discussion_number: selected,
      body: commentBody,
    });
    setCommentBody("");
    fetchDetail(selected);
    fetchList();
  };

  const toggleLock = async () => {
    if (!selected || !detail) return;
    await githubOps(detail.locked ? "discussion_unlock" : "discussion_lock", {
      owner,
      repo,
      discussion_number: selected,
    });
    fetchDetail(selected);
    fetchList();
  };

  const markAnswer = async (commentId: string, answered: boolean) => {
    if (!selected) return;
    await githubOps("discussion_answer", {
      owner,
      repo,
      comment_id: commentId,
      answered,
    });
    fetchDetail(selected);
  };

  return (
    <div className="space-y-4 max-w-4xl" data-testid="discussions-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessagesSquare size={20} style={{ color: "var(--blue)" }} />
          Discussions
        </h1>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setCreating((c) => !c)}
            data-testid="new-discussion"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{
              background: creating ? "var(--bg-3)" : "var(--green)",
              color: creating ? "var(--text-muted)" : "#000",
              border: "1px solid var(--green-dim)",
            }}
          >
            {creating ? <X size={12} /> : <Plus size={12} />}{" "}
            {creating ? "Cancel" : "New Discussion"}
          </button>
          <button
            type="button"
            onClick={fetchList}
            className="p-1.5 rounded"
            style={{
              border: "1px solid var(--border)",
              color: "var(--text-muted)",
            }}
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Repo selector */}
      <div className="flex items-center gap-2">
        <input
          className="mono text-xs px-3 py-1.5 rounded outline-none w-36"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text)",
          }}
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
          placeholder="owner"
        />
        <span style={{ color: "var(--text-dim)" }}>/</span>
        <input
          className="mono text-xs px-3 py-1.5 rounded outline-none flex-1"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text)",
          }}
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          placeholder="repo"
        />
        <button
          type="button"
          onClick={() => setAnsweredOnly((v) => !v)}
          title="Q&A with chosen answers only"
          className="px-3 py-1.5 rounded text-xs transition-colors"
          style={{
            background: answeredOnly ? "var(--bg-3)" : "transparent",
            color: answeredOnly ? "var(--text)" : "var(--text-dim)",
            border: "1px solid var(--border)",
          }}
        >
          answered
        </button>
      </div>

      {/* Category chips */}
      {categories.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={() => setCatFilter("")}
            className="px-2.5 py-1 rounded text-xs mono transition-colors"
            style={{
              background: catFilter === "" ? "var(--bg-3)" : "transparent",
              color: catFilter === "" ? "var(--text)" : "var(--text-dim)",
              border: "1px solid var(--border)",
            }}
          >
            all
          </button>
          {categories.map((c) => (
            <button
              type="button"
              key={c.slug}
              onClick={() => setCatFilter(c.slug)}
              className="px-2.5 py-1 rounded text-xs mono transition-colors"
              style={{
                background:
                  catFilter === c.slug ? "var(--bg-3)" : "transparent",
                color: catFilter === c.slug ? "var(--text)" : "var(--text-dim)",
                border: "1px solid var(--border)",
              }}
            >
              {c.slug}
            </button>
          ))}
        </div>
      )}

      {/* Create form */}
      {creating && (
        <div
          className="rounded p-4 space-y-3"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border-2)",
          }}
        >
          <div className="flex items-center gap-2">
            <select
              value={newCat}
              onChange={(e) => setNewCat(e.target.value)}
              className="mono text-xs px-2 py-1.5 rounded outline-none"
              style={{
                background: "var(--bg-3)",
                border: "1px solid var(--border)",
                color: "var(--text)",
              }}
            >
              {(categories.length > 0
                ? categories
                : [{ slug: "general" }, { slug: "ideas" }, { slug: "q-a" }]
              ).map((c) => (
                <option key={c.slug} value={c.slug}>
                  {c.slug}
                </option>
              ))}
            </select>
            <input
              className="flex-1 bg-transparent outline-none text-sm"
              style={{
                borderBottom: "1px solid var(--border)",
                paddingBottom: 6,
                color: "var(--text)",
              }}
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Discussion title..."
            />
          </div>
          <textarea
            className="w-full bg-transparent outline-none text-xs mono resize-none"
            rows={4}
            style={{ color: "var(--text-muted)" }}
            value={newBody}
            onChange={(e) => setNewBody(e.target.value)}
            placeholder="Body (markdown)..."
          />
          <button
            type="button"
            onClick={createDiscussion}
            data-testid="submit-discussion"
            className="px-4 py-1.5 rounded text-xs font-bold"
            style={{ background: "var(--green)", color: "#000" }}
          >
            Post Discussion
          </button>
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2
            className="animate-spin"
            size={20}
            style={{ color: "var(--green)" }}
          />
        </div>
      ) : error ? (
        <div
          className="p-6 text-center mono text-sm rounded"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--amber)",
          }}
        >
          {error} — ensure gh is authed and Discussions are enabled on this repo
        </div>
      ) : (
        <div
          className="rounded overflow-hidden"
          style={{ border: "1px solid var(--border)" }}
        >
          {discussions.length === 0 ? (
            <div
              className="p-8 text-center text-sm"
              style={{ color: "var(--text-dim)" }}
            >
              No discussions
              {catFilter ? ` in ${catFilter}` : ""} — start one above
            </div>
          ) : (
            discussions.map((d, i) => (
              <div key={d.number}>
                <button
                  type="button"
                  onClick={() =>
                    setSelected((s) => {
                      if (s === d.number) {
                        setDetail(null);
                        return null;
                      }
                      fetchDetail(d.number);
                      return d.number;
                    })
                  }
                  data-testid={`discussion-${d.number}`}
                  className="w-full flex items-start gap-3 px-4 py-3 hover:bg-white/[0.02] transition-colors text-left"
                  style={{
                    borderBottom:
                      i < discussions.length - 1 || selected === d.number
                        ? "1px solid var(--border)"
                        : "none",
                  }}
                >
                  {d.category === "announcements" ? (
                    <Megaphone
                      size={14}
                      className="mt-0.5 shrink-0"
                      style={{ color: "var(--amber)" }}
                    />
                  ) : (
                    <MessagesSquare
                      size={14}
                      className="mt-0.5 shrink-0"
                      style={{ color: "var(--blue)" }}
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <span
                      className="text-sm font-medium truncate block"
                      style={{ color: "var(--text)" }}
                    >
                      {d.title}
                    </span>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <span
                        className="mono text-xs"
                        style={{ color: "var(--text-dim)" }}
                      >
                        #{d.number}
                      </span>
                      <span
                        className="mono text-xs px-1.5 py-0.5 rounded"
                        style={{
                          background: "var(--bg-3)",
                          color: "var(--text-muted)",
                          border: "1px solid var(--border)",
                        }}
                      >
                        {d.category}
                      </span>
                      {d.locked && (
                        <Lock size={10} style={{ color: "var(--amber)" }} />
                      )}
                      {d.isAnswered && (
                        <CheckCircle2
                          size={11}
                          style={{ color: "var(--green)" }}
                        />
                      )}
                      <span
                        className="text-xs"
                        style={{ color: "var(--text-dim)" }}
                      >
                        {d.author} · {d.comments} comments ·{" "}
                        {new Date(d.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <a
                    href={d.url}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="shrink-0"
                  >
                    <ExternalLink
                      size={12}
                      style={{ color: "var(--text-dim)" }}
                    />
                  </a>
                </button>

                {/* Expanded detail */}
                {selected === d.number && (
                  <div
                    className="px-4 py-3 space-y-3"
                    style={{
                      background: "var(--bg-2)",
                      borderBottom:
                        i < discussions.length - 1
                          ? "1px solid var(--border)"
                          : "none",
                    }}
                    data-testid={`discussion-detail-${d.number}`}
                  >
                    {detailLoading || !detail ? (
                      <div className="flex justify-center py-6">
                        <Loader2
                          className="animate-spin"
                          size={16}
                          style={{ color: "var(--green)" }}
                        />
                      </div>
                    ) : (
                      <>
                        <p
                          className="text-xs whitespace-pre-wrap"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {detail.body?.slice(0, 1200)}
                          {(detail.body?.length ?? 0) > 1200 ? "…" : ""}
                        </p>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={toggleLock}
                            className="flex items-center gap-1 px-2.5 py-1 rounded text-xs mono transition-colors"
                            style={{
                              border: "1px solid var(--border)",
                              color: "var(--text-dim)",
                            }}
                          >
                            {detail.locked ? (
                              <>
                                <LockOpen size={11} /> unlock
                              </>
                            ) : (
                              <>
                                <Lock size={11} /> lock
                              </>
                            )}
                          </button>
                          <span
                            className="mono text-xs"
                            style={{ color: "var(--text-dim)" }}
                          >
                            {detail.comments_total} comments
                          </span>
                        </div>
                        {detail.comments_list.map((c) => (
                          <div
                            key={c.id}
                            className="rounded p-3 space-y-1.5"
                            style={{
                              background: "var(--bg-3)",
                              border: c.isAnswer
                                ? "1px solid var(--green-dim)"
                                : "1px solid var(--border)",
                            }}
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className="mono text-xs font-semibold"
                                style={{ color: "var(--text)" }}
                              >
                                {c.author}
                              </span>
                              {c.isAnswer && (
                                <span
                                  className="mono text-[10px] px-1.5 py-0.5 rounded"
                                  style={{
                                    background: "var(--green-dim)",
                                    color: "var(--green)",
                                  }}
                                >
                                  answer
                                </span>
                              )}
                              <span
                                className="mono text-[10px] ml-auto"
                                style={{ color: "var(--text-dim)" }}
                              >
                                {new Date(c.createdAt).toLocaleDateString()}
                              </span>
                              {detail.category === "q-a" && !detail.locked && (
                                <button
                                  type="button"
                                  onClick={() => markAnswer(c.id, !c.isAnswer)}
                                  className="mono text-[10px] px-1.5 py-0.5 rounded transition-colors"
                                  style={{
                                    border: "1px solid var(--border)",
                                    color: "var(--text-dim)",
                                  }}
                                >
                                  {c.isAnswer ? "unmark" : "mark answer"}
                                </button>
                              )}
                            </div>
                            <p
                              className="text-xs whitespace-pre-wrap"
                              style={{ color: "var(--text-muted)" }}
                            >
                              {c.body?.slice(0, 800)}
                            </p>
                          </div>
                        ))}
                        {!detail.locked && (
                          <div className="flex items-center gap-2">
                            <input
                              className="flex-1 bg-transparent mono text-xs px-3 py-1.5 rounded outline-none"
                              style={{
                                border: "1px solid var(--border)",
                                color: "var(--text)",
                              }}
                              value={commentBody}
                              onChange={(e) => setCommentBody(e.target.value)}
                              onKeyDown={(e) =>
                                e.key === "Enter" && postComment()
                              }
                              placeholder="Write a comment..."
                            />
                            <button
                              type="button"
                              onClick={postComment}
                              className="px-3 py-1.5 rounded text-xs font-bold"
                              style={{
                                background: "var(--green)",
                                color: "#000",
                              }}
                            >
                              Reply
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
