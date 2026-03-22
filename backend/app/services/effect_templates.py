# backend/app/services/effect_templates.py
"""
文字层 v2.0 特效参数库
20种精选特效模板，覆盖4类场景

Created: 2026-03-13
Version: 2.0

颜色格式：ASS BGR（注意不是RGB！）
- &H0000FF& = 红色
- &HFF0000& = 蓝色
- &H00FFFF& = 黄色
"""

EFFECT_TEMPLATES = {
    # ==================== 体育场景 (6种) ====================
    'E01': {
        'name': '运动标签框',
        'name_en': 'Sports Label',
        'scene': ['sports'],
        'description': '黄色文字+黑色边框+箭头装饰，适合进球集锦',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 48,
            'font_size_range': (-6, 10),
            'primary_color': '&H00FFFF&',      # 黄色
            'outline_color': '&H000000&',      # 黑色
            'back_color': '&H60000000&',       # 半透明黑背景
            'outline': 6,
            'shadow': 2,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-3, 3),
        },
        'color_variants': [
            {'outline_color': '&H000000&', 'name': '黑边'},
            {'outline_color': '&H0000FF&', 'name': '红边'},
        ],
        'decoration': 'arrow',
        'performance': 'high',
    },
    
    'E02': {
        'name': '比分牌框',
        'name_en': 'Score Board',
        'scene': ['sports'],
        'description': '白色文字+红色边框+深色背景，适合比分显示',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 56,
            'font_size_range': (-8, 12),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H0000FF&',      # 红色
            'back_color': '&HA0000000&',       # 半透明黑背景
            'outline': 8,
            'shadow': 0,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
            'border_style': 3,                 # 边框样式
        },
        'color_variants': [
            {'outline_color': '&H0000FF&', 'name': '红边'},
            {'outline_color': '&H00FF00&', 'name': '绿边'},
        ],
        'performance': 'high',
    },
    
    'E03': {
        'name': '速度线框',
        'name_en': 'Speed Line',
        'scene': ['sports'],
        'description': '白色文字+绿色边框+倾斜效果，适合超车/冲刺',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 50,
            'font_size_range': (-8, 10),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H00FF00&',      # 绿色
            'back_color': '&H60000000&',       # 半透明黑背景
            'outline': 4,
            'shadow': 2,
            'bold': True,
            'italic': True,
            'rotation_base': -5,
            'rotation_range': (-3, 2),
        },
        'color_variants': [
            {'outline_color': '&H00FF00&', 'name': '绿边'},
            {'outline_color': '&H00FFFF&', 'name': '黄边'},
        ],
        'decoration': 'speed_line',
        'performance': 'high',
    },
    
    'E04': {
        'name': '高亮标签',
        'name_en': 'Highlight Tag',
        'scene': ['sports'],
        'description': '黄色文字+深红边框，适合MVP/明星展示',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 52,
            'font_size_range': (-6, 10),
            'primary_color': '&H00FFFF&',      # 黄色
            'outline_color': '&H000080&',      # 深红
            'back_color': '&H00000000&',       # 无背景
            'outline': 3,
            'shadow': 1,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'outline_color': '&H000080&', 'name': '深红边'},
            {'outline_color': '&H0080FF&', 'name': '橙色边'},
        ],
        'decoration': 'star',
        'performance': 'high',
    },
    
    'E05': {
        'name': '渐变发光字',
        'name_en': 'Gradient Glow',
        'scene': ['sports'],
        'description': '白色文字+蓝色边框+发光效果，适合精彩回放',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 52,
            'font_size_range': (-8, 12),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&HFF0000&',      # 蓝色
            'back_color': '&H800000&',         # 深蓝阴影
            'outline': 3,
            'shadow': 2,
            'blur': 1,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-3, 3),
        },
        'color_variants': [
            {'outline_color': '&HFF0000&', 'name': '蓝边'},
            {'outline_color': '&HFF00FF&', 'name': '紫边'},
        ],
        'performance': 'medium',
    },
    
    'E06': {
        'name': '3D立体框',
        'name_en': '3D Box',
        'scene': ['sports'],
        'description': '黄色文字+多重阴影，3D立体效果，适合重点赛事',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 48,
            'font_size_range': (-6, 10),
            'primary_color': '&H00FFFF&',      # 黄色
            'outline_color': '&H000000&',      # 黑色
            'back_color': '&H404040&',         # 深灰
            'outline': 3,
            'shadow': 6,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'primary_color': '&H00FFFF&', 'name': '黄色'},
            {'primary_color': '&HFFFFFF&', 'name': '白色'},
        ],
        'performance': 'medium',
    },
    
    # ==================== 短剧场景 (5种) ====================
    'E07': {
        'name': '漫剧气泡框',
        'name_en': 'Drama Bubble',
        'scene': ['drama'],
        'description': '黑色文字+白色背景块，气泡对话框效果',
        'params': {
            'font': 'Microsoft YaHei',
            'font_size_base': 44,
            'font_size_range': (-5, 8),
            'primary_color': '&H000000&',      # 黑色
            'outline_color': '&HCCCCCC&',      # 浅灰
            'back_color': '&H10FFFFFF&',       # 白色背景
            'outline': 2,
            'shadow': 3,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'back_color': '&H10FFFFFF&', 'name': '白背景'},
            {'back_color': '&H60FFFF00&', 'name': '浅黄背景'},
        ],
        'performance': 'high',
    },
    
    'E08': {
        'name': '经典台词框',
        'name_en': 'Classic Quote',
        'scene': ['drama'],
        'description': '白色文字+灰色边框+深色背景，适合台词展示',
        'params': {
            'font': 'Microsoft YaHei',
            'font_size_base': 42,
            'font_size_range': (-5, 8),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H808080&',      # 灰色
            'back_color': '&H80404040&',       # 深灰背景
            'outline': 3,
            'shadow': 2,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'outline_color': '&H808080&', 'name': '灰边'},
            {'outline_color': '&HC0C0C0&', 'name': '浅灰边'},
        ],
        'decoration': 'quote_mark',
        'performance': 'high',
    },
    
    'E09': {
        'name': '心形装饰',
        'name_en': 'Heart Decorated',
        'scene': ['drama'],
        'description': '紫色文字+红色边框，心形装饰，适合情感内容',
        'params': {
            'font': 'Microsoft YaHei',
            'font_size_base': 44,
            'font_size_range': (-5, 8),
            'primary_color': '&HFF00FF&',      # 紫色
            'outline_color': '&H0000FF&',      # 红色
            'back_color': '&H00000000&',       # 无背景
            'outline': 2,
            'shadow': 1,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'primary_color': '&HFF00FF&', 'name': '紫色'},
            {'primary_color': '&H00FFFF&', 'name': '黄色'},
        ],
        'decoration': 'heart',
        'performance': 'high',
    },
    
    'E10': {
        'name': '闪光字幕',
        'name_en': 'Flash Subtitle',
        'scene': ['drama'],
        'description': '白色文字+青色边框+模糊效果，适合惊人反转',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 48,
            'font_size_range': (-6, 10),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&HFFFF00&',      # 青色
            'back_color': '&H00000000&',       # 无背景
            'outline': 3,
            'shadow': 2,
            'blur': 1,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'outline_color': '&HFFFF00&', 'name': '青色'},
            {'outline_color': '&HFF0000&', 'name': '蓝色'},
        ],
        'decoration': 'lightning',
        'performance': 'medium',
    },
    
    'E11': {
        'name': '渐变背景框',
        'name_en': 'Gradient Background',
        'scene': ['drama'],
        'description': '白色文字+多层颜色背景，氛围渲染效果',
        'params': {
            'font': 'Microsoft YaHei',
            'font_size_base': 44,
            'font_size_range': (-5, 8),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H8080FF&',      # 浅红
            'back_color': '&HA00000FF&',       # 深红背景
            'outline': 8,
            'shadow': 0,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'back_color': '&HA00000FF&', 'name': '红背景'},
            {'back_color': '&HA0FF0000&', 'name': '蓝背景'},
        ],
        'performance': 'medium',
    },
    
    # ==================== 访谈场景 (5种) ====================
    'E12': {
        'name': '访谈字幕卡',
        'name_en': 'Interview Card',
        'scene': ['interview'],
        'description': '米黄色文字+白色边框+引号装饰，适合访谈内容',
        'params': {
            'font': 'Georgia',
            'font_size_base': 42,
            'font_size_range': (-5, 8),
            'primary_color': '&HA5DEF5&',      # 米黄色
            'outline_color': '&HFFFFFF&',      # 白色
            'back_color': '&H80000000&',       # 半透明黑背景
            'outline': 3,
            'shadow': 2,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'primary_color': '&HA5DEF5&', 'name': '米黄'},
            {'primary_color': '&HFFFFFF&', 'name': '白色'},
        ],
        'decoration': 'quote_mark',
        'performance': 'high',
    },
    
    'E13': {
        'name': '人物标签',
        'name_en': 'Person Tag',
        'scene': ['interview'],
        'description': '白色文字+黑色边框+背景，适合嘉宾介绍',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 40,
            'font_size_range': (-5, 8),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H000000&',      # 黑色
            'back_color': '&H80000000&',       # 半透明黑背景
            'outline': 2,
            'shadow': 1,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-1, 1),
        },
        'color_variants': [
            {'primary_color': '&HFFFFFF&', 'name': '白色'},
            {'primary_color': '&H00FFFF&', 'name': '黄色'},
        ],
        'decoration': 'person_icon',
        'performance': 'high',
    },
    
    'E14': {
        'name': '对话框',
        'name_en': 'Dialog Box',
        'scene': ['interview'],
        'description': '米黄色文字+灰色边框，适合观点表达',
        'params': {
            'font': 'Microsoft YaHei',
            'font_size_base': 42,
            'font_size_range': (-5, 8),
            'primary_color': '&HA5DEF5&',      # 米黄色
            'outline_color': '&H404040&',      # 深灰
            'back_color': '&H60FFFFFF&',       # 浅白背景
            'outline': 2,
            'shadow': 2,
            'rotation_base': 0,
            'rotation_range': (-1, 1),
        },
        'color_variants': [
            {'primary_color': '&HA5DEF5&', 'name': '米黄'},
            {'primary_color': '&HFFFFFF&', 'name': '白色'},
        ],
        'decoration': 'dialog_icon',
        'performance': 'high',
    },
    
    'E15': {
        'name': '双边框',
        'name_en': 'Double Border',
        'scene': ['interview'],
        'description': '白色文字+双层边框效果，适合专业分析',
        'params': {
            'font': 'Microsoft YaHei',
            'font_size_base': 42,
            'font_size_range': (-5, 8),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H0000FF&',      # 红色内框
            'back_color': '&H000000&',         # 黑色外框
            'outline': 6,
            'shadow': 4,
            'rotation_base': 0,
            'rotation_range': (-1, 1),
        },
        'color_variants': [
            {'outline_color': '&H0000FF&', 'name': '红边'},
            {'outline_color': '&HFF0000&', 'name': '蓝边'},
        ],
        'performance': 'high',
    },
    
    'E16': {
        'name': '圆角矩形框',
        'name_en': 'Rounded Box',
        'scene': ['interview'],
        'description': '白色文字+粗边框，圆角效果，通用访谈',
        'params': {
            'font': 'Microsoft YaHei',
            'font_size_base': 42,
            'font_size_range': (-5, 8),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H0000FF&',      # 红色
            'back_color': '&HC0000000&',       # 半透明黑背景
            'outline': 10,
            'shadow': 0,
            'border_style': 3,
            'rotation_base': 0,
            'rotation_range': (-1, 1),
        },
        'color_variants': [
            {'outline_color': '&H0000FF&', 'name': '红边'},
            {'outline_color': '&H00FF00&', 'name': '绿边'},
        ],
        'performance': 'high',
    },
    
    # ==================== 品牌场景 (4种) ====================
    'E17': {
        'name': '品牌横幅',
        'name_en': 'Brand Banner',
        'scene': ['brand'],
        'description': '白色粗体+橙色边框+火焰装饰，适合活动宣传',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 48,
            'font_size_range': (-6, 10),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H0066FF&',      # 橙色
            'back_color': '&H80000000&',       # 半透明黑背景
            'outline': 6,
            'shadow': 2,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'outline_color': '&H0066FF&', 'name': '橙色'},
            {'outline_color': '&H0000FF&', 'name': '红色'},
        ],
        'decoration': 'fire',
        'performance': 'high',
    },
    
    'E18': {
        'name': '倒计时框',
        'name_en': 'Countdown Box',
        'scene': ['brand'],
        'description': '白色文字+红色边框+背景，适合限时优惠',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 52,
            'font_size_range': (-8, 12),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H0000FF&',      # 红色
            'back_color': '&HA0000000&',       # 半透明黑背景
            'outline': 6,
            'shadow': 0,
            'bold': True,
            'rotation_base': 0,
            'rotation_range': (-2, 2),
        },
        'color_variants': [
            {'outline_color': '&H0000FF&', 'name': '红色'},
            {'outline_color': '&H00FFFF&', 'name': '黄色'},
        ],
        'decoration': 'clock',
        'performance': 'high',
    },
    
    'E19': {
        'name': '底部高亮条',
        'name_en': 'Bottom Highlight',
        'scene': ['brand'],
        'description': '白色文字+底部色条，CTA引导效果',
        'params': {
            'font': 'Arial Black',
            'font_size_base': 44,
            'font_size_range': (-5, 8),
            'primary_color': '&HFFFFFF&',      # 白色
            'outline_color': '&H000000&',      # 黑色
            'back_color': '&H0000FF&',         # 红色背景条
            'outline': 2,
            'shadow': 8,
            'alignment': 6,                    # 左下对齐
            'rotation_base': 0,
            'rotation_range': (-1, 1),
        },
        'color_variants': [
            {'back_color': '&H0000FF&', 'name': '红色条'},
            {'back_color': '&HFF0000&', 'name': '蓝色条'},
        ],
        'performance': 'high',
    },
    
    'E20': {
        'name': '打字机风格',
        'name_en': 'Typewriter',
        'scene': ['brand'],
        'description': '浅绿色文字+黑色边框，打字机效果，适合剧情预告',
        'params': {
            'font': 'Courier New',
            'font_size_base': 40,
            'font_size_range': (-5, 8),
            'primary_color': '&H40FF00&',      # 浅绿
            'outline_color': '&H000000&',      # 黑色
            'back_color': '&H00000000&',       # 无背景
            'outline': 1,
            'shadow': 1,
            'rotation_base': 0,
            'rotation_range': (-1, 1),
        },
        'color_variants': [
            {'primary_color': '&H40FF00&', 'name': '浅绿'},
            {'primary_color': '&H00FFFF&', 'name': '黄色'},
        ],
        'decoration': 'cursor',
        'performance': 'high',
    },
}

