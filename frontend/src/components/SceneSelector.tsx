// frontend/src/components/SceneSelector.tsx
/**
 * 场景选择器组件
 * 用于选择视频类型（体育赛事/体育访谈/短剧漫剧/品牌宣传）
 */

import React from 'react';

interface SceneSelectorProps {
  value: string;
  onChange: (scene: string) => void;
}

const scenes = [
  { 
    id: 'sports', 
    name: '🏀 体育赛事', 
    desc: '精彩集锦、比赛回顾',
    effects: ['动感粗描边', '霓虹发光', '速度倾斜']
  },
  { 
    id: 'interview', 
    name: '🎤 体育访谈', 
    desc: '采访、对话、分析',
    effects: ['简洁白字', '色块背景', '细线分隔']
  },
  { 
    id: 'drama', 
    name: '🎬 短剧/漫剧', 
    desc: '剧情片段、情感内容',
    effects: ['暖色情感', '引号装饰', '渐变淡入']
  },
  { 
    id: 'brand', 
    name: '📢 品牌宣传', 
    desc: '广告、引流、曝光',
    effects: ['简洁白字', '复古怀旧', '色块背景']
  },
];

const SceneSelector: React.FC<SceneSelectorProps> = ({ value, onChange }) => {
  return (
    <div className="scene-selector">
      <h3 className="text-lg font-semibold mb-4">选择场景类型</h3>
      
      <div className="grid grid-cols-2 gap-4">
        {scenes.map(scene => (
          <div
            key={scene.id}
            className={`
              scene-card p-4 rounded-lg border-2 cursor-pointer transition-all
              ${value === scene.id 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'}
            `}
            onClick={() => onChange(scene.id)}
          >
            <div className="text-2xl mb-2">{scene.name.split(' ')[0]}</div>
            <div className="font-medium text-gray-800">
              {scene.name.split(' ').slice(1).join(' ')}
            </div>
            <div className="text-sm text-gray-500 mt-1">{scene.desc}</div>
            <div className="text-xs text-gray-400 mt-2">
              推荐特效: {scene.effects.slice(0, 2).join('、')}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SceneSelector;
