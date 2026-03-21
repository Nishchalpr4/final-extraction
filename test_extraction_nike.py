import asyncio
import json
from extraction import call_llm

async def test_extraction():
    text = """In January 2024, Nike Inc. announced that it would expand its manufacturing partnerships in Southeast Asia to diversify its supply chain. The initiative is being led by Nike CEO John Donahoe and COO Andy Campion as part of the company's long-term strategy to reduce reliance on single-country sourcing. Nike currently works with contract manufacturers in Vietnam, Indonesia, and Cambodia. According to a report published by Morgan Stanley in February 2024, nearly 50% of Nike’s footwear production now comes from Vietnam-based factories. Nike’s flagship product lines include the Air Jordan sneakers, Nike Air Max running shoes, and the Pegasus performance running series. The Air Jordan brand, originally developed in partnership with basketball player Michael Jordan in 1984, remains one of Nike's most profitable franchises. In the fiscal year ending May 31, 2023, Nike reported revenue of $51.2 billion, with North America accounting for approximately 42% of total sales. The company competes with global sportswear brands including Adidas AG, Puma SE, and Under Armour Inc. Analysts at Goldman Sachs estimate that the global athletic footwear market will reach $160 billion by 2027, driven by demand in China, India, and Brazil."""
    
    print("Running extraction...")
    result = await call_llm(text, "Nike Report 2024")
    
    print("\n--- ENTITIES ---")
    for e in result.entities:
        print(f"[{e.entity_type}] {e.canonical_name} - {e.attributes}")
        
    print("\n--- RELATIONS ---")
    for r in result.relations:
        print(f"{r.source_temp_id} -> {r.relation_type} -> {r.target_temp_id}")

    print("\n--- DISCOVERIES ---")
    for d in result.discoveries:
        print(d)

if __name__ == "__main__":
    asyncio.run(test_extraction())
