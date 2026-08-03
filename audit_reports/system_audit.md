# Coupon World System Audit

Generated: `2026-08-03T14:05:33.691838+00:00`

## Summary

- Python files: **45**
- Syntax errors: **2**
- Classes: **10**
- Functions: **380**
- Entrypoints: **32**
- Exact duplicate files: **0**
- Repeated function names: **42**
- Possible orphan modules: **6**

## Important Files

- PASS — `coupons.json`
- PASS — `index.html`
- PASS — `sitemap.xml`
- PASS — `python/couponworld.py`
- PASS — `python/build_product_pages.py`
- PASS — `python/build_sitemap.py`

## System Areas

### Audit / Monitoring
- `python\google_discovery_audit.py`
- `python\inventory_status_manager.py`
- `python\system_audit_agent.py`

### Build System
- `python\build_product_knowledge.py`
- `python\build_product_pages.py`
- `python\build_sitemap.py`

### Import / Intake
- `python\batch_product_importer.py`
- `python\batch_product_queue.py`
- `python\import_products.py`
- `python\migrate_product_schema.py`
- `python\price_importer.py`
- `python\product_queue.py`

### Master Controller
- `python\couponworld.py`

### Price / Inventory
- `python\price_engine.py`

### Product Intelligence
- `deal_engine.py`
- `python\intelligence\image_engine.py`
- `python\intent_engine.py`
- `python\internal_link_engine.py`
- `python\knowledge_engine.py`
- `python\product_engine.py`
- `python\product_feature_engine.py`
- `python\product_identity_engine.py`
- `python\product_identity_v2.py`
- `python\product_intelligence.py`
- `python\recommendation_engine.py`
- `python\resolver_engine.py`
- `python\site_intelligence.py`

### SEO / Discovery
- `data\python\seo_generator.py`
- `python\seo_generator.py`

### Shopping Intelligence
- `python\product_scoring.py`
- `python\shopping_brain.py`
- `python\shopping_brain_backup.py`

### Source / Data Adapter
- `python\amazon_catalog_sync.py`
- `python\amazon_data_provider.py`
- `python\official_source_resolver.py`
- `python\official_source_resolver_backup.py`
- `python\official_source_resolver_v3.py`
- `python\product_source_adapter.py`

### Utility / Other
- `coupon_bot.py`
- `python\official_spec_extractor.py`
- `python\product_classifier.py`
- `python\product_pipeline.py`
- `python\remove_amazon_branding.py`
- `python\research_agent.py`
- `python\tavily_test.py`

## Module Details

### `coupon_bot.py`
- Status: **PASS**
- Lines: 78 | Category: Utility / Other
- Functions: `amazon_link`, `load_existing`, `main`, `normalize`

### `data\python\seo_generator.py`
- Status: **PASS**
- Lines: 1 | Category: SEO / Discovery

### `deal_engine.py`
- Status: **PASS**
- Lines: 77 | Category: Product Intelligence
- Functions: `add_amazon_tag`, `clean`, `discount_text`, `main`

### `python\amazon_catalog_sync.py`
- Status: **PASS**
- Lines: 164 | Category: Source / Data Adapter
- Uses: `amazon_data_provider`
- Functions: `backup`, `calculate`, `load_products`, `main`, `save`

### `python\amazon_data_provider.py`
- Status: **PASS**
- Lines: 108 | Category: Source / Data Adapter
- Classes: `AmazonDataProvider`, `AmazonProductData`, `ManualAmazonProvider`, `UnavailableAmazonApiProvider`
- Functions: `get_default_provider`

### `python\batch_product_importer.py`
- Status: **PASS**
- Lines: 273 | Category: Import / Intake
- Uses: `amazon_data_provider`, `batch_product_queue`, `product_engine`, `product_pipeline`
- Functions: `build_record`, `import_csv`, `main`, `parse_arguments`, `prepare_csv`, `read_csv_rows`
- CLI commands: `import`, `prepare`

### `python\batch_product_queue.py`
- Status: **PASS**
- Lines: 178 | Category: Import / Intake
- Uses: `product_engine`, `product_pipeline`
- Classes: `QueueItem`
- Functions: `main`, `parse_arguments`, `print_report`, `read_urls`, `scan_urls`

