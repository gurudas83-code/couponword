# Coupon World System Audit

Generated: `2026-08-13T15:16:46.000931+00:00`

## Summary

- Python files: **280**
- Syntax errors: **59**
- Classes: **27**
- Functions: **3726**
- Entrypoints: **187**
- Exact duplicate files: **15**
- Repeated function names: **253**
- Possible orphan modules: **80**

## Important Files

- PASS — `coupons.json`
- PASS — `index.html`
- PASS — `sitemap.xml`
- PASS — `python/couponworld.py`
- PASS — `python/build_product_pages.py`
- PASS — `python/build_sitemap.py`

## System Areas

### Audit / Monitoring
- `python\couponworld_complete_audit.py`
- `python\couponworld_complete_audit_before_bom_fix_20260809.py`
- `python\google_discovery_audit.py`
- `python\inventory_status_manager.py`
- `python\system_audit_agent.py`

### Build System
- `python\build_product_knowledge.py`
- `python\build_product_pages.py`
- `python\build_product_pages_before_intelligence_v1.py`
- `python\build_product_pages_before_published_gate.py`
- `python\build_product_pages_before_published_gate_20260809_002946.py`
- `python\build_product_pages_before_verified_intelligence_20260808_232718.py`
- `python\build_sitemap.py`

### Image System
- `python\official_spec_extractor_before_universal_images_20260810_202111.py`

### Import / Intake
- `install_vision_evidence_queue_v1.py`
- `install_vision_provenance_import_gate_v1.py`
- `install_vision_result_importer_v1.py`
- `python\batch_product_importer.py`
- `python\batch_product_queue.py`
- `python\import_products.py`
- `python\migrate_product_schema.py`
- `python\official_spec_extractor_before_vision_queue_20260807_214124.py`
- `python\official_spec_extractor_before_vision_result_importer_20260807_222125.py`
- `python\price_importer.py`
- `python\product_queue.py`

### Master Controller
- `python\couponworld.py`

### Price / Inventory
- `diagnose_embedded_media_inventory.py`
- `python\price_engine.py`
- `python\retail_price_evidence.py`
- `python\retail_price_evidence_before_v11_20260809.py`
- `python\retail_price_evidence_before_v12_cache_20260809.py`
- `python\shopping_intelligence_pipeline_before_price_evidence_20260809.py`

### Product Intelligence
- `add_nothing_identity_domain.py`
- `deal_engine.py`
- `diagnose_nothing_identity.py`
- `fix_intent_engine_v2_gamer_profile.py`
- `install_couponworld_intelligence_command_v1.py`
- `install_decision_engine_v1.py`
- `install_decision_engine_v1_1.py`
- `install_decision_engine_v1_2.py`
- `install_intelligence_batch_id_freezer_v1.py`
- `install_intelligence_partial_evidence_mode_v1.py`
- `install_intelligence_vision_v2_orchestration.py`
- `install_verified_intelligence_renderer_v1.py`
- `python\couponworld_before_intelligence_v1_20260808_114212.py`
- `python\intelligence\image_engine.py`
- `python\intelligence\verified_image_engine.py`
- `python\intelligence\verified_image_engine_before_diagnostics_20260810_201836.py`
- `python\intelligence\verified_image_engine_before_exact_href_priority_20260811_235820.py`
- `python\intelligence\verified_image_engine_before_exact_product_v2.py`
- `python\intelligence\verified_image_engine_before_meta_shortlist_20260810_230418.py`
- `python\intelligence\verified_image_engine_before_official_context_fallback_20260812_232525.py`
- `python\intelligence\verified_image_engine_before_quota_output_20260812_232320.py`
- `python\intelligence\verified_image_engine_before_quota_stop_20260812_232133.py`
- `python\intent_engine.py`
- `python\intent_engine_before_explicit_priority_20260809.py`
- `python\intent_engine_before_feature_v2_20260805_232541.py`
- `python\intent_engine_before_gamer_profile_fix_20260809_143059.py`
- `python\intent_engine_before_v2_20260809.py`
- `python\internal_link_engine.py`
- `python\knowledge_engine.py`
- `python\market_identity_bridge.py`
- `python\official_spec_extractor_before_identity_fields_20260811_224104.py`
- `python\official_spec_extractor_before_identity_fields_20260811_224248.py`
- `python\official_spec_extractor_before_identity_gate_20260811_224557.py`
- `python\official_spec_extractor_before_identity_parser_20260811_224512.py`
- `python\official_spec_extractor_before_identity_result_fields_20260811_224653.py`
- `python\official_spec_extractor_before_identity_rules_20260811_224433.py`
- `python\official_spec_extractor_before_identity_vision_gate_20260811_223906.py`
- `python\official_spec_extractor_before_prompt_identity_schema_20260811_224344.py`
- `python\product_engine.py`
- `python\product_feature_engine.py`
- `python\product_identity_engine.py`
- `python\product_identity_v2.py`
- `python\product_intelligence.py`
- `python\product_intelligence_bridge.py`
- `python\recommendation_engine.py`
- `python\recommendation_engine_before_match_v1_20260803_230715.py`
- `python\resolver_engine.py`
- `python\resolver_engine_before_alpha_exact_fix_20260810_001430.py`
- `python\resolver_engine_before_brand_registry_20260808_231140.py`
- `python\resolver_engine_before_domain_noise_fix_20260810_001348.py`
- `python\resolver_engine_before_nothing_domain_20260804_224458.py`
- `python\shopping_brain_before_decision_engine_20260805_235240.py`
- `python\shopping_brain_before_decision_engine_20260805_235607.py`
- `python\shopping_decision_engine.py`
- `python\shopping_intelligence_pipeline.py`
- `python\shopping_intelligence_pipeline_before_brand_fix_20260809.py`
- `python\shopping_intelligence_pipeline_before_evidence_diag_20260809.py`
- `python\shopping_intelligence_pipeline_before_fit_diagnostics_20260809.py`
- `python\shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835.py`
- `python\shopping_intelligence_pipeline_before_resolver_diag_20260810_000343.py`
- `python\shopping_intelligence_pipeline_before_resolver_resilience_20260809.py`
- `python\site_intelligence.py`
- `python\weighted_fit_engine.py`
- `python\weighted_fit_engine_before_budget_unknown_gate_20260810_000816.py`
- `python\weighted_fit_engine_before_must_have_signal_gate_20260809.py`
- `upgrade_intent_engine_features_v2.py`

### SEO / Discovery
- `data\python\seo_generator.py`
- `python\seo_generator.py`

### Shopping Intelligence
- `python\product_scoring.py`
- `python\real_recommendation_ranker.py`
- `python\shopping_brain.py`
- `python\shopping_brain_backup.py`
- `python\shopping_brain_before_knowledge_gate_20260805_235931.py`
- `python\shopping_brain_before_knowledge_score_20260805_223921.py`
- `python\shopping_brain_before_match_v1_20260803_230715.py`
- `python\shopping_brain_before_requirement_match_finish_20260803_231339.py`

### Source / Data Adapter
- `diagnose_supporting_source_snippets.py`
- `diagnose_universal_source_discovery.py`
- `install_resolver_source_family_stability_v1.py`
- `install_universal_source_discovery_v1.py`
- `install_universal_vision_provider_v1.py`
- `python\amazon_catalog_sync.py`
- `python\amazon_data_provider.py`
- `python\official_source_resolver.py`
- `python\official_source_resolver_backup.py`
- `python\official_source_resolver_before_batch_quota_break_20260813_203745.py`
- `python\official_source_resolver_before_brand_expansion_20260804_222957.py`
- `python\official_source_resolver_before_brand_registry_20260808_184921.py`
- `python\official_source_resolver_before_identity_gate_20260810_232936.py`
- `python\official_source_resolver_before_identity_override_20260810_233123.py`
- `python\official_source_resolver_before_model_filter_20260804_225625.py`
- `python\official_source_resolver_before_model_normalization_20260806_234104.py`
- `python\official_source_resolver_before_page_priority_20260804_225410.py`
- `python\official_source_resolver_before_page_priority_20260805_230553.py`
- `python\official_source_resolver_before_query_improvement_20260804_223535.py`
- `python\official_source_resolver_before_quota_stop_20260813_203309.py`
- `python\official_source_resolver_before_quota_stop_20260813_203605.py`
- `python\official_source_resolver_before_source_stability_20260808_124706.py`
- `python\official_source_resolver_before_universal_sources_20260806_233209.py`
- `python\official_source_resolver_v3.py`
- `python\official_spec_extractor_before_vision_provider_20260807_215532.py`
- `python\product_source_adapter.py`

### Utility / Other
- `add_ask_command.py`
- `add_resolver_model_score_filter.py`
- `apply_requirement_match_v1.py`
- `approve_apple_iphone_17e_knowledge.py`
- `approve_logitech_knowledge.py`
- `approve_nothing_phone_3_knowledge.py`
- `approve_product_11_from_semantic_v1.py`
- `coupon_bot.py`
- `diagnose_apple_specs_structure.py`
- `diagnose_embedded_free_text.py`
- `diagnose_media_dimensions.py`
- `diagnose_media_ranking.py`
- `diagnose_nothing_embedded_data.py`
- `diagnose_nothing_product_evidence.py`
- `diagnose_nothing_search.py`
- `diagnose_nuxt_product_payload.py`
- `diagnose_nuxt_reference_graph.py`
- `diagnose_realme_embedded_data.py`
- `diagnose_search_evidence.py`
- `diagnose_universal_page_content.py`
- `diagnose_vision_validation_reasons.py`
- `download_media_candidates.py`
- `finish_requirement_match_v1.py`
- `fix_couponworld_vision_script_key_v1.py`
- `fix_couponworld_vision_script_key_v2.py`
- `fix_couponworld_vision_script_key_v3.py`
- `fix_display_parser.py`
- `fix_display_size_v2.py`
- `fix_extractor_core_title.py`
- `fix_universal_embedded_state_precision_v1_1.py`
- `improve_candidate_page_priority.py`
- `improve_resolver_queries.py`
- `install_apple_techspecs_extractor_v1.py`
- `install_brand_domain_registry_expansion_v1.py`
- `install_final_vision_knowledge_review_gate_v1.py`
- `install_knowledge_command_v1.py`
- `install_knowledge_gate_v2.py`
- `install_knowledge_match_score_v1.py`
- `install_knowledge_ranking_v1.py`
- `install_published_knowledge_gate_v1.py`
- `install_resolver_brand_registry_v1.py`
- `install_semantic_partial_state_persistence_v1.py`
- `install_shopify_oxygen_extractor_v6.py`
- `install_universal_embedded_state_v1.py`
- `install_universal_evidence_collector_v1.py`
- `install_universal_media_evidence_v1.py`
- `install_universal_media_ranker_v1.py`
- `install_universal_model_normalization_v1.py`
- `install_universal_semantic_cli_v1.py`
- `install_universal_semantic_core_v1_3.py`
- `install_universal_structured_sections_v1.py`
- `install_universal_structured_sections_v1_1.py`
- `install_universal_vision_job_exporter_v1.py`
- `install_verified_product_gate_v1.py`
- `install_vision_claim_promotion_gate_v1.py`
- `install_vision_claim_promotion_gate_v1_1.py`
- `install_vision_claim_schema_v1.py`
- `install_vision_claim_validator_minimal_v1_1.py`
- `install_vision_claim_validator_minimal_v1_1_2.py`
- `install_vision_claim_validator_v1.py`
- `install_vision_claim_validator_v1_1.py`
- `install_vision_claim_validator_v1_1_1.py`
- `install_vision_claim_validator_v1_1_3.py`
- `install_vision_to_knowledge_bridge_v1.py`
- `publish_approved_knowledge_v1.py`
- `python\couponworld_before_ask_20260803_200050.py`
- `python\couponworld_before_backup_tag_exclusions_20260812_233301.py`
- `python\couponworld_before_batch_id_freezer_20260808_141555.py`
- `python\couponworld_before_knowledge_command_20260805_225432.py`
- `python\couponworld_before_partial_evidence_mode_20260808_121502.py`
- `python\couponworld_before_verified_product_gate_20260808_161003.py`
- `python\couponworld_before_vision_key_fix_v2_20260808_134834.py`
- `python\couponworld_before_vision_key_fix_v3_20260808_135512.py`
- `python\couponworld_before_vision_v2_orchestration_20260808_133158.py`
- `python\market_discovery.py`
- `python\market_discovery_before_quality_v14_20260809.py`
- `python\market_discovery_before_quality_v15_20260809.py`
- `python\market_discovery_before_v151_20260809.py`
- `python\market_discovery_before_v161_quality_gate_20260809.py`
- `python\market_discovery_before_v16_resilience_20260809.py`
- `python\official_spec_extractor.py`
- `python\official_spec_extractor_before_always_rank_media_20260810_202234.py`
- `python\official_spec_extractor_before_apple_techspecs_20260805_231923.py`
- `python\official_spec_extractor_before_core_title_fallback_20260804_230342.py`
- `python\official_spec_extractor_before_embedded_precision_20260807_210218.py`
- `python\official_spec_extractor_before_embedded_state_20260807_205842.py`
- `python\official_spec_extractor_before_evidence_collector_20260806_235026.py`
- `python\official_spec_extractor_before_exact_href_priority_20260811_235529.py`
- `python\official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839.py`
- `python\official_spec_extractor_before_gemini_hero_20260810_201207.py`
- `python\official_spec_extractor_before_gemini_retry_20260811_233822.py`
- `python\official_spec_extractor_before_hero_score_20260810_195931.py`
- `python\official_spec_extractor_before_hero_suitability_20260810_195819.py`
- `python\official_spec_extractor_before_html_context.py`
- `python\official_spec_extractor_before_img_context_call.py`
- `python\official_spec_extractor_before_media_evidence_20260807_211103.py`
- `python\official_spec_extractor_before_media_hygiene_20260810_202414.py`
- `python\official_spec_extractor_before_media_hygiene_20260810_202424.py`
- `python\official_spec_extractor_before_media_ranker_20260807_212319.py`
- `python\official_spec_extractor_before_meta_priority_20260810_225601.py`
- `python\official_spec_extractor_before_partial_state_persistence_20260808_122702.py`
- `python\official_spec_extractor_before_ranker_hygiene_20260810_203041.py`
- `python\official_spec_extractor_before_ranker_hygiene_v2_20260810_203438.py`
- `python\official_spec_extractor_before_ranker_hygiene_v3_20260810_203618.py`
- `python\official_spec_extractor_before_ranker_official_url_20260811_235437.py`
- `python\official_spec_extractor_before_scan_order_fix.py`
- `python\official_spec_extractor_before_semantic_cli_20260808_111908.py`
- `python\official_spec_extractor_before_shopify_oxygen_20260804_233742.py`
- `python\official_spec_extractor_before_srcset_context.py`
- `python\official_spec_extractor_before_universal_sections_20260806_225951.py`
- `python\official_spec_extractor_before_universal_sections_20260806_230951.py`
- `python\official_spec_extractor_before_universal_semantic_core_20260808_110205.py`
- `python\official_spec_extractor_before_validator_v1_1_3_20260808_000101.py`
- `python\official_spec_extractor_before_vision_claim_schema_20260807_214754.py`
- `python\official_spec_extractor_before_vision_claim_validator_20260807_222611.py`
- `python\official_spec_extractor_before_vision_job_exporter_20260807_221202.py`
- `python\official_spec_extractor_before_vision_knowledge_bridge_20260807_223614.py`
- `python\official_spec_extractor_before_vision_promotion_gate_20260807_222918.py`
- `python\official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332.py`
- `python\official_spec_extractor_before_vision_provenance_gate_20260808_120429.py`
- `python\official_spec_extractor_before_vision_validator_minimal_20260807_235556.py`
- `python\official_spec_extractor_before_vision_validator_v1_1_20260807_234529.py`
- `python\official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840.py`
- `python\product_classifier.py`
- `python\product_fit_signal_builder.py`
- `python\product_fit_signal_builder_before_call_noise_phrase_20260809_235929.py`
- `python\product_fit_signal_builder_before_hyphen_mic_20260809_235752.py`
- `python\product_pipeline.py`
- `python\publish_product_knowledge.py`
- `python\remove_amazon_branding.py`
- `python\research_agent.py`
- `python\runtime_dependency_mapper.py`
- `python\tavily_test.py`
- `run_gemini_vision_batch_v1.py`
- `run_gemini_vision_batch_v2.py`
- `test_gemini_batch_validation.py`
- `test_gemini_vision_media01.py`
- `test_universal_semantic_consolidator_v1.py`
- `test_universal_semantic_consolidator_v1_1.py`
- `test_universal_semantic_consolidator_v1_2.py`
- `test_universal_semantic_consolidator_v1_3.py`
- `test_universal_semantic_schema_validator_v1.py`
- `test_universal_semantic_schema_validator_v2.py`
- `test_universal_semantic_schema_validator_v3.py`
- `test_vision_semantic_consolidation_v1.py`
- `upgrade_brand_domain_mappings.py`
- `upgrade_resolver_page_priority_v41.py`

