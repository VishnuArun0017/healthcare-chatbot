"use client";

import { memo, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import clsx from "clsx";

export type ChatRole = "user" | "assistant";

export interface Citation {
  source?: string;
  topic?: string;
  url?: string;
}

export interface ChatMessageModel {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  citations?: Citation[];
}

const roleStyles: Record<ChatRole, string> = {
  user:
    "border border-transparent bg-gradient-to-br from-fuchsia-500 via-pink-500 to-purple-500 text-white shadow-[0_22px_65px_rgba(236,72,153,0.35)]",
  assistant:
    "border border-white/10 bg-slate-900/70 backdrop-blur text-slate-100 shadow-[0_22px_65px_rgba(15,23,42,0.55)]",
};

const alignment: Record<ChatRole, string> = {
  user: "items-end justify-end",
  assistant: "items-start justify-start",
};

interface ChatMessageProps {
  message: ChatMessageModel;
  index: number;
}

function ChatMessage({ message, index }: ChatMessageProps) {
  const [formattedTime, setFormattedTime] = useState<string>("");

  useEffect(() => {
    try {
      const value = new Intl.DateTimeFormat("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      }).format(new Date(message.timestamp));
      setFormattedTime(value);
    } catch (error) {
      setFormattedTime(message.timestamp);
    }
  }, [message.timestamp]);

  return (
    <article
      className={clsx(
        "flex w-full",
        alignment[message.role],
        message.role === "assistant" ? "animate-fadeUp" : ""
      )}
      aria-live="polite"
      role="listitem"
      data-message-role={message.role}
      data-testid={`chat-message-${index}`}
    >
      <div
        className={clsx(
          "max-w-[90%] rounded-3xl px-5 py-4 md:px-6 md:py-5 transition-all outline-none focus-visible:ring-4 focus-visible:ring-pink-400/40",
          roleStyles[message.role]
        )}
        tabIndex={0}
      >
        <div
          className={clsx(
            "prose prose-sm md:prose-base max-w-none break-words",
            message.role === "user"
              ? "prose-invert text-white [&_a]:text-pink-200"
              : "prose-invert text-slate-100 [&_code]:rounded [&_code]:bg-white/10 [&_code]:px-1.5 [&_code]:py-0.5 [&_a]:text-pink-200 [&_a:hover]:text-pink-100"
          )}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              li: ({ children, ...props }) => (
                <li className="marker:text-ocean-500" {...props}>
                  {children}
                </li>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        <footer className="mt-4 flex flex-wrap items-center gap-3 text-xs uppercase tracking-wide text-white/70 md:text-[0.7rem]">
          <span
            className={clsx(
              "rounded-full border px-3 py-1",
              message.role === "assistant"
                ? "border-white/20 text-pink-200/80"
                : "border-white/40 text-white/80"
            )}
          >
            {message.role === "assistant" ? "Assistant" : "You"}
          </span>
          <time
            className={clsx(
              "font-medium",
              message.role === "assistant" ? "text-pink-200/70" : "text-white/70"
            )}
            dateTime={message.timestamp}
            suppressHydrationWarning
          >
            {formattedTime || ""}
          </time>
        </footer>

        {message.citations && message.citations.length > 0 && (
          <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-100 shadow-[0_18px_45px_rgba(15,23,42,0.55)]">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.32em] text-pink-200/80">
              Sources
            </p>
            <ul className="flex flex-wrap gap-2">
              {message.citations.map((citation, idx) => {
                const label = citation.topic
                  ? `${citation.topic}${citation.source ? ` (${citation.source})` : ""}`
                  : citation.source ?? `Source ${idx + 1}`;
                return (
                  <li key={`${citation.url ?? label}-${idx}`}>
                    {citation.url ? (
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-slate-900/80 px-3 py-1 text-xs font-semibold text-pink-200 transition hover:border-pink-300/60 hover:text-pink-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
                      >
                        {label}
                      </a>
                    ) : (
                      <span className="inline-flex items-center rounded-full border border-white/10 bg-slate-900/70 px-3 py-1 text-xs font-semibold text-slate-200">
                        {label}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    </article>
  );
}

export default memo(ChatMessage);

