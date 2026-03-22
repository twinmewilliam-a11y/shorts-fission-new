import React from 'react';
import {Composition, registerRoot, getInputProps} from 'remotion';
import {WordAnimation, LineData, SubtitleConfig} from './WordAnimation';

// 从配置文件加载（渲染时使用）
const loadConfig = (): {lines: LineData[], config?: SubtitleConfig} | null => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const subtitleConfig = require('./subtitle_config.json');
    return subtitleConfig as {lines: LineData[], config?: SubtitleConfig};
  } catch {
    return null;
  }
};

// 加载配置
const subtitleData = loadConfig();
const lines = subtitleData?.lines || [];
const fileConfig = subtitleData?.config;

// 计算视频时长（基于最后一行）
const lastLine = lines[lines.length - 1];
const durationInSeconds = lastLine ? lastLine.end + 1 : 5;
const fps = 30;
const durationInFrames = Math.ceil(durationInSeconds * fps);

// 获取 CLI props 并合并配置
const inputProps = getInputProps();
const finalConfig: SubtitleConfig = {
  template: inputProps?.template || fileConfig?.template || 'pop_highlight',
  position: inputProps?.position || fileConfig?.position || 'bottom_center',
  fontSize: inputProps?.fontSize || fileConfig?.fontSize || 24,
  videoWidth: inputProps?.videoWidth || fileConfig?.videoWidth || 1080,
  videoHeight: inputProps?.videoHeight || fileConfig?.videoHeight || 1920,
};

// Caption 组件（Remotion Composition 入口）
export const Caption: React.FC = () => {
  return React.createElement('div', {
    style: {
      position: 'absolute',
      width: '100%',
      height: '100%',
      backgroundColor: 'transparent',
    }
  },
  React.createElement(WordAnimation, {
    lines: lines,
    config: finalConfig,
  })
  );
};

// 注册 Root
registerRoot(() => {
  return React.createElement(Composition, {
    id: 'Caption',
    component: Caption,
    durationInFrames: durationInFrames,
    fps: fps,
    width: finalConfig.videoWidth || 1080,
    height: finalConfig.videoHeight || 1920,
  });
});
