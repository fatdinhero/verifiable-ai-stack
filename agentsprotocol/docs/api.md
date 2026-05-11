# API Reference

## PubSub topics (gossipsub)

| Topic                                | Payload                              |
|--------------------------------------|--------------------------------------|
| `/agentsprotocol/claims/1.0.0`       | New claim (JSON, signed)             |
| `/agentsprotocol/blocks/1.0.0`       | New block incl. zk-proof             |
| `/agentsprotocol/control/1.0.0`      | Control-set updates                  |
| `/agentsprotocol/peers/1.0.0`        | Peer discovery                       |

## RPC endpoints (gRPC / JSON-RPC)

- `SubmitClaim(Claim) -> ClaimId`
- `GetClaim(ClaimId) -> ClaimWithProof`
- `GetBlockHeader(height) -> BlockHeader`
- `GetBlock(height) -> Block`
- `GetValidatorStatus(pubkey) -> ValidatorInfo`
- `GetNetworkParams() -> ProtocolParams`

## Python CLI

```
agentsprotocol info
agentsprotocol validate <claim.json> --fact "..." --tau 0.7
agentsprotocol psi <error_vectors.json>
agentsprotocol wise <units.json>
agentsprotocol bound --q 0.4 --k 64 --psi-min 0.7
```
