# Production deployment checklist

This change is not deployed. The following gates are required before a separate production release:

1. Review and approve the branch diff and test receipt.
2. Confirm authorized Amazon/Flipkart/Croma provider access and fresh exact-variant observations.
3. Confirm at least one real eligible current offer for any live reference section; otherwise retain `LIVE_ELIGIBLE_POOL_EMPTY`.
4. Confirm Render build command `pip install -r requirements.txt` and start command `gunicorn --chdir python --bind 0.0.0.0:$PORT shopping_api:app`.
5. Deploy the backend revision and verify `/health` revision plus `/api/recommend` for ₹10,000, ₹20,000, ₹30,000, ₹50,000, ₹1,00,000, ₹1,50,000, ₹18,000 and ₹25,000.
6. Publish the static frontend only after verifying the response contract and responsive UI locally.
7. Recheck CTA fail-closed behavior, cache key/version and no stale offer resurrection.
8. Keep the 15-day benchmark refresh and six-hour retailer refresh separate; do not activate either scheduler as part of this review.

No merge into `main`, Render deployment, static publication or production scheduler activation was performed in this task.
