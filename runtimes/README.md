# Node.js and Rust

After [bootstrap](../bootstrap.sh) installs `fnm` and `rustup`, run this from the repository root to install Node.js LTS and stable Rust:

```sh
./runtimes/toolchains.sh
```

Pass `node` or `rust` to install just one toolchain, or add `--dry-run` to preview. In a new dotfiles shell, use `fnm list` to see installed Node.js versions or `rustc +stable --version` to check Rust.
