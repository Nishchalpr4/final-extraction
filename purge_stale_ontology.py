from database import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

def purge():
    db = DatabaseManager()
    print("PURGE: Starting hard-overwrite of ontology rules in Neon...")
    
    # We call seed_ontology with merge_with_existing=False to DELETE orphans
    db.seed_ontology(merge_with_existing=False)
    
    print("PURGE: Database ontology has been replaced with base_ontology.json (no merging).")
    print("PURGE: Stale 'ExternalOrganization' removed.")

if __name__ == "__main__":
    purge()
