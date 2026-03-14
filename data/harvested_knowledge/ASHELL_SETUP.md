# 📱 a-Shell Setup — iPhone Command Sequence
*Paste these one block at a time. Everything runs in a-Shell.*

---

## BLOCK 1 — First time setup (do this once)

```
pip install requests
```

Wait for it to finish, then:

```
cd ~/Documents
```

Then clone the repo (you need internet):

```
git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center
```

Then move into it:

```
cd meeko-nerve-center
```

---

## BLOCK 2 — Every time you open a-Shell

```
cd ~/Documents/meeko-nerve-center && git pull
```

---

## BLOCK 3 — Check what's in your system

```
ls mycelium/
```

```
cat CLAUDE_CONTEXT.md
```

---

## BLOCK 4 — Run the wiring hub (system status)

```
python mycelium/wiring_hub.py
```

---

## BLOCK 5 — ISS live position RIGHT NOW

```
python -c "import urllib.request,json; d=json.loads(urllib.request.urlopen('http://api.open-notify.org/iss-now.json').read()); p=d['iss_position']; print(f'ISS: lat {p[\"latitude\"]} lon {p[\"longitude\"]}')"
```

---

## BLOCK 6 — Space bridge (full NASA/ISS report)

```
python mycelium/space_bridge.py
```

---

## BLOCK 7 — Legal vault (FOIA, debt, rights)

```
python mycelium/identity_vault.py
```

---

## BLOCK 8 — Network status

```
python mycelium/network_node.py
```

---

## BLOCK 9 — Serve your pages locally on your phone

```
python -m http.server 8080
```

Then open Safari and go to: `http://localhost:8080/spawn.html`

Your ENTIRE system runs on your phone, locally, no internet needed.

Press Ctrl+C to stop the server.

---

## BLOCK 10 — Run ALL mycelium scripts in sequence

```
python mycelium/space_bridge.py && python mycelium/network_node.py && python mycelium/wiring_hub.py
```

---

## BLOCK 11 — Pull any updates and re-run everything

```
git pull && python mycelium/wiring_hub.py
```

---

## BLOCK 12 — Check what Python packages you have

```
pip list
```

---

## BLOCK 13 — Install more packages if needed

```
pip install flask paho-mqtt
```

---

## BLOCK 14 — See your system state JSON

```
cat data/system_state.json
```

---

## BLOCK 15 — See wiring status

```
cat data/wiring_status.json
```

---

## TIPS FOR a-Shell

- **Swipe up** on the keyboard for arrow keys / tab completion
- **Type `ls`** to see what's in the current folder
- **Type `cd ~`** to go home if you get lost
- **Type `pwd`** to see where you are
- **Ctrl+C** stops any running script
- **`history`** shows your last commands
- Use **iCloud Drive** to share files between phone and desktop:
  ```
  cp mycelium/identity_vault.py ~/Library/Mobile\ Documents/com~apple~CloudDocs/
  ```

---

## YOUR LIVE PAGES (open in Safari right now)

These should work once GitHub Pages is enabled:

- https://meekotharaccoon-cell.github.io/meeko-nerve-center/
- https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html
- https://meekotharaccoon-cell.github.io/meeko-nerve-center/proliferator.html
- https://meekotharaccoon-cell.github.io/meeko-nerve-center/revenue.html

---

## IF YOU GET 404s ON THOSE LINKS

Go to your desktop and:
1. Open github.com/meekotharaccoon-cell/meeko-nerve-center
2. Click Settings → Pages
3. Under "Source" select: **Deploy from a branch**
4. Branch: **main** / Folder: **/ (root)**
5. Click Save
6. Wait 2 minutes, then try the links again

---

*This file lives at: github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/ASHELL_SETUP.md*
*On your phone: `cat ASHELL_SETUP.md` to read it anytime*
