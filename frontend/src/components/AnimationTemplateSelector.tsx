// frontend/src/components/AnimationTemplateSelector.tsx
/**
 * 词级动画模板选择器
 * 支持 PyCaps 12 个预设模板 + 模板预览图
 * 简化为 3 个位置，距边缘 300px
 */

import React, { useState } from 'react';
// API_BASE_URL 保留用于未来扩展

interface AnimationTemplate {
  id: string;
  name: string;
  description: string;
  preview?: string;
}

interface AnimationPosition {
  id: string;
  name: string;
  description: string;
}

interface AnimationTemplateSelectorProps {
  templateId: string | null;  // null = 随机
  position: string;
  onTemplateChange: (templateId: string | null) => void;
  onPositionChange: (position: string) => void;
}

// PyCaps 12 个预设模板配置
const PYCAPS_TEMPLATES: AnimationTemplate[] = [
  { id: 'minimalist', name: 'Minimalist', description: '极简风格 - 白色无背景', preview: '/templates/minimalist.png' },
  { id: 'default', name: 'Default', description: '默认风格 - 经典字幕效果', preview: '/templates/default.png' },
  { id: 'classic', name: 'Classic', description: '经典风格 - 衬线字体', preview: '/templates/classic.png' },
  { id: 'neo_minimal', name: 'Neo Minimal', description: '新极简风格 - 现代简约', preview: '/templates/neo_minimal.png' },
  { id: 'hype', name: 'Hype', description: '动感风格 - 橙色高亮', preview: '/templates/hype.png' },
  { id: 'explosive', name: 'Explosive', description: '爆炸风格 - 黄色爆炸', preview: '/templates/explosive.png' },
  { id: 'fast', name: 'Fast', description: '快速风格 - Impact字体', preview: '/templates/fast.png' },
  { id: 'vibrant', name: 'Vibrant', description: '活力风格 - 渐变背景', preview: '/templates/vibrant.png' },
  { id: 'word_focus', name: 'Word Focus', description: '词焦点 - 当前词高亮', preview: '/templates/word_focus.png' },
  { id: 'line_focus', name: 'Line Focus', description: '行焦点 - 整行高亮', preview: '/templates/line_focus.png' },
  { id: 'retro_gaming', name: 'Retro Gaming', description: '复古游戏 - 像素风', preview: '/templates/retro_gaming.png' },
  { id: 'model', name: 'Model', description: '模特风格 - 高端斜体', preview: '/templates/model.png' },
];

// 简化为 3 个位置，距边缘 300px
const POSITIONS: AnimationPosition[] = [
  { id: 'top_center', name: '顶部居中', description: '距顶部 300px' },
  { id: 'center', name: '中部居中', description: '屏幕中央' },
  { id: 'bottom_center', name: '底部居中', description: '距底部 300px' },
];

// 模板预览占位图（SVG）
const getPreviewPlaceholder = (templateId: string, name: string): string => {
  const colors: Record<string, { bg: string; text: string }> = {
    minimalist: { bg: '#1a1a1a', text: '#FFFFFF' },
    default: { bg: '#1a1a1a', text: '#FFFFFF' },
    classic: { bg: '#2a2a2a', text: '#FFFFFF' },
    neo_minimal: { bg: '#1a1a1a', text: '#FFFFFF' },
    hype: { bg: '#1a1a1a', text: '#f76f00' },
    explosive: { bg: '#1a1a1a', text: '#FFFF00' },
    fast: { bg: '#1a1a1a', text: '#00FFFF' },
    vibrant: { bg: '#667eea', text: '#FFFFFF' },
    word_focus: { bg: '#1a1a1a', text: '#00E676' },
    line_focus: { bg: '#212121', text: '#FFFFFF' },
    retro_gaming: { bg: '#0a0a0a', text: '#00FF00' },
    model: { bg: '#1a1a1a', text: '#F5F5F5' },
  };
  
  const c = colors[templateId] || { bg: '#1a1a1a', text: '#FFFFFF' };
  
  return `data:image/svg+xml,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="140" height="70" viewBox="0 0 140 70">
      <rect width="140" height="70" fill="${c.bg}"/>
      <text x="70" y="40" text-anchor="middle" fill="${c.text}" font-family="Arial" font-size="14" font-weight="bold">
        ${name}
      </text>
    </svg>
  `)}`;
};

// 位置预览图（SVG）
const getPositionPreview = (positionId: string): string => {
  const positionY: Record<string, number> = {
    top_center: 10,
    center: 30,
    bottom_center: 50,
  };
  
  const y = positionY[positionId] || 50;
  
  return `data:image/svg+xml,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="60" height="100" viewBox="0 0 60 100">
      <rect width="60" height="100" fill="#1a1a1a" rx="4"/>
      <rect x="10" y="${y - 5}" width="40" height="10" fill="#667eea" rx="2"/>
      <text x="30" y="${y + 3}" text-anchor="middle" fill="white" font-family="Arial" font-size="6">字幕位置</text>
    </svg>
  `)}`;
};

