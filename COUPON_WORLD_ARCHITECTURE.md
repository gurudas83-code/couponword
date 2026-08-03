# Coupon World Architecture Map

**Project:** Coupon World  
**Current phase:** System completion and integration  
**Vision:** The World's First AI Shopping Intelligence Platform  
**Architecture status:** Frozen for v1.0

## 1. Core Runtime Flow

```text
User Query
   ↓
intent_engine.py
   ↓
shopping_brain.py
   ├── product_identity_engine.py / product_identity_v2.py
   ├── product_feature_engine.py
   ├── product_classifier.py
   ├── build_product_knowledge.py / knowledge_engine.py
   ├── product_scoring.py
   ├── recommendation_engine.py
   └── price_engine.py
   ↓
Structured Shopping Response
   ↓
data/shopping_response.json
   ↓
app.js
   ↓
Website Recommendation Card
```

## 2. Main Orchestrator

### `python/couponworld.py`
**Role:** Main command-line control center.

**Known responsibilities**
- Product validation
- Build orchestration
- Product intake
- Product import
- Source adaptation
- Intelligence reporting
- Safe workflow execution

**Important functions**
- `check_command()`
- `build_command()`
- `intake_products()`
- `import_products()`
- `adapt_source()`
- `intelligence_report()`
- `run_workflow()`

**Status:** READY  
**Decision:** KEEP  
**Next action:** Extend only after existing module dependencies are mapped.

## 3. Query and Recommendation Layer

### `python/intent_engine.py`
**Role:** Convert a shopping query into structured intent.

**Outputs**
- intent type
- category
- budget
- features
- brands
- comparison flag
- keywords

**Status:** READY, but basic  
**Decision:** KEEP  
**Next action:** Improve later during Need Understanding phase.

### `python/shopping_brain.py`
**Role:** Main shopping recommendation engine.

**Existing capabilities**
- Loads identity, feature, taxonomy and knowledge data
- Merges product intelligence
- Infers requested product types
- Scores taxonomy matches
- Filters and ranks products
- Builds structured responses

**Important functions**
- `load_identity_database()`
- `load_feature_database()`
- `load_taxonomy_database()`
- `merge_intelligence()`
- `merge_taxonomy()`
- `merge_product_knowledge()`
- `match_products()`
- `build_response()`

**Status:** READY and active  
**Decision:** KEEP  
**Next action:** Do not rewrite. Feed it better verified data and published knowledge.

### `python/product_scoring.py`
**Role:** Base product scoring.

**Status:** BASIC  
**Decision:** KEEP  
**Next action:** Extend only after knowledge and marketplace data are stable.

### `python/recommendation_engine.py`
**Role:** Generates recommendation reasons.

**Status:** BASIC  
**Known gap:** Produces `No matching reason available` when knowledge is missing.  
**Decision:** KEEP  
**Next action:** Improve after knowledge publishing.

## 4. Product Identity and Source Resolution

### `python/product_identity_engine.py`
**Role:** Build canonical product identity.

**Capabilities**
- ASIN extraction
- Brand detection
- Category normalization
- Variant extraction
- Model detection
- Identity confidence
- Canonical product ID

**Status:** READY  
**Decision:** KEEP

### `python/product_identity_v2.py`
**Role:** Newer/simplified identity model.

**Status:** PARTIAL / parallel implementation  
**Decision:** REVIEW BEFORE MERGE  
**Next action:** Determine which identity output is used by downstream files.

### `python/resolver_engine.py`
**Role:** Validate whether a candidate page matches the expected product.

**Capabilities**
- Brand/model parsing
- Memory and color token extraction
- Identity comparison
- Candidate validation

**Status:** READY  
**Decision:** KEEP

### `python/official_source_resolver.py`
**Role:** Find and validate official product pages using Tavily plus strict identity rules.

**Status:** READY  
**Decision:** KEEP

### Legacy candidates
- `official_source_resolver_backup.py`
- `official_source_resolver_v3.py` (empty)

**Status:** LEGACY  
**Decision:** Do not delete yet; exclude from active workflow.

## 5. Product Feature and Taxonomy Layer

### `python/product_feature_engine.py`
**Role:** Extract structured product features.

**Capabilities include**
- RAM
- Storage
- Battery
- Charging
- Display size
- Resolution
- Refresh rate
- Camera
- Processor
- Network
- Audio
- Playback time
- Capacity
- Power
- Material
- Dimensions
- Color
- Model codes

**Status:** READY  
**Decision:** KEEP  
**Next action:** Verify its generated output is loaded by Shopping Brain.

### `python/product_classifier.py`
**Role:** Product taxonomy generation.

**Current result**
- 74 total products
- 72 classified
- 2 excluded promotional listings
- 47 product types
- 42 shopping categories

**Status:** READY  
**Decision:** KEEP

### `python/product_intelligence.py`
**Role:** Catalogue quality and enrichment analysis.

