import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Header, type AppView } from './components/layout/Header';
import { Hero } from './components/features/Hero';
import { MetaphorSearch } from './components/features/MetaphorSearch';
import { SearchResults } from './components/features/SearchResults';
import { ProtocolGrid } from './components/features/ProtocolGrid';
import { ResultView } from './components/features/ResultView';
import { SignIn } from './components/features/SignIn';
import { Pricing } from './components/features/Pricing';
import { Upload } from './components/features/Upload';
import { ToastContainer } from './components/ui/Toast';
import { useUIStore } from './stores/uiStore';
import { useProtocolStore } from './stores/protocolStore';
import { useSearchStore } from './stores/searchStore';
import { useGenerationStore } from './stores/generationStore';
import { useAuthStore } from './stores/authStore';

function App() {
  const { theme } = useUIStore();
  const { protocols, fetchProtocols } = useProtocolStore();
  const { lastSearched, clearResults } = useSearchStore();
  const { result, clear, generateLesson } = useGenerationStore();
  const { user, init } = useAuthStore();
  const [view, setView] = useState<AppView>('home');

  useEffect(() => {
    init();
    document.documentElement.classList.toggle('light', theme === 'light');
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme, init]);

  useEffect(() => {
    fetchProtocols();
  }, [fetchProtocols]);

  useEffect(() => {
    if (result) setView('result');
  }, [result]);

  useEffect(() => {
    if (view === 'auth' && user) setView('account');
  }, [user, view]);

  const goHome = () => {
    clearResults();
    clear();
    setView('home');
  };

  const viewBody = () => {
    if (view === 'result' && result) return <ResultView result={result} onBack={goHome} />;
    if (view === 'auth' && !user) return <SignIn />;
    if (view === 'pricing') return <Pricing />;
    if (view === 'account') return <Upload onNavigate={setView} />;
    if (view === 'browse' || lastSearched) {
      return (
        <div className="mx-auto max-w-7xl px-6 py-10 space-y-10">
          {lastSearched ? (
            <SearchResults onBackToBrowse={() => clearResults()} />
          ) : (
            <ProtocolGrid
              protocols={protocols}
              onSelect={(p) => generateLesson(p.archetype, 'podcast_monologue', 'hopeful')}
            />
          )}
        </div>
      );
    }
    return (
      <>
        <Hero />
        <div className="mx-auto max-w-4xl px-6 pb-16">
          <MetaphorSearch />
          <SearchResults />
        </div>
      </>
    );
  };

  return (
    <div className="min-h-screen">
      <Header onLogoClick={goHome} onNavigate={setView} activeView={view} />
      <main className="relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={view}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            {viewBody()}
          </motion.div>
        </AnimatePresence>
      </main>
      <ToastContainer />
    </div>
  );
}

export default App;
