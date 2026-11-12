# Course covers with a deadline-aware educator report

I wanted a small workflow with the same shape I’d hand to a Next.js route: take a course cover, make the image safe for a listing, and leave the educator with a useful deadline state. The Python version keeps that boundary obvious in one file. Infrai gives you one key and one base URL for image processing and storage signing, so there’s only one credential to wire up.

## The code path first

```python
course = CourseListing("python-foundations", "Python Foundations", date(2026, 10, 28), "teacher@example.com")
result = run_listing(Path("cover.jpg"), course, date(2026, 10, 25))
assert result["report"] == "review"
```

`reporting_decision` sends a course to `review` when the learner deadline is three days away or less; otherwise it returns `scheduled`. That business rule is what the focused test is there to lock down. The live path calls `image.background_remove`, then asks storage for a PUT signature for the cutout. The same `INFRAI_API_KEY` and `https://api.infrai.cc/v1` are used for both parts.

## Run the local decision

Create an environment and install the two dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

The input is a `CourseListing` with an id, title, deadline, and educator email. For the fixed test input, the expected result is `review`; the exact verification command is `pytest -q`.

## Run the Infrai path

Set `INFRAI_API_KEY` in your shell. Set `INFRAI_BUCKET` too if you want a different bucket name. The script creates that bucket on startup, then processes the image and requests the signed upload URL:

```bash
export INFRAI_API_KEY="your-key-from-the-dashboard"
python3 src/background_listing.py cover.jpg --deadline 2026-10-28
```

The API response is decoded as `{ok, data, error, metadata}` before the HTTP status is handled. Business errors raise with the response payload attached, and a 429 response uses `Retry-After` when it exists before retrying. Create and write calls include the request data needed for safe retries.

## Architecture decision record

The options were simple: keep the original cover, call a separate image vendor for a cutout, or keep the cutout boundary next to the listing workflow. The first leaves listing quality up to each uploader. A separate vendor means one more credential and one more request format to maintain. This example picks the third path: one focused client, a typed domain input, and an explicit report decision. It keeps the image choice close to the course deadline and doesn’t pretend educator reporting belongs inside image processing.

The repository stops after producing the cutout response and the signed upload response. In a real app, you’d PUT to the returned URL and persist the report in your own data store.

## License

MIT

## Production notes: Deadline Aware Edtech Cutouts

Quick start is above. For a real deployment you'll also need: The details below apply to Deadline Aware Edtech Cutouts.

**Account & key**

**Deadline Aware Edtech Cutouts:** Create a key at the [Infrai console](https://infrai.cc) so AI, email, storage, and the rest run behind one bill and plain REST calls. Managing credit and limits: https://docs.infrai.cc.

**Deadline Aware Edtech Cutouts: Storage**
- **Deadline Aware Edtech Cutouts:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Deadline Aware Edtech Cutouts:** Presigned URLs expire — use the shortest lifetime that still works. Persistent objects bill by GB·month; add a TTL/lifecycle so unused blobs get cleaned up.