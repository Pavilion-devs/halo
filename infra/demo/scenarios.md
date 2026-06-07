# Halo Demo Scenarios

## Scenario 1: Bad Deploy And Model Fallback

- Trigger a service outage incident after a recent deploy.
- Route the first model call through `halo-vm-chaos-demo`.
- Show fallback to the Bedrock-backed target.
- Confirm the UI shows degraded mode, checkpoint index, and trace metadata.

## Scenario 2: Tool Timeout And Degraded Mode

- Arm `POST /demo/delay-next`.
- Run evidence gathering.
- Show Halo switching to shorter, read-only degraded behavior.

## Scenario 3: Unsafe Action Approval

- Reach the approval stage.
- Show the action waiting for explicit approval.
- Reject approval to force handoff, or approve to continue safe coordination.
