import React from 'react';
import { motion } from 'framer-motion';
import { useSearchStore } from '../../stores/searchStore';
import { useGenerationStore } from '../../stores/generationStore';

export const SearchResults: React.FC<{ onBackToBrowse?: () => void }> = ({ onBackToBrowse }) => {
  const { results, isSearching, lastSearched, clearResults } = useSearchStore();
  const { isGenerating, generateLesson } = useGenerationStore();

  if (isSearching) {
    return (
      <div className="mt-6 space-y-3">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="glass h-24 animate-pulse rounded-xl"
            style={{ animationDelay: `${i * 120}ms` }}
          />
        ))}
      </div>
    );
  }

  if (!lastSearched || results.length === 0) return null;

  return (
    <div className="mt-6">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Closest matches for <span className="font-medium text-foreground">"{lastSearched}"</span>
        </p>
        <button
          onClick={() => {
            clearResults();
            onBackToBrowse?.();
          }}
          className="text-xs text-muted-foreground underline-offset-2 hover:underline"
        >
          Clear
        </button>
      </div>
      <div className="space-y-3">
        {results.map((r, i) => (
          <motion.div
            key={r.protocol_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className="glass group flex flex-col sm:flex-row sm:items-center gap-3 rounded-xl p-4"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium uppercase tracking-wider text-primary">
                  {r.protocol_type.replace(/_/g, ' ')}
                </span>
                <span className="rounded bg-secondary px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                  {(r.similarity * 100).toFixed(0)}% match
                </span>
              </div>
              <h3 className="mt-1 truncate font-display text-base font-semibold">
                {r.archetype}
              </h3>
              <p className="mt-0.5 line-clamp-1 text-sm text-muted-foreground">{r.business_logic}</p>
            </div>
            <button
              onClick={() => generateLesson(lastSearched, 'podcast_monologue', 'hopeful')}
              disabled={isGenerating}
              className="shrink-0 rounded-lg border border-border px-3 py-2 text-xs font-medium transition hover:border-primary hover:text-primary disabled:opacity-50"
            >
              Turn into lesson
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
