#!/usr/bin/env python3
"""
Generate metaphor-informed markdown content for coding, finance, and biotech topics
using the Comic Metaphor Engine.
"""

import sys
from pathlib import Path

# Add engine to path
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine"))

from engine.index import MetaphorIndex
from engine.metaphor_engine import MetaphorEngine
from engine.codex_adapter import CodexAdapter
from engine.narrative_generator import NarrativeGenerator
from engine.schema import FormatType, ToneType, GenerationContext

def main():
    print("Loading Comic Metaphor Engine...")
    
    # Load the index (which loads the knowledge base and FAISS index)
    processed_dir = _ROOT / "processed"
    index = MetaphorIndex(processed_dir=str(processed_dir), lazy=True)
    print(f"Loaded {len(index.protocol_list)} protocols")
    
    # Create the metaphor engine with codex adapter
    engine = MetaphorEngine(index, CodexAdapter(index))
    print("Metaphor engine initialized")
    
    # Initialize narrative generator
    narrator = NarrativeGenerator()
    print("Narrative generator initialized")
    
    # Define topics to process
    topics = [
        ("coding", "AI-assisted software engineering and development practices"),
        ("finance", "Personal and institutional investment strategies in volatile markets"),
        ("biotech", "Biotechnology innovation and therapeutic development pipelines")
    ]
    
    # Output directory
    output_dir = _ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    
    for topic_key, topic_description in topics:
        print(f"\nProcessing {topic_key.upper()} topic...")
        print(f"Topic: {topic_description}")
        
        # Generate mapping - this is where the engine finds the best protocol match
        # and creates the metaphor mapping with all dimensions
        mapping = engine.generate_mapping(
            topic=topic_description,
            target_format=FormatType.BLOG_POST,  # We want markdown/blog-style output
            target_tone=ToneType.PHILOSOPHICAL   # Thoughtful, analytical tone
        )
        
        print(f"  Mapped to protocol: {mapping.protocol_id}")
        print(f"  Core tension: {mapping.core_tension}")
        print(f"  Target emotion: {mapping.target_emotion}")
        print(f"  Trueness score: {mapping.trueness_score:.3f}")
        print(f"  Flow score: {mapping.flow_score:.3f}")
        print(f"  PCS score: {mapping.pcs_score:.3f}")
        
        # Get the protocol from the index
        protocol = index.get_protocol_by_id(mapping.protocol_id)
        if not protocol:
            print(f"  ERROR: Could not find protocol {mapping.protocol_id}")
            continue
            
        print(f"  Protocol: {protocol.archetype}")
        print(f"  Business logic: {protocol.business_logic[:100]}...")
        
        # Create generation context
        ctx = GenerationContext(
            mapping=mapping,
            protocol=protocol,
            word_count_target=800,  # Target ~800 words for each markdown file
            pov="second",  # Second person for engaging, direct address
            style_notes=[
                "Use clear, accessible language",
                "Include concrete examples and applications", 
                "Structure with clear thematic sections",
                "End with actionable insights"
            ]
        )
        
        # Generate the narrative output
        print("  Generating narrative content...")
        output = narrator.generate(ctx)
        
        print(f"  Generated {output.word_count} words")
        print(f"  Title: {output.title}")
        
        # Write to markdown file
        output_file = output_dir / f"{topic_key}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write the title as a header
            f.write(f"# {output.title}\n\n")
            
            # Write the main content
            f.write(output.content)
            
            # Add a footer with metadata about the metaphor engine process
            f.write("\n\n---\n\n")
            f.write(f"*Generated using Comic Metaphor Engine*\n")
            f.write(f"- Source Protocol: {protocol.archetype}\n")
            f.write(f"- Core Tension: {mapping.core_tension}\n")
            f.write(f"- Trueness Score: {mapping.trueness_score:.3f}/1.000\n")
            f.write(f"- Flow Score: {mapping.flow_score:.3f}/1.000\n")
            f.write(f"- PCS Score: {mapping.pcs_score:.3f}/1.000\n")
            f.write(f"- Target Emotion: {mapping.target_emotion}\n")
        
        print(f"  Saved to: {output_file}")
    
    print(f"\n✅ All content generated and saved to {output_dir}")
    print("Files created:")
    for topic_key, _ in topics:
        print(f"  - {output_dir}/{topic_key}.md")

if __name__ == "__main__":
    main()