## Module Details

### `add_ask_command.py`
- Status: **FAIL**
- Lines: 116 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `add_nothing_identity_domain.py`
- Status: **FAIL**
- Lines: 42 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `add_resolver_model_score_filter.py`
- Status: **PASS**
- Lines: 91 | Category: Utility / Other
- Functions: `main`

### `apply_requirement_match_v1.py`
- Status: **PASS**
- Lines: 245 | Category: Utility / Other
- Functions: `backup`, `main`, `patch_shopping_brain`, `replace_once`, `write_recommendation_engine`

### `approve_apple_iphone_17e_knowledge.py`
- Status: **PASS**
- Lines: 118 | Category: Utility / Other
- Functions: `main`

### `approve_logitech_knowledge.py`
- Status: **FAIL**
- Lines: 81 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `approve_nothing_phone_3_knowledge.py`
- Status: **FAIL**
- Lines: 122 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `approve_product_11_from_semantic_v1.py`
- Status: **PASS**
- Lines: 222 | Category: Utility / Other
- Functions: `load`, `main`

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

### `diagnose_apple_specs_structure.py`
- Status: **FAIL**
- Lines: 67 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_embedded_free_text.py`
- Status: **FAIL**
- Lines: 86 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_embedded_media_inventory.py`
- Status: **FAIL**
- Lines: 120 | Category: Price / Inventory
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_media_dimensions.py`
- Status: **FAIL**
- Lines: 50 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_media_ranking.py`
- Status: **FAIL**
- Lines: 195 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_nothing_embedded_data.py`
- Status: **FAIL**
- Lines: 74 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_nothing_identity.py`
- Status: **FAIL**
- Lines: 66 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_nothing_product_evidence.py`
- Status: **FAIL**
- Lines: 108 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_nothing_search.py`
- Status: **FAIL**
- Lines: 55 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_nuxt_product_payload.py`
- Status: **FAIL**
- Lines: 52 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_nuxt_reference_graph.py`
- Status: **FAIL**
- Lines: 86 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_realme_embedded_data.py`
- Status: **FAIL**
- Lines: 59 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_search_evidence.py`
- Status: **FAIL**
- Lines: 46 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_supporting_source_snippets.py`
- Status: **FAIL**
- Lines: 42 | Category: Source / Data Adapter
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_universal_page_content.py`
- Status: **FAIL**
- Lines: 68 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_universal_source_discovery.py`
- Status: **FAIL**
- Lines: 94 | Category: Source / Data Adapter
- Error: `Line 1: invalid non-printable character U+FEFF`

### `diagnose_vision_validation_reasons.py`
- Status: **FAIL**
- Lines: 62 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `download_media_candidates.py`
- Status: **FAIL**
- Lines: 37 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `finish_requirement_match_v1.py`
- Status: **PASS**
- Lines: 157 | Category: Utility / Other
- Functions: `main`, `replace_once`

### `fix_couponworld_vision_script_key_v1.py`
- Status: **PASS**
- Lines: 56 | Category: Utility / Other
- Functions: `main`

### `fix_couponworld_vision_script_key_v2.py`
- Status: **PASS**
- Lines: 64 | Category: Utility / Other
- Functions: `main`

### `fix_couponworld_vision_script_key_v3.py`
- Status: **PASS**
- Lines: 62 | Category: Utility / Other
- Functions: `main`

### `fix_display_parser.py`
- Status: **FAIL**
- Lines: 34 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `fix_display_size_v2.py`
- Status: **FAIL**
- Lines: 27 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `fix_extractor_core_title.py`
- Status: **FAIL**
- Lines: 49 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `fix_intent_engine_v2_gamer_profile.py`
- Status: **PASS**
- Lines: 61 | Category: Product Intelligence
- Functions: `main`

### `fix_universal_embedded_state_precision_v1_1.py`
- Status: **PASS**
- Lines: 163 | Category: Utility / Other
- Functions: `main`

### `improve_candidate_page_priority.py`
- Status: **PASS**
- Lines: 192 | Category: Utility / Other
- Functions: `main`

### `improve_resolver_queries.py`
- Status: **PASS**
- Lines: 106 | Category: Utility / Other
- Functions: `main`

### `install_apple_techspecs_extractor_v1.py`
- Status: **PASS**
- Lines: 373 | Category: Utility / Other
- Functions: `main`

### `install_brand_domain_registry_expansion_v1.py`
- Status: **PASS**
- Lines: 68 | Category: Utility / Other
- Functions: `main`

### `install_couponworld_intelligence_command_v1.py`
- Status: **PASS**
- Lines: 91 | Category: Product Intelligence
- Functions: `main`

### `install_decision_engine_v1.py`
- Status: **PASS**
- Lines: 273 | Category: Product Intelligence
- Functions: `main`

### `install_decision_engine_v1_1.py`
- Status: **PASS**
- Lines: 267 | Category: Product Intelligence
- Functions: `main`

### `install_decision_engine_v1_2.py`
- Status: **PASS**
- Lines: 268 | Category: Product Intelligence
- Functions: `main`

### `install_final_vision_knowledge_review_gate_v1.py`
- Status: **PASS**
- Lines: 148 | Category: Utility / Other
- Functions: `main`

### `install_intelligence_batch_id_freezer_v1.py`
- Status: **PASS**
- Lines: 86 | Category: Product Intelligence
- Functions: `main`

### `install_intelligence_partial_evidence_mode_v1.py`
- Status: **PASS**
- Lines: 155 | Category: Product Intelligence
- Functions: `main`

### `install_intelligence_vision_v2_orchestration.py`
- Status: **PASS**
- Lines: 295 | Category: Product Intelligence
- Functions: `main`

### `install_knowledge_command_v1.py`
- Status: **PASS**
- Lines: 280 | Category: Utility / Other
- Functions: `main`

### `install_knowledge_gate_v2.py`
- Status: **PASS**
- Lines: 190 | Category: Utility / Other
- Functions: `main`

### `install_knowledge_match_score_v1.py`
- Status: **PASS**
- Lines: 12 | Category: Utility / Other

### `install_knowledge_ranking_v1.py`
- Status: **PASS**
- Lines: 234 | Category: Utility / Other
- Functions: `main`

### `install_published_knowledge_gate_v1.py`
- Status: **PASS**
- Lines: 88 | Category: Utility / Other
- Functions: `main`

### `install_resolver_brand_registry_v1.py`
- Status: **FAIL**
- Lines: 73 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `install_resolver_source_family_stability_v1.py`
- Status: **PASS**
- Lines: 115 | Category: Source / Data Adapter
- Functions: `main`

### `install_semantic_partial_state_persistence_v1.py`
- Status: **PASS**
- Lines: 125 | Category: Utility / Other
- Functions: `main`

### `install_shopify_oxygen_extractor_v6.py`
- Status: **PASS**
- Lines: 314 | Category: Utility / Other
- Functions: `main`

### `install_universal_embedded_state_v1.py`
- Status: **PASS**
- Lines: 431 | Category: Utility / Other
- Functions: `main`

### `install_universal_evidence_collector_v1.py`
- Status: **PASS**
- Lines: 319 | Category: Utility / Other
- Functions: `main`

### `install_universal_media_evidence_v1.py`
- Status: **PASS**
- Lines: 356 | Category: Utility / Other
- Functions: `main`

### `install_universal_media_ranker_v1.py`
- Status: **PASS**
- Lines: 331 | Category: Utility / Other
- Functions: `main`

### `install_universal_model_normalization_v1.py`
- Status: **PASS**
- Lines: 172 | Category: Utility / Other
- Functions: `main`

### `install_universal_semantic_cli_v1.py`
- Status: **PASS**
- Lines: 80 | Category: Utility / Other
- Functions: `main`

### `install_universal_semantic_core_v1_3.py`
- Status: **PASS**
- Lines: 49 | Category: Utility / Other
- Functions: `main`

### `install_universal_source_discovery_v1.py`
- Status: **PASS**
- Lines: 286 | Category: Source / Data Adapter
- Functions: `main`

### `install_universal_structured_sections_v1.py`
- Status: **PASS**
- Lines: 284 | Category: Utility / Other
- Functions: `main`

### `install_universal_structured_sections_v1_1.py`
- Status: **PASS**
- Lines: 285 | Category: Utility / Other
- Functions: `main`

### `install_universal_vision_job_exporter_v1.py`
- Status: **PASS**
- Lines: 184 | Category: Utility / Other
- Functions: `main`

### `install_universal_vision_provider_v1.py`
- Status: **PASS**
- Lines: 237 | Category: Source / Data Adapter
- Functions: `main`

### `install_verified_intelligence_renderer_v1.py`
- Status: **PASS**
- Lines: 185 | Category: Product Intelligence
- Functions: `main`

### `install_verified_product_gate_v1.py`
- Status: **PASS**
- Lines: 293 | Category: Utility / Other
- Functions: `main`

### `install_vision_claim_promotion_gate_v1.py`
- Status: **PASS**
- Lines: 163 | Category: Utility / Other
- Functions: `main`

### `install_vision_claim_promotion_gate_v1_1.py`
- Status: **PASS**
- Lines: 161 | Category: Utility / Other
- Functions: `main`

### `install_vision_claim_schema_v1.py`
- Status: **PASS**
- Lines: 210 | Category: Utility / Other
- Functions: `main`

### `install_vision_claim_validator_minimal_v1_1.py`
- Status: **PASS**
- Lines: 236 | Category: Utility / Other
- Functions: `main`, `replace_once`

### `install_vision_claim_validator_minimal_v1_1_2.py`
- Status: **PASS**
- Lines: 220 | Category: Utility / Other
- Functions: `main`, `replace_one`

### `install_vision_claim_validator_v1.py`
- Status: **PASS**
- Lines: 343 | Category: Utility / Other
- Functions: `main`

### `install_vision_claim_validator_v1_1.py`
- Status: **PASS**
- Lines: 376 | Category: Utility / Other
- Functions: `main`

### `install_vision_claim_validator_v1_1_1.py`
- Status: **PASS**
- Lines: 370 | Category: Utility / Other
- Functions: `main`

### `install_vision_claim_validator_v1_1_3.py`
- Status: **PASS**
- Lines: 52 | Category: Utility / Other
- Functions: `main`

### `install_vision_evidence_queue_v1.py`
- Status: **PASS**
- Lines: 201 | Category: Import / Intake
- Functions: `main`

### `install_vision_provenance_import_gate_v1.py`
- Status: **PASS**
- Lines: 157 | Category: Import / Intake
- Functions: `main`

### `install_vision_result_importer_v1.py`
- Status: **PASS**
- Lines: 288 | Category: Import / Intake
- Functions: `main`

### `install_vision_to_knowledge_bridge_v1.py`
- Status: **PASS**
- Lines: 173 | Category: Utility / Other
- Functions: `main`

### `publish_approved_knowledge_v1.py`
- Status: **PASS**
- Lines: 204 | Category: Utility / Other
- Functions: `load_json`, `main`, `normalize`, `product_key`, `save_json`

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
- Lines: 807 | Category: Build System
- Functions: `clean`, `detect_family`, `excerpt`, `load_products`, `load_published_product_ids`, `load_verified_intelligence_index`, `main`, `page_dir`, `page_url`, `related`, `render`, `render_verified_intelligence`, `searchable_text`, `slugify`

### `python\build_product_pages_before_intelligence_v1.py`
- Status: **PASS**
- Lines: 666 | Category: Build System
- Functions: `clean`, `detect_family`, `excerpt`, `load_products`, `main`, `page_dir`, `page_url`, `related`, `render`, `searchable_text`, `slugify`

### `python\build_product_pages_before_published_gate.py`
- Status: **FAIL**
- Lines: 778 | Category: Build System
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\build_product_pages_before_published_gate_20260809_002946.py`
- Status: **FAIL**
- Lines: 778 | Category: Build System
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\build_product_pages_before_verified_intelligence_20260808_232718.py`
- Status: **PASS**
- Lines: 666 | Category: Build System
- Functions: `clean`, `detect_family`, `excerpt`, `load_products`, `main`, `page_dir`, `page_url`, `related`, `render`, `searchable_text`, `slugify`

### `python\build_sitemap.py`
- Status: **PASS**
- Lines: 261 | Category: Build System
- Functions: `add_url`, `canonical_url`, `clean`, `extra_page_urls`, `main`, `product_identity`, `product_path`, `product_url`, `slugify`

### `python\couponworld.py`
- Status: **FAIL**
- Lines: 1770 | Category: Master Controller
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\couponworld_before_ask_20260803_200050.py`
- Status: **PASS**
- Lines: 944 | Category: Utility / Other
- Functions: `adapt_source`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_report`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls`, `slugify`, `validate_build_source`
- CLI commands: `adapt`, `build`, `check`, `import`, `intake`, `report`, `run`

