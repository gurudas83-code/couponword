# Coupon World System Audit

Generated: `2026-07-26T16:46:04.068311+00:00`

## Summary

- Python files: **33**
- Syntax errors: **0**
- Classes: **8**
- Functions: **276**
- Entrypoints: **27**
- Exact duplicate files: **0**
- Repeated function names: **31**
- Possible orphan modules: **1**

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
- `python\product_engine.py`
- `python\product_feature_engine.py`
- `python\product_identity_engine.py`
- `python\product_intelligence.py`
- `python\recommendation_engine.py`
- `python\site_intelligence.py`

### SEO / Discovery
- `data\python\seo_generator.py`
- `python\seo_generator.py`

### Shopping Intelligence
- `python\product_scoring.py`
- `python\shopping_brain.py`

### Source / Data Adapter
- `python\amazon_catalog_sync.py`
- `python\amazon_data_provider.py`
- `python\product_source_adapter.py`

### Utility / Other
- `coupon_bot.py`
- `python\product_pipeline.py`
- `python\remove_amazon_branding.py`

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

### `python\migrate_product_schema.py`
- Status: **PASS**
- Lines: 215 | Category: Import / Intake
- Functions: `clean_text`, `create_backup`, `load_products`, `main`, `normalize_number`, `normalize_product`, `save_products`

### `python\price_engine.py`
- Status: **PASS**
- Lines: 108 | Category: Price / Inventory
- Functions: `analyze_price`, `calculate_discount`, `check_budget`, `normalize_price`

### `python\price_importer.py`
- Status: **PASS**
- Lines: 230 | Category: Import / Intake
- Functions: `apply_updates`, `create_backup`, `find_product`, `load_products`, `load_updates`, `main`, `normalize_price`, `save_products`

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

### `python\seo_generator.py`
- Status: **PASS**
- Lines: 57 | Category: SEO / Discovery
- Functions: `generate_page`, `main`, `safe_text`

### `python\shopping_brain.py`
- Status: **PASS**
- Lines: 189 | Category: Shopping Intelligence
- Uses: `intent_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `load_products`, `main`, `match_products`

### `python\site_intelligence.py`
- Status: **PASS**
- Lines: 355 | Category: Product Intelligence
- Functions: `clean`, `determine_next_action`, `has_price`, `identity`, `is_product_link`, `main`, `missing_fields`, `percentage`, `priority_score`

### `python\system_audit_agent.py`
- Status: **PASS**
- Lines: 338 | Category: Audit / Monitoring
- Classes: `ModuleInfo`
- Functions: `args`, `build`, `category`, `cli_commands`, `coupons`, `git`, `main`, `markdown`, `module_name`, `parse_module`, `py_files`

## Review Warnings

### Possible Orphan Modules
- `data.python.seo_generator`

### Repeated Public Function Names
Repeated names are review indicators, not automatic bugs.
- `backup`: `amazon_catalog_sync`, `inventory_status_manager`
- `build_record`: `batch_product_importer`, `product_pipeline`
- `clean`: `build_product_pages`, `build_sitemap`, `deal_engine`, `google_discovery_audit`, `import_products`, `internal_link_engine`, `product_intelligence`, `product_queue`, `product_source_adapter`, `site_intelligence`
- `clean_text`: `migrate_product_schema`, `product_engine`, `product_feature_engine`, `product_identity_engine`, `remove_amazon_branding`
- `create_backup`: `migrate_product_schema`, `price_importer`, `product_engine`
- `detect_brand`: `product_engine`, `product_identity_engine`, `product_intelligence`
- `detect_family`: `build_product_pages`, `internal_link_engine`
- `extract_asin`: `product_identity_engine`, `product_pipeline`
- `has_price`: `product_queue`, `site_intelligence`
- `link_type`: `product_intelligence`, `product_queue`
- `load_existing`: `coupon_bot`, `import_products`
- `load_json`: `product_engine`, `product_feature_engine`
- `load_products`: `amazon_catalog_sync`, `build_product_pages`, `couponworld`, `migrate_product_schema`, `price_importer`, `product_feature_engine`, `product_identity_engine`, `shopping_brain`
- `main`: `amazon_catalog_sync`, `batch_product_importer`, `batch_product_queue`, `build_product_pages`, `build_sitemap`, `coupon_bot`, `couponworld`, `deal_engine`, `google_discovery_audit`, `import_products`, `intelligence.image_engine`, `internal_link_engine`, `inventory_status_manager`, `migrate_product_schema`, `price_importer`, `product_engine`, `product_feature_engine`, `product_identity_engine`, `product_intelligence`, `product_pipeline`, `product_queue`, `product_source_adapter`, `remove_amazon_branding`, `seo_generator`, `shopping_brain`, `site_intelligence`, `system_audit_agent`
- `normalize`: `coupon_bot`, `intent_engine`
- `normalize_number`: `migrate_product_schema`, `product_feature_engine`
- `normalize_price`: `price_engine`, `price_importer`, `product_source_adapter`
- `normalize_row`: `import_products`, `product_source_adapter`
- `page_directory`: `couponworld`, `internal_link_engine`
- `page_url`: `build_product_pages`, `google_discovery_audit`, `internal_link_engine`
- `parse_args`: `product_feature_engine`, `product_identity_engine`
- `parse_arguments`: `batch_product_importer`, `batch_product_queue`, `product_engine`, `product_pipeline`
- `print_preview`: `product_engine`, `product_pipeline`
- `print_report`: `batch_product_queue`, `product_engine`, `product_feature_engine`, `product_identity_engine`
- `print_section`: `couponworld`, `product_intelligence`, `product_queue`
- `priority_score`: `product_queue`, `site_intelligence`
- `product_identity`: `build_sitemap`, `couponworld`, `internal_link_engine`, `product_intelligence`, `product_queue`
- `save`: `amazon_catalog_sync`, `inventory_status_manager`
- `save_products`: `migrate_product_schema`, `price_importer`
- `searchable_text`: `build_product_pages`, `internal_link_engine`
- `slugify`: `build_product_pages`, `build_sitemap`, `couponworld`, `internal_link_engine`, `product_identity_engine`

## Product Database

- Products: **74**
- Missing `sl_no`: **74**
- Missing `image`: **57**
- Missing `price`: **73**
- Missing `mrp`: **73**
- Missing `brand`: **7**

## Decision Rule

Before making a new engine: check existing responsibility, extend the matching module, and create a new module only for a genuinely separate responsibility.
