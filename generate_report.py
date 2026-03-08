#!/usr/bin/env python3
"""
TikTok 视频去重 - 视觉特效参数参考报告 (中文版)
使用 reportlab 内置的 Asian 字体支持
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from datetime import datetime

def create_pdf():
    # 注册中文字体 - 使用 Adobe 的 Asian 字体
    try:
        # 尝试注册 Adobe 的 Asian 字体
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        chinese_font = 'STSong-Light'
        print("使用字体: STSong-Light")
    except Exception as e:
        print(f"STSong-Light 加载失败: {e}")
        try:
            pdfmetrics.registerFont(UnicodeCIDFont('AdobeSongStd-Light'))
            chinese_font = 'AdobeSongStd-Light'
            print("使用字体: AdobeSongStd-Light")
        except Exception as e2:
            print(f"AdobeSongStd-Light 加载失败: {e2}")
            chinese_font = 'Helvetica'
    
    # 创建 PDF
    doc = SimpleDocTemplate(
        "/root/.openclaw/workspace/projects/shorts-fission/TikTok_Video_Deduplication_Report.pdf",
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # 样式
    styles = getSampleStyleSheet()
    
    # 自定义中文样式
    title_style = ParagraphStyle(
        'ChineseTitle',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=22,
        leading=28,
        alignment=1,
        spaceAfter=20
    )
    
    heading2_style = ParagraphStyle(
        'ChineseHeading2',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=16,
        leading=20,
        spaceAfter=12
    )
    
    heading3_style = ParagraphStyle(
        'ChineseHeading3',
        parent=styles['Heading3'],
        fontName=chinese_font,
        fontSize=13,
        leading=17,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'ChineseNormal',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=10,
        leading=14
    )
    
    story = []
    
    # 标题页
    story.append(Paragraph("TikTok 视频去重", title_style))
    story.append(Paragraph("视觉特效参数参考报告", title_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("基于 video-mover + AB-Video-Deduplicator + GitHub/Reddit 研究", normal_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"生成日期: {datetime.now().strftime('%Y-%m-%d')}", normal_style))
    story.append(PageBreak())
    
    # 目录
    story.append(Paragraph("目录", heading2_style))
    story.append(Spacer(1, 12))
    toc_items = [
        "1. 研究概述",
        "2. 核心发现",
        "3. 视觉特效参数详解",
        "4. 参数验证结果",
        "5. 最佳实践建议",
        "6. 参考项目",
    ]
    for item in toc_items:
        story.append(Paragraph(item, normal_style))
        story.append(Spacer(1, 6))
    story.append(PageBreak())
    
    # 1. 研究概述
    story.append(Paragraph("1. 研究概述", heading2_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "本报告基于对多个开源 TikTok 视频去重项目的深入研究，包括 video-mover (361 stars)、"
        "AB-Video-Deduplicator (139 stars) 等热门项目，以及 GitHub Issues 和相关技术文档。",
        normal_style
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "研究目标：分析 TikTok 视频去重的最佳实践，验证视觉特效参数的合理性，提供可落地的参数配置建议。",
        normal_style
    ))
    story.append(PageBreak())
    
    # 2. 核心发现
    story.append(Paragraph("2. 核心发现", heading2_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("关键发现 1：组合策略最有效 - 使用 3-5 种特效组合效果最佳，单一特效容易被检测。", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("关键发现 2：轻度调整优于重度变形 - 参数变化要轻微，避免明显变形。", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("关键发现 3：随机性很重要 - 不同变体使用不同特效组合，增加检测难度。", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("关键发现 4：平台算法持续更新 - 需要不断调整参数，单一方法效果有限。", normal_style))
    story.append(PageBreak())
    
    # 3. 视觉特效参数详解
    story.append(Paragraph("3. 视觉特效参数详解", heading2_style))
    story.append(Spacer(1, 12))
    
    # 颜色调整参数表
    story.append(Paragraph("3.1 颜色调整参数", heading3_style))
    story.append(Spacer(1, 6))
    
    color_data = [
        ['特效', '参数范围', '推荐值', '说明'],
        ['饱和度', '0.8 - 1.2', '1.05', '值越大颜色越鲜艳'],
        ['亮度', '-0.3 - 0.3', '0.05', '正值增加亮度'],
        ['对比度', '0.8 - 1.2', '1.05', '值越大对比度越高'],
        ['RGB偏移', '0 - 10', '3', 'RGB通道偏移'],
    ]
    
    color_table = Table(color_data, colWidths=[1.2*inch, 1.3*inch, 0.9*inch, 2.1*inch])
    color_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(color_table)
    story.append(Spacer(1, 12))
    
    # 几何变换参数表
    story.append(Paragraph("3.2 几何变换参数", heading3_style))
    story.append(Spacer(1, 6))
    
    geo_data = [
        ['特效', '参数范围', '推荐值', '说明'],
        ['旋转角度', '-6 - +6度', '-3 - +3', '轻微旋转避免检测'],
        ['水平翻转', 'true/false', '随机', '随机水平镜像'],
        ['裁剪比例', '0 - 0.5', '0.1', '每边裁剪10%'],
    ]
    
    geo_table = Table(geo_data, colWidths=[1.2*inch, 1.3*inch, 0.9*inch, 2.1*inch])
    geo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(geo_table)
    story.append(PageBreak())
    
    # 模糊效果参数
    story.append(Paragraph("3.3 模糊效果参数", heading3_style))
    story.append(Spacer(1, 6))
    
    blur_data = [
        ['特效', '参数范围', '推荐值', '说明'],
        ['背景模糊', '0 - 100%', '3%', '顶部/底部/侧边模糊'],
        ['边缘模糊', 'true/false', 'true', '边缘模糊效果'],
        ['高斯模糊核', '1, 3, 5, 7', '3', '必须为正奇数'],
        ['高斯模糊间隔', '5 - 20帧', '15', '每隔N帧应用'],
    ]
    
    blur_table = Table(blur_data, colWidths=[1.2*inch, 1.3*inch, 0.9*inch, 2.1*inch])
    blur_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(blur_table)
    story.append(Spacer(1, 12))
    
    # 高级特效参数
    story.append(Paragraph("3.4 高级特效参数", heading3_style))
    story.append(Spacer(1, 6))
    
    advanced_data = [
        ['特效', '参数范围', '推荐值', '说明'],
        ['帧交换间隔', '5 - 20', '15', '每隔N帧交换帧'],
        ['颜色偏移范围', '0 - 10', '3', 'RGB通道偏移'],
        ['频域扰乱', '0.0 - 1.0', '0.0', '0表示禁用'],
        ['纹理噪声强度', '0 - 1', '0.5', '噪声强度'],
        ['淡入帧数', '10 - 30', '5', '开头淡入'],
        ['淡出帧数', '10 - 30', '20', '结尾淡出'],
    ]
    
    advanced_table = Table(advanced_data, colWidths=[1.2*inch, 1.3*inch, 0.9*inch, 2.1*inch])
    advanced_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(advanced_table)
    story.append(PageBreak())
    
    # 画中画参数
    story.append(Paragraph("3.5 画中画 (PIP) 参数", heading3_style))
    story.append(Spacer(1, 6))
    
    pip_data = [
        ['参数', '范围', '推荐值', '说明'],
        ['大小因子', '0.1 - 0.3', '0.15-0.25', 'PIP为原视频的15%-25%'],
        ['透明度', '0.05 - 0.15', '0.1', '透明度10%'],
        ['位置', '4个角落', '随机', '左上/右上/左下/右下'],
    ]
    
    pip_table = Table(pip_data, colWidths=[1.2*inch, 1.3*inch, 0.9*inch, 2.1*inch])
    pip_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(pip_table)
    story.append(PageBreak())
    
    # 4. 参数验证结果
    story.append(Paragraph("4. 参数验证结果", heading2_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("通过与行业标准项目对比，我们的参数设置验证结果如下：", normal_style))
    story.append(Spacer(1, 12))
    
    validation_data = [
        ['参数类别', '我们的设置', '行业标准', '结果'],
        ['饱和度', '0.9-1.15', '0.8-1.2 (推荐1.05)', '合理'],
        ['亮度', '-0.1 ~ 0.15', '-0.3~0.3 (推荐0.05)', '合理'],
        ['对比度', '0.9-1.15', '0.8-1.2 (推荐1.05)', '合理'],
        ['旋转角度', '-3 ~ +3度', '-6~6 (推荐-3~3)', '合理'],
        ['裁剪比例', '2%-8%', '0-50% (推荐10%)', '合理'],
        ['BGM音量', '10%', '10%', '合理'],
        ['特效数量', '3-5种', '3-5种', '合理'],
    ]
    
    validation_table = Table(validation_data, colWidths=[1.1*inch, 1.2*inch, 1.7*inch, 0.7*inch])
    validation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(validation_table)
    story.append(PageBreak())
    
    # 5. 最佳实践建议
    story.append(Paragraph("5. 最佳实践建议", heading2_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("建议 1：组合使用特效 - 每次生成变体时，确保包含：1种颜色调整 + 1-2种几何变换 + 1-2种高级特效", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("建议 2：保持参数轻度 - 旋转角度控制在正负3度以内，裁剪比例控制在2%-8%，颜色调整幅度不超过正负15%", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("建议 3：增加随机性 - 不同变体使用不同的特效组合，参数值在推荐范围内随机选择，画中画位置随机选择", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("建议 4：持续优化 - 关注平台算法更新，根据实际效果调整参数，重度去重考虑抽帧混合技术", normal_style))
    story.append(PageBreak())
    
    # 6. 参考项目
    story.append(Paragraph("6. 参考项目", heading2_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("video-mover - 361 stars | 64 forks - 全自动短视频搬运工具，支持自动下载、去重、AI生成标题+标签、上传。URL: https://github.com/toki-plus/video-mover", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("AB-Video-Deduplicator - 139 stars | 31 forks - 采用高帧率抽帧混合算法，以规避短视频平台查重。URL: https://github.com/toki-plus/AB-Video-Deduplicator", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("ai-mixed-cut - AI内容生产工具，通过解构-重构模式将爆款视频解构成创作素材库。URL: https://github.com/toki-plus/ai-mixed-cut", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("ai-ttv-workflow - AI驱动的文本转视频工具，支持AI文案提取、二创和翻译。URL: https://github.com/toki-plus/ai-ttv-workflow", normal_style))
    story.append(PageBreak())
    
    # 结论
    story.append(Paragraph("结论", heading2_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "通过对多个开源项目的深入研究和参数对比，我们确认当前的视觉特效参数设置符合行业最佳实践。"
        "关键要点：参数范围合理，既保证去重效果又不影响观看体验；组合策略有效，使用3-5种特效的组合能够有效规避平台检测；"
        "随机性充足，随机选择参数和特效增加了变体的多样性；持续优化空间，建议根据平台算法更新和实际效果持续调整参数。",
        normal_style
    ))
    story.append(Spacer(1, 30))
    story.append(Paragraph("---", normal_style))
    story.append(Paragraph("本报告由 Shorts Fission 系统自动生成", normal_style))
    
    # 生成 PDF
    doc.build(story)
    print("PDF 生成完成!")

if __name__ == "__main__":
    create_pdf()
