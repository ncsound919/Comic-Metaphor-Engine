"""
Narrative Generator Module
==========================

Generates narrative content in multiple formats (podcast, marketing, dialogue)
using comic book metaphor mappings.
"""

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional

from schema import (
    FormatType,
    GenerationContext,
    MetaphorMapping,
    NarrativeOutline,
    NarrativeOutput,
    OutlineBeat,
    Protocol,
)


class NarrativeGenerator:
    """Generator for narrative content in various formats."""

    def __init__(self, processed_dir: str = "processed"):
        """Initialize with processed data directory

        Args:
            processed_dir: Directory containing knowledge_base.json
        """
        self.processed_dir = Path(processed_dir) if not isinstance(processed_dir, Path) else processed_dir
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load format-specific templates."""
        return {
            "podcast_monologue": """
# {title}

**Hook:** {hook}

**The Story So Far:**
{story}

**Act One — The Setup:**
{beat_content}

**Act Two — The Turn:**
{turn}

**Act Three — The Resolution:**
{conclusion}

**Word count:** {word_count}
""",
            "marketing_email": """
Subject: {title}

Dear Reader,

{hook}

{story}

{beat_content}

{turn}

{conclusion}

Best regards,
The Comic Metaphor Team

P.S. {call_to_action}
""",
            "blog_post": """
# {title}

## The Hook
{hook}

## The Story Behind It
{story}

## Where It All Breaks Down
{beat_content}

## The Turn
{turn}

## What This Means For You
{conclusion}

*Word count: {word_count}*
""",
            "dialogue_script": """
**Title:** {title}

**Characters:**
- Narrator
- Expert
- Listener (you)

**Scene 1: Setup**
**Narrator:** {hook}

**Scene 2: The Story**
**Narrator:** {story}

**Scene 3: The Breakdown**
{beat_content}

**Scene 4: The Turn**
**Expert:** {turn}

**Scene 5: Resolution**
**Expert:** {conclusion}

**Listener:** That makes so much sense!

