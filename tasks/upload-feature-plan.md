# 视频上传功能开发计划

## 需求分析

1. **批量视频上传** - 用户可以上传多个视频文件
2. **分辨率检测** - 上传后自动获取并展示视频分辨率
3. **延迟处理流程** - 下载/上传后不立即生成变体，需要在视频详情中选择数量后才处理

## 技术方案

### Phase 1: 后端 API

#### 1.1 添加上传接口
- 文件: `backend/app/api/routes/videos.py`
- 新增 `POST /upload` 端点
- 使用 `UploadFile` 处理多文件上传
- 使用 ffprobe 获取视频分辨率

#### 1.2 修改数据模型
- 添加 `source_type` 字段: `download` | `upload`
- 保持 `target_variant_count` 默认为 0（未选择时不处理）

#### 1.3 修改处理流程
- 下载/上传完成后状态改为 `downloaded`
- 只有用户手动设置 `target_variant_count > 0` 才触发变体生成

### Phase 2: 前端界面

#### 2.1 添加上传组件
- 文件: `frontend/src/components/VideoUploader.tsx`
- 支持拖拽上传
- 支持批量选择
- 显示上传进度

#### 2.2 修改视频卡片
- 文件: `frontend/src/components/VideoCard.tsx`
- 显示视频来源（下载/上传）
- 点击卡片进入详情页选择变体数量

#### 2.3 修改视频详情弹窗
- 文件: `frontend/src/components/VideoDetailModal.tsx`
- 添加变体数量选择器
- 添加"开始处理"按钮
- 仅在 `target_variant_count = 0` 时显示选择界面

## 实施步骤

- [ ] Phase 1.1: 后端上传 API
- [ ] Phase 1.2: 数据库迁移
- [ ] Phase 1.3: 修改处理流程
- [ ] Phase 2.1: 前端上传组件
- [ ] Phase 2.2: 修改视频卡片
- [ ] Phase 2.3: 修改详情弹窗
- [ ] Phase 3: 集成测试

## 预计时间

- 后端: 30 分钟
- 前端: 45 分钟
- 测试: 15 分钟
- 总计: 1.5 小时
