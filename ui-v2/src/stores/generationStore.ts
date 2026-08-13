import { create } from 'zustand';
import { api, type Explanation, type Lesson, type Mapping, type Narrative } from '../lib/api';

export interface GenerationResult {
  topic: string;
  format: string;
  tone: string;
  mapping: Mapping;
  explanation?: Explanation;
  lesson?: Lesson;
  narrative?: Narrative;
}

interface GenerationState {
  result: GenerationResult | null;
  isGenerating: boolean;
  error: string | null;
  generateLesson: (topic: string, format: string, tone: string) => Promise<GenerationResult | null>;
  generateNarrative: (topic: string, format: string, tone: string) => Promise<GenerationResult | null>;
  clear: () => void;
}

export const useGenerationStore = create<GenerationState>((set) => ({
  result: null,
  isGenerating: false,
  error: null,
  generateLesson: async (topic, format, tone) => {
    set({ isGenerating: true, error: null });
    try {
      const data = await api.lesson(topic, format, tone);
      const result: GenerationResult = { topic, format, tone, mapping: data.mapping, lesson: data.lesson };
      set({ result, isGenerating: false });
      return result;
    } catch (e) {
      set({ isGenerating: false, error: e instanceof Error ? e.message : 'Generation failed' });
      return null;
    }
  },
  generateNarrative: async (topic, format, tone) => {
    set({ isGenerating: true, error: null });
    try {
      const data = await api.narrative(topic, format, tone, 800);
      const result: GenerationResult = { topic, format, tone, mapping: data.mapping, narrative: data.narrative };
      set({ result, isGenerating: false });
      return result;
    } catch (e) {
      set({ isGenerating: false, error: e instanceof Error ? e.message : 'Generation failed' });
      return null;
    }
  },
  clear: () => set({ result: null, error: null }),
}));
