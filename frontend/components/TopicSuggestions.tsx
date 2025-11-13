"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";
import { Search, Sparkles } from "lucide-react";
import { TOPIC_CATEGORIES, type TopicCategory, type TopicSuggestion } from "../data/topics";

interface TopicSuggestionsProps {
  onSuggestionSelect: (prompt: string) => void;
  onAfterSelect?: () => void;
}

interface PreparedCategory extends TopicCategory {
  matches: number;
}

function matchScore(text: string, query: string): number {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) return 0;
  const haystack = text.toLowerCase();
  let score = 0;
  normalizedQuery
    .split(/\s+/)
    .filter(Boolean)
    .forEach((token) => {
      if (haystack.includes(token)) {
        score += 1;
      }
    });
  return score;
}

const iconMap: Record<string, string> = {
  "alert-triangle": "⚠️",
  heart: "❤️",
  activity: "🩺",
  shield: "🛡️",
  users: "👥",
};

export default function TopicSuggestions({ onSuggestionSelect, onAfterSelect }: TopicSuggestionsProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeCategoryId, setActiveCategoryId] = useState<string>(TOPIC_CATEGORIES[0]?.id ?? "");

  const { categories, suggestions } = useMemo(() => {
    const preparedCategories: PreparedCategory[] = TOPIC_CATEGORIES.map((category) => {
      const match = matchScore(`${category.title} ${category.description}`, searchTerm);
      return { ...category, matches: match };
    });

    preparedCategories.sort((a, b) => {
      if (a.matches === b.matches) {
        return a.title.localeCompare(b.title);
      }
      return b.matches - a.matches;
    });

    const baseCategory = preparedCategories.find((category) => category.id === activeCategoryId) ?? preparedCategories[0];
    const normalizedTerm = searchTerm.trim().toLowerCase();
    const flattenedSuggestions = (normalizedTerm
      ? preparedCategories
          .flatMap((category) =>
            category.suggestions.map((suggestion) => ({
              category,
              suggestion,
              score:
                matchScore(`${suggestion.prompt} ${(suggestion.tags ?? []).join(" ")}`, normalizedTerm) +
                matchScore(`${category.title} ${category.description}`, normalizedTerm) * 0.5,
            }))
          )
          .filter((item) => item.score > 0)
          .sort((a, b) => {
            if (b.score === a.score) {
              return a.suggestion.prompt.localeCompare(b.suggestion.prompt);
            }
            return b.score - a.score;
          })
          .slice(0, 12)
      : baseCategory.suggestions.map((suggestion) => ({
          category: baseCategory,
          suggestion,
          score: 0,
        })));

    return {
      categories: preparedCategories,
      suggestions: flattenedSuggestions,
    };
  }, [activeCategoryId, searchTerm]);

  const handleSelect = (item: TopicSuggestion) => {
    onSuggestionSelect(item.prompt);
    onAfterSelect?.();
  };

  return (
    <section className="space-y-4" aria-label="Topic suggestions">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.32em] text-pink-300/70">Browse topics</p>
        <h3 className="text-lg font-semibold text-white">Get started quickly</h3>
        <p className="text-sm text-slate-300">
          Explore popular questions or search for specific symptoms, conditions, or self-care goals.
        </p>
      </header>

      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
        <input
          type="search"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          placeholder="Search topics, e.g. headache, diabetes, stress"
          className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-10 py-2 text-sm text-slate-100 shadow-inner shadow-black/20 transition focus:border-pink-300/60 focus:outline-none focus:ring-4 focus:ring-pink-500/15"
          aria-label="Search care topics"
        />
      </div>

      <div className="flex flex-wrap gap-2" role="list">
        {categories.map((category) => {
          const isActive = category.id === activeCategoryId && !searchTerm;
          const fallbackIcon = iconMap[category.icon] ?? "✨";
          return (
            <button
              key={category.id}
              type="button"
              role="listitem"
              onClick={() => {
                setActiveCategoryId(category.id);
                setSearchTerm("");
              }}
              className={clsx(
                "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
                isActive
                  ? "border-pink-400/70 bg-pink-500/20 text-pink-100 focus-visible:outline-pink-300"
                  : "border-white/10 bg-slate-900/60 text-slate-200 hover:border-pink-300/50 hover:text-pink-100 focus-visible:outline-pink-200"
              )}
            >
              <span aria-hidden>{fallbackIcon}</span>
              {category.title}
            </button>
          );
        })}
      </div>

      <div className="space-y-3" role="list">
        {suggestions.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 text-sm text-slate-300">
            No quick prompts found. Try a different keyword like "cough" or "nutrition".
          </div>
        ) : (
          suggestions.map(({ category, suggestion }) => (
            <article
              key={suggestion.id}
              role="listitem"
              className="group relative overflow-hidden rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-sm text-slate-100 shadow-[0_18px_45px_rgba(15,23,42,0.45)] transition hover:border-pink-400/40 hover:text-white"
            >
              <div className="flex items-start gap-3">
                <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-pink-500 via-fuchsia-500 to-purple-500 text-base">
                  {iconMap[category.icon] ?? "✨"}
                </span>
                <div className="flex-1 space-y-1">
                  <p className="text-xs uppercase tracking-[0.28em] text-pink-300/70">
                    {category.title}
                  </p>
                  <p className="font-semibold text-slate-100">{suggestion.prompt}</p>
                  {suggestion.tags && suggestion.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1 text-[0.7rem] text-pink-200/80">
                      {suggestion.tags.map((tag) => (
                        <span key={tag} className="rounded-full border border-pink-200/30 px-2 py-0.5">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleSelect(suggestion)}
                className="mt-3 inline-flex items-center gap-2 rounded-full border border-transparent bg-gradient-to-r from-pink-500 via-fuchsia-500 to-purple-500 px-3 py-1.5 text-xs font-semibold text-white shadow-[0_10px_30px_rgba(236,72,153,0.35)] transition hover:scale-[1.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
              >
                <Sparkles className="h-3.5 w-3.5" aria-hidden />
                Ask this
              </button>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
