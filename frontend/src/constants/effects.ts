// frontend/src/constants/effects.ts
/**
 * 文字层 v2.0 特效常量
 */

export const SCENES = [
  {
    id: 'sports',
    name: '🏀 体育赛事',
    nameEn: 'Sports',
    description: '精彩集锦、比赛回顾、进球集锦',
    effects: ['E01', 'E04', 'E06'],
  },
  {
    id: 'interview',
    name: '🎤 体育访谈',
    nameEn: 'Interview',
    description: '采访、对话、战术分析',
    effects: ['E02', 'E08', 'E09'],
  },
  {
    id: 'drama',
    name: '🎬 短剧/漫剧',
    nameEn: 'Drama',
    description: '剧情片段、情感内容、台词展示',
    effects: ['E03', 'E07', 'E10'],
  },
  {
    id: 'brand',
    name: '📢 品牌宣传',
    nameEn: 'Brand',
    description: '广告、引流、品牌曝光',
    effects: ['E02', 'E05', 'E08'],
  },
];

export const EFFECTS = [
  {
    id: 'E01',
    name: '动感粗描边',
    nameEn: 'Dynamic Bold Outline',
    description: '粗描边+高对比色，适合体育赛事精彩镜头',
    scene: ['sports'],
    performance: 'high',
  },
  {
    id: 'E02',
    name: '简洁白字',
    nameEn: 'Clean White',
    description: '简洁白字+黑边，清晰易读，专业感',
    scene: ['interview', 'brand'],
    performance: 'high',
  },
  {
    id: 'E03',
    name: '暖色情感',
    nameEn: 'Warm Emotional',
    description: '暖色调+柔和描边，适合情感表达',
    scene: ['drama'],
    performance: 'high',
  },
  {
    id: 'E04',
    name: '霓虹发光',
    nameEn: 'Neon Glow',
    description: '霓虹发光效果，适合潮流内容',
    scene: ['sports'],
    performance: 'medium',
  },
  {
    id: 'E05',
    name: '复古怀旧',
    nameEn: 'Retro Vintage',
    description: '复古暖色调，适合经典内容',
    scene: ['brand'],
    performance: 'high',
  },
  {
    id: 'E06',
    name: '速度倾斜',
    nameEn: 'Speed Italic',
    description: '倾斜+粗体，速度感和动感',
    scene: ['sports'],
    performance: 'high',
  },
  {
    id: 'E07',
    name: '引号装饰',
    nameEn: 'Quote Decorated',
    description: '引号装饰，适合台词展示',
    scene: ['drama'],
    performance: 'high',
  },
  {
    id: 'E08',
    name: '色块背景',
    nameEn: 'Color Block',
    description: '半透明色块背景，提升可读性',
    scene: ['interview', 'brand'],
    performance: 'medium',
  },
  {
    id: 'E09',
    name: '细线分隔',
    nameEn: 'Thin Line',
    description: '上下细线装饰，专业感',
    scene: ['interview'],
    performance: 'high',
  },
  {
    id: 'E10',
    name: '渐变淡入',
    nameEn: 'Fade In',
    description: '淡入动画效果，情感表达',
    scene: ['drama'],
    performance: 'medium',
  },
];

export const POSITIONS = [
  { id: 'TL', name: '左上', align: 7 },
  { id: 'TC', name: '上中', align: 8 },
  { id: 'TR', name: '右上', align: 9 },
  { id: 'ML', name: '左中', align: 4 },
  { id: 'MC', name: '正中', align: 5 },
  { id: 'MR', name: '右中', align: 6 },
  { id: 'BL', name: '左下', align: 1 },
  { id: 'BC', name: '下中', align: 2 },
  { id: 'BR', name: '右下', align: 3 },
];

// 根据场景获取特效列表
export function getEffectsByScene(sceneId: string) {
  const scene = SCENES.find(s => s.id === sceneId);
  if (!scene) return [];
  return EFFECTS.filter(e => scene.effects.includes(e.id));
}

// 随机选择特效
export function getRandomEffects(sceneId: string, count: number = 2) {
  const effects = getEffectsByScene(sceneId);
  const shuffled = [...effects].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, Math.min(count, effects.length));
}
