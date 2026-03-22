# backend/app/services/text_layer_engine_v2.py
"""
文字层 v2.0 引擎
"""
import random
import os
import re
from typing import Dict, Optional, List
from loguru import logger

from .effect_templates import EFFECT_TEMPLATES, POSITION_GRID, SCENE_CONFIG


class TextLayerEngineV2:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.templates = EFFECT_TEMPLATES
        self.positions = POSITION_GRID
        
    def generate_variant(self, subtitle_path: str, output_ass_path: str,
                         video_width: int, video_height: int,
                         effect_id: str = None, scene: str = None, seed: int = None) -> Dict:
        if seed is not None:
            random.seed(seed)
        
        if not effect_id:
            effect_id = self._select_effect(scene)
        if effect_id not in self.templates:
            return {'success': False, 'error': f'Invalid effect: {effect_id}'}
        
        template = self.templates[effect_id]
        params = self._randomize_params(template, video_width, video_height)
        
        subtitle_content = self._read_subtitle(subtitle_path)
        if not subtitle_content:
            return {'success': False, 'error': 'Cannot read subtitle file'}
        
        ass_content = self._generate_ass(subtitle_content, params, video_width, video_height)
        
        os.makedirs(os.path.dirname(output_ass_path), exist_ok=True)
        with open(output_ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        logger.info(f"[文字层 v2.0] 特效: {template['name']}, 字号: {params['font_size']}")
        
        return {
            'success': True,
            'effect_id': effect_id,
            'effect_name': template['name'],
            'params': params,
            'ass_path': output_ass_path,
        }
    
    def _select_effect(self, scene: str = None) -> str:
        if scene and scene in SCENE_CONFIG:
            effects = SCENE_CONFIG[scene].get('effects', [])
            if effects:
                return random.choice(effects)
        return random.choice(list(self.templates.keys()))
    
    def _randomize_params(self, template: Dict, video_width: int, video_height: int) -> Dict:
        params = template['params'].copy()
        
        font_size_base = params.get('font_size_base', 45)
        font_size_range = params.get('font_size_range', (-5, 10))
        params['font_size'] = font_size_base + random.randint(*font_size_range)
        
        rotation_base = params.get('rotation_base', 0)
        rotation_range = params.get('rotation_range', (-2, 2))
        params['rotation'] = rotation_base + random.uniform(*rotation_range)
        
        position_key = random.choice(list(self.positions.keys()))
        position = self.positions[position_key].copy()
        position['margin_l'] = max(0, position['margin_l'] + random.randint(-30, 30))
        position['margin_v'] = max(0, position['margin_v'] + random.randint(-20, 20))
        position['key'] = position_key
        params['position'] = position
        params['position_name'] = position['name']
        
        color_variants = template.get('color_variants', [{}])
        selected_color = random.choice(color_variants)
        params.update(selected_color)
        
        if template.get('animation') == 'fade_in':
            params['animation'] = 'fade_in'
            params['animation_duration'] = template.get('animation_duration', 300)
        
        return params
    
    def _read_subtitle(self, subtitle_path: str) -> str:
        if not subtitle_path or not os.path.exists(subtitle_path):
            return None
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            try:
                with open(subtitle_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except:
                return None
    
    def _generate_ass(self, subtitle_content: str, params: Dict, video_width: int, video_height: int) -> str:
        style_line = self._build_style_line(params)
        dialogues = self._build_dialogues(subtitle_content, params)
        
        return f"""[Script Info]
Title: Text Layer v2.0
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
{style_line}

[Events]
{dialogues}
"""
    
    def _build_style_line(self, params: Dict) -> str:
        primary = params.get('primary_color', '&HFFFFFF')
        outline_color = params.get('outline_color', '&H000000')
        back_color = params.get('back_color', '&H000000')
        outline = params.get('outline', 2)
        shadow = params.get('shadow', 1)
        font = params.get('font', 'Arial')
        font_size = params.get('font_size', 45)
        bold = -1 if params.get('bold', False) else 0
        italic = -1 if params.get('italic', False) else 0
        rotation = params.get('rotation', 0)
        position = params.get('position', {})
        align = position.get('align', 2)
        margin_l = position.get('margin_l', 10)
        margin_r = position.get('margin_r', 10)
        margin_v = position.get('margin_v', 50)
        
        format_line = "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
        style_data = f"Style: Default,{font},{font_size},{primary},&H000000,{outline_color},{back_color},{bold},{italic},0,0,100,100,0,{rotation:.2f},1,{outline},{shadow},{align},{margin_l},{margin_r},{margin_v},1"
        
        return f"{format_line}\n{style_data}"
    
    def _build_dialogues(self, subtitle_content: str, params: Dict) -> str:
        lines = []
        animation = params.get('animation')
        animation_duration = params.get('animation_duration', 300)
        
        if '[Events]' in subtitle_content:
            in_events = False
            for line in subtitle_content.split('\n'):
                if line.strip() == '[Events]':
                    in_events = True
                    lines.append(line)
                    continue
                if in_events and line.startswith('Format:'):
                    lines.append(line)
                    continue
                if in_events and line.startswith('Dialogue:'):
                    if animation == 'fade_in':
                        parts = line.split(',', 9)
                        if len(parts) >= 10:
                            text = parts[9]
                            if text.startswith('{'):
                                text = text.replace('{', f'{{\\t(0,{animation_duration},\\1a&HFF&)', 1)
                            else:
                                text = f'{{\\t(0,{animation_duration},\\1a&HFF&)}}' + text
                            parts[9] = text
                            line = ','.join(parts)
                    lines.append(line)
                elif in_events and line.startswith('['):
                    break
        else:
            blocks = re.split(r'\n\s*\n', subtitle_content.strip())
            for block in blocks:
                lines_in_block = block.strip().split('\n')
                if len(lines_in_block) < 3:
                    continue
                time_line = lines_in_block[1]
                text_lines = lines_in_block[2:]
                text = ' '.join(text_lines)
                
                time_match = re.match(
                    r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                    time_line
                )
                if not time_match:
                    continue
                
                start_h, start_m, start_s, start_ms = time_match.groups()[:4]
                end_h, end_m, end_s, end_ms = time_match.groups()[4:]
                start_time = f"{int(start_h)}:{start_m}:{start_s}.{int(start_ms)//10}"
                end_time = f"{int(end_h)}:{end_m}:{end_s}.{int(end_ms)//10}"
                
                if animation == 'fade_in':
                    text = f'{{\\t(0,{animation_duration},\\1a&HFF&)}}' + text
                
                lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
        
        return '\n'.join(lines)


def generate_text_layer(subtitle_path: str, output_path: str, video_width: int, video_height: int,
                        effect_id: str = None, scene: str = None) -> Dict:
    engine = TextLayerEngineV2()
    return engine.generate_variant(subtitle_path, output_path, video_width, video_height, effect_id, scene)

def get_available_effects(scene: str = None) -> list:
    if scene and scene in SCENE_CONFIG:
        effect_ids = SCENE_CONFIG[scene].get('effects', [])
        return [{'id': eid, 'name': EFFECT_TEMPLATES[eid]['name']} for eid in effect_ids if eid in EFFECT_TEMPLATES]
    return [{'id': eid, 'name': t['name']} for eid, t in EFFECT_TEMPLATES.items()]

def get_available_scenes() -> list:
    return [{'id': sid, 'name': c['name']} for sid, c in SCENE_CONFIG.items()]
