# Local API

The project exposes deterministic and AI-assisted local routing endpoints:

```text
POST http://127.0.0.1:8000/route
POST http://127.0.0.1:8000/ai/route
```

The API accepts structured ticket facts as JSON and passes them to the existing `rule_engine.py`. It does not make routing decisions itself. The rule engine returns the result, which the API sends back as JSON.

`POST /ai/route` accepts `{ "text": "..." }`, obtains strict structured facts from the OpenAI extractor, then passes those facts to the same rule engine. Its response exposes `facts`, `decision`, and separate token/cost `usage` diagnostics.

```text
Postman → POST /route → Python API → rule_engine.py → JSON response
```

Start it from the repository root with:

```powershell
python -m src.api
```

Two manual Postman checks were successfully completed: the local reservation case returned `L1` / `Normal`, and the mass availability case returned `Incident` / `Critical`, both with HTTP `200 OK`.

Two real OpenAI-backed Postman checks were also completed through `/ai/route`: the mass availability text returned `Incident` / `Critical`, while the one-booking text preserved unknown `problem_active = null` and returned `Clarify` / no priority. Both returned HTTP `200` and usage diagnostics.
