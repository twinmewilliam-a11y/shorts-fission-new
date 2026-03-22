import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

// 词级数据类型
export interface WordData {
  text: string;
  start: number;
  end: number;
  confidence?: number;
  tags?: string[];
}

// 行数据类型
export interface LineData {
  id: number;
  text: string;
  start: number;
  end: number;
  words: WordData[];
  tags?: string[];
}

// 配置类型
export interface SubtitleConfig {
  template?: string;
  position?: string;
  fontSize?: number;
  videoWidth?: number;
  videoHeight?: number;
}

// Props 类型
export interface WordAnimationProps {
  lines: LineData[];
  config?: SubtitleConfig;
}

// 位置映射 - 简化为 3 个位置，距边缘 300px
const POSITION_STYLES: Record<string, React.CSSProperties> = {
  top_center: { top: 300, left: '50%', transform: 'translateX(-50%)' },
  center: { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
  bottom_center: { bottom: 300, left: '50%', transform: 'translateX(-50%)' },
  // 保留旧位置的兼容性（映射到新位置）
  bottom_left: { bottom: 300, left: 40 },
  bottom_right: { bottom: 300, right: 40 },
};

// PyCaps 12 个预设模板配置
interface TemplateConfig {
  fontFamily: string;
  fontWeight: React.CSSProperties['fontWeight'];
  fontStyle?: React.CSSProperties['fontStyle'];
  color: string;
  narratedColor: string;
  highlightColor?: string;
  bgColor: string;
  textShadow: string;
  borderRadius?: number;
  textTransform?: React.CSSProperties['textTransform'];
  letterSpacing?: number;
}

const TEMPLATES: Record<string, TemplateConfig> = {
  // 1. minimalist - 极简风格
  minimalist: {
    fontFamily: "'Helvetica Neue', Arial, sans-serif",
    fontWeight: 400,
    color: '#FFFFFF',
    narratedColor: 'rgba(255, 255, 255, 0.5)',
    bgColor: 'transparent',
    textShadow: '1px 1px 2px rgba(0,0,0,0.5)',
  },
  
  // 2. default - 默认风格
  default: {
    fontFamily: "'Helvetica Neue', Arial, sans-serif",
    fontWeight: 600,
    color: '#FFFFFF',
    narratedColor: 'rgba(255, 255, 255, 0.6)',
    bgColor: 'rgba(0, 0, 0, 0.5)',
    textShadow: '1px 1px 3px rgba(0,0,0,0.8)',
  },
  
  // 3. classic - 经典风格
  classic: {
    fontFamily: 'Georgia, serif',
    fontWeight: 400,
    color: '#FFFFFF',
    narratedColor: 'rgba(255, 255, 255, 0.5)',
    bgColor: 'rgba(0, 0, 0, 0.6)',
    textShadow: '2px 2px 4px rgba(0,0,0,0.9)',
  },
  
  // 4. neo_minimal - 新极简风格
  neo_minimal: {
    fontFamily: "'SF Pro Display', -apple-system, sans-serif",
    fontWeight: 600,
    color: '#FFFFFF',
    narratedColor: 'rgba(255, 255, 255, 0.4)',
    bgColor: 'transparent',
    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
    letterSpacing: 1,
  },
  
  // 5. hype - 动感风格
  hype: {
    fontFamily: 'Arial Black, sans-serif',
    fontWeight: 900,
    color: '#FFFFFF',
    narratedColor: '#FFFFFF',
    highlightColor: '#f76f00',
    bgColor: 'rgba(0, 0, 0, 0.6)',
    textShadow: '-2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000',
  },
  
  // 6. explosive - 爆炸风格
  explosive: {
    fontFamily: 'Arial Black, sans-serif',
    fontWeight: 900,
    color: '#FFFFFF',
    narratedColor: '#FFFF00',
    highlightColor: '#FF6B00',
    bgColor: 'rgba(0, 0, 0, 0.5)',
    textShadow: '-3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 3px 3px 0 #000',
  },
  
  // 7. fast - 快速风格
  fast: {
    fontFamily: "'Impact', Arial Black, sans-serif",
    fontWeight: 900,
    color: '#FFFFFF',
    narratedColor: '#00FFFF',
    highlightColor: '#FFFF00',
    bgColor: 'transparent',
    textShadow: '2px 2px 0 #000',
    textTransform: 'uppercase',
  },
  
  // 8. vibrant - 活力风格
  vibrant: {
    fontFamily: "'Poppins', Arial, sans-serif",
    fontWeight: 700,
    color: '#FFFFFF',
    narratedColor: '#FF4081',
    highlightColor: '#7C4DFF',
    bgColor: 'rgba(102, 126, 234, 0.8)',
    textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
    borderRadius: 8,
  },
  
  // 9. word_focus - 词焦点风格
  word_focus: {
    fontFamily: "'Montserrat', Arial, sans-serif",
    fontWeight: 700,
    color: 'rgba(255, 255, 255, 0.35)',
    narratedColor: '#FFFFFF',
    highlightColor: '#00E676',
    bgColor: 'transparent',
    textShadow: '2px 2px 4px rgba(0,0,0,0.8)',
  },
  
  // 10. line_focus - 行焦点风格
  line_focus: {
    fontFamily: "'Roboto', Arial, sans-serif",
    fontWeight: 500,
    color: '#FFFFFF',
    narratedColor: '#FFFFFF',
    bgColor: 'rgba(33, 33, 33, 0.85)',
    textShadow: '1px 1px 2px rgba(0,0,0,0.5)',
    borderRadius: 8,
  },
  
  // 11. retro_gaming - 复古游戏风格
  retro_gaming: {
    fontFamily: "'Courier New', monospace",
    fontWeight: 700,
    color: '#00FF00',
    narratedColor: '#FFFF00',
    highlightColor: '#00FFFF',
    bgColor: 'rgba(0, 0, 0, 0.9)',
    textShadow: '2px 2px 0 #008800, 4px 4px 0 #004400',
    textTransform: 'uppercase',
    letterSpacing: 2,
  },
  
  // 12. model - 模特风格（高端简约）
  model: {
    fontFamily: "'Playfair Display', Georgia, serif",
    fontWeight: 400,
    fontStyle: 'italic',
    color: '#FFFFFF',
    narratedColor: '#F5F5F5',
    bgColor: 'transparent',
    textShadow: '1px 1px 3px rgba(0,0,0,0.6)',
    letterSpacing: 1,
  },
};

// 样式生成函数
const getWordStyle = (
  word: WordData,
  isBeingNarrated: boolean,
  isAlreadyNarrated: boolean,
  templateName: string,
  fontSize: number
): React.CSSProperties => {
  const baseStyle: React.CSSProperties = {
    display: 'inline-block',
    marginLeft: 6,
    marginRight: 6,
    marginBottom: 4,
    padding: '6px 10px',
    transition: 'all 0.08s ease-out',
    fontSize: fontSize,
  };
  
  const template = TEMPLATES[templateName] || TEMPLATES.default;
  
  let style: React.CSSProperties = {
    ...baseStyle,
    fontFamily: template.fontFamily,
    fontWeight: template.fontWeight,
    color: template.color,
    textShadow: template.textShadow,
  };
  
  // 应用字体样式
  if (template.fontStyle) {
    style.fontStyle = template.fontStyle;
  }
  if (template.textTransform) {
    style.textTransform = template.textTransform;
  }
  if (template.letterSpacing) {
    style.letterSpacing = `${template.letterSpacing}px`;
  }
  if (template.borderRadius) {
    style.borderRadius = template.borderRadius;
  }
  
  // 应用背景
  if (template.bgColor && template.bgColor !== 'transparent') {
    style.backgroundColor = template.bgColor;
  }
  
  // 状态样式
  if (isBeingNarrated) {
    style.transform = 'scale(1.1)';
    if (template.highlightColor) {
      style.color = template.highlightColor;
    } else if (template.narratedColor) {
      style.color = template.narratedColor;
    }
  } else if (isAlreadyNarrated) {
    if (template.narratedColor) {
      style.color = template.narratedColor;
    } else {
      style.opacity = 0.5;
    }
  }
  
  // 词级圆角
  if (word.tags?.includes('first-word-in-line')) {
    style.borderTopLeftRadius = 6;
    style.borderBottomLeftRadius = 6;
  }
  if (word.tags?.includes('last-word-in-line')) {
    style.borderTopRightRadius = 6;
    style.borderBottomRightRadius = 6;
  }
  
  return style;
};

// 主组件
export const WordAnimation: React.FC<WordAnimationProps> = ({ lines, config }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const template = config?.template || 'default';
  const position = config?.position || 'bottom_center';
  const fontSize = config?.fontSize || 56;  // 放大1倍：28 → 56
  
  const currentTime = frame / fps;
  
  // 找到当前应该显示的行
  const visibleLines = lines.filter(line => {
    const showTime = line.start - 0.3;
    const hideTime = line.end + 0.5;
    return currentTime >= showTime && currentTime <= hideTime;
  });
  
  if (visibleLines.length === 0) return null;
  
  return (
    <div
      style={{
        position: 'absolute',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        ...POSITION_STYLES[position],
      }}
    >
      {visibleLines.map((line) => (
        <div
          key={line.id}
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            maxWidth: '85%',
          }}
        >
          {line.words.map((word, idx) => {
            const startFrame = Math.floor(word.start * fps);
            const endFrame = Math.floor(word.end * fps);
            
            const isBeingNarrated = frame >= startFrame && frame < endFrame;
            const isAlreadyNarrated = frame >= endFrame;
            
            return (
              <span
                key={idx}
                style={getWordStyle(word, isBeingNarrated, isAlreadyNarrated, template, fontSize)}
              >
                {word.text}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// 导出模板列表供前端使用
export const TEMPLATE_LIST = [
  { id: 'minimalist', name: 'Minimalist', description: '极简风格 - 白色无背景', preview: '/templates/minimalist.png' },
  { id: 'default', name: 'Default', description: '默认风格 - 经典字幕效果', preview: '/templates/default.png' },
  { id: 'classic', name: 'Classic', description: '经典风格 - 衬线字体', preview: '/templates/classic.png' },
  { id: 'neo_minimal', name: 'Neo Minimal', description: '新极简风格 - 现代简约', preview: '/templates/neo_minimal.png' },
  { id: 'hype', name: 'Hype', description: '动感风格 - 橙色高亮 + 缩放', preview: '/templates/hype.png' },
  { id: 'explosive', name: 'Explosive', description: '爆炸风格 - 黄色爆炸效果', preview: '/templates/explosive.png' },
  { id: 'fast', name: 'Fast', description: '快速风格 - Impact 字体', preview: '/templates/fast.png' },
  { id: 'vibrant', name: 'Vibrant', description: '活力风格 - 渐变背景', preview: '/templates/vibrant.png' },
  { id: 'word_focus', name: 'Word Focus', description: '词焦点风格 - 当前词高亮', preview: '/templates/word_focus.png' },
  { id: 'line_focus', name: 'Line Focus', description: '行焦点风格 - 整行高亮', preview: '/templates/line_focus.png' },
  { id: 'retro_gaming', name: 'Retro Gaming', description: '复古游戏风格 - 像素风', preview: '/templates/retro_gaming.png' },
  { id: 'model', name: 'Model', description: '模特风格 - 高端斜体', preview: '/templates/model.png' },
];

// 导出位置列表供前端使用
export const POSITION_LIST = [
  { id: 'top_center', name: '顶部居中', description: '距顶部 300px', preview: '/positions/top.png' },
  { id: 'center', name: '中部居中', description: '屏幕中央', preview: '/positions/center.png' },
  { id: 'bottom_center', name: '底部居中', description: '距底部 300px', preview: '/positions/bottom.png' },
];

export default WordAnimation;