**Word count:** {word_count}
""",
        }

    def generate(self, context: GenerationContext) -> NarrativeOutput:
        """
        Generate narrative content from context.

        Args:
            context: Generation context with mapping, protocol, etc.

        Returns:
            Generated narrative output
        """
        start_time = time.time()

        # Generate outline first
        outline = self._generate_outline(context)

        # Generate content based on format
        content = self._generate_content(context, outline)

        # Create output
        output_id = (
            f"narrative_{hashlib.sha256(context.mapping.id.encode()).hexdigest()[:8]}"
        )

        output = NarrativeOutput(
            id=output_id,
            mapping_id=context.mapping.id,
            outline_id=outline.mapping_id if outline else None,
            format_type=context.mapping.target_format,
            title=outline.title if outline else context.mapping.topic,
            content=content,
            word_count=len(content.split()),
            generation_model="template_based_v1",
            generation_time_ms=int((time.time() - start_time) * 1000),
            codex_scores={
                "trueness": context.mapping.trueness_score,
                "flow": context.mapping.flow_score,
                "pcs": context.mapping.pcs_score,
                "tap": context.mapping.tap_score,
            },
        )

        return output

    def _generate_outline(self, context: GenerationContext) -> NarrativeOutline:
        """Generate a narrative outline from context."""
        mapping = context.mapping
        protocol = context.protocol

        # Clean archetype for title grammar ("The X" -> "X" when prefixed)
        archetype = (protocol.archetype or protocol.id or "the hero").strip()
        clean_archetype = archetype
        if clean_archetype.lower().startswith("the "):
            clean_archetype = clean_archetype[4:]

        # Create beats based on protocol dimensions
        beats = []
        beat_num = 1

        # Opening beat
        story = (protocol.narrative or "").strip()
        story_short = story[:400] if story else f"The {clean_archetype} pattern"

        beats.append(
            OutlineBeat(
                number=beat_num,
                title="The Setup",
                description=f"Introduce {mapping.topic} through the lens of {archetype}",
                comic_reference=f"{archetype} opening",
                word_count_target=150,
                key_points=[
                    p for p in [mapping.core_tension, protocol.business_logic[:120]] if p
                ],
            )
        )
        beat_num += 1

        # Dimension beats
        for dim in protocol.dimensions[:3]:  # Limit to 3 main dimensions
            lesson = dim.lesson or dim.analysis or ""
            dim_label = dim.id.value if hasattr(dim.id, "value") else str(dim.id)
            beats.append(
                OutlineBeat(
                    number=beat_num,
                    title=f"Dimension {dim_label}: {dim.title}",
                    description=f"Explore {dim.analysis or dim.title} with lesson: {lesson}",
                    comic_reference=f"{archetype} - {dim.title}",
                    word_count_target=200,
                    key_points=[
                        p for p in [dim.analysis, dim.metric, lesson] if p
                    ][:3],
                )
            )
            beat_num += 1

        # Resolution beat
        beats.append(
            OutlineBeat(
                number=beat_num,
                title="The Resolution",
                description=f"Apply {archetype} to overcome {mapping.target_emotion}",
                comic_reference=f"{archetype} climax",
                word_count_target=150,
                key_points=[mapping.target_emotion, "Actionable insights"],
            )
        )

        # Calculate total word count
        total_words = sum(beat.word_count_target for beat in beats)

        outline = NarrativeOutline(
            mapping_id=mapping.id,
            format_type=mapping.target_format,
            title=f"{mapping.topic}: The {clean_archetype} Story",
            hook=f"What if {mapping.topic} was playing out the {clean_archetype} story?",
            beats=beats,
            conclusion=f"By embracing the {archetype} approach, you can turn {mapping.topic} into a comeback arc instead of a tragedy.",
            total_word_count=total_words,
        )
        outline.story = story_short
        outline.turn = self._build_turn(context, clean_archetype)
        return outline

    def _build_turn(self, context: GenerationContext, clean_archetype: str) -> str:
        """Craft the midpoint 'turn' — where the lesson lands."""
        mapping = context.mapping
        protocol = context.protocol
        translation = (protocol.business_translation or "").strip()
        parts = [
            f"The twist is that {mapping.topic} is not a series of random failures — "
            f"it is following the {clean_archetype} script beat for beat."
        ]
        if translation:
            parts.append(translation[:220])
        if protocol.business_logic:
            parts.append(f"Here's the operating principle: {protocol.business_logic[:160]}")
        return " ".join(parts)

    def _generate_content(
        self, context: GenerationContext, outline: NarrativeOutline
    ) -> str:
        """Generate formatted content from outline."""
        mapping = context.mapping
        protocol = context.protocol

        # Get template
        template_key = self._get_template_key(mapping.target_format)
        template = self.templates.get(template_key, self.templates["podcast_monologue"])

        # Generate beat content with narrative prose
        beat_sections = []
        for i, beat in enumerate(outline.beats):
            section = f"**{beat.title}**\n{beat.description}\n"
            if beat.key_points:
                rendered = []
                for point in beat.key_points:
                    if not point:
                        continue
                    if point == "Actionable insights":
                        rendered.append(
                            f"- Actionable insight: name the exact decision that is "
                            f"the {protocol.archetype or 'hero'}'s 'snap', and ask "
                            f"whether it solves the problem or just removes it."
                        )
                    elif point == mapping.target_emotion:
                        rendered.append(
                            f"- The emotion to steer toward: {mapping.target_emotion}"
                        )
                    else:
                        rendered.append(f"- {point}")
                if rendered:
                    section += "\n" + "\n".join(rendered) + "\n"
            beat_sections.append(section)

        beat_content = "\n\n".join(beat_sections)

        # Fill template
        content = template.format(
            title=outline.title,
            hook=outline.hook,
            story=outline.story or outline.hook,
            beat_content=beat_content,
            turn=outline.turn,
            conclusion=outline.conclusion,
            word_count=outline.total_word_count,
            call_to_action="Ready to apply this metaphor to your life?",
        )

        return content

    def _get_template_key(self, format_type: FormatType) -> str:
        """Map format type to template key."""
        mapping = {
            FormatType.PODCAST_MONOLOGUE: "podcast_monologue",
            FormatType.MARKETING_EMAIL: "marketing_email",
            FormatType.BLOG_POST: "blog_post",
            FormatType.DIALOGUE_SCRIPT: "dialogue_script",
        }
        return mapping.get(format_type, "podcast_monologue")


def generate_narrative(context: GenerationContext) -> NarrativeOutput:
    """
    Convenience function to generate narrative content.

    Args:
        context: Generation context

    Returns:
        Generated narrative output
    """
    generator = NarrativeGenerator()
    return generator.generate(context)


if __name__ == "__main__":
    # Test the generator
    from schema import (
        Dimension,
        DimensionType,
        FormatType,
        MetaphorMapping,
        Protocol,
        ProtocolType,
        ToneType,
    )

    # Create test protocol
    protocol = Protocol(
        id="test_protocol",
        protocol_type=ProtocolType.ARMOR_WARS,
        archetype="Iron Man's Armor Wars",
        business_logic="Technology proliferation and responsibility",
        application="Managing innovation risks",
        narrative="Tony Stark faces the consequences of his technology falling into the wrong hands",
        business_translation="Innovation without oversight leads to chaos",
        dimensions=[
            Dimension(
                id=DimensionType.D1_BIO,
                title="Bio/Internal",
                science_concept="Evolutionary Mismatch",
                character_anchor="Tony vs. Guilt",
                analysis="Internal conflict between innovation and responsibility",
                lesson="Balance progress with accountability",
                metric="Innovation oversight ratio",
            )
        ],
        vector_entry={},
        risk_categories=[],
        themes=["responsibility", "innovation", "control"],
        tone_compatibility=[ToneType.GRITTY],
        format_compatibility=[FormatType.PODCAST_MONOLOGUE],
    )

    # Create test mapping
    mapping = MetaphorMapping(
        id="test_mapping",
        topic="startup scaling challenges",
        domain="business",
        target_format=FormatType.PODCAST_MONOLOGUE,
        target_tone=ToneType.GRITTY,
        protocol_id="test_protocol",
        core_tension="Growth vs. stability",
        target_emotion="controlled empowerment",
        trueness_score=0.75,
        flow_score=0.65,
        pcs_score=0.70,
        tap_score=0.60,
    )

    # Create context
    context = GenerationContext(
        mapping=mapping, protocol=protocol, word_count_target=800
    )

    # Generate content
    output = generate_narrative(context)
    print(f"Generated {output.format_type.value} content:")
    print(f"Title: {output.title}")
    print(f"Word count: {output.word_count}")
    print("\nContent preview:")
    print(output.content[:500] + "...")
