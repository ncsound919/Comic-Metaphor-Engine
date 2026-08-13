"""
EMOTIONAL INTELLIGENCE LAYER
============================

Adds emotional analysis to comic metaphor protocols, enabling:
1. Emotional state mapping for characters and situations
2. Emotional arc analysis across narratives
3. Emotional resonance scoring for insights
4. Emotion-based metaphor recommendations
5. Therapeutic metaphor generation

This layer bridges cognitive metaphor analysis with emotional intelligence.
"""

import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


class EmotionalState(Enum):
    """Core emotional states with valence and arousal"""

    # High Arousal, Positive Valence
    JOY = "joy"  # Happiness, delight
    EXCITEMENT = "excitement"  # Anticipation, thrill
    PRIDE = "pride"  # Accomplishment, self-worth
    HOPE = "hope"  # Optimism, expectation
    GRATITUDE = "gratitude"  # Thankfulness, appreciation
    INSPIRATION = "inspiration"  # Motivation, creativity

    # High Arousal, Negative Valence
    ANGER = "anger"  # Frustration, rage
    FEAR = "fear"  # Anxiety, terror
    DISGUST = "disgust"  # Revulsion, contempt
    SHAME = "shame"  # Embarrassment, guilt
    ENVY = "envy"  # Jealousy, resentment
    DESPAIR = "despair"  # Hopelessness, devastation

    # Low Arousal, Positive Valence
    CONTENTMENT = "contentment"  # Satisfaction, peace
    CALM = "calm"  # Serenity, tranquility
    NOSTALGIA = "nostalgia"  # Bittersweet remembrance
    AWE = "awe"  # Wonder, reverence
    TRUST = "trust"  # Confidence, reliance

    # Low Arousal, Negative Valence
    SADNESS = "sadness"  # Grief, melancholy
    BOREDOM = "boredom"  # Apathy, disinterest
    LONELINESS = "loneliness"  # Isolation, abandonment
    CONFUSION = "confusion"  # Uncertainty, disorientation
    FATIGUE = "fatigue"  # Exhaustion, weariness


class EmotionalArc(Enum):
    """Common emotional narrative arcs"""

    RAGS_TO_RICHES = "rags_to_riches"  # Sadness → Joy
    TRAGEDY = "tragedy"  # Joy → Sadness
    MAN_IN_HOLE = "man_in_hole"  # Down → Up → Down
    ICARUS = "icarus"  # Up → Down
    CINDERELLA = "cinderella"  # Up → Down → Up
    OEDIPUS = "oedipus"  # Down → Up → Down
    TRANSFORMATION = "transformation"  # Fear → Courage
    REDEMPTION = "redemption"  # Shame → Pride
    AWAKENING = "awakening"  # Confusion → Clarity
    RESILIENCE = "resilience"  # Despair → Hope


class EmotionalIntelligenceDimension(Enum):
    """Dimensions of emotional intelligence"""

    SELF_AWARENESS = "self_awareness"  # Recognizing own emotions
    SELF_REGULATION = "self_regulation"  # Managing emotions
    MOTIVATION = "motivation"  # Harnessing emotions for goals
    EMPATHY = "empathy"  # Recognizing others' emotions
    SOCIAL_SKILLS = "social_skills"  # Managing relationships


@dataclass
class EmotionalProfile:
    """Complete emotional profile for a character or situation"""

    primary_emotion: EmotionalState
    secondary_emotions: List[EmotionalState]
    emotional_intensity: float  # 0.0-1.0
    emotional_valence: float  # -1.0 (negative) to 1.0 (positive)
    emotional_arousal: float  # 0.0 (calm) to 1.0 (aroused)
    emotional_stability: float  # 0.0 (volatile) to 1.0 (stable)
    emotional_triggers: List[str]
    emotional_coping: List[str]
    emotional_needs: List[str]
    emotional_blockers: List[str]


@dataclass
class EmotionalArcAnalysis:
    """Analysis of emotional journey"""

    arc_type: EmotionalArc
    starting_emotion: EmotionalState
    ending_emotion: EmotionalState
    turning_points: List[Dict[str, Any]]
    emotional_growth: float  # 0.0-1.0
    catharsis_potential: float  # 0.0-1.0
    therapeutic_value: float  # 0.0-1.0
    resilience_built: float  # 0.0-1.0