### `python\couponworld_before_backup_tag_exclusions_20260812_233301.py`
- Status: **PASS**
- Lines: 1755 | Category: Utility / Other
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `freeze_pending_intelligence_ids`, `import_products`, `intake_products`, `intelligence_command`, `intelligence_report`, `knowledge_command`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow` ...
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `intelligence`, `knowledge`, `report`, `run`, `status`, `update`

### `python\couponworld_before_batch_id_freezer_20260808_141555.py`
- Status: **PASS**
- Lines: 1523 | Category: Utility / Other
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_command`, `intelligence_report`, `knowledge_command`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls` ...
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `intelligence`, `knowledge`, `report`, `run`, `status`, `update`

### `python\couponworld_before_intelligence_v1_20260808_114212.py`
- Status: **PASS**
- Lines: 1151 | Category: Product Intelligence
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_report`, `knowledge_command`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls`, `slugify` ...
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `knowledge`, `report`, `run`, `status`, `update`

### `python\couponworld_before_knowledge_command_20260805_225432.py`
- Status: **PASS**
- Lines: 985 | Category: Utility / Other
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_report`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls`, `slugify`, `validate_build_source`
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `report`, `run`

### `python\couponworld_before_partial_evidence_mode_20260808_121502.py`
- Status: **PASS**
- Lines: 1383 | Category: Utility / Other
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_command`, `intelligence_report`, `knowledge_command`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls` ...
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `intelligence`, `knowledge`, `report`, `run`, `status`, `update`

### `python\couponworld_before_verified_product_gate_20260808_161003.py`
- Status: **PASS**
- Lines: 1610 | Category: Utility / Other
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `freeze_pending_intelligence_ids`, `import_products`, `intake_products`, `intelligence_command`, `intelligence_report`, `knowledge_command`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow` ...
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `intelligence`, `knowledge`, `report`, `run`, `status`, `update`

### `python\couponworld_before_vision_key_fix_v2_20260808_134834.py`
- Status: **PASS**
- Lines: 1522 | Category: Utility / Other
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_command`, `intelligence_report`, `knowledge_command`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls` ...
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `intelligence`, `knowledge`, `report`, `run`, `status`, `update`

### `python\couponworld_before_vision_key_fix_v3_20260808_135512.py`
- Status: **PASS**
- Lines: 1522 | Category: Utility / Other
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_command`, `intelligence_report`, `knowledge_command`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls` ...
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `intelligence`, `knowledge`, `report`, `run`, `status`, `update`

### `python\couponworld_before_vision_v2_orchestration_20260808_133158.py`
- Status: **PASS**
- Lines: 1464 | Category: Utility / Other
- Functions: `adapt_source`, `ask_command`, `build_command`, `build_parser`, `check_command`, `import_products`, `intake_products`, `intelligence_command`, `intelligence_report`, `knowledge_command`, `load_products`, `main`, `page_directory`, `print_section`, `product_identity`, `product_link`, `public_files`, `run_command`, `run_workflow`, `sitemap_urls` ...
- CLI commands: `adapt`, `ask`, `build`, `check`, `import`, `intake`, `intelligence`, `knowledge`, `report`, `run`, `status`, `update`

### `python\couponworld_complete_audit.py`
- Status: **PASS**
- Lines: 818 | Category: Audit / Monitoring
- Classes: `Finding`
- Functions: `add`, `build_findings`, `clean`, `collect_audit`, `count_html_product_pages`, `exists`, `inspect_backend_api`, `inspect_backup_clutter`, `inspect_core_modules`, `inspect_coupon_db`, `inspect_frontend`, `inspect_gitignore`, `inspect_knowledge`, `inspect_security`, `inspect_seo`, `main`, `module_functions`, `next_actions`, `print_audit`, `read_text` ...

### `python\couponworld_complete_audit_before_bom_fix_20260809.py`
- Status: **PASS**
- Lines: 818 | Category: Audit / Monitoring
- Classes: `Finding`
- Functions: `add`, `build_findings`, `clean`, `collect_audit`, `count_html_product_pages`, `exists`, `inspect_backend_api`, `inspect_backup_clutter`, `inspect_core_modules`, `inspect_coupon_db`, `inspect_frontend`, `inspect_gitignore`, `inspect_knowledge`, `inspect_security`, `inspect_seo`, `main`, `module_functions`, `next_actions`, `print_audit`, `read_text` ...

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

### `python\intelligence\verified_image_engine.py`
- Status: **FAIL**
- Lines: 662 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\intelligence\verified_image_engine_before_diagnostics_20260810_201836.py`
- Status: **FAIL**
- Lines: 503 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\intelligence\verified_image_engine_before_exact_href_priority_20260811_235820.py`
- Status: **PASS**
- Lines: 545 | Category: Product Intelligence
- Uses: `official_spec_extractor`
- Functions: `classify_candidate`, `clean`, `is_old_amazon_widget`, `load_json`, `main`, `official_spec_list`, `product_id`, `product_list`, `ranked_candidates`, `resolve_product_image`, `save_json`

### `python\intelligence\verified_image_engine_before_exact_product_v2.py`
- Status: **PASS**
- Lines: 545 | Category: Product Intelligence
- Uses: `official_spec_extractor`
- Functions: `classify_candidate`, `clean`, `is_old_amazon_widget`, `load_json`, `main`, `official_spec_list`, `product_id`, `product_list`, `ranked_candidates`, `resolve_product_image`, `save_json`

### `python\intelligence\verified_image_engine_before_meta_shortlist_20260810_230418.py`
- Status: **PASS**
- Lines: 531 | Category: Product Intelligence
- Uses: `official_spec_extractor`
- Functions: `classify_candidate`, `clean`, `is_old_amazon_widget`, `load_json`, `main`, `official_spec_list`, `product_id`, `product_list`, `ranked_candidates`, `resolve_product_image`, `save_json`

### `python\intelligence\verified_image_engine_before_official_context_fallback_20260812_232525.py`
- Status: **FAIL**
- Lines: 607 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\intelligence\verified_image_engine_before_quota_output_20260812_232320.py`
- Status: **FAIL**
- Lines: 580 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\intelligence\verified_image_engine_before_quota_stop_20260812_232133.py`
- Status: **FAIL**
- Lines: 551 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\intent_engine.py`
- Status: **PASS**
- Lines: 429 | Category: Product Intelligence
- Classes: `ShoppingIntent`
- Functions: `build_priority_weights`, `detect_brands`, `detect_budget`, `detect_category`, `detect_features`, `detect_intent`, `detect_requirements`, `detect_use_cases`, `detect_user_profile`, `normalize`, `normalize_weights`, `parse_query`

### `python\intent_engine_before_explicit_priority_20260809.py`
- Status: **PASS**
- Lines: 386 | Category: Product Intelligence
- Classes: `ShoppingIntent`
- Functions: `build_priority_weights`, `detect_brands`, `detect_budget`, `detect_category`, `detect_features`, `detect_intent`, `detect_requirements`, `detect_use_cases`, `detect_user_profile`, `normalize`, `normalize_weights`, `parse_query`

### `python\intent_engine_before_feature_v2_20260805_232541.py`
- Status: **PASS**
- Lines: 153 | Category: Product Intelligence
- Classes: `ShoppingIntent`
- Functions: `detect_brands`, `detect_budget`, `detect_category`, `detect_features`, `detect_intent`, `normalize`, `parse_query`

### `python\intent_engine_before_gamer_profile_fix_20260809_143059.py`
- Status: **PASS**
- Lines: 376 | Category: Product Intelligence
- Classes: `ShoppingIntent`
- Functions: `build_priority_weights`, `detect_brands`, `detect_budget`, `detect_category`, `detect_features`, `detect_intent`, `detect_requirements`, `detect_use_cases`, `detect_user_profile`, `normalize`, `normalize_weights`, `parse_query`

### `python\intent_engine_before_v2_20260809.py`
- Status: **PASS**
- Lines: 177 | Category: Product Intelligence
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

### `python\market_discovery.py`
- Status: **PASS**
- Lines: 819 | Category: Utility / Other
- Uses: `intent_engine`, `official_source_resolver`
- Functions: `build_discovery_queries`, `candidate_quality_score`, `clean`, `compact_product_title`, `discover_market`, `has_category_hint`, `host_of`, `is_editorial_title`, `is_generic_listing_title`, `is_search_or_listing_url`, `known_brand_from_title`, `looks_like_product_result`, `main`, `model_identity_signal`, `normalize_key`, `path_of`, `print_result`, `search_channel`, `strong_product_url`

### `python\market_discovery_before_quality_v14_20260809.py`
- Status: **PASS**
- Lines: 454 | Category: Utility / Other
- Uses: `intent_engine`
- Functions: `build_discovery_queries`, `clean`, `compact_product_title`, `discover_market`, `has_category_hint`, `host_of`, `is_editorial_title`, `looks_like_product_result`, `main`, `normalize_key`, `path_of`, `print_result`, `search_channel`, `strong_product_url`

### `python\market_discovery_before_quality_v15_20260809.py`
- Status: **PASS**
- Lines: 476 | Category: Utility / Other
- Uses: `intent_engine`
- Functions: `build_discovery_queries`, `clean`, `compact_product_title`, `discover_market`, `has_category_hint`, `host_of`, `is_editorial_title`, `looks_like_product_result`, `main`, `normalize_key`, `path_of`, `print_result`, `search_channel`, `strong_product_url`

### `python\market_discovery_before_v151_20260809.py`
- Status: **PASS**
- Lines: 593 | Category: Utility / Other
- Uses: `intent_engine`, `official_source_resolver`
- Functions: `build_discovery_queries`, `candidate_quality_score`, `clean`, `compact_product_title`, `discover_market`, `has_category_hint`, `host_of`, `is_editorial_title`, `is_generic_listing_title`, `known_brand_from_title`, `looks_like_product_result`, `main`, `model_identity_signal`, `normalize_key`, `path_of`, `print_result`, `search_channel`, `strong_product_url`

### `python\market_discovery_before_v161_quality_gate_20260809.py`
- Status: **PASS**
- Lines: 778 | Category: Utility / Other
- Uses: `intent_engine`, `official_source_resolver`
- Functions: `build_discovery_queries`, `candidate_quality_score`, `clean`, `compact_product_title`, `discover_market`, `has_category_hint`, `host_of`, `is_editorial_title`, `is_generic_listing_title`, `is_search_or_listing_url`, `known_brand_from_title`, `looks_like_product_result`, `main`, `model_identity_signal`, `normalize_key`, `path_of`, `print_result`, `search_channel`, `strong_product_url`

### `python\market_discovery_before_v16_resilience_20260809.py`
- Status: **PASS**
- Lines: 603 | Category: Utility / Other
- Uses: `intent_engine`, `official_source_resolver`
- Functions: `build_discovery_queries`, `candidate_quality_score`, `clean`, `compact_product_title`, `discover_market`, `has_category_hint`, `host_of`, `is_editorial_title`, `is_generic_listing_title`, `known_brand_from_title`, `looks_like_product_result`, `main`, `model_identity_signal`, `normalize_key`, `path_of`, `print_result`, `search_channel`, `strong_product_url`

### `python\market_identity_bridge.py`
- Status: **PASS**
- Lines: 214 | Category: Product Intelligence
- Uses: `market_discovery`, `product_identity_v2`
- Functions: `build_market_identities`, `candidate_to_product`, `main`, `print_result`

### `python\migrate_product_schema.py`
- Status: **PASS**
- Lines: 215 | Category: Import / Intake
- Functions: `clean_text`, `create_backup`, `load_products`, `main`, `normalize_number`, `normalize_product`, `save_products`

### `python\official_source_resolver.py`
- Status: **FAIL**
- Lines: 1056 | Category: Source / Data Adapter
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_source_resolver_backup.py`
- Status: **PASS**
- Lines: 355 | Category: Source / Data Adapter
- Functions: `core_product_title`, `hostname_matches`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `resolve_product`, `save_json`, `significant_tokens`, `token_match_score`