# 9宫格位置配置
POSITION_GRID = {
    'TL': {'align': 7, 'margin_l': 50, 'margin_r': 0, 'margin_v': 50, 'name': '左上'},
    'TC': {'align': 8, 'margin_l': 0, 'margin_r': 0, 'margin_v': 50, 'name': '上中'},
    'TR': {'align': 9, 'margin_l': 0, 'margin_r': 50, 'margin_v': 50, 'name': '右上'},
    'ML': {'align': 4, 'margin_l': 50, 'margin_r': 0, 'margin_v': 0, 'name': '左中'},
    'MC': {'align': 5, 'margin_l': 0, 'margin_r': 0, 'margin_v': 0, 'name': '正中'},
    'MR': {'align': 6, 'margin_l': 0, 'margin_r': 50, 'margin_v': 0, 'name': '右中'},
    'BL': {'align': 1, 'margin_l': 50, 'margin_r': 0, 'margin_v': 80, 'name': '左下'},
    'BC': {'align': 2, 'margin_l': 0, 'margin_r': 0, 'margin_v': 80, 'name': '下中'},
    'BR': {'align': 3, 'margin_l': 0, 'margin_r': 50, 'margin_v': 80, 'name': '右下'},
}

# 场景配置
SCENE_CONFIG = {
    'sports': {
        'name': '🏀 体育赛事',
        'name_en': 'Sports',
        'description': '精彩集锦、比赛回顾、进球集锦',
        'effects': ['E01', 'E02', 'E03', 'E04', 'E05', 'E06'],
        'effect_count': (2, 3),
        'auto_subtitle': True,
        'recommended_position': 'BC',
    },
    'drama': {
        'name': '🎬 短剧/漫剧',
        'name_en': 'Drama',
        'description': '剧情片段、情感内容、台词展示',
        'effects': ['E07', 'E08', 'E09', 'E10', 'E11'],
        'effect_count': (2, 3),
        'auto_subtitle': True,
        'recommended_position': 'MC',
    },
    'interview': {
        'name': '🎤 体育访谈',
        'name_en': 'Interview',
        'description': '采访、对话、战术分析',
        'effects': ['E12', 'E13', 'E14', 'E15', 'E16'],
        'effect_count': (2, 3),
        'auto_subtitle': True,
        'recommended_position': 'BL',
    },
    'brand': {
        'name': '📢 品牌宣传',
        'name_en': 'Brand',
        'description': '广告、引流、品牌曝光',
        'effects': ['E17', 'E18', 'E19', 'E20'],
        'effect_count': (2, 3),
        'auto_subtitle': False,
        'show_manual_input': True,
        'recommended_position': 'BR',
    },
}

def get_scene_effects(scene: str) -> list:
    """获取场景对应的特效列表"""
    config = SCENE_CONFIG.get(scene, {})
    return config.get('effects', [])

def get_random_effects(scene: str, count: int = None) -> list:
    """随机选择场景对应的特效"""
    import random
    effects = get_scene_effects(scene)
    if not effects:
        return []
    
    config = SCENE_CONFIG.get(scene, {})
    min_count, max_count = config.get('effect_count', (2, 3))
    
    if count is None:
        count = random.randint(min_count, max_count)
    
    return random.sample(effects, min(count, len(effects)))

def get_effect_template(effect_id: str) -> dict:
    """获取特效模板"""
    return EFFECT_TEMPLATES.get(effect_id)

def get_all_effects() -> dict:
    """获取所有特效"""
    return EFFECT_TEMPLATES

def get_all_scenes() -> dict:
    """获取所有场景"""
    return SCENE_CONFIG
