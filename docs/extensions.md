# Extensions

Silinosic-X uses plugins and filters as scope-aware intelligence layers.

## Plugins

Plugins enrich findings, run secondary intelligence passes, or attach specialized data to the current case. Examples include public-media reconnaissance, post-text analysis, stego-style probes, and OCR extraction.

Media-focused extensions are ordered when chaining is enabled: **Media Recon
Engine → EXIF Metadata Extractor → Geo-location Intelligence**. The collector
can archive each downloaded public image under `output/<target>/images/` with
the raw asset, `manifest.json`, and `exif.json`; set
`media_recon.save_images_to_disk: false` in `config/silinosic_x_config.yml` to
disable that local archive. Exact GPS and wallet-address values stay redacted
unless the operator explicitly enables sensitive-information output.

The Hash Identifier and Wallet Address Intelligence plugins are identification
only: they do not crack hashes, access wallets, query balances, or inspect
transactions.

The bundled plugins under `plugins/` are trusted project code. Plugin inventory
now reads each literal `PLUGIN_SPEC` without importing every plugin, so optional
dependencies in an unused extension do not affect startup. Third-party plugins
should be treated as untrusted: `SecurityManager.sandbox_plugin()` describes a
requested policy but does not provide process isolation. Run untrusted code in
an OS or container sandbox with its network, filesystem, and subprocess access
explicitly restricted.

## Filters

Filters suppress noise, rank findings, classify exposure, or reshape signals into a more triage-friendly form.

## Scope control

Extensions are not applied blindly. Silinosic-X checks compatibility with the active scope, such as:

- `profile`
- `surface`
- `fusion`
- `ocr`

## Operator guidance

- Keep the extension set minimal for baseline scans.
- Add media/OCR plugins when the target case is content-heavy.
- Prefer Reporter output to validate whether a plugin or filter is adding useful signal.