### `python\official_source_resolver_before_batch_quota_break_20260813_203745.py`
- Status: **FAIL**
- Lines: 1051 | Category: Source / Data Adapter
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_source_resolver_before_brand_expansion_20260804_222957.py`
- Status: **PASS**
- Lines: 595 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `core_product_title`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `token_match_score`
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_brand_registry_20260808_184921.py`
- Status: **PASS**
- Lines: 1015 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `build_source_queries`, `classify_source_type`, `core_product_title`, `has_extra_model_modifier`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `normalized_model_tokens`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `source_family_key` ...
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_identity_gate_20260810_232936.py`
- Status: **PASS**
- Lines: 1021 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `build_source_queries`, `classify_source_type`, `core_product_title`, `has_extra_model_modifier`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `normalized_model_tokens`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `source_family_key` ...
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_identity_override_20260810_233123.py`
- Status: **PASS**
- Lines: 1021 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `build_source_queries`, `classify_source_type`, `core_product_title`, `has_extra_model_modifier`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `normalized_model_tokens`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `source_family_key` ...
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_model_filter_20260804_225625.py`
- Status: **PASS**
- Lines: 667 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `core_product_title`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `token_match_score`
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_model_normalization_20260806_234104.py`
- Status: **PASS**
- Lines: 822 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `build_source_queries`, `classify_source_type`, `core_product_title`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `token_match_score`
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_page_priority_20260804_225410.py`
- Status: **PASS**
- Lines: 634 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `core_product_title`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `token_match_score`
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_page_priority_20260805_230553.py`
- Status: **PASS**
- Lines: 674 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `core_product_title`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `token_match_score`
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_query_improvement_20260804_223535.py`
- Status: **PASS**
- Lines: 603 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `core_product_title`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `token_match_score`
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_quota_stop_20260813_203309.py`
- Status: **PASS**
- Lines: 1034 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `build_source_queries`, `classify_source_type`, `core_product_title`, `has_extra_model_modifier`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `normalized_model_tokens`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `source_family_key` ...
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_quota_stop_20260813_203605.py`
- Status: **PASS**
- Lines: 1034 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `build_source_queries`, `classify_source_type`, `core_product_title`, `has_extra_model_modifier`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `normalized_model_tokens`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `source_family_key` ...
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_source_stability_20260808_124706.py`
- Status: **PASS**
- Lines: 893 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `build_source_queries`, `classify_source_type`, `core_product_title`, `has_extra_model_modifier`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `normalized_model_tokens`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `token_match_score`
- CLI commands: `run`, `status`

### `python\official_source_resolver_before_universal_sources_20260806_233209.py`
- Status: **PASS**
- Lines: 680 | Category: Source / Data Adapter
- Uses: `resolver_engine`
- Functions: `build_parser`, `core_product_title`, `hostname_matches`, `is_unwanted_page`, `load_existing_results`, `load_json`, `main`, `normalize_brand`, `normalize_text`, `page_type_score`, `resolve_product`, `save_json`, `select_products`, `show_status`, `significant_tokens`, `token_match_score`
- CLI commands: `run`, `status`

### `python\official_source_resolver_v3.py`
- Status: **PASS**
- Lines: 0 | Category: Source / Data Adapter

### `python\official_spec_extractor.py`
- Status: **FAIL**
- Lines: 5507 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_always_rank_media_20260810_202234.py`
- Status: **PASS**
- Lines: 5331 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_apple_techspecs_20260805_231923.py`
- Status: **PASS**
- Lines: 1504 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `backup_output`, `build_output`, `clean_text`, `decode_shopify_oxygen_stream`, `extract_definition_lists`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs`, `extract_tables`, `feature_relevance_score`, `feature_scope`, `fetch_page`, `hostname`, `identity_tokens`, `is_noise_feature` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_core_title_fallback_20260804_230342.py`
- Status: **PASS**
- Lines: 1289 | Category: Utility / Other
- Functions: `add_specification`, `backup_output`, `build_output`, `clean_text`, `extract_definition_lists`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_tables`, `feature_relevance_score`, `feature_scope`, `fetch_page`, `hostname`, `identity_tokens`, `is_noise_feature`, `is_unwanted_url`, `load_existing_output`, `load_identity_index` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_embedded_precision_20260807_210218.py`
- Status: **PASS**
- Lines: 2448 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `backup_output`, `build_output`, `clean_text`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs`, `extract_structured_sections` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_embedded_state_20260807_205842.py`
- Status: **PASS**
- Lines: 2130 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `backup_output`, `build_output`, `clean_text`, `collect_official_source_urls`, `decode_shopify_oxygen_stream`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs`, `extract_structured_sections`, `extract_tables`, `feature_relevance_score`, `feature_scope` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_evidence_collector_20260806_235026.py`
- Status: **PASS**
- Lines: 1896 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `backup_output`, `build_output`, `clean_text`, `decode_shopify_oxygen_stream`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs`, `extract_structured_sections`, `extract_tables`, `feature_relevance_score`, `feature_scope`, `fetch_page`, `hostname` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_exact_href_priority_20260811_235529.py`
- Status: **FAIL**
- Lines: 5501 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839.py`
- Status: **PASS**
- Lines: 4138 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_gemini_hero_20260810_201207.py`
- Status: **PASS**
- Lines: 5000 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_gemini_retry_20260811_233822.py`
- Status: **FAIL**
- Lines: 5427 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_hero_score_20260810_195931.py`
- Status: **PASS**
- Lines: 4957 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_hero_suitability_20260810_195819.py`
- Status: **PASS**
- Lines: 4957 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_html_context.py`
- Status: **FAIL**
- Lines: 5459 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_identity_fields_20260811_224104.py`
- Status: **PASS**
- Lines: 5376 | Category: Product Intelligence
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_identity_fields_20260811_224248.py`
- Status: **PASS**
- Lines: 5376 | Category: Product Intelligence
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_identity_gate_20260811_224557.py`
- Status: **FAIL**
- Lines: 5419 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_identity_parser_20260811_224512.py`
- Status: **FAIL**
- Lines: 5397 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_identity_result_fields_20260811_224653.py`
- Status: **FAIL**
- Lines: 5423 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_identity_rules_20260811_224433.py`
- Status: **FAIL**
- Lines: 5384 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_identity_vision_gate_20260811_223906.py`
- Status: **PASS**
- Lines: 5376 | Category: Product Intelligence
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_img_context_call.py`
- Status: **FAIL**
- Lines: 5468 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_media_evidence_20260807_211103.py`
- Status: **PASS**
- Lines: 2503 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `backup_output`, `build_output`, `clean_text`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs`, `extract_structured_sections` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_media_hygiene_20260810_202414.py`
- Status: **PASS**
- Lines: 5346 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_media_hygiene_20260810_202424.py`
- Status: **PASS**
- Lines: 5346 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_media_ranker_20260807_212319.py`
- Status: **PASS**
- Lines: 2728 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `backup_output`, `build_output`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_meta_priority_20260810_225601.py`
- Status: **PASS**
- Lines: 5362 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_partial_state_persistence_20260808_122702.py`
- Status: **PASS**
- Lines: 4947 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_prompt_identity_schema_20260811_224344.py`
- Status: **FAIL**
- Lines: 5380 | Category: Product Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_ranker_hygiene_20260810_203041.py`
- Status: **PASS**
- Lines: 5346 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_ranker_hygiene_v2_20260810_203438.py`
- Status: **PASS**
- Lines: 5346 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_ranker_hygiene_v3_20260810_203618.py`
- Status: **PASS**
- Lines: 5346 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_ranker_official_url_20260811_235437.py`
- Status: **FAIL**
- Lines: 5499 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_scan_order_fix.py`
- Status: **FAIL**
- Lines: 5427 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_semantic_cli_20260808_111908.py`
- Status: **PASS**
- Lines: 4645 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_shopify_oxygen_20260804_233742.py`
- Status: **PASS**
- Lines: 1290 | Category: Utility / Other
- Functions: `add_specification`, `backup_output`, `build_output`, `clean_text`, `extract_definition_lists`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_tables`, `feature_relevance_score`, `feature_scope`, `fetch_page`, `hostname`, `identity_tokens`, `is_noise_feature`, `is_unwanted_url`, `load_existing_output`, `load_identity_index` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_srcset_context.py`
- Status: **FAIL**
- Lines: 5495 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_universal_images_20260810_202111.py`
- Status: **PASS**
- Lines: 5203 | Category: Image System
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_universal_semantic_result`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_universal_semantic_input`, `build_universal_semantic_prompt`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs` ...
- CLI commands: `extract`, `semantic`, `status`

### `python\official_spec_extractor_before_universal_sections_20260806_225951.py`
- Status: **PASS**
- Lines: 1744 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `backup_output`, `build_output`, `clean_text`, `decode_shopify_oxygen_stream`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs`, `extract_tables`, `feature_relevance_score`, `feature_scope`, `fetch_page`, `hostname`, `identity_tokens` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_universal_sections_20260806_230951.py`
- Status: **PASS**
- Lines: 1744 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `backup_output`, `build_output`, `clean_text`, `decode_shopify_oxygen_stream`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs`, `extract_tables`, `feature_relevance_score`, `feature_scope`, `fetch_page`, `hostname`, `identity_tokens` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_universal_semantic_core_20260808_110205.py`
- Status: **PASS**
- Lines: 4315 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_validator_v1_1_3_20260808_000101.py`
- Status: **PASS**
- Lines: 4227 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_claim_schema_20260807_214754.py`
- Status: **PASS**
- Lines: 3063 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `backup_output`, `build_output`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_claim_validator_20260807_222611.py`
- Status: **PASS**
- Lines: 3630 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_job_exporter_20260807_221202.py`
- Status: **PASS**
- Lines: 3276 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_knowledge_bridge_20260807_223614.py`
- Status: **PASS**
- Lines: 4024 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_promotion_gate_20260807_222918.py`
- Status: **PASS**
- Lines: 3914 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332.py`
- Status: **PASS**
- Lines: 3914 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_provenance_gate_20260808_120429.py`
- Status: **FAIL**
- Lines: 4908 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\official_spec_extractor_before_vision_provider_20260807_215532.py`
- Status: **PASS**
- Lines: 3154 | Category: Source / Data Adapter
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `backup_output`, `build_output`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_queue_20260807_214124.py`
- Status: **PASS**
- Lines: 2977 | Category: Import / Intake
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `backup_output`, `build_output`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs`, `extract_label_value_blocks`, `extract_meta`, `extract_one`, `extract_shopify_oxygen_specs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_result_importer_20260807_222125.py`
- Status: **PASS**
- Lines: 3401 | Category: Import / Intake
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features`, `extract_json_ld_specs` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_validator_minimal_20260807_235556.py`
- Status: **PASS**
- Lines: 4227 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_validator_v1_1_20260807_234529.py`
- Status: **PASS**
- Lines: 4227 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features` ...
- CLI commands: `extract`, `status`

### `python\official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840.py`
- Status: **PASS**
- Lines: 4227 | Category: Utility / Other
- Functions: `add_specification`, `add_stream_spec`, `apply_review_decision`, `attach_vision_provider_state`, `backup_output`, `build_output`, `build_vision_job_payload`, `build_vision_knowledge_candidates`, `build_vision_provider_config`, `clean_text`, `collect_embedded_media_evidence`, `collect_official_source_urls`, `decode_indexed_state_graph`, `decode_shopify_oxygen_stream`, `embedded_value_is_useful`, `empty_vision_claim`, `extract_apple_techspecs`, `extract_definition_lists`, `extract_embedded_state_specs`, `extract_features` ...
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

