import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

import retailer_offer_store as offers
import shopping_intelligence_pipeline as pipeline


VIVO_URL = "https://shop.vivo.com/in/product/10344?skuId=19410"


def _offer(observed_at: str, *, variant: str = "8GB/128GB", sku_url: str = VIVO_URL):
    return {
        "product_id": "cw-mobile-96",
        "retailer": "vivo",
        "retailer_product_id": "19410",
        "brand": "Vivo",
        "model": "T5 Pro 5G",
        "variant": variant,
        "title": "vivo T5 Pro 5G 8GB+128GB Cosmic Black",
        "price": 41999,
        "availability": "in_stock",
        "product_url": sku_url,
        "source": "json_ld_offer",
        "last_checked": observed_at,
        "metadata": {
            "evidence_source_url": sku_url,
            "evidence_source_type": "json_ld_offer",
            "evidence_observed_at": observed_at,
        },
    }


class ManufacturerOfferAdmissionTests(unittest.TestCase):
    def test_exact_fresh_first_party_offer_is_reusable(self):
        observed = datetime.now(timezone.utc).isoformat()
        with patch.object(offers, "load_offer_database", return_value={"offers": [_offer(observed)]}):
            result = offers.find_fresh_verified_offer(
                product_id="cw-mobile-96",
                brand="Vivo",
                model="T5 Pro 5G",
                variant="vivo T5 Pro 5G 8GB RAM 128GB Storage",
            )
        self.assertIsNotNone(result)
        self.assertEqual(result["retailer"], "vivo")
        self.assertEqual(result["retailer_product_id"], "19410")
        self.assertEqual(result["price"], 41999.0)

    def test_variant_and_selected_sku_guards_reject_mismatches(self):
        observed = datetime.now(timezone.utc).isoformat()
        wrong_variant = _offer(observed, variant="12GB/256GB")
        wrong_variant["retailer_product_id"] = "19411"
        with patch.object(offers, "load_offer_database", return_value={"offers": [wrong_variant]}):
            result = offers.find_fresh_verified_offer(
                product_id="cw-mobile-96",
                brand="Vivo",
                model="T5 Pro 5G",
                variant="8GB/128GB",
            )
        self.assertIsNone(result)

    def test_runtime_profile_uses_exact_fresh_manufacturer_offer_when_listing_price_is_missing(self):
        observed = datetime.now(timezone.utc).isoformat()
        extraction = {
            "search_name": "vivo T5 Pro 5G",
            "brand": "Vivo",
            "specifications": {
                "ram": {"value": "8 GB"},
                "storage": {"value": "128 GB"},
            },
            "features": ["9020 mAh battery"],
            "review": {"status": "candidate_ready"},
            "fetch_status": "success",
            "resolver_verified": True,
            "page_identity_score": 1.0,
            "official_url": VIVO_URL,
        }
        identity = {
            "product_id": "cw-mobile-96",
            "brand": "Vivo",
            "model": "T5 Pro 5G",
            "search_name": "vivo T5 Pro 5G",
            "original_title": "vivo T5 Pro 5G (Cosmic Black, 8GB RAM, 128GB Storage)",
            "asin": "B0H6F4KZGF",
            "confidence": {"score": 100},
        }
        resolved = {
            "status": "candidate_verified",
            "verified": True,
            "official_url": VIVO_URL,
            "official_title": "T5 Pro 5G 8GB+128GB Cosmic Black",
            "resolver_mode": "verified_official_source",
            "identity_score": 100,
            "match_score": 1.0,
        }
        candidate = {
            "candidate_id": "market-t5-pro",
            "asin": "B0H6F4KZGF",
            "title": identity["original_title"],
            "source_title": identity["original_title"],
            "source_url": "https://www.amazon.in/dp/B0H6F4KZGF",
            "source_host": "www.amazon.in",
        }
        intent = {
            "category": "smartphone",
            "budget_max": 50000,
            "priority_weights": {"budget": 30, "battery": 20, "camera": 20, "performance": 30},
        }
        with patch.object(
            pipeline,
            "build_price_evidence",
            return_value={"verified": False, "price": None, "availability": "unknown"},
        ), patch.object(
            offers,
            "load_offer_database",
            return_value={"offers": [_offer(observed)]},
        ):
            profile = pipeline.runtime_profile_from_extraction(
                candidate=candidate,
                identity=identity,
                resolved=resolved,
                extraction=extraction,
                intent=intent,
            )

        self.assertEqual(profile["price"], 41999.0)
        self.assertEqual(
            profile["provenance"]["price_evidence"]["retailer_product_id"],
            "19410",
        )
        self.assertEqual(
            profile["provenance"]["price_evidence"]["availability"],
            "in_stock",
        )


if __name__ == "__main__":
    unittest.main()
