# 部署 Marketplace 到 Claude

## 部署步驟

### 1. 確保檔案結構正確

```
macro-skills/
├── .claude-plugin/
│   ├── manifest.json       # Plugin 清單
│   ├── marketplace.json    # Marketplace 設定
│   └── index.json          # 技能索引 (自動產生)
├── skills/
│   └── */SKILL.md          # 技能定義
└── commands/
    └── *.md                # Slash commands
```

### 2. 建置技能索引

```bash
bun run build:marketplace
```

### 3. 推送到 GitHub

```bash
git add .
git commit -m "deploy: update marketplace"
git push origin master
```

### 4. 完成！

使用者現在可以執行以下指令安裝：

```bash
/plugin marketplace add fatfingererr/macro-skills
```

---

## 更新 Marketplace

### 新增技能

```bash
# 1. 建立技能目錄
mkdir skills/new-skill

# 2. 建立 SKILL.md
# 編輯 skills/new-skill/SKILL.md

# 3. 重新建置
bun run build:marketplace

# 4. 推送
git add .
git commit -m "feat: add new-skill"
git push
```

### 更新現有技能

```bash
# 1. 編輯技能
# 修改 skills/skill-name/SKILL.md

# 2. 重新建置
bun run build:marketplace

# 3. 推送
git add .
git commit -m "update: skill-name"
git push
```

### 刪除技能

```bash
# 1. 刪除技能目錄
rm -rf skills/skill-to-delete

# 2. 重新建置
bun run build:marketplace

# 3. 推送
git add .
git commit -m "remove: skill-to-delete"
git push
```

---

## 使用者端操作

| 操作     | 指令                                                |
|----------|-----------------------------------------------------|
| 安裝     | `/plugin marketplace add fatfingererr/macro-skills` |
| 更新     | `/plugin marketplace update macro-skills`           |
| 列出技能 | `/plugin marketplace list macro-skills`             |
| 啟動技能 | `/plugin enable {skill}@macro-skills`               |
| 移除     | `/plugin marketplace remove macro-skills`           |
