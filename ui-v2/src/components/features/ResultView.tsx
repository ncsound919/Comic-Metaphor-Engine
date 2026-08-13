import React from 'react';
import { motion } from 'framer-motion';
import type { GenerationResult } from '../../stores/generationStore';

interface ResultViewProps {
  result: GenerationResult;
  onBack: () => void;
}

const ToneBadge: Record<string, string> = {
  hopeful: 'text-emerald-300 bg-emerald-500/10',
  gritty: 'text-orange-300 bg-orange-500/10',
  cautionary: 'text-amber-300 bg-amber-500/10',
  comedic: 'text-fuchsia-300 bg-fuchsia-500/10',
  inspirational: 'text-sky-300 bg-sky-500/10',
  dark: 'text-red-300 bg-red-500/10',
  philosophical: 'text-violet-300 bg-violet-500/10',
};

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{Math.round(value * 100)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

export const ResultView: React.FC<ResultViewProps> = ({ result, onBack }) => {
  const { mapping, lesson, narrative } = result;
  const toneClass = ToneBadge[mapping.target_tone] ?? ToneBadge.hopeful;

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <button
        onClick={onBack}
        className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground transition hover:text-foreground"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
        Back
      </button>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="glass rounded-2xl p-8">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className={`rounded-full px-2.5 py-1 font-medium ${toneClass}`}>{mapping.target_tone}</span>
            <span className="rounded-full bg-secondary px-2.5 py-1 text-muted-foreground">
              {mapping.target_format.replace(/_/g, ' ')}
            </span>
            <span className="rounded-full bg-secondary px-2.5 py-1 text-muted-foreground">
              {mapping.protocol_id.replace(/^protocol_/, 'protocol: ')}
            </span>
          </div>
          <h1 className="mt-4 font-display text-3xl sm:text-4xl font-bold leading-tight">
            {lesson?.title ?? mapping.topic}
          </h1>
          <p className="mt-3 text-muted-foreground">
            {lesson?.hook ?? mapping.core_tension}
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Lesson / narrative column */}
          <div className="lg:col-span-2 space-y-6">
            {(lesson || narrative) && (
              <div className="glass rounded-2xl p-8 space-y-6">
                {lesson?.story && (
                  <section>
                    <h2 className="font-display text-lg font-semibold mb-2">The Story</h2>
                    <p className="text-sm leading-relaxed text-muted-foreground">{lesson.story}</p>
                  </section>
                )}
                {lesson?.translation && (
                  <section>
                    <h2 className="font-display text-lg font-semibold mb-2">Translated to Your World</h2>
                    <p className="text-sm leading-relaxed text-muted-foreground">{lesson.translation}</p>
                  </section>
                )}
                {lesson && lesson.takeaways.length > 0 && (
                  <section>
                    <h2 className="font-display text-lg font-semibold mb-2">Takeaways</h2>
                    <ul className="space-y-2">
                      {lesson.takeaways.map((t, i) => (
                        <li key={i} className="flex gap-2 text-sm">
                          <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                          {t}
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
                {lesson && lesson.actions.length > 0 && (
                  <section>
                    <h2 className="font-display text-lg font-semibold mb-2">Try This This Week</h2>
                    <div className="space-y-2">
                      {lesson.actions.map((a, i) => (
                        <div key={i} className="flex gap-3 rounded-xl border border-border/70 p-3 text-sm">
                          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/15 font-mono text-xs text-primary">
                            {i + 1}
                          </span>
                          {a}
                        </div>
                      ))}
                    </div>
                  </section>
                )}
                {narrative && (
                  <section>
                    <h2 className="font-display text-lg font-semibold mb-2">
                      Your Story · {narrative.word_count} words
                    </h2>
                    <div className="max-h-[28rem] overflow-y-auto rounded-xl bg-background/50 p-5 font-mono text-[13px] leading-relaxed whitespace-pre-wrap">
                      {narrative.content}
                    </div>
                  </section>
                )}
              </div>
            )}

            {/* Core tension */}
            <div className="glass rounded-2xl p-8">
              <h2 className="font-display text-lg font-semibold mb-3">The Core Tension</h2>
              <p className="text-sm leading-relaxed text-muted-foreground">{mapping.core_tension}</p>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {mapping.mappings.map((m, i) => (
                  <div key={i} className="rounded-xl border border-border/70 p-3 text-sm">
                    <div className="text-xs text-muted-foreground">{m.real_world}</div>
                    <div className="font-medium text-primary">{m.comic_analog}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Scores column */}
          <div className="space-y-6">
            <div className="glass rounded-2xl p-6">
              <h2 className="font-display text-lg font-semibold mb-4">Fit Score</h2>
              <div className="space-y-4">
                <ScoreBar label="Trueness" value={mapping.trueness_score} />
                <ScoreBar label="Flow" value={mapping.flow_score} />
                <ScoreBar label="Precision (PCS)" value={mapping.pcs_score} />
                <ScoreBar label="TAP" value={mapping.tap_score} />
              </div>
              <div className="mt-5 rounded-xl bg-gradient-to-br from-primary/15 to-accent/10 p-4 text-center">
                <div className="text-xs text-muted-foreground">Overall Fit</div>
                <div className="font-display text-3xl font-bold text-gradient">
                  {Math.round(mapping.overall_fit * 100)}
                </div>
              </div>
            </div>

            <div className="glass rounded-2xl p-6">
              <h2 className="font-display text-lg font-semibold mb-3">Story Arc</h2>
              <ol className="space-y-2">
                {mapping.beat_structure.map((beat, i) => (
                  <li key={i} className="flex gap-3 text-sm text-muted-foreground">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-secondary font-mono text-[10px] text-primary">
                      {i + 1}
                    </span>
                    {beat}
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
