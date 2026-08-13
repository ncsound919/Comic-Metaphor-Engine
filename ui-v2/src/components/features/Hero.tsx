import React from 'react';
import { motion } from 'framer-motion';

const EXEMPLARS = [
  'A sales team chasing volume instead of value',
  'Scaling without losing your culture',
  'When your AI tools start making decisions for you',
  'Impostor syndrome the week before the launch',
];

export const Hero: React.FC = () => {
  return (
    <section className="relative overflow-hidden">
      <div className="halftone absolute inset-0 opacity-40" />
      <motion.div
        className="relative mx-auto max-w-4xl px-6 pt-24 pb-14 text-center"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full glass px-4 py-1.5 text-xs font-medium text-muted-foreground"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
          61 comic protocols · 220 business lessons · every hero you know
        </motion.div>

        <h1 className="font-display text-4xl sm:text-6xl font-bold leading-[1.05] tracking-tight">
          Your problem is a <span className="text-gradient">storyline</span>.
          <br className="hidden sm:block" />
          Let's find its hero.
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
          Type any challenge — work, leadership, mental health, strategy — and the
          Comic Metaphor Engine will map it to a comic book arc, score the fit,
          and hand you a lesson you'll actually remember.
        </p>

        <div className="mx-auto mt-10 max-w-2xl">
          <motion.div
            className="flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            {EXEMPLARS.map((ex) => (
              <span key={ex} className="glass rounded-full px-3 py-1.5">
                {ex}
              </span>
            ))}
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
};