@dataclass
class EmotionalMetaphor:
    """Metaphor enriched with emotional intelligence"""

    base_metaphor: str
    emotional_layers: List[Dict[str, Any]]
    emotional_resonance: float  # 0.0-1.0
    therapeutic_potential: float  # 0.0-1.0
    empathy_triggering: List[str]
    emotional_insights: List[str]
    recommended_emotional_states: List[EmotionalState]
    emotional_warnings: List[str]  # When metaphor might be harmful


class EmotionalIntelligenceEngine:
    """
    Adds emotional analysis to comic metaphor protocols, enabling
    deeper psychological insights and therapeutic applications.
    """

    def __init__(self):
        self.emotional_lexicon = self._build_emotional_lexicon()
        self.therapeutic_frameworks = self._build_therapeutic_frameworks()
        self.emotional_archetypes = self._build_emotional_archetypes()
        self.cached_profiles: Dict[str, EmotionalProfile] = {}

    def _build_emotional_lexicon(self) -> Dict[EmotionalState, Dict[str, Any]]:
        """Build comprehensive emotional lexicon"""
        return {
            EmotionalState.JOY: {
                "description": "Feeling of great pleasure and happiness",
                "physiological_signs": ["smiling", "laughter", "energy"],
                "cognitive_patterns": ["optimism", "creativity", "openness"],
                "behavioral_tendencies": ["sharing", "celebrating", "creating"],
                "therapeutic_value": 0.9,
                "growth_potential": 0.8,
            },
            EmotionalState.SADNESS: {
                "description": "Feeling of sorrow or unhappiness",
                "physiological_signs": ["tears", "slowed movement", "low energy"],
                "cognitive_patterns": ["reflection", "loss focus", "realism"],
                "behavioral_tendencies": [
                    "withdrawing",
                    "seeking comfort",
                    "processing",
                ],
                "therapeutic_value": 0.7,
                "growth_potential": 0.6,
            },
            EmotionalState.ANGER: {
                "description": "Strong feeling of annoyance, displeasure, or hostility",
                "physiological_signs": ["increased heart rate", "tension", "flushing"],
                "cognitive_patterns": [
                    "injustice focus",
                    "boundary setting",
                    "action orientation",
                ],
                "behavioral_tendencies": ["confronting", "protecting", "asserting"],
                "therapeutic_value": 0.5,
                "growth_potential": 0.7,
            },
            EmotionalState.FEAR: {
                "description": "Unpleasant emotion caused by threat or danger",
                "physiological_signs": ["alertness", "adrenaline", "caution"],
                "cognitive_patterns": ["risk assessment", "preparation", "vigilance"],
                "behavioral_tendencies": ["avoiding", "preparing", "seeking safety"],
                "therapeutic_value": 0.4,
                "growth_potential": 0.8,
            },
            EmotionalState.HOPE: {
                "description": "Feeling of expectation and desire for certain thing to happen",
                "physiological_signs": ["lightness", "forward lean", "bright eyes"],
                "cognitive_patterns": [
                    "future orientation",
                    "possibility thinking",
                    "planning",
                ],
                "behavioral_tendencies": [
                    "goal setting",
                    "persisting",
                    "inspiring others",
                ],
                "therapeutic_value": 0.8,
                "growth_potential": 0.9,
            },
            EmotionalState.SHAME: {
                "description": "Painful feeling of humiliation or distress",
                "physiological_signs": [
                    "hiding",
                    "slumped posture",
                    "avoiding eye contact",
                ],
                "cognitive_patterns": [
                    "self-criticism",
                    "worthlessness",
                    "isolation thoughts",
                ],
                "behavioral_tendencies": ["concealing", "apologizing", "withdrawing"],
                "therapeutic_value": 0.6,
                "growth_potential": 0.5,
            },
            EmotionalState.PRIDE: {
                "description": "Feeling of deep pleasure from one's own achievements",
                "physiological_signs": [
                    "upright posture",
                    "confident gestures",
                    "smiling",
                ],
                "cognitive_patterns": [
                    "self-efficacy",
                    "accomplishment focus",
                    "identity affirmation",
                ],
                "behavioral_tendencies": [
                    "sharing success",
                    "setting new goals",
                    "mentoring",
                ],
                "therapeutic_value": 0.7,
                "growth_potential": 0.8,
            },
            EmotionalState.GRATITUDE: {
                "description": "Quality of being thankful; readiness to show appreciation",
                "physiological_signs": ["warmth", "relaxation", "open posture"],
                "cognitive_patterns": [
                    "abundance thinking",
                    "connection focus",
                    "present moment awareness",
                ],
                "behavioral_tendencies": [
                    "thanking",
                    "giving back",
                    "acknowledging others",
                ],
                "therapeutic_value": 0.9,
                "growth_potential": 0.8,
            },
        }

    def _build_therapeutic_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Build therapeutic frameworks for emotional processing"""
        return {
            "cognitive_behavioral": {
                "approach": "Identify and change negative thought patterns",
                "emotional_focus": ["anger", "anxiety", "depression"],
                "metaphor_strategy": "Thought restructuring through narrative",
                "effectiveness": 0.85,
            },
            "narrative_therapy": {
                "approach": "Re-author personal narratives",
                "emotional_focus": ["shame", "trauma", "identity_confusion"],
                "metaphor_strategy": "Story reconstruction and meaning-making",
                "effectiveness": 0.80,
            },
            "acceptance_commitment": {
                "approach": "Accept emotions while committing to values-based action",
                "emotional_focus": ["fear", "avoidance", "emotional_struggle"],
                "metaphor_strategy": "Values clarification through heroic journeys",
                "effectiveness": 0.82,
            },
            "positive_psychology": {
                "approach": "Build strengths and cultivate positive emotions",
                "emotional_focus": ["sadness", "hopelessness", "lack_of_meaning"],
                "metaphor_strategy": "Strength identification through superhero analogies",
                "effectiveness": 0.78,
            },
            "trauma_informed": {
                "approach": "Safety, trust, and empowerment in healing",
                "emotional_focus": ["fear", "shame", "hypervigilance"],
                "metaphor_strategy": "Safe exploration through controlled narratives",
                "effectiveness": 0.75,
            },
        }

    def _build_emotional_archetypes(self) -> Dict[str, Dict[str, Any]]:
        """Build emotional archetypes based on comic characters"""
        return {
            "wounded_healer": {
                "description": "Character who heals others through understanding own wounds",
                "examples": ["Professor X", "Daredevil", "Doctor Strange"],
                "primary_emotions": [
                    EmotionalState.EMPATHY,
                    EmotionalState.PAIN,
                    EmotionalState.HOPE,
                ],
                "emotional_strengths": ["compassion", "resilience", "understanding"],
                "emotional_challenges": [
                    "over-identification",
                    "burnout",
                    "boundary issues",
                ],
                "therapeutic_value": 0.9,
            },
            "rageful_protector": {
                "description": "Character whose anger fuels protection of others",
                "examples": ["Hulk", "Wolverine", "Punisher"],
                "primary_emotions": [
                    EmotionalState.ANGER,
                    EmotionalState.PROTECTIVENESS,
                    EmotionalState.LONELINESS,
                ],
                "emotional_strengths": [
                    "boundary enforcement",
                    "immediate action",
                    "fierce loyalty",
                ],
                "emotional_challenges": [
                    "impulsivity",
                    "isolation",
                    "emotional overwhelm",
                ],
                "therapeutic_value": 0.7,
            },
            "fearful_overcomer": {
                "description": "Character who acts despite overwhelming fear",
                "examples": ["Spider-Man", "Batman", "Green Lantern"],
                "primary_emotions": [
                    EmotionalState.FEAR,
                    EmotionalState.DETERMINATION,
                    EmotionalState.ANXIETY,
                ],
                "emotional_strengths": ["courage", "preparation", "persistence"],
                "emotional_challenges": [
                    "exhaustion",
                    "hypervigilance",
                    "trust issues",
                ],
                "therapeutic_value": 0.8,
            },
            "joyful_inspirer": {
                "description": "Character who spreads hope and positivity",
                "examples": ["Superman", "Captain America", "Ms. Marvel"],
                "primary_emotions": [
                    EmotionalState.JOY,
                    EmotionalState.HOPE,
                    EmotionalState.OPTIMISM,
                ],
                "emotional_strengths": [
                    "motivation",
                    "team building",
                    "positive reframing",
                ],
                "emotional_challenges": [
                    "unrealistic expectations",
                    "avoiding negativity",
                    "emotional labor",
                ],
                "therapeutic_value": 0.85,
            },
            "shamed_redeemer": {
                "description": "Character seeking redemption from past shame",
                "examples": ["Iron Man", "Black Widow", "Magneto"],
                "primary_emotions": [
                    EmotionalState.SHAME,
                    EmotionalState.GUILT,
                    EmotionalState.HOPE,
                ],
                "emotional_strengths": [
                    "self-awareness",
                    "determination",
                    "empathy for others' struggles",
                ],
                "emotional_challenges": [
                    "self-sabotage",
                    "perfectionism",
                    "difficulty accepting forgiveness",
                ],
                "therapeutic_value": 0.75,
            },
        }

    def analyze_emotional_profile(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> EmotionalProfile:
        """
        Analyze emotional profile from text description.

        Args:
            text: Text describing character or situation
            context: Additional context for analysis

        Returns:
            Emotional profile with primary and secondary emotions
        """
        if context is None:
            context = {}

        # Create hash for caching
        text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        if text_hash in self.cached_profiles:
            return self.cached_profiles[text_hash]

        # Extract emotional cues from text
        emotional_cues = self._extract_emotional_cues(text)

        # Determine primary emotion
        primary_emotion = self._determine_primary_emotion(emotional_cues, context)

        # Determine secondary emotions
        secondary_emotions = self._determine_secondary_emotions(
            emotional_cues, primary_emotion
        )

        # Calculate emotional metrics
        emotional_intensity = self._calculate_emotional_intensity(emotional_cues)
        emotional_valence = self._calculate_emotional_valence(
            primary_emotion, secondary_emotions
        )
        emotional_arousal = self._calculate_emotional_arousal(
            primary_emotion, emotional_cues
        )
        emotional_stability = self._calculate_emotional_stability(emotional_cues)

        # Identify triggers, coping, needs, and blockers
        emotional_triggers = self._identify_emotional_triggers(text, context)
        emotional_coping = self._identify_coping_mechanisms(text, primary_emotion)
        emotional_needs = self._identify_emotional_needs(primary_emotion, context)
        emotional_blockers = self._identify_emotional_blockers(text, emotional_cues)

        profile = EmotionalProfile(
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            emotional_intensity=emotional_intensity,
            emotional_valence=emotional_valence,
            emotional_arousal=emotional_arousal,
            emotional_stability=emotional_stability,
            emotional_triggers=emotional_triggers,
            emotional_coping=emotional_coping,
            emotional_needs=emotional_needs,
            emotional_blockers=emotional_blockers,
        )

        # Cache the profile
        self.cached_profiles[text_hash] = profile

        return profile

    def _extract_emotional_cues(self, text: str) -> Dict[str, List[str]]:
        """Extract emotional cues from text"""
        cues = {
            "positive_words": [],
            "negative_words": [],
            "intensity_indicators": [],
            "body_language": [],
            "action_verbs": [],
            "metaphors": [],
        }

        # Simple keyword analysis (in production, would use NLP)
        positive_keywords = [
            "happy",
            "joy",
            "excited",
            "proud",
            "hopeful",
            "grateful",
            "love",
            "win",
            "success",
        ]
        negative_keywords = [
            "sad",
            "angry",
            "afraid",
            "ashamed",
            "lonely",
            "hurt",
            "loss",
            "failure",
            "pain",
        ]
        intensity_indicators = [
            "very",
            "extremely",
            "intensely",
            "overwhelming",
            "slightly",
            "somewhat",
        ]

        words = text.lower().split()

        for word in words:
            if word in positive_keywords:
                cues["positive_words"].append(word)
            elif word in negative_keywords:
                cues["negative_words"].append(word)
            elif word in intensity_indicators:
                cues["intensity_indicators"].append(word)

        # Extract body language cues
        body