const AnimationTemplateSelector: React.FC<AnimationTemplateSelectorProps> = ({
  templateId,
  position,
  onTemplateChange,
  onPositionChange,
}) => {
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

  return (
    <div className="animation-template-selector space-y-4">
      {/* 模板选择标题 */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700">
          📝 字幕模板
          <span className="text-xs text-gray-400 ml-2">(PyCaps 12 种预设)</span>
        </h4>
        <button
          onClick={() => onTemplateChange(null)}
          className={`px-3 py-1 text-xs rounded-full transition-all ${
            templateId === null
              ? 'bg-purple-500 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          🎲 随机
        </button>
      </div>
      
      {/* 模板选择网格 - 4 列 */}
      <div className="grid grid-cols-4 gap-2">
        {PYCAPS_TEMPLATES.map((template) => (
          <button
            key={template.id}
            onClick={() => onTemplateChange(template.id)}
            onMouseEnter={() => setHoveredTemplate(template.id)}
            onMouseLeave={() => setHoveredTemplate(null)}
            className={`relative p-2 rounded-lg border-2 transition-all ${
              templateId === template.id
                ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            {/* 预览图 */}
            <div className="w-full h-10 bg-gray-900 rounded overflow-hidden mb-1 flex items-center justify-center">
              <img
                src={template.preview || getPreviewPlaceholder(template.id, template.name)}
                alt={template.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = getPreviewPlaceholder(template.id, template.name);
                }}
              />
            </div>
            {/* 模板名称 */}
            <div className="text-xs font-medium text-gray-700 truncate text-center">
              {template.name}
            </div>
          </button>
        ))}
      </div>

      {/* 模板详情预览（hover 时显示）*/}
      {hoveredTemplate && (
        <div className="p-3 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-28 h-14 bg-gray-900 rounded overflow-hidden flex-shrink-0">
              <img
                src={getPreviewPlaceholder(hoveredTemplate, PYCAPS_TEMPLATES.find(t => t.id === hoveredTemplate)?.name || '')}
                alt="preview"
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <div className="font-medium text-gray-900">
                {PYCAPS_TEMPLATES.find(t => t.id === hoveredTemplate)?.name}
              </div>
              <div className="text-sm text-gray-500">
                {PYCAPS_TEMPLATES.find(t => t.id === hoveredTemplate)?.description}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 位置选择 - 简化为 3 个 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          📍 字幕位置
          <span className="text-xs text-gray-400 ml-2">(距边缘 300px)</span>
        </label>
        <div className="grid grid-cols-3 gap-2">
          {POSITIONS.map((pos) => (
            <button
              key={pos.id}
              onClick={() => onPositionChange(pos.id)}
              className={`flex flex-col items-center p-2 rounded-lg transition-all ${
                position === pos.id
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {/* 位置预览图 */}
              <div className="w-10 h-16 mb-1">
                <img
                  src={getPositionPreview(pos.id)}
                  alt={pos.name}
                  className="w-full h-full"
                />
              </div>
              <div className="text-xs font-medium">{pos.name}</div>
              <div className={`text-xs ${position === pos.id ? 'text-blue-100' : 'text-gray-400'}`}>
                {pos.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 当前配置摘要 */}
      <div className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">当前配置:</span>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-white rounded text-xs font-medium text-gray-700">
              {templateId 
                ? PYCAPS_TEMPLATES.find(t => t.id === templateId)?.name || templateId
                : '🎲 随机'}
            </span>
            <span className="text-gray-300">+</span>
            <span className="px-2 py-1 bg-white rounded text-xs font-medium text-gray-700">
              {POSITIONS.find(p => p.id === position)?.name || position}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnimationTemplateSelector;
