# Rime Ice on Fcitx5

Install Git, Python 3.7+, Fcitx5 with its Rime addon, and librime with Lua support. From the repository root, fetch the pinned Rime Ice files and link the Fcitx5 profile:

```sh
python3 scripts/rime-setup.py
./install.sh --only rime
```

Both commands keep existing files. If the installer skips a conflicting profile, back it up and move it aside before retrying.

With Fcitx5 running, finish any text composition and choose **Deploy** from the Rime menu. In a text field, press **F4** and select **中 · 雾凇拼音** (`rime_ice`). New input sessions start in English; tap either **Shift** key to switch between English and Chinese.
