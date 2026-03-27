import json
import logging
from typing import List, Dict, Any, Optional
from models import ExtractionPayload, EntityCandidate, RelationCandidate

logger = logging.getLogger(__name__)

def safe_json_loads(data: Any, default: Any = None) -> Any:
    if data is None: return default
    if isinstance(data, (dict, list)): return data
    if not isinstance(data, str) or not data.strip(): return default
    try:
        cleaned = data.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[-1].split("```")[0].strip()
        return json.loads(cleaned)
    except:
        import re
        try:
            dict_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            list_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
            if dict_match and (not list_match or dict_match.start() < list_match.start()): return json.loads(dict_match.group())
            elif list_match: return json.loads(list_match.group())
        except: pass
        return default

def find_list_data(data: Any) -> List[Any]:
    if isinstance(data, list): return data
    if isinstance(data, dict):
        for key in ["entities", "relations", "facts", "data"]:
            if key in data and isinstance(data[key], list): return data[key]
    return []

class LogicGuard:
    def __init__(self, ontology: Dict[str, Any]):
        self.ontology = ontology

    def refine_payload(self, payload: ExtractionPayload) -> ExtractionPayload:
        """
        PLATINUM STANDARD HEALER (v2):
        1. Identifies Global Root (LegalEntity).
        2. Normalizes Multi-Portfolio Hierarchy (Domain > Portfolios > Lines).
        3. Supports Products vs Services segregation.
        4. Protects Strategy & Financial nodes from pruning.
        5. Forces 100% Root-to-Leaf connectivity using BFS.
        """
        def norm(t): return str(t).lower().replace(" ", "").replace("_", "")
        
        # --- PHASE 0: Pre-processing ---
        entity_map = {str(e.temp_id): e for e in payload.entities}
        
        # 1. Identify Root
        root = next((e for e in payload.entities if norm(e.entity_type) in ["legalentity", "company"]), None)
        if not root and payload.entities: root = payload.entities[0]
        if not root: return payload
        root_id = str(root.temp_id)

        # --- PHASE 1: Taxonomy Anchoring (The Spine) ---
        pl_types = {"productline", "product", "item", "brand", "digitalproduct"}
        ps_types = {"service", "subscription"} 
        pf_types = {"productfamily", "productportfolio", "businessunit"}
        sf_types = {"serviceportfolio"}
        pd_types = {"productdomain", "industry", "subindustry"}
        non_tax_types = {"person", "legalentity", "location", "facility", "competitor", "strategy", "capability", "financial", "financialreport"}

        # 1. Identify existing or required taxonomic anchors
        all_families = [e for e in payload.entities if norm(e.entity_type) in pf_types]
        all_domains = [e for e in payload.entities if norm(e.entity_type) in pd_types]
        service_fams = [e for e in payload.entities if norm(e.entity_type) in sf_types]
        
        # Ensure Domain exists
        if not all_domains:
            primary_dom_id = "bridge_taxonomic_domain"
            payload.entities.append(EntityCandidate(
                temp_id=primary_dom_id, canonical_name="Core Operations", 
                entity_type="ProductDomain", short_info="Primary industry sector."
            ))
            entity_map[primary_dom_id] = payload.entities[-1]
        else:
            primary_dom_id = str(all_domains[0].temp_id)

        # Ensure Product Family exists
        if not all_families:
            primary_fam_id = "bridge_taxonomic_family"
            payload.entities.append(EntityCandidate(
                temp_id=primary_fam_id, canonical_name="Product Portfolio", 
                entity_type="ProductPortfolio", short_info="Core portfolio of products."
            ))
            entity_map[primary_fam_id] = payload.entities[-1]
        else:
            primary_fam_id = str(all_families[0].temp_id)

        # Ensure Service Family exists if services are present
        has_services = any(norm(e.entity_type) in ps_types or any(x in str(e.canonical_name).lower() for x in ["icloud", "music", "cloud", "service"]) for e in payload.entities)
        if has_services and not service_fams:
            service_fam_id = "bridge_service_portfolio"
            payload.entities.append(EntityCandidate(
                temp_id=service_fam_id, canonical_name="Service Portfolio", 
                entity_type="ServicePortfolio", short_info="Portfolio of digital services."
            ))
            entity_map[service_fam_id] = payload.entities[-1]
        elif service_fams:
            service_fam_id = str(service_fams[0].temp_id)
        else:
            service_fam_id = None

        # --- PHASE 2: Relation Re-anchoring ---
        final_rels = []
        # We start with ALL relations that are NOT purely taxonomic (we'll rebuild the spine)
        tax_rel_types = {"HAS_PRODUCT_DOMAIN", "HAS_FAMILY", "HAS_PRODUCT_FAMILY", "HAS_SERVICE_PORTFOLIO", "INCLUDES", "HAS_PRODUCTS"}
        
        for r in payload.relations:
            src_id, tgt_id = str(r.source_temp_id), str(r.target_temp_id)
            if src_id not in entity_map or tgt_id not in entity_map: continue
            
            tgt_ent = entity_map[tgt_id]
            tgt_type = norm(tgt_ent.entity_type)
            tgt_name = str(tgt_ent.canonical_name).lower()

            # If it's a Line/Service, force move it to the right family
            if tgt_type in pl_types or tgt_type in ps_types:
                if service_fam_id and (tgt_type in ps_types or any(x in tgt_name for x in ["icloud", "music", "cloud", "service"])):
                    r.source_temp_id = service_fam_id
                else:
                    r.source_temp_id = primary_fam_id
                r.relation_type = "INCLUDES"
            
            # If it's a family being linked to root, move it to domain
            elif tgt_type in pf_types and src_id == root_id and tgt_id != primary_fam_id:
                r.source_temp_id = primary_dom_id
                r.relation_type = "HAS_FAMILY"
            
            # Filter out existing spine relations to avoid duplicates before we add our own
            if r.relation_type in tax_rel_types and tgt_id in [primary_dom_id, primary_fam_id, service_fam_id]:
                continue
                
            final_rels.append(r)

        # Add the Hard Spine
        # Root -> Domain
        final_rels.append(RelationCandidate(source_temp_id=root_id, target_temp_id=primary_dom_id, relation_type="HAS_PRODUCT_DOMAIN"))
        # Domain -> Family
        final_rels.append(RelationCandidate(source_temp_id=primary_dom_id, target_temp_id=primary_fam_id, relation_type="HAS_FAMILY"))
        # Root -> Service Portfolio
        if service_fam_id:
            final_rels.append(RelationCandidate(source_temp_id=root_id, target_temp_id=service_fam_id, relation_type="HAS_SERVICE_PORTFOLIO"))

        # --- PHASE 3: Connectivity & Pruning ---
        keep_ids = {root_id, primary_dom_id, primary_fam_id}
        if service_fam_id: keep_ids.add(service_fam_id)
        
        # Allowed entities are root, spine, lines, and non-taxonomic (Strategy, Financial, etc.)
        allowed_entities = []
        for e in payload.entities:
            eid = str(e.temp_id)
            etype = norm(e.entity_type)
            if eid in keep_ids or etype in pl_types or etype in ps_types or etype in non_tax_types:
                allowed_entities.append(e)
            else:
                logger.info(f"Purging redundant node: {e.canonical_name} ({e.entity_type})")
        
        payload.entities = allowed_entities
        allowed_ids = {str(e.temp_id) for e in payload.entities}

        # BFS for strict connectivity
        tree_rels = []
        visited = {root_id}
        queue = [root_id]
        
        # Filter rels to only include allowed IDs
        final_rels = [r for r in final_rels if str(r.source_temp_id) in allowed_ids and str(r.target_temp_id) in allowed_ids]
        
        while queue:
            curr = queue.pop(0)
            for r in final_rels:
                if str(r.source_temp_id) == curr:
                    tid = str(r.target_temp_id)
                    if tid not in visited:
                        tree_rels.append(r)
                        visited.add(tid)
                        queue.append(tid)
        
        # Orphan handling
        for e in payload.entities:
            eid = str(e.temp_id)
            if eid not in visited and eid != root_id:
                # strategy/financial nodes might be floating, anchor them to root or nearest
                tree_rels.append(RelationCandidate(
                    source_temp_id=root_id, 
                    target_temp_id=eid, 
                    relation_type="HAS_STRATEGY" if norm(e.entity_type) in ["strategy", "capability"] else "ASSOCIATED_WITH"
                ))
                visited.add(eid)

        payload.relations = tree_rels
        return payload

    def validate_extraction(self, payload: ExtractionPayload) -> List[str]:
        return []