### `python\build_product_knowledge.py`
- Status: **PASS**
- Lines: 649 | Category: Build System
- Functions: `build_approved_indexes`, `build_draft_index`, `create_draft`, `get_brand`, `get_product_id`, `load_approved_knowledge`, `load_existing_drafts`, `load_json`, `load_official_specs`, `load_products`, `load_research_results`, `main`, `merge_official_specs_into_draft`, `merge_research_into_draft`, `normalize_text`, `prepare_drafts`, `save_json`, `show_status`
- CLI commands: `prepare`, `status`

### `python\build_product_pages.py`
- Status: **PASS**
- Lines: 666 | Category: Build System
- Functions: `clean`, `detect_family`, `excerpt`, `load_products`, `main`, `page_dir`, `page_url`, `related`, `render`, `searchable_text`, `slugify`

### `python\build_sitemap.py`
- Status: **PASS**
- Lines: 261 | Category: Build System
- Functions: `add_url`, `canonical_url`, `clean`, `extra_page_urls`, `main`, `product_identity`, `product_path`, `product_url`, `slugify`

### `python\couponworld.py`
- Status: **PASS**
- Lines: 944 | Category: Master Controller
- Functions: `adapt_source`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_report`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls`, `slugify`, `validate_build_source`
- CLI commands: `adapt`, `build`, `check`, `import`, `intake`, `report`, `run`

### `python\google_discovery_audit.py`
- Status: **PASS**
- Lines: 791 | Category: Audit / Monitoring
- Functions: `clean`, `extract_canonical`, `extract_description`, `extract_title`, `has_disclosure`, `has_h1`, `has_schema`, `internal_href_to_url`, `is_noindex`, `load_sitemap`, `main`, `page_url`, `robots_audit`

### `python\import_products.py`
- Status: **PASS**
- Lines: 339 | Category: Import / Intake
- Functions: `clean`, `get_tag`, `load_existing`, `main`, `next_id`, `normalize_row`, `parse_int`, `read_csv`, `run_build`, `validate_rows`, `write_atomic`

### `python\intelligence\image_engine.py`
- Status: **PASS**
- Lines: 67 | Category: Product Intelligence
- Classes: `ImageEngine`
- Functions: `main`

### `python\intent_engine.py`
- Status: **PASS**
- Lines: 153 | Category: Product Intelligence
- Classes: `ShoppingIntent`
- Functions: `detect_brands`, `detect_budget`, `detect_category`, `detect_features`, `detect_intent`, `normalize`, `parse_query`

### `python\internal_link_engine.py`
- Status: **PASS**
- Lines: 457 | Category: Product Intelligence
- Functions: `active_products`, `clean`, `detect_family`, `main`, `page_directory`, `page_url`, `product_identity`, `related_products`, `searchable_text`, `slugify`

### `python\inventory_status_manager.py`
- Status: **PASS**
- Lines: 87 | Category: Audit / Monitoring
- Functions: `backup`, `load`, `main`, `num`, `save`
- CLI commands: `available`, `unavailable`

### `python\knowledge_engine.py`
- Status: **PASS**
- Lines: 26 | Category: Product Intelligence
- Functions: `load_product_knowledge`

### `python\migrate_product_schema.py`
- Status: **PASS**
- Lines: 215 | Category: Import / Intake
- Functions: `clean_text`, `create_backup`, `load_products`, `main`, `normalize_number`, `normalize_product`, `save_products`

### `python\official_source_resolver.py`
- Status: **PASS**
- Lines: 421 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `core_product_title`, `hostname_matches`, `is_unwanted_page`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `resolve_product`, `save_json`, `significant_tokens`, `token_match_score`

### `python\official_source_resolver_backup.py`
- Status: **PASS**
- Lines: 355 | Category: Source / Data Adapter
- Functions: `core_product_title`, `hostname_matches`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `resolve_product`, `save_json`, `significant_tokens`, `token_match_score`

