# Submitting hyprcam to the AUR

**Status: not submitted.** These files are ready for the repository owner to
publish from their own AUR account. Nothing here has been pushed to the AUR and
no credentials are stored in this repository.

## Prerequisites

1. An [AUR account](https://aur.archlinux.org/account/register.php) with a
   verified email address.
2. An SSH public key added to that account under
   [Account → SSH Public Keys](https://aur.archlinux.org/account/). If you do
   not have one:
   ```sh
   ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_aur -C "aur"
   # add ~/.ssh/id_ed25519_aur.pub in the AUR account settings
   ```
3. `git` and `base-devel` locally:
   ```sh
   sudo pacman -S --needed git base-devel
   ```

## Check the package locally first

From a checkout of this repository:

```sh
cd packaging/aur
bash -n PKGBUILD
makepkg --verifysource
makepkg -si
hyprcam --list-devices
```

`makepkg --verifysource` checks the real sha256 of the `v0.1.0` source tarball.
The `sha256sums` entry is a real checksum, not `SKIP`. If the `v0.1.0` tag is
ever recreated, download the tarball again and update the checksum plus
`.SRCINFO`.

## Submit

The AUR package name is expected to be `hyprcam`. If it is already taken,
choose another name and update `pkgname` in `PKGBUILD` before submitting.

```sh
git clone ssh://aur@aur.archlinux.org/hyprcam.git
cd hyprcam
cp /path/to/hyprcam/packaging/aur/PKGBUILD .
cp /path/to/hyprcam/packaging/aur/.SRCINFO .
# Optional but recommended after any PKGBUILD edit:
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m 'feat: add hyprcam 0.1.0'
git push
```

After the push, the package appears at <https://aur.archlinux.org/packages/hyprcam>.
Users can then install it with an AUR helper, for example `yay -S hyprcam`.

## Updating later

1. Bump `pkgver` (or `pkgrel` for packaging-only changes) in `PKGBUILD`.
2. Update `source`/`sha256sums` if the upstream tag changed.
3. Regenerate `.SRCINFO` with `makepkg --printsrcinfo > .SRCINFO`.
4. Commit and push to the AUR remote again.
