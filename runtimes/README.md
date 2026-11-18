# Runtimes

Runtime setup is separate from native package installation. The software manifest installs tools such as `fnm` and `rustup`; scripts in this directory use those tools to select language versions and components.

```sh
./runtimes/toolchains.sh node
./runtimes/toolchains.sh rust
./runtimes/toolchains.sh
```