### `python\official_source_resolver_v3.py`
- Status: **PASS**
- Lines: 0 | Category: Source / Data Adapter

### `python\official_spec_extractor.py`
- Status: **PASS**
- Lines: 1093 | Category: Utility / Other
- Functions: `add_specification`, `build_output`, `clean_text`, `extract_definition_lists`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_tables`, `feature_relevance_score`, `feature_scope`, `fetch_page`, `hostname`, `identity_tokens`, `is_noise_feature`, `is_unwanted_url`, `load_identity_index`, `load_json`, `main` ...
- CLI commands: `extract`, `status`

### `python\price_engine.py`
- Status: **PASS**
- Lines: 108 | Category: Price / Inventory
- Functions: `analyze_price`, `calculate_discount`, `check_budget`, `normalize_price`

### `python\price_importer.py`
- Status: **PASS**
- Lines: 230 | Category: Import / Intake
- Functions: `apply_updates`, `create_backup`, `find_product`, `load_products`, `load_updates`, `main`, `normalize_price`, `save_products`

### `python\product_classifier.py`
- Status: **PASS**
- Lines: 946 | Category: Utility / Other
- Functions: `build_taxonomy`, `classify_product`, `derive_features`, `get_product_id`, `load_json`, `main`, `normalize`, `phrase_match`, `print_report`, `save_json`, `utc_now`
- CLI commands: `build`, `status`

### `python\product_engine.py`
- Status: **PASS**
- Lines: 482 | Category: Product Intelligence
- Functions: `calculate_health`, `clean_text`, `create_backup`, `detect_brand`, `generate_description`, `improve_products`, `load_json`, `main`, `parse_arguments`, `print_preview`, `print_report`, `save_json`, `validate_products`

### `python\product_feature_engine.py`
- Status: **PASS**
- Lines: 1040 | Category: Product Intelligence
- Functions: `atomic_write`, `build_output`, `clean_text`, `extract_audio_features`, `extract_battery`, `extract_camera`, `extract_capacity`, `extract_charging`, `extract_color`, `extract_dimensions`, `extract_display_size`, `extract_material`, `extract_model_codes`, `extract_network`, `extract_pack_quantity`, `extract_playback_time`, `extract_power`, `extract_processor`, `extract_product_features`, `extract_ram` ...

### `python\product_identity_engine.py`
- Status: **PASS**
- Lines: 694 | Category: Product Intelligence
- Functions: `build_identity`, `canonical_product_id`, `clean_text`, `create_payload`, `detect_brand`, `detect_model`, `detect_subcategory`, `extract_asin`, `extract_launch_year`, `extract_variant`, `identity_confidence`, `load_products`, `main`, `normalize_category`, `parse_args`, `print_report`, `product_identifier`, `slugify`, `write_output`

### `python\product_identity_v2.py`
- Status: **FAIL**
- Lines: 358 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\product_intelligence.py`
- Status: **PASS**
- Lines: 745 | Category: Product Intelligence
- Functions: `build_description`, `clean`, `database_health`, `detect_brand`, `duplicate_values`, `enrichment_score`, `has_value`, `link_type`, `main`, `normalize_text`, `print_section`, `product_completeness`, `product_identity`, `product_missing_fields`, `proposal_confidence`

### `python\product_pipeline.py`
- Status: **PASS**
- Lines: 203 | Category: Utility / Other
- Uses: `amazon_data_provider`, `product_engine`
- Functions: `build_affiliate_url`, `build_record`, `collect_interactive_input`, `confirm_write`, `existing_asin`, `extract_asin`, `find_duplicate`, `main`, `next_product_id`, `parse_arguments`, `print_preview`, `validate_url`

### `python\product_queue.py`
- Status: **PASS**
- Lines: 558 | Category: Import / Intake
- Functions: `allocate_batch`, `category_health`, `clean`, `has_asin`, `has_image`, `has_price`, `link_type`, `main`, `print_section`, `priority_score`, `product_identity`

### `python\product_scoring.py`
- Status: **PASS**
- Lines: 60 | Category: Shopping Intelligence
- Functions: `score_product`

