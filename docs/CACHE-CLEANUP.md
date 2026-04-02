# Shorts-Fission 缓存清理定时任务

## ⏰ 清理策略

| 类型 | 频率 | 说明 |
|------|------|------|
| **即时清理** | 变体生成完成后 | 清理当前视频的 PNG 序列 |
| **定时清理** | 每天凌晨 3:00 | 清理所有超过 24 小时的缓存 |
| **大小清理** | 超过 500 MB 时 | 清理最旧的缓存直到 80% |

---

## 🔧 配置

### 1. Cron 定时任务

添加到系统 crontab：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 3:00 执行）
0 3 * * * cd /root/.openclaw/workspace/projects/shorts-fission && /usr/bin/python3 scripts/cleanup_cache.py --max-age-hours 24 >> /var/log/shorts-fission-cleanup.log 2>&1
```

### 2. 手动执行

```bash
# 干运行（只查看将删除的内容）
cd /root/.openclaw/workspace/projects/shorts-fission
python scripts/cleanup_cache.py --dry-run

# 实际清理（超过 24 小时的缓存）
python scripts/cleanup_cache.py --max-age-hours 24

# 清理超过 12 小时的缓存
python scripts/cleanup_cache.py --max-age-hours 12
```

---

## 📊 清理目标

| 目录 | 清理条件 | 说明 |
|------|---------|------|
| `remotion-caption/out/png_*` | 超过 24 小时 | PNG 序列帧 |
| `remotion-caption/out/*.webm` | 超过 24 小时 | 测试视频 |
| `backend/temp_variants/*` | 超过 24 小时 | 临时变体 |

---

## 🔗 集成点

### 1. Celery 任务集成

已在 `celery_tasks.py` 中集成：
- 变体生成完成后自动清理当前视频的 PNG 序列

### 2. Heartbeat 集成（可选）

可以在心跳检查时执行清理：

```python
# 在 HEARTBEAT.md 的检查清单中添加
- [ ] 检查缓存大小，超过 500MB 则清理
```

---

## 📝 日志

清理日志保存在：
- 系统日志：`/var/log/shorts-fission-cleanup.log`
- 应用日志：通过 loguru 输出

---

*最后更新: 2026-03-29*