### `python\product_fit_signal_builder.py`
- Status: **PASS**
- Lines: 573 | Category: Utility / Other
- Uses: `intent_engine`, `product_intelligence_bridge`, `weighted_fit_engine`
- Functions: `anc_signal`, `battery_signal`, `budget_signal`, `build_fit_signals`, `call_quality_signal`, `camera_signal`, `connectivity_signal`, `display_signal`, `ease_of_use_signal`, `generic_unknown`, `main`, `numeric`, `performance_signal`, `ram_signal`, `score_product`, `signal`, `software_support_signal`, `sound_quality_signal`, `storage_signal`, `text_blob`

### `python\product_fit_signal_builder_before_call_noise_phrase_20260809_235929.py`
- Status: **PASS**
- Lines: 572 | Category: Utility / Other
- Uses: `intent_engine`, `product_intelligence_bridge`, `weighted_fit_engine`
- Functions: `anc_signal`, `battery_signal`, `budget_signal`, `build_fit_signals`, `call_quality_signal`, `camera_signal`, `connectivity_signal`, `display_signal`, `ease_of_use_signal`, `generic_unknown`, `main`, `numeric`, `performance_signal`, `ram_signal`, `score_product`, `signal`, `software_support_signal`, `sound_quality_signal`, `storage_signal`, `text_blob`

### `python\product_fit_signal_builder_before_hyphen_mic_20260809_235752.py`
- Status: **PASS**
- Lines: 572 | Category: Utility / Other
- Uses: `intent_engine`, `product_intelligence_bridge`, `weighted_fit_engine`
- Functions: `anc_signal`, `battery_signal`, `budget_signal`, `build_fit_signals`, `call_quality_signal`, `camera_signal`, `connectivity_signal`, `display_signal`, `ease_of_use_signal`, `generic_unknown`, `main`, `numeric`, `performance_signal`, `ram_signal`, `score_product`, `signal`, `software_support_signal`, `sound_quality_signal`, `storage_signal`, `text_blob`

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

### `python\product_intelligence_bridge.py`
- Status: **PASS**
- Lines: 390 | Category: Product Intelligence
- Functions: `build_profile`, `fact_value`, `facts_by_key`, `find_spec`, `first_fact`, `flatten`, `load_json`, `main`, `pick`, `products_by_id`, `regex_first`, `semantic_facts`, `spec_value`

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

### `python\publish_product_knowledge.py`
- Status: **PASS**
- Lines: 175 | Category: Utility / Other
- Functions: `backup`, `load_json`, `normalize`, `publish`, `save_json`

### `python\real_recommendation_ranker.py`
- Status: **PASS**
- Lines: 328 | Category: Shopping Intelligence
- Uses: `intent_engine`, `product_fit_signal_builder`, `product_intelligence_bridge`, `weighted_fit_engine`
- Functions: `build_real_candidates`, `criterion_summary`, `load_json`, `main`, `normalize_category`, `print_ranked`, `profile_matches_category`, `published_product_ids`, `rank_real_products`

### `python\recommendation_engine.py`
- Status: **PASS**
- Lines: 147 | Category: Product Intelligence
- Functions: `_clean`, `_has_list_values`, `build_requirement_assessment`, `calculate_data_confidence`, `explain_product`

### `python\recommendation_engine_before_match_v1_20260803_230715.py`
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
- Lines: 623 | Category: Product Intelligence
- Classes: `ParsedIdentity`, `ResolverDecision`
- Functions: `compare_identity`, `equivalent_model`, `extract_brand`, `extract_color_tokens`, `extract_memory_tokens`, `infer_brand_from_url`, `model_score`, `normalize_text`, `parse_identity`, `subset_match`, `tokenize`, `validate_candidate`

### `python\resolver_engine_before_alpha_exact_fix_20260810_001430.py`
- Status: **PASS**
- Lines: 615 | Category: Product Intelligence
- Classes: `ParsedIdentity`, `ResolverDecision`
- Functions: `compare_identity`, `equivalent_model`, `extract_brand`, `extract_color_tokens`, `extract_memory_tokens`, `infer_brand_from_url`, `model_score`, `normalize_text`, `parse_identity`, `subset_match`, `tokenize`, `validate_candidate`

### `python\resolver_engine_before_brand_registry_20260808_231140.py`
- Status: **PASS**
- Lines: 585 | Category: Product Intelligence
- Classes: `ParsedIdentity`, `ResolverDecision`
- Functions: `compare_identity`, `equivalent_model`, `extract_brand`, `extract_color_tokens`, `extract_memory_tokens`, `infer_brand_from_url`, `model_score`, `normalize_text`, `parse_identity`, `subset_match`, `tokenize`, `validate_candidate`

### `python\resolver_engine_before_domain_noise_fix_20260810_001348.py`
- Status: **PASS**
- Lines: 596 | Category: Product Intelligence
- Classes: `ParsedIdentity`, `ResolverDecision`
- Functions: `compare_identity`, `equivalent_model`, `extract_brand`, `extract_color_tokens`, `extract_memory_tokens`, `infer_brand_from_url`, `model_score`, `normalize_text`, `parse_identity`, `subset_match`, `tokenize`, `validate_candidate`

### `python\resolver_engine_before_nothing_domain_20260804_224458.py`
- Status: **PASS**
- Lines: 584 | Category: Product Intelligence
- Classes: `ParsedIdentity`, `ResolverDecision`
- Functions: `compare_identity`, `equivalent_model`, `extract_brand`, `extract_color_tokens`, `extract_memory_tokens`, `infer_brand_from_url`, `model_score`, `normalize_text`, `parse_identity`, `subset_match`, `tokenize`, `validate_candidate`

### `python\retail_price_evidence.py`
- Status: **FAIL**
- Lines: 514 | Category: Price / Inventory
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\retail_price_evidence_before_v11_20260809.py`
- Status: **FAIL**
- Lines: 127 | Category: Price / Inventory
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\retail_price_evidence_before_v12_cache_20260809.py`
- Status: **FAIL**
- Lines: 364 | Category: Price / Inventory
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\runtime_dependency_mapper.py`
- Status: **PASS**
- Lines: 44 | Category: Utility / Other
- Functions: `main`

### `python\seo_generator.py`
- Status: **PASS**
- Lines: 57 | Category: SEO / Discovery
- Functions: `generate_page`, `main`, `safe_text`

### `python\shopping_brain.py`
- Status: **PASS**
- Lines: 1260 | Category: Shopping Intelligence
- Uses: `intent_engine`, `knowledge_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `_index_by_product_id`, `_load_database`, `_normalize_query_text`, `build_decision_summary`, `build_response`, `infer_requested_product_types`, `knowledge_gate_adjustment`, `knowledge_match_score`, `load_feature_database`, `load_identity_database`, `load_products`, `load_taxonomy_database`, `main`, `match_products`, `merge_intelligence`, `merge_product_knowledge`, `merge_taxonomy`, `print_text_response`, `taxonomy_match_score`, `taxonomy_search_text`

### `python\shopping_brain_backup.py`
- Status: **FAIL**
- Lines: 280 | Category: Shopping Intelligence
- Error: `Line 1: invalid non-printable character U+FEFF`

### `python\shopping_brain_before_decision_engine_20260805_235240.py`
- Status: **PASS**
- Lines: 1052 | Category: Product Intelligence
- Uses: `intent_engine`, `knowledge_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `_index_by_product_id`, `_load_database`, `_normalize_query_text`, `build_response`, `infer_requested_product_types`, `knowledge_match_score`, `load_feature_database`, `load_identity_database`, `load_products`, `load_taxonomy_database`, `main`, `match_products`, `merge_intelligence`, `merge_product_knowledge`, `merge_taxonomy`, `print_text_response`, `taxonomy_match_score`, `taxonomy_search_text`

### `python\shopping_brain_before_decision_engine_20260805_235607.py`
- Status: **PASS**
- Lines: 1052 | Category: Product Intelligence
- Uses: `intent_engine`, `knowledge_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `_index_by_product_id`, `_load_database`, `_normalize_query_text`, `build_response`, `infer_requested_product_types`, `knowledge_match_score`, `load_feature_database`, `load_identity_database`, `load_products`, `load_taxonomy_database`, `main`, `match_products`, `merge_intelligence`, `merge_product_knowledge`, `merge_taxonomy`, `print_text_response`, `taxonomy_match_score`, `taxonomy_search_text`

### `python\shopping_brain_before_knowledge_gate_20260805_235931.py`
- Status: **PASS**
- Lines: 1194 | Category: Shopping Intelligence
- Uses: `intent_engine`, `knowledge_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `_index_by_product_id`, `_load_database`, `_normalize_query_text`, `build_decision_summary`, `build_response`, `infer_requested_product_types`, `knowledge_match_score`, `load_feature_database`, `load_identity_database`, `load_products`, `load_taxonomy_database`, `main`, `match_products`, `merge_intelligence`, `merge_product_knowledge`, `merge_taxonomy`, `print_text_response`, `taxonomy_match_score`, `taxonomy_search_text`

### `python\shopping_brain_before_knowledge_score_20260805_223921.py`
- Status: **PASS**
- Lines: 930 | Category: Shopping Intelligence
- Uses: `intent_engine`, `knowledge_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `_index_by_product_id`, `_load_database`, `_normalize_query_text`, `build_response`, `infer_requested_product_types`, `load_feature_database`, `load_identity_database`, `load_products`, `load_taxonomy_database`, `main`, `match_products`, `merge_intelligence`, `merge_product_knowledge`, `merge_taxonomy`, `print_text_response`, `taxonomy_match_score`, `taxonomy_search_text`