### `python\product_source_adapter.py`
- Status: **PASS**
- Lines: 214 | Category: Source / Data Adapter
- Functions: `add_affiliate_tag`, `clean`, `detect_link_type`, `main`, `normalize_price`, `normalize_row`

### `python\recommendation_engine.py`
- Status: **PASS**
- Lines: 69 | Category: Product Intelligence
- Functions: `explain_product`

### `python\remove_amazon_branding.py`
- Status: **PASS**
- Lines: 166 | Category: Utility / Other
- Functions: `backup_file`, `clean_json_value`, `clean_text`, `main`, `process_json_file`, `process_text_file`

### `python\research_agent.py`
- Status: **PASS**
- Lines: 64 | Category: Utility / Other

### `python\resolver_engine.py`
- Status: **PASS**
- Lines: 584 | Category: Product Intelligence
- Classes: `ParsedIdentity`, `ResolverDecision`
- Functions: `compare_identity`, `equivalent_model`, `extract_brand`, `extract_color_tokens`, `extract_memory_tokens`, `infer_brand_from_url`, `model_score`, `normalize_text`, `parse_identity`, `subset_match`, `tokenize`, `validate_candidate`

### `python\seo_generator.py`
- Status: **PASS**
- Lines: 57 | Category: SEO / Discovery
- Functions: `generate_page`, `main`, `safe_text`

### `python\shopping_brain.py`
- Status: **PASS**
- Lines: 875 | Category: Shopping Intelligence
- Uses: `intent_engine`, `knowledge_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `_index_by_product_id`, `_load_database`, `_normalize_query_text`, `build_response`, `infer_requested_product_types`, `load_feature_database`, `load_identity_database`, `load_products`, `load_taxonomy_database`, `main`, `match_products`, `merge_intelligence`, `merge_product_knowledge`, `merge_taxonomy`, `print_text_response`, `taxonomy_match_score`, `taxonomy_search_text`

### `python\shopping_brain_backup.py`
- Status: **FAIL**
- Lines: 280 | Category: Shopping Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\site_intelligence.py`
- Status: **PASS**
- Lines: 355 | Category: Product Intelligence
- Functions: `clean`, `determine_next_action`, `has_price`, `identity`, `is_product_link`, `main`, `missing_fields`, `percentage`, `priority_score`

### `python\system_audit_agent.py`
- Status: **PASS**
- Lines: 338 | Category: Audit / Monitoring
- Classes: `ModuleInfo`
- Functions: `args`, `build`, `category`, `cli_commands`, `coupons`, `git`, `main`, `markdown`, `module_name`, `parse_module`, `py_files`

### `python\tavily_test.py`
- Status: **PASS**
- Lines: 23 | Category: Utility / Other

## Review Warnings

### Syntax Errors
- `python\product_identity_v2.py` — Line 1: invalid non-printable character U+FEFF
- `python\shopping_brain_backup.py` — Line 1: invalid non-printable character U+FEFF

### Possible Orphan Modules
- `data.python.seo_generator`
- `official_source_resolver_v3`
- `product_identity_v2`
- `research_agent`
- `shopping_brain_backup`
- `tavily_test`

