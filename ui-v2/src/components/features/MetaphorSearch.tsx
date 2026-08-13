import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useSearchStore } from '../../stores/searchStore';
import { useGenerationStore } from '../../stores/generationStore';

const FORMATS = [
  { value: 'podcast_monologue', label: 'Podcast' },
  { value: 'blog_post', label: 'Blog' },
  { value: 'marketing_email', label: 'Email' },
  { value: 'dialogue_script', label: 'Dialogue' },
];

const TONES = [
  { value: 'hopeful', label: 'Hopeful' },
  { value: 'gritty', label: 'Gritty' },
  { value: 'cautionary', label: 'Cautionary' },
  { value: 'comedic', label: 'Comedic' },
];

export const MetaphorSearch: React.FC = () => {
  const { query, setQuery, isSearching, search } = useSearchStore();
  const { isGenerating, generateLesson, generateNarrative, clear } = useGenerationStore();
  const [format, setFormat] = useState('podcast_monologue');
  const [tone, setTone] = useState('hopeful');
  const [mode, setMode] = useState<'lesson' | 'narrative'>('lesson');
  const [error, setError] = useState<string | null>(null);

  const busy = isSearching || isGenerating;

  const handlePrimary = useCallback(async () => {
    if (!query.trim() || busy) return;
    setError(null);
    clear();
    const trimmed = query.trim();
    if (mode === 'lesson') {
      await generateLesson(trimmed, format, tone);
    } else {
      await generateNarrative(trimmed, format, tone);
    }
  }, [query, format, tone, mode, busy, generateLesson, generateNarrative, clear]);

  const handleSearch = useCallback(async () => {
    if (!query.trim() || busy) return;
    setError(null);
    clear();
    const results = await search(query.trim());
    if (results.length === 0) {
      setError('No close matches — try generating a lesson instead.');
    }
  }, [query, busy, search, clear]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass rounded-2xl p-6 shadow-xl"
    >
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handlePrimary()}
            placeholder="Describe your challenge..."
            aria-label="Describe your challenge"
            name="challenge"
            className="flex-1 rounded-xl border border-input bg-background/60 px-4 py-3.5 text-base outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground"
          />
          <div className="flex gap-2">
            <button
              onClick={handleSearch}
              disabled={busy || !query.trim()}
              className="rounded-xl border border-border bg-secondary/60 px-5 py-3.5 text-sm font-medium transition hover:bg-secondary disabled:opacity-50"
            >
              Search
            </button>
            <button
              onClick={handlePrimary}
              disabled={busy || !query.trim()}
              className="rounded-xl bg-gradient-to-r from-primary to-accent px-6 py-3.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition hover:opacity-90 disabled:opacity-50"
            >
              {busy ? (isGenerating ? 'Generating…' : 'Searching…') : 'Generate'}
            </button>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Output</span>
            <div className="flex rounded-lg border border-input p-0.5">
              {(['lesson', 'narrative'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium capitalize transition ${
                    mode === m ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {m === 'lesson' ? 'Learn' : 'Story'}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Format</span>
            <div className="flex rounded-lg border border-input p-0.5 gap-0.5">
              {FORMATS.map((f) => (
                <button
                  key={f.value}
                  onClick={() => setFormat(f.value)}
                  className={`rounded-md px-2.5 py-1.5 text-xs transition ${
                    format === f.value ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Tone</span>
            <div className="flex rounded-lg border border-input p-0.5 gap-0.5">
              {TONES.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTone(t.value)}
                  className={`rounded-md px-2.5 py-1.5 text-xs transition ${
                    tone === t.value ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>
    </motion.div>
  );
};
