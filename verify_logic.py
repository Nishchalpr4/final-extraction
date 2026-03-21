import asyncio
from extraction import call_llm

async def verify():
    text = """In January 2024, Nike Inc. announced that it would expand its manufacturing partnerships in Southeast Asia to diversify its supply chain. The initiative is being led by Nike CEO John Donahoe and COO Andy Campion as part of the company's long-term strategy to reduce reliance on single-country sourcing. Nike currently works with contract manufacturers in Vietnam, Indonesia, and Cambodia. According to a report published by Morgan Stanley in February 2024, nearly 50% of Nike’s footwear production now comes from Vietnam-based factories. Nike’s flagship product lines include the Air Jordan sneakers, Nike Air Max running shoes, and the Pegasus performance running series. The Air Jordan brand, originally developed in partnership with basketball player Michael Jordan in 1984, remains one of Nike's most profitable franchises. In the fiscal year ending May 31, 2023, Nike reported revenue of $51.2 billion, with North America accounting for approximately 42% of total sales. The company competes with global sportswear brands including Adidas AG, Puma SE, and Under Armour Inc. Analysts at Goldman Sachs estimate that the global athletic footwear market will reach $160 billion by 2027, driven by demand in China, India, and Brazil."""
    res = await call_llm(text, "test")
    
    missing_context = [e.canonical_name for e in res.entities if "context" not in (e.attributes or {}) and "description" not in (e.attributes or {})]
    
    has_management = any(e.entity_type == "Management" for e in res.entities)
    has_market = any(e.entity_type == "Market" for e in res.entities)
    has_product_portfolio = any(e.entity_type == "ProductPortfolio" for e in res.entities)
    
    print(f"Entities: {len(res.entities)}")
    print(f"Relations: {len(res.relations)}")
    print(f"Missing Context Attributes: {len(missing_context)}")
    if missing_context:
        print(f"Examples: {missing_context[:3]}")
    print(f"Has Management Node: {has_management}")
    print(f"Has Market Node: {has_market}")
    print(f"Has ProductPortfolio Node: {has_product_portfolio}")

if __name__ == "__main__":
    asyncio.run(verify())
