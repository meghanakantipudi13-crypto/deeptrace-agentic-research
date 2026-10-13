# Deployment Compliance Check

Last reviewed: 2026-10-12

## Phase 8 status

**PARTIALLY COMPLETE — USER ACTION REQUIRED.** The official topology is now sufficiently defined for a minimal implementation, but no cloud resource has been created and no live provider has been called. This computer has no Google Cloud CLI, Docker, Google credentials/project selection, Tavily key, GCS bucket, or PostgreSQL URI.

## Exact topology

“Cloud Run Instances” is a distinct preview/pre-GA Google Cloud resource, not an ordinary Cloud Run service. An instance is a manually managed, directly addressable, long-lived singleton intended for stateful agent loops such as Hermes. It receives a default HTTPS `run.app` URL and is created with `gcloud beta run instances deploy`. Stopping, updating, or replacing it loses local/in-memory state, so durable state cannot live only in the container filesystem.

The selected implementation path is:

1. A Cloud Run Instance hosts a pinned Hermes Agent image as the ingress/dashboard process on port 8080.
2. DeepTrace is exposed through Hermes' documented dashboard-plugin mechanism: a plugin manifest/JavaScript tab plus a `plugin_api.py` FastAPI router mounted below `/api/plugins/<name>/`. DeepTrace domain/workflow code remains a package used by that adapter. This makes the grader-facing URL the authenticated Hermes dashboard rather than an unrelated ordinary Cloud Run service.
3. Vertex AI Gemini supplies production planning through the Google Gen AI SDK and Application Default Credentials. Tavily remains the search provider, with its key supplied by Secret Manager.
4. GCS stores immutable user-facing research-session records. Cloud SQL PostgreSQL remains the official LangGraph checkpointer for mutable interrupt/resume state. GCS is not used as a bespoke graph checkpointer.
5. Cloud Logging automatically receives instance/container logs. A Phase 9 dashboard and alert will use the `cloud_run_instance` monitored resource.

The repository does not yet contain the Hermes packaging/container adapter. Creating it before the runtime is installed and before an authenticated project is selected would not prove compatibility.

## Platform and runtime constraints

- Cloud Run Instances are preview/pre-GA and unavailable in some regions, including `us-central1`, `us-east1`, and `europe-west1` in the current documentation. The final region must come from the then-current supported list.
- The official Hermes codelab deploys a 2-vCPU, 4-GiB instance, enables Run, Secret Manager, Storage, Compute, and Vertex AI APIs, mounts GCS through GCSFuse, and uses a service account. It notes a seven-day continuous-runtime limit followed by automatic restart.
- Hermes supports dashboard extensions with an authenticated plugin backend. A public bind must use a supported dashboard authentication provider; no unauthenticated DeepTrace approval endpoint is acceptable.
- One ingress container is supported, with optional sidecars. The exact final process/supervisor layout must be tested against the pinned Hermes release.
- Cloud Run Instance billing applies for the resource lifecycle; this is not request-only scale-to-zero behavior. Stop/delete the instance after grading when it is no longer needed.

## IAM and APIs

The deployer needs Cloud Run administration/development and Service Account User permissions. The runtime service account needs only the roles required by its calls: Vertex AI access, Secret Manager Secret Accessor for pinned secret versions, and Storage Object User on the selected bucket. Cloud SQL client access is additionally required if Cloud SQL remains the PostgreSQL host. Roles and API enablement must be reviewed in the actual project before creation.

## Production configuration contract

`DEEPTRACE_ENV=production` now fails closed unless all of these are explicit:

- `DEEPTRACE_MODEL_PROVIDER=vertex`, project, location, and model
- `SEARCH_PROVIDER=tavily` and `TAVILY_API_KEY`
- `DEEPTRACE_MEMORY_BACKEND=gcs` and bucket
- `DEEPTRACE_CHECKPOINT_BACKEND=postgres` and PostgreSQL URI

Development/test defaults remain deterministic. The Vertex planner uses structured output and captures provider model version, input/output/total tokens, call count, and latency when returned. No live values are claimed.

## Cost/provisioning gate

Before any create/enable command, the user must approve these potentially billable resources: one continuously billed Cloud Run Instance (official example: 2 vCPU/4 GiB), Vertex model calls, Tavily calls/credits, GCS storage/operations, Secret Manager operations, and a recurring Cloud SQL PostgreSQL instance (likely the largest idle cost). The teardown plan must stop/delete the instance and delete or retain the database/bucket deliberately after grading.

## Required user actions before live verification

1. Install the current Google Cloud CLI and Docker Desktop (or an instructor-approved container builder). The repaired Python 3.11 environment already passes the local suite.
2. Run `gcloud auth login` and `gcloud auth application-default login`.
3. Run `gcloud projects list`, then `gcloud config set project YOUR_PROJECT_ID`; do not invent a project ID.
4. Confirm billing is enabled and provide/approve a supported Cloud Run Instance region.
5. Put `TAVILY_API_KEY` in the local environment for a smoke test and later in Secret Manager; never commit it or paste it into source.
6. Approve the resource/cost plan before APIs, GCS, Cloud SQL, service accounts, secrets, or the Cloud Run Instance are created.

## Remaining instructor question

The official plugin path is the strongest current interpretation. To remove grading risk, ask: **“For the required Cloud Run Instances with Hermes topology, is DeepTrace compliant when it is exposed as an authenticated Hermes dashboard plugin whose backend calls the DeepTrace package in the same Cloud Run Instance, with the Hermes dashboard URL as the grader URL?”** A negative answer would change the packaging boundary, not justify substituting an ordinary Cloud Run service.

## Verification still required

- Live Vertex and Tavily calls, citation sample, and usage artifact.
- Live GCS save/load/list/new-instance/create-only test.
- Live PostgreSQL interrupt, process replacement, resume, cancellation, duplicate, and concurrency tests.
- Hermes plugin/container smoke test and externally reachable authenticated URL.
- Cloud Logging/Monitoring dashboard and alert evidence.
- Deployed safety attacks and final production evaluation.

## Official references

- [Host AI agents on Cloud Run resources](https://docs.cloud.google.com/run/docs/ai-agents)
- [Create and manage Cloud Run instances](https://docs.cloud.google.com/run/docs/instances/create-and-manage-instances)
- [Google codelab: deploy Hermes Agent on Cloud Run instances](https://codelabs.developers.google.com/codelabs/cloud-run/deploy-hermes-cloud-run-instances)
- [Cloud Run resource model](https://docs.cloud.google.com/run/docs/resource-model)
- [Cloud Run instance secrets](https://docs.cloud.google.com/run/docs/configuring/instances/secrets)
- [Cloud Storage volume mounts](https://docs.cloud.google.com/run/docs/configuring/instances/cloud-storage-volume-mounts)
- [Cloud Run monitoring](https://docs.cloud.google.com/run/docs/monitoring)
- [Cloud Run logging](https://docs.cloud.google.com/run/docs/logging)
- [Cloud Run container contract](https://docs.cloud.google.com/run/docs/container-contract)
- [Hermes dashboard extensions](https://hermes-agent.nousresearch.com/docs/user-guide/features/extending-the-dashboard)
- [Hermes dashboard authentication](https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard)
- [Google Gen AI SDK on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview)