### `python\shopping_brain_before_match_v1_20260803_230715.py`
- Status: **PASS**
- Lines: 875 | Category: Shopping Intelligence
- Uses: `intent_engine`, `knowledge_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `_index_by_product_id`, `_load_database`, `_normalize_query_text`, `build_response`, `infer_requested_product_types`, `load_feature_database`, `load_identity_database`, `load_products`, `load_taxonomy_database`, `main`, `match_products`, `merge_intelligence`, `merge_product_knowledge`, `merge_taxonomy`, `print_text_response`, `taxonomy_match_score`, `taxonomy_search_text`

### `python\shopping_brain_before_requirement_match_finish_20260803_231339.py`
- Status: **PASS**
- Lines: 875 | Category: Shopping Intelligence
- Uses: `intent_engine`, `knowledge_engine`, `price_engine`, `product_scoring`, `recommendation_engine`
- Functions: `_index_by_product_id`, `_load_database`, `_normalize_query_text`, `build_response`, `infer_requested_product_types`, `load_feature_database`, `load_identity_database`, `load_products`, `load_taxonomy_database`, `main`, `match_products`, `merge_intelligence`, `merge_product_knowledge`, `merge_taxonomy`, `print_text_response`, `taxonomy_match_score`, `taxonomy_search_text`

### `python\shopping_decision_engine.py`
- Status: **PASS**
- Lines: 194 | Category: Product Intelligence
- Uses: `intent_engine`, `weighted_fit_engine`
- Functions: `decide`, `print_decision`

### `python\shopping_intelligence_pipeline.py`
- Status: **PASS**
- Lines: 1132 | Category: Product Intelligence
- Uses: `intent_engine`, `market_discovery`, `official_source_resolver`, `official_spec_extractor`, `product_fit_signal_builder`, `product_identity_v2`, `resolver_engine`, `retail_price_evidence`, `weighted_fit_engine`
- Functions: `call_build_identity`, `candidate_to_identity_input`, `canonical_brand_from_title`, `clean`, `criterion_groups`, `extraction_is_usable`, `fallback_brand_from_title`, `hostname`, `is_possible_official_page`, `main`, `print_result`, `repair_identity`, `resolve_with_fallback`, `resolver_input_from_identity`, `run_pipeline`, `runtime_profile_from_extraction`, `safe_float`, `sanitize_discovery_title`, `save_runtime_payload`, `universal_official_resolve`

### `python\shopping_intelligence_pipeline_before_brand_fix_20260809.py`
- Status: **PASS**
- Lines: 1056 | Category: Product Intelligence
- Uses: `intent_engine`, `market_discovery`, `official_source_resolver`, `official_spec_extractor`, `product_fit_signal_builder`, `product_identity_v2`, `resolver_engine`, `weighted_fit_engine`
- Functions: `call_build_identity`, `candidate_to_identity_input`, `canonical_brand_from_title`, `clean`, `criterion_groups`, `extraction_is_usable`, `fallback_brand_from_title`, `hostname`, `is_possible_official_page`, `main`, `print_result`, `repair_identity`, `resolve_with_fallback`, `resolver_input_from_identity`, `run_pipeline`, `runtime_profile_from_extraction`, `safe_float`, `sanitize_discovery_title`, `save_runtime_payload`, `universal_official_resolve`

### `python\shopping_intelligence_pipeline_before_evidence_diag_20260809.py`
- Status: **PASS**
- Lines: 1101 | Category: Product Intelligence
- Uses: `intent_engine`, `market_discovery`, `official_source_resolver`, `official_spec_extractor`, `product_fit_signal_builder`, `product_identity_v2`, `resolver_engine`, `retail_price_evidence`, `weighted_fit_engine`
- Functions: `call_build_identity`, `candidate_to_identity_input`, `canonical_brand_from_title`, `clean`, `criterion_groups`, `extraction_is_usable`, `fallback_brand_from_title`, `hostname`, `is_possible_official_page`, `main`, `print_result`, `repair_identity`, `resolve_with_fallback`, `resolver_input_from_identity`, `run_pipeline`, `runtime_profile_from_extraction`, `safe_float`, `sanitize_discovery_title`, `save_runtime_payload`, `universal_official_resolve`

### `python\shopping_intelligence_pipeline_before_fit_diagnostics_20260809.py`
- Status: **PASS**
- Lines: 1031 | Category: Product Intelligence
- Uses: `intent_engine`, `market_discovery`, `official_source_resolver`, `official_spec_extractor`, `product_fit_signal_builder`, `product_identity_v2`, `resolver_engine`, `weighted_fit_engine`
- Functions: `call_build_identity`, `candidate_to_identity_input`, `canonical_brand_from_title`, `clean`, `criterion_groups`, `extraction_is_usable`, `fallback_brand_from_title`, `hostname`, `is_possible_official_page`, `main`, `print_result`, `repair_identity`, `resolve_with_fallback`, `resolver_input_from_identity`, `run_pipeline`, `runtime_profile_from_extraction`, `safe_float`, `sanitize_discovery_title`, `save_runtime_payload`, `universal_official_resolve`

### `python\shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835.py`
- Status: **PASS**
- Lines: 1114 | Category: Product Intelligence
- Uses: `intent_engine`, `market_discovery`, `official_source_resolver`, `official_spec_extractor`, `product_fit_signal_builder`, `product_identity_v2`, `resolver_engine`, `retail_price_evidence`, `weighted_fit_engine`
- Functions: `call_build_identity`, `candidate_to_identity_input`, `canonical_brand_from_title`, `clean`, `criterion_groups`, `extraction_is_usable`, `fallback_brand_from_title`, `hostname`, `is_possible_official_page`, `main`, `print_result`, `repair_identity`, `resolve_with_fallback`, `resolver_input_from_identity`, `run_pipeline`, `runtime_profile_from_extraction`, `safe_float`, `sanitize_discovery_title`, `save_runtime_payload`, `universal_official_resolve`

### `python\shopping_intelligence_pipeline_before_price_evidence_20260809.py`
- Status: **PASS**
- Lines: 1091 | Category: Price / Inventory
- Uses: `intent_engine`, `market_discovery`, `official_source_resolver`, `official_spec_extractor`, `product_fit_signal_builder`, `product_identity_v2`, `resolver_engine`, `weighted_fit_engine`
- Functions: `call_build_identity`, `candidate_to_identity_input`, `canonical_brand_from_title`, `clean`, `criterion_groups`, `extraction_is_usable`, `fallback_brand_from_title`, `hostname`, `is_possible_official_page`, `main`, `print_result`, `repair_identity`, `resolve_with_fallback`, `resolver_input_from_identity`, `run_pipeline`, `runtime_profile_from_extraction`, `safe_float`, `sanitize_discovery_title`, `save_runtime_payload`, `universal_official_resolve`

### `python\shopping_intelligence_pipeline_before_resolver_diag_20260810_000343.py`
- Status: **PASS**
- Lines: 1108 | Category: Product Intelligence
- Uses: `intent_engine`, `market_discovery`, `official_source_resolver`, `official_spec_extractor`, `product_fit_signal_builder`, `product_identity_v2`, `resolver_engine`, `retail_price_evidence`, `weighted_fit_engine`
- Functions: `call_build_identity`, `candidate_to_identity_input`, `canonical_brand_from_title`, `clean`, `criterion_groups`, `extraction_is_usable`, `fallback_brand_from_title`, `hostname`, `is_possible_official_page`, `main`, `print_result`, `repair_identity`, `resolve_with_fallback`, `resolver_input_from_identity`, `run_pipeline`, `runtime_profile_from_extraction`, `safe_float`, `sanitize_discovery_title`, `save_runtime_payload`, `universal_official_resolve`

### `python\shopping_intelligence_pipeline_before_resolver_resilience_20260809.py`
- Status: **PASS**
- Lines: 1031 | Category: Product Intelligence
- Uses: `intent_engine`, `market_discovery`, `official_source_resolver`, `official_spec_extractor`, `product_fit_signal_builder`, `product_identity_v2`, `resolver_engine`, `weighted_fit_engine`
- Functions: `call_build_identity`, `candidate_to_identity_input`, `canonical_brand_from_title`, `clean`, `criterion_groups`, `extraction_is_usable`, `fallback_brand_from_title`, `hostname`, `is_possible_official_page`, `main`, `print_result`, `repair_identity`, `resolve_with_fallback`, `resolver_input_from_identity`, `run_pipeline`, `runtime_profile_from_extraction`, `safe_float`, `sanitize_discovery_title`, `save_runtime_payload`, `universal_official_resolve`

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

### `python\weighted_fit_engine.py`
- Status: **PASS**
- Lines: 402 | Category: Product Intelligence
- Classes: `CriterionResult`
- Functions: `_clamp01`, `_hard_constraint_failures`, `_normalize_signal`, `calculate_product_fit`, `rank_recommendations`

### `python\weighted_fit_engine_before_budget_unknown_gate_20260810_000816.py`
- Status: **PASS**
- Lines: 394 | Category: Product Intelligence
- Classes: `CriterionResult`
- Functions: `_clamp01`, `_hard_constraint_failures`, `_normalize_signal`, `calculate_product_fit`, `rank_recommendations`

### `python\weighted_fit_engine_before_must_have_signal_gate_20260809.py`
- Status: **PASS**
- Lines: 352 | Category: Product Intelligence
- Classes: `CriterionResult`
- Functions: `_clamp01`, `_hard_constraint_failures`, `_normalize_signal`, `calculate_product_fit`, `rank_recommendations`

### `run_gemini_vision_batch_v1.py`
- Status: **FAIL**
- Lines: 163 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `run_gemini_vision_batch_v2.py`
- Status: **PASS**
- Lines: 286 | Category: Utility / Other
- Functions: `load_json`, `main`, `result_provenance_matches`

### `test_gemini_batch_validation.py`
- Status: **FAIL**
- Lines: 99 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `test_gemini_vision_media01.py`
- Status: **FAIL**
- Lines: 131 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `test_universal_semantic_consolidator_v1.py`
- Status: **PASS**
- Lines: 141 | Category: Utility / Other
- Uses: `official_spec_extractor`

### `test_universal_semantic_consolidator_v1_1.py`
- Status: **PASS**
- Lines: 197 | Category: Utility / Other
- Uses: `official_spec_extractor`

### `test_universal_semantic_consolidator_v1_2.py`
- Status: **PASS**
- Lines: 243 | Category: Utility / Other
- Uses: `official_spec_extractor`

### `test_universal_semantic_consolidator_v1_3.py`
- Status: **PASS**
- Lines: 259 | Category: Utility / Other
- Uses: `official_spec_extractor`

### `test_universal_semantic_schema_validator_v1.py`
- Status: **PASS**
- Lines: 135 | Category: Utility / Other

### `test_universal_semantic_schema_validator_v2.py`
- Status: **PASS**
- Lines: 151 | Category: Utility / Other

### `test_universal_semantic_schema_validator_v3.py`
- Status: **PASS**
- Lines: 214 | Category: Utility / Other

### `test_vision_semantic_consolidation_v1.py`
- Status: **PASS**
- Lines: 218 | Category: Utility / Other
- Uses: `official_spec_extractor`
- Functions: `canonical_key`, `norm`

### `upgrade_brand_domain_mappings.py`
- Status: **FAIL**
- Lines: 49 | Category: Utility / Other
- Error: `Line 1: invalid non-printable character U+FEFF`

### `upgrade_intent_engine_features_v2.py`
- Status: **PASS**
- Lines: 121 | Category: Product Intelligence
- Functions: `main`

### `upgrade_resolver_page_priority_v41.py`
- Status: **PASS**
- Lines: 155 | Category: Utility / Other
- Functions: `main`

## Review Warnings

### Syntax Errors
- `add_ask_command.py` — Line 1: invalid non-printable character U+FEFF
- `add_nothing_identity_domain.py` — Line 1: invalid non-printable character U+FEFF
- `approve_logitech_knowledge.py` — Line 1: invalid non-printable character U+FEFF
- `approve_nothing_phone_3_knowledge.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_apple_specs_structure.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_embedded_free_text.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_embedded_media_inventory.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_media_dimensions.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_media_ranking.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_nothing_embedded_data.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_nothing_identity.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_nothing_product_evidence.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_nothing_search.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_nuxt_product_payload.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_nuxt_reference_graph.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_realme_embedded_data.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_search_evidence.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_supporting_source_snippets.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_universal_page_content.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_universal_source_discovery.py` — Line 1: invalid non-printable character U+FEFF
- `diagnose_vision_validation_reasons.py` — Line 1: invalid non-printable character U+FEFF
- `download_media_candidates.py` — Line 1: invalid non-printable character U+FEFF
- `fix_display_parser.py` — Line 1: invalid non-printable character U+FEFF
- `fix_display_size_v2.py` — Line 1: invalid non-printable character U+FEFF
- `fix_extractor_core_title.py` — Line 1: invalid non-printable character U+FEFF
- `install_resolver_brand_registry_v1.py` — Line 1: invalid non-printable character U+FEFF
- `python\build_product_pages_before_published_gate.py` — Line 1: invalid non-printable character U+FEFF
- `python\build_product_pages_before_published_gate_20260809_002946.py` — Line 1: invalid non-printable character U+FEFF
- `python\couponworld.py` — Line 1: invalid non-printable character U+FEFF
- `python\intelligence\verified_image_engine.py` — Line 1: invalid non-printable character U+FEFF
- `python\intelligence\verified_image_engine_before_diagnostics_20260810_201836.py` — Line 1: invalid non-printable character U+FEFF
- `python\intelligence\verified_image_engine_before_official_context_fallback_20260812_232525.py` — Line 1: invalid non-printable character U+FEFF
- `python\intelligence\verified_image_engine_before_quota_output_20260812_232320.py` — Line 1: invalid non-printable character U+FEFF
- `python\intelligence\verified_image_engine_before_quota_stop_20260812_232133.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_source_resolver.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_source_resolver_before_batch_quota_break_20260813_203745.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_exact_href_priority_20260811_235529.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_gemini_retry_20260811_233822.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_html_context.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_identity_gate_20260811_224557.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_identity_parser_20260811_224512.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_identity_result_fields_20260811_224653.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_identity_rules_20260811_224433.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_img_context_call.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_prompt_identity_schema_20260811_224344.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_ranker_official_url_20260811_235437.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_scan_order_fix.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_srcset_context.py` — Line 1: invalid non-printable character U+FEFF
- `python\official_spec_extractor_before_vision_provenance_gate_20260808_120429.py` — Line 1: invalid non-printable character U+FEFF
- `python\product_identity_v2.py` — Line 1: invalid non-printable character U+FEFF
- `python\retail_price_evidence.py` — Line 1: invalid non-printable character U+FEFF
- `python\retail_price_evidence_before_v11_20260809.py` — Line 1: invalid non-printable character U+FEFF
- `python\retail_price_evidence_before_v12_cache_20260809.py` — Line 1: invalid non-printable character U+FEFF
- `python\shopping_brain_backup.py` — Line 1: invalid non-printable character U+FEFF
- `run_gemini_vision_batch_v1.py` — Line 1: invalid non-printable character U+FEFF
- `test_gemini_batch_validation.py` — Line 1: invalid non-printable character U+FEFF
- `test_gemini_vision_media01.py` — Line 1: invalid non-printable character U+FEFF
- `upgrade_brand_domain_mappings.py` — Line 1: invalid non-printable character U+FEFF

### Possible Orphan Modules
- `add_ask_command`
- `add_nothing_identity_domain`
- `approve_logitech_knowledge`
- `approve_nothing_phone_3_knowledge`
- `build_product_pages_before_published_gate`
- `build_product_pages_before_published_gate_20260809_002946`
- `data.python.seo_generator`
- `diagnose_apple_specs_structure`
- `diagnose_embedded_free_text`
- `diagnose_embedded_media_inventory`
- `diagnose_media_dimensions`
- `diagnose_media_ranking`
- `diagnose_nothing_embedded_data`
- `diagnose_nothing_identity`
- `diagnose_nothing_product_evidence`
- `diagnose_nothing_search`
- `diagnose_nuxt_product_payload`
- `diagnose_nuxt_reference_graph`
- `diagnose_realme_embedded_data`
- `diagnose_search_evidence`
- `diagnose_supporting_source_snippets`
- `diagnose_universal_page_content`
- `diagnose_universal_source_discovery`
- `diagnose_vision_validation_reasons`
- `download_media_candidates`
- `fix_display_parser`
- `fix_display_size_v2`
- `fix_extractor_core_title`
- `install_knowledge_match_score_v1`
- `install_resolver_brand_registry_v1`
- `intelligence.verified_image_engine`
- `intelligence.verified_image_engine_before_diagnostics_20260810_201836`
- `intelligence.verified_image_engine_before_official_context_fallback_20260812_232525`
- `intelligence.verified_image_engine_before_quota_output_20260812_232320`
- `intelligence.verified_image_engine_before_quota_stop_20260812_232133`
- `intent_engine_before_explicit_priority_20260809`
- `intent_engine_before_feature_v2_20260805_232541`
- `intent_engine_before_gamer_profile_fix_20260809_143059`
- `intent_engine_before_v2_20260809`
- `official_source_resolver_before_batch_quota_break_20260813_203745`
- `official_source_resolver_v3`
- `official_spec_extractor_before_exact_href_priority_20260811_235529`
- `official_spec_extractor_before_gemini_retry_20260811_233822`
- `official_spec_extractor_before_html_context`
- `official_spec_extractor_before_identity_gate_20260811_224557`
- `official_spec_extractor_before_identity_parser_20260811_224512`
- `official_spec_extractor_before_identity_result_fields_20260811_224653`
- `official_spec_extractor_before_identity_rules_20260811_224433`
- `official_spec_extractor_before_img_context_call`
- `official_spec_extractor_before_prompt_identity_schema_20260811_224344`
- `official_spec_extractor_before_ranker_official_url_20260811_235437`
- `official_spec_extractor_before_scan_order_fix`
- `official_spec_extractor_before_srcset_context`
- `official_spec_extractor_before_vision_provenance_gate_20260808_120429`
- `publish_product_knowledge`
- `recommendation_engine_before_match_v1_20260803_230715`
- `research_agent`
- `resolver_engine_before_alpha_exact_fix_20260810_001430`
- `resolver_engine_before_brand_registry_20260808_231140`
- `resolver_engine_before_domain_noise_fix_20260810_001348`
- `resolver_engine_before_nothing_domain_20260804_224458`
- `retail_price_evidence_before_v11_20260809`
- `retail_price_evidence_before_v12_cache_20260809`
- `run_gemini_vision_batch_v1`
- `shopping_brain_backup`
- `shopping_decision_engine`
- `tavily_test`
- `test_gemini_batch_validation`
- `test_gemini_vision_media01`
- `test_universal_semantic_consolidator_v1`
- `test_universal_semantic_consolidator_v1_1`
- `test_universal_semantic_consolidator_v1_2`
- `test_universal_semantic_consolidator_v1_3`
- `test_universal_semantic_schema_validator_v1`
- `test_universal_semantic_schema_validator_v2`
- `test_universal_semantic_schema_validator_v3`
- `test_vision_semantic_consolidation_v1`
- `upgrade_brand_domain_mappings`
- `weighted_fit_engine_before_budget_unknown_gate_20260810_000816`
- `weighted_fit_engine_before_must_have_signal_gate_20260809`

### Exact Duplicate Files
- `python\build_product_pages_before_intelligence_v1.py`, `python\build_product_pages_before_verified_intelligence_20260808_232718.py`
- `python\build_product_pages_before_published_gate.py`, `python\build_product_pages_before_published_gate_20260809_002946.py`
- `python\couponworld_before_vision_key_fix_v2_20260808_134834.py`, `python\couponworld_before_vision_key_fix_v3_20260808_135512.py`
- `python\intelligence\verified_image_engine_before_exact_href_priority_20260811_235820.py`, `python\intelligence\verified_image_engine_before_exact_product_v2.py`
- `python\official_source_resolver_before_identity_gate_20260810_232936.py`, `python\official_source_resolver_before_identity_override_20260810_233123.py`
- `python\official_source_resolver_before_quota_stop_20260813_203309.py`, `python\official_source_resolver_before_quota_stop_20260813_203605.py`
- `python\official_spec_extractor_before_hero_score_20260810_195931.py`, `python\official_spec_extractor_before_hero_suitability_20260810_195819.py`
- `python\official_spec_extractor_before_identity_fields_20260811_224104.py`, `python\official_spec_extractor_before_identity_fields_20260811_224248.py`, `python\official_spec_extractor_before_identity_vision_gate_20260811_223906.py`
- `python\official_spec_extractor_before_media_hygiene_20260810_202414.py`, `python\official_spec_extractor_before_media_hygiene_20260810_202424.py`, `python\official_spec_extractor_before_ranker_hygiene_20260810_203041.py`, `python\official_spec_extractor_before_ranker_hygiene_v2_20260810_203438.py`, `python\official_spec_extractor_before_ranker_hygiene_v3_20260810_203618.py`
- `python\official_spec_extractor_before_universal_sections_20260806_225951.py`, `python\official_spec_extractor_before_universal_sections_20260806_230951.py`
- `python\official_spec_extractor_before_validator_v1_1_3_20260808_000101.py`, `python\official_spec_extractor_before_vision_validator_minimal_20260807_235556.py`, `python\official_spec_extractor_before_vision_validator_v1_1_20260807_234529.py`, `python\official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840.py`
- `python\official_spec_extractor_before_vision_promotion_gate_20260807_222918.py`, `python\official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332.py`
- `python\shopping_brain_before_decision_engine_20260805_235240.py`, `python\shopping_brain_before_decision_engine_20260805_235607.py`
- `python\shopping_brain_before_match_v1_20260803_230715.py`, `python\shopping_brain_before_requirement_match_finish_20260803_231339.py`
- `python\shopping_intelligence_pipeline_before_fit_diagnostics_20260809.py`, `python\shopping_intelligence_pipeline_before_resolver_resilience_20260809.py`

### Repeated Public Function Names
Repeated names are review indicators, not automatic bugs.
- `adapt_source`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `add`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `add_specification`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `add_stream_spec`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `anc_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `apply_review_decision`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `ask_command`: `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `attach_universal_semantic_result`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`
- `attach_vision_provider_state`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `backup`: `amazon_catalog_sync`, `apply_requirement_match_v1`, `inventory_status_manager`, `publish_product_knowledge`
- `backup_output`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `battery_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `budget_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `build_command`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `build_decision_summary`: `shopping_brain`, `shopping_brain_before_knowledge_gate_20260805_235931`
- `build_discovery_queries`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `build_findings`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `build_fit_signals`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `build_output`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`, `product_feature_engine`
- `build_parser`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `build_priority_weights`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_gamer_profile_fix_20260809_143059`
- `build_record`: `batch_product_importer`, `product_pipeline`
- `build_response`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `build_source_queries`: `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`
- `build_universal_semantic_input`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`
- `build_universal_semantic_prompt`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`
- `build_vision_job_payload`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `build_vision_knowledge_candidates`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `build_vision_provider_config`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `calculate_product_fit`: `weighted_fit_engine`, `weighted_fit_engine_before_budget_unknown_gate_20260810_000816`, `weighted_fit_engine_before_must_have_signal_gate_20260809`
- `call_build_identity`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `call_quality_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `camera_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `candidate_quality_score`: `market_discovery`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `candidate_to_identity_input`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `canonical_brand_from_title`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `check_command`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `classify_candidate`: `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`
- `classify_source_type`: `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`
- `clean`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`, `build_sitemap`, `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`, `deal_engine`, `google_discovery_audit`, `import_products`, `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`, `internal_link_engine`, `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`, `product_intelligence`, `product_queue`, `product_source_adapter`, `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`, `site_intelligence`
- `clean_text`: `migrate_product_schema`, `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`, `product_engine`, `product_feature_engine`, `product_identity_engine`, `remove_amazon_branding`
- `collect_audit`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `collect_embedded_media_evidence`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `collect_official_source_urls`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `compact_product_title`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `compare_identity`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `connectivity_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `core_product_title`: `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `count_html_product_pages`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `create_backup`: `migrate_product_schema`, `price_importer`, `product_engine`
- `criterion_groups`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `decode_indexed_state_graph`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `decode_shopify_oxygen_stream`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `detect_brand`: `product_engine`, `product_identity_engine`, `product_intelligence`
- `detect_brands`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_feature_v2_20260805_232541`, `intent_engine_before_gamer_profile_fix_20260809_143059`, `intent_engine_before_v2_20260809`
- `detect_budget`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_feature_v2_20260805_232541`, `intent_engine_before_gamer_profile_fix_20260809_143059`, `intent_engine_before_v2_20260809`
- `detect_category`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_feature_v2_20260805_232541`, `intent_engine_before_gamer_profile_fix_20260809_143059`, `intent_engine_before_v2_20260809`
- `detect_family`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`, `internal_link_engine`
- `detect_features`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_feature_v2_20260805_232541`, `intent_engine_before_gamer_profile_fix_20260809_143059`, `intent_engine_before_v2_20260809`
- `detect_intent`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_feature_v2_20260805_232541`, `intent_engine_before_gamer_profile_fix_20260809_143059`, `intent_engine_before_v2_20260809`
- `detect_requirements`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_gamer_profile_fix_20260809_143059`
- `detect_use_cases`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_gamer_profile_fix_20260809_143059`
- `detect_user_profile`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_gamer_profile_fix_20260809_143059`
- `discover_market`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `display_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `ease_of_use_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `embedded_value_is_useful`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `empty_vision_claim`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `equivalent_model`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `excerpt`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`
- `exists`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `explain_product`: `recommendation_engine`, `recommendation_engine_before_match_v1_20260803_230715`
- `extract_apple_techspecs`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_asin`: `product_identity_engine`, `product_pipeline`
- `extract_brand`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `extract_color_tokens`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `extract_definition_lists`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_embedded_state_specs`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_features`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_json_ld_specs`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_label_value_blocks`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_memory_tokens`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `extract_meta`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_one`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_shopify_oxygen_specs`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_structured_sections`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extract_tables`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `extraction_is_usable`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `fallback_brand_from_title`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `feature_relevance_score`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `feature_scope`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `fetch_page`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `finalize_vision_knowledge_candidates`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `freeze_pending_intelligence_ids`: `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_verified_product_gate_20260808_161003`
- `generic_unknown`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `get_product_id`: `build_product_knowledge`, `product_classifier`
- `has_category_hint`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `has_extra_model_modifier`: `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`
- `has_price`: `product_queue`, `site_intelligence`
- `host_of`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `hostname`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`, `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `hostname_matches`: `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `identity_tokens`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `import_products`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `import_vision_result_payload`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `infer_brand_from_url`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `infer_requested_product_types`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `initialize_vision_claim_slots`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `inspect_backend_api`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `inspect_backup_clutter`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `inspect_core_modules`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `inspect_coupon_db`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `inspect_frontend`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `inspect_gitignore`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `inspect_knowledge`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `inspect_security`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `inspect_seo`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `intake_products`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `intelligence_command`: `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `intelligence_report`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `is_editorial_title`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `is_generic_listing_title`: `market_discovery`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `is_noise_feature`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `is_old_amazon_widget`: `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`
- `is_possible_official_page`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `is_search_or_listing_url`: `market_discovery`, `market_discovery_before_v161_quality_gate_20260809`
- `is_unwanted_page`: `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `is_unwanted_url`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `knowledge_command`: `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `knowledge_match_score`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`
- `known_brand_from_title`: `market_discovery`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `link_type`: `product_intelligence`, `product_queue`
- `load`: `approve_product_11_from_semantic_v1`, `inventory_status_manager`
- `load_existing`: `coupon_bot`, `import_products`
- `load_existing_output`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `load_existing_results`: `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `load_feature_database`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `load_identity_database`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `load_identity_index`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `load_json`: `build_product_knowledge`, `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`, `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`, `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`, `product_classifier`, `product_engine`, `product_feature_engine`, `product_intelligence_bridge`, `publish_approved_knowledge_v1`, `publish_product_knowledge`, `real_recommendation_ranker`, `run_gemini_vision_batch_v2`
- `load_products`: `amazon_catalog_sync`, `build_product_knowledge`, `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`, `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`, `migrate_product_schema`, `price_importer`, `product_feature_engine`, `product_identity_engine`, `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `load_taxonomy_database`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `load_vision_result_payload`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `looks_like_product_result`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `main`: `add_resolver_model_score_filter`, `amazon_catalog_sync`, `apply_requirement_match_v1`, `approve_apple_iphone_17e_knowledge`, `approve_product_11_from_semantic_v1`, `batch_product_importer`, `batch_product_queue`, `build_product_knowledge`, `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`, `build_sitemap`, `coupon_bot`, `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`, `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`, `deal_engine`, `finish_requirement_match_v1`, `fix_couponworld_vision_script_key_v1`, `fix_couponworld_vision_script_key_v2`, `fix_couponworld_vision_script_key_v3`, `fix_intent_engine_v2_gamer_profile`, `fix_universal_embedded_state_precision_v1_1`, `google_discovery_audit`, `import_products`, `improve_candidate_page_priority`, `improve_resolver_queries`, `install_apple_techspecs_extractor_v1`, `install_brand_domain_registry_expansion_v1`, `install_couponworld_intelligence_command_v1`, `install_decision_engine_v1`, `install_decision_engine_v1_1`, `install_decision_engine_v1_2`, `install_final_vision_knowledge_review_gate_v1`, `install_intelligence_batch_id_freezer_v1`, `install_intelligence_partial_evidence_mode_v1`, `install_intelligence_vision_v2_orchestration`, `install_knowledge_command_v1`, `install_knowledge_gate_v2`, `install_knowledge_ranking_v1`, `install_published_knowledge_gate_v1`, `install_resolver_source_family_stability_v1`, `install_semantic_partial_state_persistence_v1`, `install_shopify_oxygen_extractor_v6`, `install_universal_embedded_state_v1`, `install_universal_evidence_collector_v1`, `install_universal_media_evidence_v1`, `install_universal_media_ranker_v1`, `install_universal_model_normalization_v1`, `install_universal_semantic_cli_v1`, `install_universal_semantic_core_v1_3`, `install_universal_source_discovery_v1`, `install_universal_structured_sections_v1`, `install_universal_structured_sections_v1_1`, `install_universal_vision_job_exporter_v1`, `install_universal_vision_provider_v1`, `install_verified_intelligence_renderer_v1`, `install_verified_product_gate_v1`, `install_vision_claim_promotion_gate_v1`, `install_vision_claim_promotion_gate_v1_1`, `install_vision_claim_schema_v1`, `install_vision_claim_validator_minimal_v1_1`, `install_vision_claim_validator_minimal_v1_1_2`, `install_vision_claim_validator_v1`, `install_vision_claim_validator_v1_1`, `install_vision_claim_validator_v1_1_1`, `install_vision_claim_validator_v1_1_3`, `install_vision_evidence_queue_v1`, `install_vision_provenance_import_gate_v1`, `install_vision_result_importer_v1`, `install_vision_to_knowledge_bridge_v1`, `intelligence.image_engine`, `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`, `internal_link_engine`, `inventory_status_manager`, `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`, `market_identity_bridge`, `migrate_product_schema`, `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`, `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`, `price_importer`, `product_classifier`, `product_engine`, `product_feature_engine`, `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`, `product_identity_engine`, `product_intelligence`, `product_intelligence_bridge`, `product_pipeline`, `product_queue`, `product_source_adapter`, `publish_approved_knowledge_v1`, `real_recommendation_ranker`, `remove_amazon_branding`, `run_gemini_vision_batch_v2`, `runtime_dependency_mapper`, `seo_generator`, `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`, `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`, `site_intelligence`, `system_audit_agent`, `upgrade_intent_engine_features_v2`, `upgrade_resolver_page_priority_v41`
- `match_products`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `merge_evidence_records`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `merge_intelligence`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `merge_product_knowledge`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `merge_taxonomy`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `model_identity_signal`: `market_discovery`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `model_score`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `module_functions`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `next_actions`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `normalize`: `coupon_bot`, `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_feature_v2_20260805_232541`, `intent_engine_before_gamer_profile_fix_20260809_143059`, `intent_engine_before_v2_20260809`, `product_classifier`, `publish_approved_knowledge_v1`, `publish_product_knowledge`
- `normalize_brand`: `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `normalize_category`: `product_identity_engine`, `real_recommendation_ranker`
- `normalize_imported_vision_claim`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `normalize_key`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`, `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `normalize_number`: `migrate_product_schema`, `product_feature_engine`
- `normalize_price`: `price_engine`, `price_importer`, `product_source_adapter`
- `normalize_row`: `import_products`, `product_source_adapter`
- `normalize_text`: `build_product_knowledge`, `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`, `product_intelligence`, `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `normalize_weights`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_gamer_profile_fix_20260809_143059`
- `normalized_model_tokens`: `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`
- `numeric`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `official_spec_list`: `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`
- `page_dir`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`
- `page_directory`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`, `internal_link_engine`
- `page_identity_score`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `page_type_score`: `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `page_url`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`, `google_discovery_audit`, `internal_link_engine`
- `parse_args`: `product_feature_engine`, `product_identity_engine`
- `parse_arguments`: `batch_product_importer`, `batch_product_queue`, `product_engine`, `product_pipeline`
- `parse_identity`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `parse_json_ld`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `parse_query`: `intent_engine`, `intent_engine_before_explicit_priority_20260809`, `intent_engine_before_feature_v2_20260805_232541`, `intent_engine_before_gamer_profile_fix_20260809_143059`, `intent_engine_before_v2_20260809`
- `path_of`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `performance_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `prepare_vision_evidence_queue`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `print_audit`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `print_preview`: `product_engine`, `product_pipeline`
- `print_report`: `batch_product_queue`, `product_classifier`, `product_engine`, `product_feature_engine`, `product_identity_engine`
- `print_result`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`, `market_identity_bridge`, `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `print_section`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`, `product_intelligence`, `product_queue`
- `print_status`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `print_text_response`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `priority_score`: `product_queue`, `site_intelligence`
- `product_id`: `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`
- `product_identity`: `build_sitemap`, `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`, `internal_link_engine`, `product_intelligence`, `product_queue`
- `product_link`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `product_list`: `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`
- `promote_reviewed_vision_claims`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `public_files`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `ram_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `rank_media_evidence`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `rank_recommendations`: `weighted_fit_engine`, `weighted_fit_engine_before_budget_unknown_gate_20260810_000816`, `weighted_fit_engine_before_must_have_signal_gate_20260809`
- `ranked_candidates`: `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`
- `read_text`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `readiness_score`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `related`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`
- `remove_page_chrome`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `render`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`
- `repair_identity`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `replace_once`: `apply_requirement_match_v1`, `finish_requirement_match_v1`, `install_vision_claim_validator_minimal_v1_1`
- `resolve_product`: `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `resolve_product_image`: `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`
- `resolve_with_fallback`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `resolver_input_from_identity`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `run_command`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `run_pipeline`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `run_universal_semantic_cli`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_universal_images_20260810_202111`
- `run_workflow`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `runtime_profile_from_extraction`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `safe_float`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `safe_load_json`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`
- `sanitize_discovery_title`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `save`: `amazon_catalog_sync`, `inventory_status_manager`
- `save_json`: `build_product_knowledge`, `intelligence.verified_image_engine_before_exact_href_priority_20260811_235820`, `intelligence.verified_image_engine_before_exact_product_v2`, `intelligence.verified_image_engine_before_meta_shortlist_20260810_230418`, `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`, `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`, `product_classifier`, `product_engine`, `publish_approved_knowledge_v1`, `publish_product_knowledge`
- `save_products`: `migrate_product_schema`, `price_importer`
- `save_runtime_payload`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `save_vision_job_payload`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `score_product`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`, `product_scoring`
- `search_channel`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `searchable_text`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`, `internal_link_engine`
- `select_products`: `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `select_research_results`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `show_status`: `build_product_knowledge`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `significant_tokens`: `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `sitemap_urls`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `slugify`: `build_product_pages`, `build_product_pages_before_intelligence_v1`, `build_product_pages_before_verified_intelligence_20260808_232718`, `build_sitemap`, `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`, `internal_link_engine`, `product_identity_engine`
- `software_support_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `sound_quality_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `source_family_key`: `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`
- `stabilize_verified_source`: `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`
- `storage_signal`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `strong_product_url`: `market_discovery`, `market_discovery_before_quality_v14_20260809`, `market_discovery_before_quality_v15_20260809`, `market_discovery_before_v151_20260809`, `market_discovery_before_v161_quality_gate_20260809`, `market_discovery_before_v16_resilience_20260809`
- `subset_match`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `taxonomy_match_score`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `taxonomy_search_text`: `shopping_brain`, `shopping_brain_before_decision_engine_20260805_235240`, `shopping_brain_before_decision_engine_20260805_235607`, `shopping_brain_before_knowledge_gate_20260805_235931`, `shopping_brain_before_knowledge_score_20260805_223921`, `shopping_brain_before_match_v1_20260803_230715`, `shopping_brain_before_requirement_match_finish_20260803_231339`
- `text_blob`: `product_fit_signal_builder`, `product_fit_signal_builder_before_call_noise_phrase_20260809_235929`, `product_fit_signal_builder_before_hyphen_mic_20260809_235752`
- `token_match_score`: `official_source_resolver_backup`, `official_source_resolver_before_brand_expansion_20260804_222957`, `official_source_resolver_before_brand_registry_20260808_184921`, `official_source_resolver_before_identity_gate_20260810_232936`, `official_source_resolver_before_identity_override_20260810_233123`, `official_source_resolver_before_model_filter_20260804_225625`, `official_source_resolver_before_model_normalization_20260806_234104`, `official_source_resolver_before_page_priority_20260804_225410`, `official_source_resolver_before_page_priority_20260805_230553`, `official_source_resolver_before_query_improvement_20260804_223535`, `official_source_resolver_before_quota_stop_20260813_203309`, `official_source_resolver_before_quota_stop_20260813_203605`, `official_source_resolver_before_source_stability_20260808_124706`, `official_source_resolver_before_universal_sources_20260806_233209`
- `tokenize`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `universal_official_resolve`: `shopping_intelligence_pipeline`, `shopping_intelligence_pipeline_before_brand_fix_20260809`, `shopping_intelligence_pipeline_before_evidence_diag_20260809`, `shopping_intelligence_pipeline_before_fit_diagnostics_20260809`, `shopping_intelligence_pipeline_before_official_domain_gate_20260810_000835`, `shopping_intelligence_pipeline_before_price_evidence_20260809`, `shopping_intelligence_pipeline_before_resolver_diag_20260810_000343`, `shopping_intelligence_pipeline_before_resolver_resilience_20260809`
- `utc_now`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_apple_techspecs_20260805_231923`, `official_spec_extractor_before_core_title_fallback_20260804_230342`, `official_spec_extractor_before_embedded_precision_20260807_210218`, `official_spec_extractor_before_embedded_state_20260807_205842`, `official_spec_extractor_before_evidence_collector_20260806_235026`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_evidence_20260807_211103`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_media_ranker_20260807_212319`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_shopify_oxygen_20260804_233742`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_sections_20260806_225951`, `official_spec_extractor_before_universal_sections_20260806_230951`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_schema_20260807_214754`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_provider_20260807_215532`, `official_spec_extractor_before_vision_queue_20260807_214124`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`, `product_classifier`
- `validate_build_source`: `couponworld_before_ask_20260803_200050`, `couponworld_before_backup_tag_exclusions_20260812_233301`, `couponworld_before_batch_id_freezer_20260808_141555`, `couponworld_before_intelligence_v1_20260808_114212`, `couponworld_before_knowledge_command_20260805_225432`, `couponworld_before_partial_evidence_mode_20260808_121502`, `couponworld_before_verified_product_gate_20260808_161003`, `couponworld_before_vision_key_fix_v2_20260808_134834`, `couponworld_before_vision_key_fix_v3_20260808_135512`, `couponworld_before_vision_v2_orchestration_20260808_133158`
- `validate_candidate`: `resolver_engine`, `resolver_engine_before_alpha_exact_fix_20260810_001430`, `resolver_engine_before_brand_registry_20260808_231140`, `resolver_engine_before_domain_noise_fix_20260810_001348`, `resolver_engine_before_nothing_domain_20260804_224458`
- `validate_universal_semantic_result`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`
- `validate_vision_claim`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `validate_vision_claims`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `vision_provider_analyze`: `official_spec_extractor_before_always_rank_media_20260810_202234`, `official_spec_extractor_before_final_vision_knowledge_gate_20260807_223839`, `official_spec_extractor_before_gemini_hero_20260810_201207`, `official_spec_extractor_before_hero_score_20260810_195931`, `official_spec_extractor_before_hero_suitability_20260810_195819`, `official_spec_extractor_before_identity_fields_20260811_224104`, `official_spec_extractor_before_identity_fields_20260811_224248`, `official_spec_extractor_before_identity_vision_gate_20260811_223906`, `official_spec_extractor_before_media_hygiene_20260810_202414`, `official_spec_extractor_before_media_hygiene_20260810_202424`, `official_spec_extractor_before_meta_priority_20260810_225601`, `official_spec_extractor_before_partial_state_persistence_20260808_122702`, `official_spec_extractor_before_ranker_hygiene_20260810_203041`, `official_spec_extractor_before_ranker_hygiene_v2_20260810_203438`, `official_spec_extractor_before_ranker_hygiene_v3_20260810_203618`, `official_spec_extractor_before_semantic_cli_20260808_111908`, `official_spec_extractor_before_universal_images_20260810_202111`, `official_spec_extractor_before_universal_semantic_core_20260808_110205`, `official_spec_extractor_before_validator_v1_1_3_20260808_000101`, `official_spec_extractor_before_vision_claim_validator_20260807_222611`, `official_spec_extractor_before_vision_job_exporter_20260807_221202`, `official_spec_extractor_before_vision_knowledge_bridge_20260807_223614`, `official_spec_extractor_before_vision_promotion_gate_20260807_222918`, `official_spec_extractor_before_vision_promotion_gate_v1_1_20260807_223332`, `official_spec_extractor_before_vision_result_importer_20260807_222125`, `official_spec_extractor_before_vision_validator_minimal_20260807_235556`, `official_spec_extractor_before_vision_validator_v1_1_20260807_234529`, `official_spec_extractor_before_vision_validator_v1_1_2_20260807_235840`
- `write_report`: `couponworld_complete_audit`, `couponworld_complete_audit_before_bom_fix_20260809`

## Product Database

- Products: **74**
- Missing `sl_no`: **74**
- Missing `image`: **56**
- Missing `price`: **74**
- Missing `mrp`: **74**
- Missing `brand`: **7**

## Decision Rule

Before making a new engine: check existing responsibility, extend the matching module, and create a new module only for a genuinely separate responsibility.
