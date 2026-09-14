# Local API

The project exposes one local endpoint:

```text
POST http://127.0.0.1:8000/route
```

The API accepts structured ticket facts as JSON and passes them to the existing `rule_engine.py`. It does not make routing decisions itself. The rule engine returns the result, which the API sends back as JSON.

```text
Postman → POST /route → Python API → rule_engine.py → JSON response
```

Start it from the repository root with:

```powershell
python -m src.api
```

Two manual Postman checks were successfully completed: the local reservation case returned `L1` / `Normal`, and the mass availability case returned `Incident` / `Critical`, both with HTTP `200 OK`.
