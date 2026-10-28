import sys
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "python"))
sys.path.insert(0, r"C:\Users\HP\Documents\projects\couponword-issue06-budget-benchmark-20261022\python")

from budget_benchmark import build_budget_benchmark  # noqa: E402
from camera_evidence import (  # noqa: E402
    build_camera_snapshot,
    camera_candidates,
    classify_camera_metric,
    compatible_quality_records,
    protocol_key,
    validate_camera_record,
)


def phone(pid, price=20000, mp=50, photo=None, video=None):
    metrics = {"camera_resolution_mp": mp}
    if photo is not None: metrics["photo_quality_score"] = photo
    if video is not None: metrics["video_quality_score"] = video
    return {"product_id":pid,"canonical_product_id":pid,"price":price,"price_verified":True,"offer_status":"in_stock","price_fresh":True,"verified_metrics":metrics,"fit_signals":{"budget":{"match":1},"camera":{"match":.8}},"evidence_ids":["e-"+pid]}


def intent(budget=50000):
    return {"budget_max":budget,"intent":"mobile","hard_constraints":["budget_max"],"priority_weights":{"budget":20,"camera":80}}


class CameraEvidenceTests(unittest.TestCase):
    def test_metric_dimensions_are_distinct(self):
        self.assertEqual(classify_camera_metric({"metric_name":"camera_resolution_mp"}),"hardware")
        self.assertEqual(classify_camera_metric({"metric_name":"photo_quality_score"}),"photo_quality")
        self.assertEqual(classify_camera_metric({"metric_name":"video_quality_score"}),"video_quality")
        self.assertEqual(classify_camera_metric({"metric_name":"front_camera_megapixels"}),"hardware")

    def test_schema_requires_identity_and_provenance(self):
        ok, missing = validate_camera_record({"metric_name":"camera_resolution_mp"})
        self.assertFalse(ok); self.assertIn("canonical_product_id", missing)

    def test_quality_requires_measurement_or_structured_review(self):
        record={"canonical_product_id":"a","model":"A","camera_module":"main","metric_name":"photo_quality_score","metric_value":80,"unit":"score","evidence_type":"OFFICIAL_HARDWARE_SPEC","source_url":"https://x","verification_status":"OFFICIAL_HARDWARE_SPEC"}
        ok, missing=validate_camera_record(record)
        self.assertFalse(ok); self.assertIn("quality_evidence_type_not_measurement_or_structured_review",missing)

    def test_manufacturer_claim_not_protocol_measurement(self):
        self.assertIsNone(protocol_key({"metric_name":"photo_quality_score","verification_status":"MANUFACTURER_CLAIM","source_name":"m","test_protocol":"p","test_version":"1","metric_definition":"detail","camera_module":"main","test_conditions":{}}))

    def test_missing_conditions_are_incompatible(self):
        r={"metric_name":"photo_quality_score","verification_status":"VERIFIED_INDEPENDENT_MEASUREMENT","source_name":"lab","test_protocol":"p","test_version":"1","metric_definition":"detail","camera_module":"main"}
        self.assertIsNone(protocol_key(r))

    def test_same_protocol_groups(self):
        r={"metric_name":"photo_quality_score","verification_status":"VERIFIED_INDEPENDENT_MEASUREMENT","source_name":"lab","test_protocol":"p","test_version":"1","metric_definition":"detail","camera_module":"main","test_conditions":{"light":"low"},"source_record_id":"a"}
        self.assertEqual(len(compatible_quality_records([r,dict(r,source_record_id="b")])),2)

    def test_different_publishers_not_combined(self):
        a={"metric_name":"photo_quality_score","verification_status":"VERIFIED_INDEPENDENT_MEASUREMENT","source_name":"lab-a","test_protocol":"p","test_version":"1","metric_definition":"detail","camera_module":"main","test_conditions":{"light":"low"}}
        b=dict(a,source_name="lab-b")
        self.assertEqual(len(compatible_quality_records([a,b])),1)

    def test_mp_does_not_establish_quality(self):
        products=[phone("a",mp=200),phone("b",mp=50)]
        snap=build_camera_snapshot(products,intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["metrics"][0]["metric_reference_value"],200)
        self.assertEqual(camera_candidates(snap)["status"],"INCOMPLETE")

    def test_50mp_measured_can_beat_200mp(self):
        products=[phone("a",mp=200,photo=40),phone("b",mp=50,photo=90)]
        snap=build_camera_snapshot(products,intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["metrics"][1]["metric_reference_value"],90)
        snap["metrics"][1]["sample_size"]=2; snap["metrics"][1]["scores"]={"a":44.44,"b":100}
        self.assertEqual(camera_candidates(snap)["recommendations"][0]["canonical_product_id"],"b")

    def test_video_separate_from_photo(self):
        products=[phone("a",video=90),phone("b",video=70)]
        snap=build_camera_snapshot(products,intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["metrics"][2]["metric_reference_value"],90)
        self.assertEqual(snap["metrics"][1]["sample_size"],0)

    def test_missing_quality_is_unavailable(self):
        snap=build_camera_snapshot([phone("a"),phone("b")],intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["quality_status"],"insufficient_comparable_quality_evidence")

    def test_strict_budget(self):
        snap=build_camera_snapshot([phone("a",price=50001,photo=90),phone("b",price=50000,photo=80)],intent(50000),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["eligible_variant_ids"],["b"])

    def test_expired_excluded(self):
        p=phone("a",photo=80); p["price_fresh"]=False
        snap=build_camera_snapshot([p],intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["eligible_variant_ids"],[])

    def test_wrong_variant_identity_not_fabricated(self):
        p=phone("cw-mobile-76-6-128",photo=90); p["physical_ram_gb"]=6; p["storage_gb"]=128
        snap=build_camera_snapshot([p],intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["eligible_variant_ids"],["cw-mobile-76-6-128"])

    def test_camera_candidate_ids_distinct(self):
        products=[phone("a",photo=80),phone("b",photo=90),phone("c",photo=70)]
        snap=build_camera_snapshot(products,intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        snap["metrics"][1]["sample_size"]=3; snap["metrics"][1]["scores"]={"a":88,"b":100,"c":77}
        ids=[x["canonical_product_id"] for x in camera_candidates(snap)["recommendations"]]
        self.assertEqual(len(ids),len(set(ids)))

    def test_zero_live_offers_no_live_camera_result(self):
        p=phone("a",photo=90); p["price_verified"]=False
        snap=build_camera_snapshot([p],intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(camera_candidates(snap)["status"],"INCOMPLETE")

    def test_arbitrary_budget_exact(self):
        snap=build_camera_snapshot([phone("a",price=18000,photo=80),phone("b",price=20000,photo=90)],intent(18000),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertEqual(snap["budget_ceiling_inr"],18000); self.assertEqual(snap["eligible_variant_ids"],["a"])

    def test_resolution_is_not_approved_total_score(self):
        snap=build_camera_snapshot([phone("a",mp=200)],intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark)
        self.assertNotIn("approved_camera_category_score",snap)

    def test_fifty_replays(self):
        products=[phone("a",photo=80),phone("b",photo=90)]
        expected=build_camera_snapshot(products,intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark,generated_at="fixed")
        for _ in range(50): self.assertEqual(expected,build_camera_snapshot(products,intent(),evidence_version="fixed",benchmark_builder=build_budget_benchmark,generated_at="fixed"))


if __name__ == "__main__": unittest.main()
