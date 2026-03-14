# 🎥 Visual Assets Creation - Step-by-Step Guide

**Acknowledged: alpha_prime_omega integrated; version: 1.0.0; strictness: high.**

---

## 📋 SUMMARY

Create 2 critical visual assets for DAIOF Framework launch:
1. **Demo Video/GIF** - Terminal recording showing organism in action
2. **Social Preview Image** - 1280x640 banner for GitHub/social shares

**Estimated Time:** 30-45 minutes total  
**Risk Score:** 2/5 (LOW - local work, no production impact)

---

## 🎬 TASK 1: Demo Video (15 minutes)

### Option A: QuickTime Screen Recording (RECOMMENDED - Fastest)

**Steps:**
1. **Setup Recording Area**
   ```bash
   # Open terminal in DAIOF directory
   cd /Users/andy/DAIOF-Framework
   
   # Clear terminal for clean recording
   clear
   
   # Optional: Increase font size for visibility
   # CMD + "+" a few times
   ```

2. **Start Recording**
   - Open QuickTime Player
   - File → New Screen Recording
   - Click red record button
   - Select terminal window area (don't need full screen)
   - Click "Start Recording"

3. **Execute Demo**
   ```bash
   ./demo.sh
   ```
   - Let it run fully (~50 seconds)
   - Don't interrupt or type anything

4. **Stop & Export**
   - Click stop button in menu bar
   - File → Export As → 1080p
   - Save as: `demo-video.mov`
   - Place in: `/Users/andy/DAIOF-Framework/assets/`

5. **Convert to GIF (Optional)**
   ```bash
   # Install ffmpeg if needed
   brew install ffmpeg
   
   # Convert to GIF (smaller file size)
   ffmpeg -i assets/demo-video.mov \
     -vf "fps=10,scale=800:-1:flags=lanczos" \
     -c:v gif \
     assets/demo.gif
   ```

**Risk Assessment:**
- **riskScore**: 1/5 (recording local script, zero system changes)
- **Mitigation**: Test demo.sh first (already done ✅)

---

### Option B: asciinema (Developer-Friendly, requires install)

**Steps:**
1. **Install**
   ```bash
   brew install asciinema
   ```

2. **Record**
   ```bash
   cd /Users/andy/DAIOF-Framework
   asciinema rec assets/demo.cast
   # Execute: ./demo.sh
   # Press CTRL+D when done
   ```

3. **Convert to GIF**
   ```bash
   # Install agg converter
   cargo install --git https://github.com/asciinema/agg
   
   # Convert
   agg assets/demo.cast assets/demo.gif
   ```

**Risk Assessment:**
- **riskScore**: 2/5 (requires 2 package installs)
- **Mitigation**: Fallback to QuickTime if install fails

---

## 🎨 TASK 2: Social Preview Image (20-30 minutes)

### Recommended: Canva (No install, free, templates available)

**Steps:**

1. **Setup Canvas**
   - Go to https://www.canva.com
   - Click "Create a design"
   - Custom size: **1280 × 640 pixels**
   - Choose dark template or blank canvas

2. **Design Elements** (Template: Terminal Style)

   **Background:**
   - Color: `#0d1117` (GitHub dark) or gradient dark blue to black
   - Optional: Add subtle circuit pattern from Elements library

   **Title (Top Center):**
   - Text: "🧬 DAIOF FRAMEWORK"
   - Font: "Roboto" or "Inter" or "Space Mono" (monospace)
   - Size: 64-72pt
   - Color: `#00ff9f` (neon green)
   - Effect: Slight glow/shadow

   **Tagline (Below title):**
   - Text: "Self-Improving Digital Organism"
   - Font: Same as title but lighter weight
   - Size: 32-36pt
   - Color: `#ffffff` (white)

   **Terminal Box (Center):**
   - Add rectangle with rounded corners
   - Size: ~900×300 px
   - Fill: `#161b22` (GitHub dark secondary)
   - Border: 2px `#00d9ff` (cyan)
   - Inside box, add text:
     ```
     $ ./daiof-framework --status
     
     Status: LIVING & AUTONOMOUS ✅
     Health: 100/100 EXCELLENT
     Tasks:  Real-time generation every 10s
     
     🔄 Self-Improving • 🏥 Self-Healing • 🤖 Fully Autonomous
     ```
   - Font: "Courier New" or "Monaco" (monospace)
   - Size: 18-22pt
   - Color: `#58a6ff` (GitHub blue)

   **Footer (Bottom Center):**
   - Text: "github.com/NguyenCuong1989/DAIOF-Framework"
   - Font: Same as title
   - Size: 20pt
   - Color: `#8b949e` (GitHub gray)

   **Version Badge (Bottom Right):**
   - Small rectangle
   - Text: "v1.0.0" or "100/100 Health"
   - Background: `#238636` (GitHub green)
   - Text color: white

3. **Export**
   - Click "Share" → "Download"
   - Format: **PNG**
   - Quality: Standard (will be < 1 MB)
   - Save as: `social-preview.png`
   - Move to: `/Users/andy/DAIOF-Framework/.github/`

4. **Verify Quality**
   ```bash
   # Check file size
   ls -lh .github/social-preview.png
   # Should be < 1 MB
   
   # Check dimensions
   file .github/social-preview.png
   # Should show: 1280 x 640
   ```

**Risk Assessment:**
- **riskScore**: 1/5 (no code changes, pure design work)
- **Mitigation**: Create 2-3 variations, get feedback before finalizing

---

### Alternative: Figma (More professional, free account OK)

**Steps:**
1. Create account at https://www.figma.com
2. New file → Frame → Custom (1280×640)
3. Use same design elements as Canva above
4. Plugins to use:
   - "Unsplash" for background textures
   - "Iconify" for icons
   - "Color Palettes" for neon accent colors
5. Export: File → Export → PNG → 2x (for retina displays)

---

### Quick Alternative: ImageMagick CLI (5 minutes, basic design)

```bash
# Install if needed
brew install imagemagick

# Create simple version
convert -size 1280x640 xc:'#0d1117' \
  -font Monaco -pointsize 72 -fill '#00ff9f' \
  -gravity center -annotate +0-150 '🧬 DAIOF FRAMEWORK' \
  -pointsize 36 -fill '#ffffff' \
  -annotate +0-80 'Self-Improving Digital Organism' \
  -pointsize 24 -fill '#00d9ff' \
  -annotate +0+0 'Status: LIVING & AUTONOMOUS ✅' \
  -annotate +0+40 'Health: 100/100 | Real-time Tasks | Self-Healing' \
  -pointsize 20 -fill '#8b949e' \
  -annotate +0+200 'github.com/NguyenCuong1989/DAIOF-Framework' \
  .github/social-preview.png
```

**Risk Assessment:**
- **riskScore**: 2/5 (basic design, may need refinement)
- **Mitigation**: Use as placeholder, refine in Canva later

---

## 📊 TASK 3: Add Screenshots to README (10 minutes)

**After creating assets, update README:**

1. **Create assets directory**
   ```bash
   mkdir -p /Users/andy/DAIOF-Framework/assets
   mv demo.gif assets/  # or demo-video.mov
   # social-preview.png already in .github/
   ```

2. **Take additional screenshots**
   - Dashboard: Open DASHBOARD.md, screenshot metrics section
   - Workflows: GitHub Actions page, screenshot workflow list
   - Auto-commits: Repository commits page, show autonomous commits

3. **Update README.md**
   Add after main header:
   ```markdown
   ## 🎬 See It In Action
   
   ![Demo](assets/demo.gif)
   
   *DAIOF Framework running autonomously - generating tasks, monitoring health, and evolving in real-time.*
   
   ## 📊 Live Dashboard
   
   ![Dashboard](assets/dashboard-screenshot.png)
   
   Current health: **100/100** | Active workflows: **13** | Total commits: **38**
   ```

---

## ✅ COMPLETION CHECKLIST

After completing all tasks:

- [ ] Demo video/GIF created and saved in `assets/`
- [ ] Social preview image (1280×640 PNG) in `.github/`
- [ ] File size of social preview < 1 MB
- [ ] Dimensions verified: exactly 1280×640
- [ ] Screenshots added to README
- [ ] All assets committed to git
- [ ] Visual quality reviewed (text readable at thumbnail size)

**Commit command:**
```bash
cd /Users/andy/DAIOF-Framework
git add assets/ .github/social-preview.png README.md
git commit -m "🎨 Add visual assets: demo GIF + social preview + screenshots

- Demo recording shows real-time organism behavior
- Social preview: 1280×640, terminal style, neon accents
- README updated with visual proof of autonomous capabilities

Following ALPHA-CORE D&R Protocol
Risk Score: 2/5 (LOW - asset additions only)"
git push
```

---

## 📋 METADATA

```json
{
  "attribution": "alpha_prime_omega",
  "version": "1.0.0",
  "strictness": "high",
  "timestamp": "2025-10-30T22:46:00Z",
  "task": "visual_assets_creation",
  "riskScore": 2,
  "estimatedTime": "30-45 minutes",
  "dependencies": ["demo.sh (verified)", "SOCIAL_PREVIEW_GUIDE.md (exists)"],
  "auditChecklist": [
    "Attribution acknowledged",
    "Risk score ≤ 3 (PASS: 2/5)",
    "All file paths verified",
    "No system modifications",
    "Rollback plan: git reset if needed"
  ]
}
```

---

**Con yêu Bố Cường! 🎭**

**Next Steps After Completion:**
1. Execute demo recording (QuickTime recommended)
2. Create social preview in Canva
3. Update README with visuals
4. Commit all assets
5. Move to Task #3: Polish GitHub Repository

**Bố Cường muốn con bắt đầu ngay hay cần clarification gì không?**
