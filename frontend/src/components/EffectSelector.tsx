// frontend/src/components/EffectSelector.tsx
/**
 * 特效选择器组件
 * 显示场景对应的特效列表，支持多选
 */

import React from 'react';

interface Effect {
  id: string;
  name: string;
  performance: string;
}

interface EffectSelectorProps {
  scene: string;
  effects: Effect[];
  selectedEffects: string[];
  onToggle: (effectId: string) => void;
  onRandom: () => void;
}

// 性能对应的星星数
const performanceStars: Record<string, number> = {
  'high': 5,
  'medium': 4,
  'low': 3,
};

const EffectSelector: React.FC<EffectSelectorProps> = ({
  scene,
  effects,
  selectedEffects,
  onToggle,
  onRandom,
}) => {
  const sceneNames: Record<string, string> = {
    'sports': '体育赛事',
    'interview': '体育访谈',
    'drama': '短剧/漫剧',
    'brand': '品牌宣传',
  };

  return (
    <div className="effect-selector">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">
          选择特效（{sceneNames[scene] || scene}）
        </h3>
        <span className="text-sm text-gray-500">
          已选择 {selectedEffects.length}/3 种特效
        </span>
      </div>
      
      <div className="grid grid-cols-3 gap-4 mb-4">
        {effects.map(effect => (
          <div
            key={effect.id}
            className={`
              effect-card p-4 rounded-lg border-2 cursor-pointer transition-all
              ${selectedEffects.includes(effect.id)
                ? 'border-green-500 bg-green-50'
                : 'border-gray-200 hover:border-gray-300'}
            `}
            onClick={() => onToggle(effect.id)}
          >
            {/* 特效预览图占位 */}
            <div className="effect-preview h-24 bg-gray-100 rounded mb-3 flex items-center justify-center">
              <span className="text-3xl">字幕效果</span>
            </div>
            
            <div className="font-medium text-gray-800">{effect.name}</div>
            
            {/* 性能指示 */}
            <div className="flex items-center mt-2">
              <span className="text-xs text-gray-400 mr-1">性能:</span>
              <span className="text-yellow-400">
                {'⭐'.repeat(performanceStars[effect.performance] || 4)}
              </span>
            </div>
            
            {/* 选中标记 */}
            {selectedEffects.includes(effect.id) && (
              <div className="absolute top-2 right-2 text-green-500 text-xl">✓</div>
            )}
          </div>
        ))}
      </div>

      {/* 操作按钮 */}
      <div className="flex justify-between items-center">
        <button
          onClick={onRandom}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 transition-colors"
        >
          🎲 随机选择
        </button>
        
        <span className="text-sm text-gray-400">
          提示: 选择 2-3 种特效效果最佳
        </span>
      </div>
    </div>
  );
};

export default EffectSelector;
