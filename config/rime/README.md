# Rime Ice on Fcitx5

The Linux profile uses the macOS Rime Ice revision with Linux-specific mode
defaults and labels. It requires Git, Python 3, Fcitx5 with its Rime addon, librime with the Lua
plugin, and `rime_deployer`. From the repository root:

```sh
python3 scripts/rime-setup.py
./install.sh --only rime
```

The helper fetches commit `3aea6d3694fb3d94ec663641f021f788822897ad` of
`iDvel/rime-ice`. It adds the schemas, dictionaries, Lua, OpenCC, symbols and
baseline defaults under `${XDG_DATA_HOME:-$HOME/.local/share}/fcitx5/rime`.
Re-running the helper fills missing files; existing files (including custom
phrases and edited schemas) are never compared or replaced. An existing
installation may therefore differ from the pin. No optional grammar model is
needed by this revision's default configuration.

To deploy while Fcitx5 is running, finish the current composition, then choose
**Deploy** from the Rime menu. Select **Rime Ice** (`rime_ice`, first in the
baseline schema list) from Rime's F4 menu. For an offline deployment, exit
Fcitx5 first, then run:

```sh
(
  cd "${XDG_DATA_HOME:-$HOME/.local/share}/fcitx5/rime" || exit 1
  rime_deployer --build "$PWD" /usr/share/rime-data "$PWD/build" &&
    rime_deployer --set-active-schema rime_ice
)
```

Start Fcitx5 again after an offline deployment. Rime is the only Fcitx5 input
method; `us` is the underlying key layout. New Rime input contexts start
in English. Either Shift key switches between English and Chinese; pressing Shift while composing
commits the raw code. Classic UI uses Noto Sans CJK SC and the system light/dark
preference; inline preedit also depends on the application.

Mode labels are `A` (English) and `中` (Chinese). Fcitx5-rime 5.1.16 uses the
schema's ASCII switch label only with `LatinModeNameFromSchema=True`. Its Chinese
label is the first character of `schema/name`, so the displayed schema name is
prefixed with `中`; `schema/abbrev` is not used by this addon version.

The punctuation patch follows the macOS settings. In particular, the punctuation
patch replaces the schema's punctuation table: its compiled configuration has
six ASCII full-shape mappings and no explicit half-shape or symbol table.
