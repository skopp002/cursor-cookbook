#!/usr/bin/env bash
# List the EC2 instances currently backing sessions on the capacity provider.
#
# There is no API that lists sessions, so this is the closest substitute. AgentCore launches
# EC2 *managed* instances, which are hidden from the default console and API list views, so
# --include-managed-resources is required. Terminated instances are omitted so a successful
# delete is not confused with a live session. StopRuntimeSession leaves instances running
# until idle timeout or DeleteCapacityProviderSession.
#
# Usage:
#   scripts/list-instances.sh
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

# shellcheck disable=SC2016 # the backticks are JMESPath literals, not shell substitution
aws_cli ec2 describe-instances \
  --include-managed-resources \
  --filters \
    "Name=tag-key,Values=bedrock-agentcore:capacity-provider-id" \
    "Name=instance-state-name,Values=pending,running,shutting-down,stopping,stopped" \
  --query 'Reservations[].Instances[].{
    InstanceId: InstanceId,
    State: State.Name,
    InstanceType: InstanceType,
    LaunchTime: LaunchTime,
    Operator: Operator.Principal,
    AgentCoreTags: Tags[?starts_with(Key, `bedrock-agentcore`)]
  }' \
  --output json

echo >&2
echo "StopRuntimeSession does not terminate these instances. Use make agentcore-delete-session" >&2
echo "with each AGENTCORE_SESSION_ID to deprovision the box and its volume." >&2
