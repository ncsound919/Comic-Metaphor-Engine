import React from 'react';
import { motion } from 'framer-motion';
import type { ProtocolSummary } from '../../lib/api';

interface ProtocolGridProps {
  protocols: ProtocolSummary[];
  onSelect?: (protocol: ProtocolSummary) => void;
}

const TYPE_COLORS: Record<string, string> = {
  cosmic_entity: 'from-violet-500/40 to-indigo-500/20 text-violet-300',
  claremont_arc: 'from-emerald-500/40 to-teal-500/20 text-emerald-300',
  modern_xmen: 'from-sky-500/40 to-blue-500/20 text-sky-300',
  avengers_cosmic: 'from-red-500/40 to-rose-500/20 text-red-300',
  character_deep_dive: 'from-amber-500/40 to-orange-500/20 text-amber-300',
};

export const ProtocolGrid: React.FC<ProtocolGridProps> = ({ protocols, onSelect }) => {
  if (!protocols.length) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground">
        Loading the vault…
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="font-display text-2xl font-bold">The Vault</h2>
        <p className="text-sm text-muted-foreground">
          {protocols.length} comic protocols, each a reusable business and life lesson.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {protocols.map((p, i) => {
          const tint = TYPE_COLORS[p.protocol_type] ?? 'from-slate-500/40 to-slate-500/20 text-slate-300';
          return (
            <motion.div
              key={p.id}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ delay: (i % 6) * 0.05, duration: 0.35 }}
              className="glass group cursor-pointer overflow-hidden rounded-2xl p-5 transition hover:border-primary/50"
              onClick={() => onSelect?.(p)}
            >
              <div className={`mb-3 inline-flex rounded-lg bg-gradient-to-br px-2 py-1 text-[10px] font-semibold uppercase tracking-wider ${tint}`}>
                {p.protocol_type.replace(/_/g, ' ')}
              </div>
              <h3 className="font-display text-base font-semibold leading-snug">
                {p.archetype}
              </h3>
              <p className="mt-2 line-clamp-3 text-sm text-muted-foreground">{p.business_logic}</p>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {p.themes.slice(0, 3).map((theme) => (
                  <span key={theme} className="rounded-full bg-secondary/70 px-2 py-0.5 text-[10px] text-muted-foreground">
                    {theme}
                  </span>
                ))}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
