import React, { useCallback, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../stores/authStore';
import { api, type Comic, type InsightReport } from '../../lib/api';
import { isActivePlan } from '../../lib/billing';
import { supabase } from '../../lib/supabase';
import type { AppView } from '../layout/Header';

const ACCEPT = '.pdf,.txt,.md,.epub,.cbz,.cbr,.cb7';
const MAX_BYTES = 25 * 1024 * 1024;

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round((value ?? 0) * 100);
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 shrink-0 text-xs text-muted-foreground">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6 }}
        />
      </div>
      <span className="w-10 shrink-0 text-right text-xs">{pct}%</span>
    </div>
  );
}

export const Upload: React.FC<{ onNavigate: (view: AppView) => void }> = ({ onNavigate }) => {
  const { user, refreshPlan } = useAuthStore();
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<InsightReport | null>(null);
  const [comics, setComics] = useState<Comic[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const paid = isActivePlan(user);

  const loadComics = useCallback(async () => {
    if (!supabase) return;
    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (!token) return;
      const data = await api.listComics(token);
      setComics(data.comics);
    } catch {
      /* list is best-effort */
    }
  }, []);

  useEffect(() => {
    if (user) {
      refreshPlan();
      loadComics();
    }
  }, [user, refreshPlan, loadComics]);

  const submit = useCallback(async () => {
    if (!file) return;
    if (!supabase) {
      setError('Authentication is not configured (set VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY).');
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (!token) throw new Error('You must be signed in.');
      const data = await api.uploadComic(file, token);
      if (data.insight) setReport(data.insight);
      if (data.message) setNotice(data.message);
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      loadComics();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setBusy(false);
    }
  }, [file, loadComics]);

  if (!user) {
    return (
      <div className="mx-auto max-w-md px-6 py-20 text-center">
        <p className="text-lg">Sign in to use the Studio.</p>
      </div>
    );
  }

  if (!paid) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto max-w-md px-6 py-20"
      >
        <div className="glass rounded-2xl p-8 text-center shadow-xl">
          <h2 className="font-display text-2xl font-bold">Creator plan required</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Upload your comics and get insight reports for just $1/month.
          </p>
          <button
            onClick={() => onNavigate('pricing')}
            className="mt-6 inline-block rounded-xl bg-gradient-to-r from-primary to-accent px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition hover:opacity-90"
          >
            View pricing
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-5xl px-6 py-10"
    >
      <h2 className="font-display text-2xl font-bold">Studio</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Upload a comic (PDF, TXT, MD, EPUB). Get an insight report — themes, real-world
        mappings, and scored lessons from the metaphor engine.
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files?.[0];
          if (f) {
            if (f.size > MAX_BYTES) setError('File exceeds the 25 MB limit');
            else {
              setError(null);
              setFile(f);
            }
          }
        }}
        onClick={() => inputRef.current?.click()}
        className={`mt-6 cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition ${
          dragging ? 'border-primary bg-primary/10' : 'border-border'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) {
              if (f.size > MAX_BYTES) setError('File exceeds the 25 MB limit');
              else {
                setError(null);
                setFile(f);
              }
            }
          }}
        />
        <p className="text-sm font-medium">
          {file ? file.name : 'Drag & drop your comic, or click to browse'}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : `${ACCEPT} · up to 25 MB`}
        </p>
      </div>

      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      {notice && <p className="mt-3 text-sm text-muted-foreground">{notice}</p>}

      <button
        onClick={submit}
        disabled={!file || busy}
        className="mt-4 rounded-xl bg-gradient-to-r from-primary to-accent px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition hover:opacity-90 disabled:opacity-50"
      >
        {busy ? 'Analyzing…' : 'Generate insights'}
      </button>

      {report && (
        <div className="mt-8 space-y-6">
          <div className="glass rounded-2xl p-6 shadow-xl">
            <h3 className="font-display text-xl font-bold">{report.title}</h3>
            <p className="mt-1 text-xs text-muted-foreground">{report.source_file}</p>
            {report.summary && <p className="mt-3 text-sm">{report.summary}</p>}

            <div className="mt-4 flex flex-wrap gap-2">
              {report.themes.map((t) => (
                <span key={t} className="rounded-full bg-primary/15 px-3 py-1 text-xs font-medium text-primary">
                  {t}
                </span>
              ))}
            </div>

            {report.characters.length > 0 && (
              <p className="mt-4 text-xs text-muted-foreground">
                Characters: {report.characters.join(', ')}
              </p>
            )}

            {Object.keys(report.codex_scores).length > 0 && (
              <div className="mt-5 space-y-2">
                {Object.entries(report.codex_scores).map(([k, v]) => (
                  <ScoreBar key={k} label={k} value={v} />
                ))}
              </div>
            )}

            {report.takeaways.length > 0 && (
              <div className="mt-5">
                <h4 className="text-sm font-semibold">Takeaways</h4>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {report.takeaways.map((t, i) => (
                    <li key={i}>{t}</li>
                  ))}
                </ul>
              </div>
            )}

            {report.action_items.length > 0 && (
              <div className="mt-5">
                <h4 className="text-sm font-semibold">Action items</h4>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {report.action_items.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {comics.length > 0 && (
        <div className="mt-10">
          <h3 className="text-lg font-semibold">Your uploads</h3>
          <ul className="mt-3 divide-y divide-border rounded-xl border border-border">
            {comics.map((c) => (
              <li key={c.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <span>{c.filename}</span>
                <span className="text-xs text-muted-foreground capitalize">{c.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
};
