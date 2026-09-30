# AFF public name and OAFF v0.1 compatibility

Status: accepted naming decision; no wire-format revision. AFF means **Agent
Findings Format**. A Finding is one independently assessable unit of durable
agent learning. OAFF is the published identifier of the current v0.1 wire
contract, originally called Open Agent Findings Format.

## Compatibility decision

| Surface | Current behavior | Compatibility rule |
| --- | --- | --- |
| Public name | AFF — Agent Findings Format | Use AFF in product-facing prose. Do not reinterpret existing OAFF files. |
| JSON key and version | `oaff_version: "0.1.0"` | Required unchanged for v0.1. Readers reject unknown versions under the current spec. |
| Filename convention | `.oaff.json` | Keep for v0.1 interchange and all golden fixtures. A filename alone never determines validity. |
| Python distribution/import | `oaff` | Keep the published distribution and `import oaff`; an `aff` distribution name is not reserved or promised. |
| CLI | `aff` and `oaff` | Both call the same offline verifier and accept the same arguments; keep `oaff` for scripts. |
| Media type | `application/json` | No custom or registered media type is claimed for v0.1. Consumers identify the contract from `oaff_version` and validate it. |
| Package digest | SHA-256 over RFC 8785 JCS without top-level `integrity` | Exact existing bytes and all golden vectors remain valid. A label change outside the package does not alter the digest. |

The CLI alias is an ergonomic addition, not a second serialization or a new
protocol. `aff` and `oaff` must produce the same machine-readable report for
the same input. Public examples may use `aff`; existing commands remain valid.

## Future wire naming

A future wire rename requires its own versioned proposal and fixtures. It must
specify the new version identifier, filename and media-type policy, dual-read
period, deterministic conversion, digest and identity consequences, downgrade
behavior, and how a reader reports unsupported versions. No v0.1 reader may
silently treat `aff_version` as `oaff_version`, rewrite package bytes, or infer
authority from a new label. Existing v0.1 packages remain readable by v0.1
implementations.

The repository URL is also stable for now; renaming it would create redirects
and integration work without changing the format. The AFF name should be tested
through real producers and receivers before any repository or package migration.
