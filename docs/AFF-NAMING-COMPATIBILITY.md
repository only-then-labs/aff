# AFF public name and OAFF v0.1 compatibility

Status: accepted naming decision; no wire-format revision. AFF means **Agent
Findings Format**. A Finding is one independently assessable unit of durable
agent learning. OAFF is the published identifier of the current v0.1 wire
contract, originally called Open Agent Findings Format.

## Compatibility decision

| Surface | Current behavior | Compatibility rule |
| --- | --- | --- |
| Public name | AFF — Agent Findings Format | Use AFF in product-facing prose. Do not reinterpret existing OAFF files. |
| Public repository | `only-then-labs/aff` | Renamed from `only-then-labs/oaff` on 30 Sep 2026. Use the new URL for installation and new links; existing GitHub links redirect. |
| JSON key and version | `oaff_version: "0.1.0"` | Required unchanged for v0.1. Readers reject unknown versions under the current spec. |
| Filename convention | `.aff` for new packages | Existing `.oaff.json` files remain valid and readable. A filename alone never determines validity. |
| Python distribution/import | `oaff` | Keep the published distribution and `import oaff`; an `aff` distribution name is not reserved or promised. |
| CLI | `aff` and `oaff` | Both call the same offline verifier and accept the same arguments; keep `oaff` for scripts. |
| Media type | `application/json` | No custom or registered media type is claimed for v0.1. Consumers identify the contract from `oaff_version` and validate it. |
| Package digest | SHA-256 over RFC 8785 JCS without top-level `integrity` | Exact existing bytes and all golden vectors remain valid. A label change outside the package does not alter the digest. |

The extension change is an ergonomic label, not a second serialization or a
new protocol. `aff` and `oaff` must produce the same machine-readable report
for the same input regardless of whether it is named `.aff` or `.oaff.json`.
The new golden fixtures use `.aff`; previously distributed fixture bytes and
packages remain valid under their old names. The verifier inspects content,
not extension. Public examples use `.aff`; existing commands remain valid.

## Future wire naming

A future wire rename requires its own versioned proposal and fixtures. It must
specify the new version identifier, filename and media-type policy, dual-read
period, deterministic conversion, digest and identity consequences, downgrade
behavior, and how a reader reports unsupported versions. No v0.1 reader may
silently treat `aff_version` as `oaff_version`, rewrite package bytes, or infer
authority from a new label. Existing v0.1 packages remain readable by v0.1
implementations.

The repository rename changed the discovery and installation URL, not package
bytes or the v0.1 wire contract. The v0.1 schema's historical `$id` still uses
the old repository URL, which GitHub redirects; changing that schema identity
would be a separate compatibility review. The Python package name and wire
identifier remain `oaff` until a separately versioned migration is justified.
