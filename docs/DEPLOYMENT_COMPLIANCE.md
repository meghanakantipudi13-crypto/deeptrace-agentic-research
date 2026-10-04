# Deployment Compliance Check

## Current status

**BLOCKED pending instructor clarification.** No deployment topology is locked, and no deployment compliance is claimed.

The assignment says the preferred path must use “Google Cloud Run Instances with OpenClaw or Hermes Agent and monitoring.” This appears to refer to the distinct long-lived Cloud Run Instances product and not an ordinary Cloud Run service. Google's official Hermes codelab uses `gcloud beta run instances deploy`, a Hermes Agent container, a mounted GCS bucket, Secret Manager, a service account, and Vertex AI. That confirms a plausible compliant path but does not specify how a student-built web application must integrate with Hermes.

## Proposed candidate topology

- Cloud Run Instance running a pinned Hermes Agent image plus a reviewed DeepTrace integration.
- DeepTrace domain/workflow package installed as a Hermes skill/plugin or launched by an instructor-approved supervisor pattern.
- GCS bucket mounted or accessed through the client API for durable artifacts and long-term memory.
- Firestore for transactional workflow/approval metadata, subject to instructor approval.
- Secret Manager for provider credentials.
- Vertex AI for the default model.
- Cloud Logging and Cloud Monitoring dashboard/alert for monitoring evidence.
- Public HTTPS URL with grader access and application authentication appropriate to course instructions.

## Exact questions to send the instructor

1. Does compliance require DeepTrace to be implemented as a Hermes Agent/OpenClaw skill or plugin, or is running the DeepTrace service alongside a configured Hermes/OpenClaw process in the same Cloud Run Instance acceptable?
2. Must the grader-facing URL be the Hermes/OpenClaw dashboard, or may it be DeepTrace's own FastAPI UI exposed from the same Cloud Run Instance?
3. Is Firestore permitted for transactional session and approval state when the required GCS bucket remains the durable store for long-term memory artifacts, evidence, reports, and traces?
4. Is the beta `gcloud run instances` product specifically required, and are there course-provided region/project/quota constraints?
5. What monitoring evidence is expected: Cloud Logging alone, or a Cloud Monitoring dashboard and alert policy?

## What will not be assumed equivalent

- An ordinary Cloud Run service without Hermes/OpenClaw.
- Vercel, Render, Railway, or another convenient host.
- Local SQLite or container filesystem persistence.
- Merely documenting Hermes/OpenClaw without running it.
- Multiple LangGraph nodes described as multi-agent A2A.

## Evidence required before marking verified

- Instructor response or unambiguous course clarification.
- Infrastructure/deployment configuration committed without secrets.
- Deployment command/output tied to a commit and revision.
- Restart persistence test using GCS-backed state.
- Monitoring dashboard/log evidence and alert test.
- External smoke test of the live grader URL.
- Secret scan and least-privilege service-account review.

## Authoritative references reviewed on 2026-10-04

- Google codelab: <https://codelabs.developers.google.com/codelabs/cloud-run/deploy-hermes-cloud-run-instances>
- Cloud Run container filesystem contract: <https://docs.cloud.google.com/run/docs/container-contract>
- Cloud Run ephemeral disk behavior: <https://docs.cloud.google.com/run/docs/configuring/services/ephemeral-disk>
- Hermes Agent documentation: <https://hermes-agent.nousresearch.com/docs/>
