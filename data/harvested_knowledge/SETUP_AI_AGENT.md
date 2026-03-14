# 🚀 Setup GitHub CLI cho AI Agent

## Bước 1: Cài đặt GitHub CLI (nếu chưa có)

```bash
# macOS
brew install gh

# Hoặc download từ: https://cli.github.com/
```

## Bước 2: Authenticate với GitHub

```bash
gh auth login
```

Chọn:
- ✅ GitHub.com
- ✅ HTTPS
- ✅ Login with a web browser

Copy code và paste vào browser để authenticate.

## Bước 3: Verify Setup

```bash
# Kiểm tra authentication
gh auth status

# List workflows
gh workflow list

# View repo info
gh repo view
```

## Bước 4: Enable AI Agent Workflow

### Option A: Qua GitHub Web UI (Recommended)

1. Vào https://github.com/NguyenCuong1989/DAIOF-Framework/actions
2. Click vào workflow "AI Agent Autonomous Operations"
3. Click "Enable workflow" (nếu bị disable)
4. Click "Run workflow" → Chọn task type → "Run workflow"

### Option B: Qua CLI (Sau khi setup gh)

```bash
cd ~/DAIOF-Framework

# Manual trigger với task type cụ thể
gh workflow run ai-agent-autonomous.yml -f task_type=metrics_report

# Xem kết quả
gh run list --workflow=ai-agent-autonomous.yml

# Xem logs của run gần nhất
gh run view --log
```

## Bước 5: Verify Permissions

Kiểm tra xem GITHUB_TOKEN có đủ permissions:

```bash
gh api /repos/NguyenCuong1989/DAIOF-Framework
```

Nếu cần thêm permissions:
1. Settings → Actions → General
2. Workflow permissions → "Read and write permissions" ✅
3. "Allow GitHub Actions to create and approve pull requests" ✅

## 🎯 Test AI Agent Lần Đầu

### Test 1: Metrics Report (An toàn nhất)

```bash
# Chỉ đọc và tạo report, không sửa gì
gh workflow run ai-agent-autonomous.yml -f task_type=metrics_report
```

Sau ~2 phút, check:
- Actions tab: Xem run có thành công không
- `metrics/` folder: Xem có file report mới không

### Test 2: Auto Maintain

```bash
# Tạo metrics report + auto-label issues (nếu có)
gh workflow run ai-agent-autonomous.yml -f task_type=auto_maintain
```

### Test 3: Community Engagement

```bash
# Welcome contributors, thank merges
gh workflow run ai-agent-autonomous.yml -f task_type=community_engagement
```

## 📊 Monitor AI Agent Activity

### Xem Logs Real-time

```bash
# List runs
gh run list --workflow=ai-agent-autonomous.yml

# Xem log của run mới nhất
gh run view --log

# Hoặc specify run ID
gh run view 12345678 --log
```

### Check Outputs

```bash
# Xem files AI Agent tạo ra
ls -la metrics/

# Xem latest report
cat metrics/report_*.md

# Xem logs
cat metrics/agent_log_*.txt
```

## 🛑 Disable/Pause AI Agent

### Temporary Pause

```bash
# Disable workflow (có thể enable lại)
gh workflow disable ai-agent-autonomous.yml

# Enable lại
gh workflow enable ai-agent-autonomous.yml
```

### Permanent Removal

```bash
# Xóa workflow file
rm .github/workflows/ai-agent-autonomous.yml
git commit -am "Disable AI Agent"
git push
```

## 🔧 Troubleshooting

### Issue: Workflow không chạy

**Solution**: Check Actions settings
```bash
# Repository → Settings → Actions → General
# Ensure: "Allow all actions and reusable workflows" is selected
```

### Issue: Permission denied

**Solution**: Update workflow permissions
```bash
# Repository → Settings → Actions → General → Workflow permissions
# Select: "Read and write permissions"
```

### Issue: PyGithub import error trong workflow

**Solution**: Workflow tự động install dependencies
```yaml
# Đã có trong workflow:
- name: 📦 Install Dependencies
  run: |
    pip install PyGithub requests pyyaml
```

### Issue: Git push fails trong workflow

**Solution**: Check git config
```yaml
# Đã có trong workflow:
git config --local user.email "github-actions[bot]@users.noreply.github.com"
git config --local user.name "AI Agent 🤖"
```

## 📅 Schedule Configuration

Workflow hiện tại chạy mỗi 6 giờ:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Mỗi 6 giờ
```

Để thay đổi:

```yaml
# Mỗi 12 giờ
- cron: '0 */12 * * *'

# Mỗi ngày lúc 9AM UTC
- cron: '0 9 * * *'

# Mỗi tuần Monday 9AM UTC
- cron: '0 9 * * 1'
```

## 🎯 Next Steps

1. ✅ Setup gh CLI authentication
2. ✅ Enable workflow in Actions tab
3. ✅ Run first test (metrics_report)
4. ✅ Monitor results
5. ✅ Let it run on schedule

## 📞 Support

Nếu có vấn đề:
1. Check Actions tab logs
2. Check `metrics/agent_log_*.txt`
3. Review `.github/AI_AGENT_AUTONOMOUS.md`
4. Create issue với tag `ai-agent`

---

**Tạo bởi**: DAIOF AI Agent 🤖  
**Mục đích**: Autonomous operations cho GitHub repository  
**Tuân thủ**: 4 Pillars - An toàn, Đường dài, Tin vào số liệu, Hạn chế rủi ro con người
