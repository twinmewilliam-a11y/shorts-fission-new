// frontend/src/components/TextLayerConfig.tsx
/**
 * 文字层配置组件
 * 配置字幕来源、水印、话题标签
 */

import React from 'react';

interface TextLayerConfigProps {
  scene: string;
  config: {
    subtitleSource: string;
    brandWatermark: string;
    watermarkPosition: string;
    hashtag: string;
    hashtagPosition: string;
  };
  onConfigChange: (config: TextLayerConfigProps['config']) => void;
}

const positions = [
  { value: 'TL', label: '左上角' },
  { value: 'TC', label: '上中' },
  { value: 'TR', label: '右上角' },
  { value: 'ML', label: '左中' },
  { value: 'MC', label: '正中' },
  { value: 'MR', label: '右中' },
  { value: 'BL', label: '左下角' },
  { value: 'BC', label: '下中' },
  { value: 'BR', label: '右下角' },
];

const TextLayerConfig: React.FC<TextLayerConfigProps> = ({
  scene,
  config,
  onConfigChange,
}) => {
  // 品牌宣传场景显示手动输入选项
  const showManualInput = scene === 'brand';

  const updateConfig = (key: string, value: string) => {
    onConfigChange({ ...config, [key]: value });
  };

  return (
    <div className="text-layer-config">
      <h3 className="text-lg font-semibold mb-4">配置文字层</h3>
      
      {/* 字幕来源 */}
      <div className="config-section mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          字幕来源
        </label>
        <div className="flex gap-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="file"
              checked={config.subtitleSource === 'file'}
              onChange={() => updateConfig('subtitleSource', 'file')}
              className="mr-2"
            />
            字幕文件
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="whisperx"
              checked={config.subtitleSource === 'whisperx'}
              onChange={() => updateConfig('subtitleSource', 'whisperx')}
              className="mr-2"
            />
            WhisperX 提取
          </label>
          {showManualInput && (
            <label className="flex items-center">
              <input
                type="radio"
                value="manual"
                checked={config.subtitleSource === 'manual'}
                onChange={() => updateConfig('subtitleSource', 'manual')}
                className="mr-2"
              />
              手动输入
            </label>
          )}
        </div>
      </div>

      {/* 品牌水印 */}
      <div className="config-section mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          品牌水印（可选）
        </label>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="@账号名 或 品牌名"
            value={config.brandWatermark}
            onChange={(e) => updateConfig('brandWatermark', e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={config.watermarkPosition}
            onChange={(e) => updateConfig('watermarkPosition', e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {positions.map(pos => (
              <option key={pos.value} value={pos.value}>{pos.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 话题标签 */}
      <div className="config-section">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          话题标签（可选）
        </label>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="#话题标签"
            value={config.hashtag}
            onChange={(e) => updateConfig('hashtag', e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={config.hashtagPosition}
            onChange={(e) => updateConfig('hashtagPosition', e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {positions.map(pos => (
              <option key={pos.value} value={pos.value}>{pos.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

export default TextLayerConfig;