**Status:** AUDIT/ENRICHMENT SUPPORT  
**Decision:** KEEP  
**Next action:** Use for data gap prioritisation, not as the main decision engine.

## 6. Official Specification and Knowledge Layer

### `python/official_spec_extractor.py`
**Role:** Extract structured specs and features from official pages.

**Capabilities**
- JSON-LD
- HTML tables
- Definition lists
- Label/value blocks
- Meta data
- Identity scoring
- Noise filtering

**Status:** READY  
**Decision:** KEEP

### `python/build_product_knowledge.py`
**Role:** Build and publish product knowledge.

**Current result**
- Published knowledge: 1
- Drafts awaiting review: 73

**Status:** PARTIAL  
**Decision:** KEEP  
**Main gap:** Review/publish workflow is incomplete.

### `python/knowledge_engine.py`
**Role:** Lightweight loader for published product knowledge.

**Status:** READY but minimal  
**Decision:** KEEP

## 7. Marketplace, Price and Availability Layer

### `python/amazon_data_provider.py`
**Role:** Provider abstraction for Amazon product data.

**Known classes**
- `AmazonProductData`
- `AmazonDataProvider`
- `ManualAmazonProvider`
- `UnavailableAmazonApiProvider`

**Status:** PARTIAL  
**Important finding:** The abstraction exists, but a working live API provider has not been confirmed.

### `python/amazon_catalog_sync.py`
**Role:** Synchronise catalogue fields such as price/MRP.

**Status:** PARTIAL  
**Decision:** REVIEW

### `python/product_source_adapter.py`
**Role:** Normalize source rows, link type, prices and affiliate tags.

**Status:** READY  
**Decision:** KEEP

### `python/price_engine.py`
**Role:** Price normalization, discount and budget analysis.

**Status:** READY but depends on valid price data  
**Decision:** KEEP

### `python/price_importer.py`
**Role:** Apply verified price updates from CSV.

**Status:** READY  
**Decision:** KEEP

### `python/inventory_status_manager.py`
**Role:** Manage inventory/availability status.

**Status:** PARTIAL  
**Decision:** REVIEW

### Marketplace audit result
- Direct product links: 27
- Search/other links: 47
- Missing images: 57
- Missing prices: 74
- Missing ASINs: 54

**Conclusion:** Marketplace/data quality is currently the largest operational gap.

## 8. Product Intake and Import Layer

### `python/product_pipeline.py`
**Role:** Add a single validated Amazon product.

### `python/import_products.py`
**Role:** CSV validation and import.

### `python/batch_product_importer.py`
**Role:** Batch import preparation and execution.

### `python/batch_product_queue.py`
**Role:** URL batch queue preparation.

### `python/product_queue.py`
**Role:** Prioritise products needing enrichment.

### `python/migrate_product_schema.py`
**Role:** Normalize database schema.

**Status of import layer:** READY  
**Decision:** KEEP

## 9. Build, SEO and Delivery Layer

### `python/build_product_pages.py`
**Role:** Generate product pages.

### `python/build_sitemap.py`
**Role:** Generate sitemap.

### `python/internal_link_engine.py`
**Role:** Generate related/internal product links.

### `python/seo_generator.py`
**Role:** Generate SEO pages/templates.

### `python/google_discovery_audit.py`
**Role:** Audit crawlability, metadata, canonical URLs, schema and internal links.

**Status:** READY  
**Decision:** KEEP

## 10. Audit and Control Layer

### `python/site_intelligence.py`
**Role:** Read-only data completeness audit.

### `python/system_audit_agent.py`
**Role:** AST-based module, CLI and system audit.

### Current audit result
- Core Python files compile
- Product/page/sitemap counts are consistent
- Affiliate tags are correct in active product data
- One old wrong tag remains in `system_core_audit.txt`
- Core JSON files are valid
- Shopping Brain returns the expected Logitech keyboard result

**Status:** READY  
**Decision:** KEEP

## 11. Legacy and Backup Files

Candidates:
- `shopping_brain_backup.py`
- `official_source_resolver_backup.py`
- `official_source_resolver_v3.py`
- `tavily_test.py`

**Rule:** Do not delete until active imports and Git history are verified.

## 12. Frozen Execution Order

1. Repository map and active dependency verification
2. Backend cleanup without deleting unverified files
3. Marketplace/data integration
4. Product knowledge review and publishing
5. Recommendation/decision quality improvement
6. Need understanding
7. Frontend intelligence
8. SEO and traffic
9. Revenue optimisation

## 13. Immediate Next Task

### Task-002 — Active Dependency Map

We must determine:
- Which modules are imported by `couponworld.py`
- Which modules are imported by `shopping_brain.py`
- Which generated JSON files each active module reads/writes
- Which modules are not used anywhere
- Whether `product_identity_engine.py` or `product_identity_v2.py` is the active identity source

No new engine should be created before Task-002 is complete.