### Repeated Public Function Names
Repeated names are review indicators, not automatic bugs.
- `backup`: `amazon_catalog_sync`, `inventory_status_manager`
- `build_output`: `official_spec_extractor`, `product_feature_engine`
- `build_record`: `batch_product_importer`, `product_pipeline`
- `clean`: `build_product_pages`, `build_sitemap`, `deal_engine`, `google_discovery_audit`, `import_products`, `internal_link_engine`, `product_intelligence`, `product_queue`, `product_source_adapter`, `site_intelligence`
- `clean_text`: `migrate_product_schema`, `official_spec_extractor`, `product_engine`, `product_feature_engine`, `product_identity_engine`, `remove_amazon_branding`
- `core_product_title`: `official_source_resolver`, `official_source_resolver_backup`
- `create_backup`: `migrate_product_schema`, `price_importer`, `product_engine`
- `detect_brand`: `product_engine`, `product_identity_engine`, `product_intelligence`
- `detect_family`: `build_product_pages`, `internal_link_engine`
- `extract_asin`: `product_identity_engine`, `product_pipeline`
- `get_product_id`: `build_product_knowledge`, `product_classifier`
- `has_price`: `product_queue`, `site_intelligence`
- `hostname_matches`: `official_source_resolver`, `official_source_resolver_backup`
- `link_type`: `product_intelligence`, `product_queue`
- `load_existing`: `coupon_bot`, `import_products`
- `load_json`: `build_product_knowledge`, `official_source_resolver`, `official_source_resolver_backup`, `official_spec_extractor`, `product_classifier`, `product_engine`, `product_feature_engine`
- `load_products`: `amazon_catalog_sync`, `build_product_knowledge`, `build_product_pages`, `couponworld`, `migrate_product_schema`, `price_importer`, `product_feature_engine`, `product_identity_engine`, `shopping_brain`
- `main`: `amazon_catalog_sync`, `batch_product_importer`, `batch_product_queue`, `build_product_knowledge`, `build_product_pages`, `build_sitemap`, `coupon_bot`, `couponworld`, `deal_engine`, `google_discovery_audit`, `import_products`, `intelligence.image_engine`, `internal_link_engine`, `inventory_status_manager`, `migrate_product_schema`, `official_source_resolver`, `official_source_resolver_backup`, `official_spec_extractor`, `price_importer`, `product_classifier`, `product_engine`, `product_feature_engine`, `product_identity_engine`, `product_intelligence`, `product_pipeline`, `product_queue`, `product_source_adapter`, `remove_amazon_branding`, `seo_generator`, `shopping_brain`, `site_intelligence`, `system_audit_agent`
- `normalize`: `coupon_bot`, `intent_engine`, `product_classifier`
- `normalize_brand`: `official_source_resolver`, `official_source_resolver_backup`
- `normalize_number`: `migrate_product_schema`, `product_feature_engine`
- `normalize_price`: `price_engine`, `price_importer`, `product_source_adapter`
- `normalize_row`: `import_products`, `product_source_adapter`
- `normalize_text`: `build_product_knowledge`, `official_source_resolver`, `official_source_resolver_backup`, `product_intelligence`, `resolver_engine`
- `page_directory`: `couponworld`, `internal_link_engine`
- `page_url`: `build_product_pages`, `google_discovery_audit`, `internal_link_engine`
- `parse_args`: `product_feature_engine`, `product_identity_engine`
- `parse_arguments`: `batch_product_importer`, `batch_product_queue`, `product_engine`, `product_pipeline`
- `print_preview`: `product_engine`, `product_pipeline`
- `print_report`: `batch_product_queue`, `product_classifier`, `product_engine`, `product_feature_engine`, `product_identity_engine`
- `print_section`: `couponworld`, `product_intelligence`, `product_queue`
- `priority_score`: `product_queue`, `site_intelligence`
- `product_identity`: `build_sitemap`, `couponworld`, `internal_link_engine`, `product_intelligence`, `product_queue`
- `resolve_product`: `official_source_resolver`, `official_source_resolver_backup`
- `save`: `amazon_catalog_sync`, `inventory_status_manager`
- `save_json`: `build_product_knowledge`, `official_source_resolver`, `official_source_resolver_backup`, `official_spec_extractor`, `product_classifier`, `product_engine`
- `save_products`: `migrate_product_schema`, `price_importer`
- `searchable_text`: `build_product_pages`, `internal_link_engine`
- `significant_tokens`: `official_source_resolver`, `official_source_resolver_backup`
- `slugify`: `build_product_pages`, `build_sitemap`, `couponworld`, `internal_link_engine`, `product_identity_engine`
- `token_match_score`: `official_source_resolver`, `official_source_resolver_backup`
- `utc_now`: `official_spec_extractor`, `product_classifier`

## Product Database

- Products: **74**
- Missing `sl_no`: **74**
- Missing `image`: **57**
- Missing `price`: **74**
- Missing `mrp`: **74**
- Missing `brand`: **7**

## Decision Rule

Before making a new engine: check existing responsibility, extend the matching module, and create a new module only for a genuinely separate responsibility.
