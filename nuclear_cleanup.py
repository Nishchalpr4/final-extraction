import os
import json
import logging
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def nuclear_cleanup():
    db = DatabaseManager()
    
    logger.info("Starting Nuclear Cleanup of Database Ontology...")
    
    conn = db._get_connection()
    try:
        cursor = db._get_cursor(conn)
        
        # 1. Wipe discoveries
        logger.info("Wiping discovered entity types and relations...")
        cursor.execute("TRUNCATE TABLE new_entity_types RESTART IDENTITY")
        cursor.execute("TRUNCATE TABLE new_relation_types RESTART IDENTITY")
        
        # 2. Wipe ontology rules
        logger.info("Wiping existing ontology rules...")
        cursor.execute("TRUNCATE TABLE ontology_rules RESTART IDENTITY")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to wipe tables: {e}")
        return
    finally:
        conn.close()

    # 3. Re-seed from fresh base_ontology.json
    logger.info("Re-seeding ontology from base_ontology.json...")
    db.seed_ontology(merge_with_existing=False)
    
    logger.info("Nuclear Cleanup COMPLETE. The system is now reset to factory hierarchy rules.")

if __name__ == "__main__":
    nuclear_cleanup()
