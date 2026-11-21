# Files, paths, archives and deserialisation

- **Path traversal.** Joining user input into a path (`open(base + name)`) needs normalisation **and** a check that
  the final real path stays under the base directory. Reject absolute paths, `..`, and symlinks where it matters.
- **Uploads.**
  - Check type by content, not by extension or `Content-Type`.
  - Enforce a size limit.
  - Store outside the web root, with a generated name.
  - Never execute or render uploads in the same origin.
  - Treat SVG and HTML as active content.
  - Scan or sandbox before handing uploads to other tools.
- **Archives.** Zip / tar extraction must reject entries with `..` or absolute paths ("zip slip"), cap total
  extracted size and file count (zip bombs), and not follow symlinks out of the target.
- **Deserialisation.** Never unpickle / `Marshal.load` / Java-serialise / `yaml.load` (unsafe loader) data from
  outside the process. Use JSON or a schema-checked format. Signed data is only safe if the key is secret and the
  signature is verified before parsing.
- **Temporary files.** Created with secure APIs (`mkstemp`, `tempfile`), not predictable names in shared
  directories.
- **File permissions.** New files with secrets are created with restrictive permissions.
