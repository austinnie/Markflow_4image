"""
MarkFlow GUI 启动器 - 统一管理所有技能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import sys
import io
import json
import os
import subprocess
import platform
from datetime import datetime
from typing import Dict, Any, Optional, List

# 导入技能核心
from markflow.core.executor import SkillExecutor


class MarkFlowLauncher:
    """MarkFlow 图形化启动器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 MarkFlow - 技能管理平台")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)
        
        # 设置颜色主题
        self.colors = {
            'bg': '#f0f2f5',
            'card': '#ffffff',
            'primary': '#4a90d9',
            'success': '#27ae60',
            'error': '#e74c3c',
            'warn': '#f39c12',
            'text': '#2c3e50',
            'text_light': '#7f8c8d'
        }
        
        # 技能执行器
        self.executor = SkillExecutor()
        self.skill_dir = Path("./skills")
        if self.skill_dir.exists():
            self.executor.registry.load_from_directory(self.skill_dir)
        
        self.current_skill = None
        self.current_skill_metadata = None
        self.param_widgets = {}
        self.running = False
        
        self._setup_ui()
        self._load_skills()
    
    def _setup_ui(self):
        """设置 UI 布局"""
        # 配置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== 顶部：标题和工具栏 =====
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 标题
        title_label = ttk.Label(top_frame, text="🚀 MarkFlow 技能管理", 
                                font=('Microsoft YaHei', 18, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # 版本信息
        version_label = ttk.Label(top_frame, text="v0.1.0", 
                                  font=('Arial', 10), foreground='gray')
        version_label.pack(side=tk.LEFT, padx=10)
        
        # 工具栏
        toolbar = ttk.Frame(top_frame)
        toolbar.pack(side=tk.RIGHT)
        
        ttk.Button(toolbar, text="🔄 刷新技能", 
                  command=self._load_skills).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 打开技能目录", 
                  command=self._open_skill_dir).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="❓ 帮助", 
                  command=self._show_help).pack(side=tk.LEFT, padx=2)
        
        # ===== 主内容：左右布局 =====
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：技能列表
        left_frame = ttk.Frame(content_frame, width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # 技能列表标题
        list_title = ttk.Label(left_frame, text="📦 已安装技能", 
                               font=('Microsoft YaHei', 12, 'bold'))
        list_title.pack(anchor=tk.W, pady=(0, 5))
        
        # 技能列表（带滚动条）
        list_container = ttk.Frame(left_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.skill_listbox = tk.Listbox(list_container, 
                                        font=('Consolas', 10),
                                        selectmode=tk.SINGLE,
                                        bg='white',
                                        fg='#2c3e50',
                                        selectbackground='#4a90d9',
                                        selectforeground='white',
                                        relief=tk.FLAT,
                                        highlightthickness=0)
        self.skill_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, 
                                  command=self.skill_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.skill_listbox.config(yscrollcommand=scrollbar.set)
        
        self.skill_listbox.bind('<<ListboxSelect>>', self._on_skill_select)
        
        # 技能数量
        self.skill_count_label = ttk.Label(left_frame, text="", 
                                           font=('Arial', 9), foreground='gray')
        self.skill_count_label.pack(anchor=tk.W, pady=(5, 0))
        
        # 右侧：技能详情和操作
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # ===== 技能信息 =====
        info_frame = ttk.LabelFrame(right_frame, text="📋 技能信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.skill_name_label = ttk.Label(info_frame, text="请选择一个技能", 
                                          font=('Microsoft YaHei', 14, 'bold'))
        self.skill_name_label.pack(anchor=tk.W)
        
        self.skill_desc_label = ttk.Label(info_frame, text="", 
                                          font=('Arial', 10), foreground='gray')
        self.skill_desc_label.pack(anchor=tk.W)
        
        self.skill_deps_label = ttk.Label(info_frame, text="", 
                                          font=('Arial', 9), foreground='#7f8c8d')
        self.skill_deps_label.pack(anchor=tk.W)
        
        # ===== 参数配置 =====
        param_frame = ttk.LabelFrame(right_frame, text="⚙️ 参数配置", padding="10")
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.param_container = ttk.Frame(param_frame)
        self.param_container.pack(fill=tk.X)
        
        # 初始提示
        self.no_skill_label = ttk.Label(self.param_container, 
                                        text="👈 请从左侧选择要执行的技能", 
                                        font=('Arial', 11), foreground='gray')
        self.no_skill_label.pack(pady=20)
        
        # ===== 操作按钮 =====
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.execute_btn = ttk.Button(btn_frame, text="▶️ 执行技能", 
                                      command=self._execute_skill,
                                      state=tk.DISABLED,
                                      width=15)
        self.execute_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(btn_frame, text="🗑️ 清空输出", 
                                    command=self._clear_output,
                                    width=12)
        self.clear_btn.pack(side=tk.LEFT)
        
        # ===== 输出区域 =====
        output_frame = ttk.LabelFrame(right_frame, text="📋 执行日志", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, 
                                                     font=('Consolas', 9),
                                                     wrap=tk.WORD,
                                                     bg='#1e1e2e',
                                                     fg='#cdd6f4',
                                                     insertbackground='white',
                                                     relief=tk.FLAT,
                                                     highlightthickness=0)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置文本标签
        self.output_text.tag_config('info', foreground='#89b4fa')
        self.output_text.tag_config('success', foreground='#a6e3a1')
        self.output_text.tag_config('error', foreground='#f38ba8')
        self.output_text.tag_config('warn', foreground='#f9e2af')
        self.output_text.tag_config('highlight', foreground='#cba6f7')
        
        # ===== 底部状态栏 =====
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Separator(status_frame).pack(fill=tk.X, pady=(0, 5))
        
        self.status_label = ttk.Label(status_frame, text="✅ 就绪", 
                                      font=('Arial', 9))
        self.status_label.pack(side=tk.LEFT)
        
        # 日志输出初始信息
        self._log("🚀 MarkFlow GUI 启动成功", 'highlight')
        self._log(f"📁 技能目录: {self.skill_dir.absolute()}", 'info')
        self._log("💡 请从左侧选择技能开始使用\n", 'info')
    
    def _load_skills(self):
        """加载技能列表"""
        self.skill_listbox.delete(0, tk.END)
        
        # ✅ 强制清除缓存
        self.executor.registry.clear()

        # ========== 新增：刷新模型索引 ==========
        try:
            from markflow.utils.model_config import refresh_index
            refresh_index()
            self._log("🔄 模型索引已刷新", 'info')
        except Exception as e:
            self._log(f"⚠️ 刷新模型索引失败: {e}", 'warn')
        
        
        # 重新加载技能
        if self.skill_dir.exists():
            self.executor.registry.load_from_directory(self.skill_dir)
        
        skills = self.executor.list_skills()
        
        print("=" * 50)
        print(f"📦 加载技能，共 {len(skills)} 个")
        for name, meta in skills.items():
            inputs = meta.get('inputs', [])
            print(f"  - {name}: {len(inputs)} 个参数")
            for inp in inputs:
                print(f"      {inp.get('name')} ({inp.get('type')})")
        print("=" * 50)
        
        if not skills:
            self.skill_listbox.insert(tk.END, "⚠️ 没有找到技能")
            self.skill_count_label.config(text="请先用 build 构建技能")
            return
        
        # 初始化 _metadata
        if not hasattr(self.skill_listbox, '_metadata'):
            self.skill_listbox._metadata = {}
        
        for name in sorted(skills.keys()):
            metadata = skills[name]
            self.skill_listbox.insert(tk.END, name)
            self.skill_listbox._metadata[name] = metadata
        
        self.skill_count_label.config(text=f"共 {len(skills)} 个技能")
        self._log(f"🔄 已加载 {len(skills)} 个技能", 'info')
    
    def _on_skill_select(self, event):
        """技能选择事件"""
        selection = self.skill_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        skill_name = self.skill_listbox.get(index)
        
        # 直接从 _metadata 获取
        metadata = getattr(self.skill_listbox, '_metadata', {}).get(skill_name, {})
        
        print(f"\n🔍 选择技能: {skill_name}")
        print(f"   metadata: {metadata.keys()}")
        print(f"   inputs: {metadata.get('inputs', [])}")
        
        self.current_skill = skill_name
        self.current_skill_metadata = metadata
        
        # 更新技能信息
        self.skill_name_label.config(text=f"📌 {skill_name}")
        
        desc = metadata.get('description', '无描述')
        self.skill_desc_label.config(text=desc)
        
        deps = metadata.get('dependencies', [])
        self.skill_deps_label.config(text=f"依赖: {', '.join(deps) if deps else '无'}")
        
        # 生成参数输入
        self._build_param_inputs(metadata)
        
        # 启用执行按钮
        self.execute_btn.config(state=tk.NORMAL)
        
        self._log(f"✅ 已选择技能: {skill_name}", 'success')
    

    def _build_param_inputs(self, metadata: Dict):
        """动态生成参数输入控件（分组折叠）"""
        # 清空旧控件
        for widget in self.param_container.winfo_children():
            widget.destroy()
        
        self.param_widgets = {}
        inputs = metadata.get('inputs', [])
        
        if not inputs:
            label = ttk.Label(self.param_container, 
                              text="⚠️ 此技能没有定义参数", 
                              font=('Arial', 10), foreground='orange')
            label.pack(anchor=tk.W, pady=5)
            return
        
        # 定义参数分组
        skill_name = self.current_skill or ''
        groups = self._get_param_groups(skill_name, inputs)
        
        # 渲染分组
        for group_name, group_inputs in groups.items():
            # 分组标题（可点击折叠）
            group_frame = ttk.Frame(self.param_container)
            group_frame.pack(fill=tk.X, pady=(5, 0))
            
            # 判断是否有必填参数
            has_required = any(inp.get('required', False) for inp in group_inputs)
            is_expanded = has_required
            
            # 分组标题按钮
            toggle_btn = ttk.Button(group_frame, text=f"▼ {group_name}",
                                    command=lambda f=group_frame: self._toggle_group(f),
                                    width=20)
            toggle_btn.pack(side=tk.LEFT)
            
            # 分组内容容器
            content_frame = ttk.Frame(self.param_container)
            content_frame.pack(fill=tk.X, padx=(20, 0))
            
            # 存储引用 - 直接设置为属性
            content_frame._is_expanded = is_expanded
            content_frame._toggle_btn = toggle_btn
            
            if not is_expanded:
                content_frame.pack_forget()
                toggle_btn.config(text=f"▶ {group_name}")
            
            # 渲染参数
            for inp in group_inputs:
                self._render_param(content_frame, inp)
            
    def _get_param_groups(self, skill_name: str, inputs: List[Dict]) -> Dict[str, List[Dict]]:
        """获取参数分组"""
        groups = {}
        
        # 根据技能名称定义分组规则
        if skill_name == 'Sdimagegenerator':
            groups = {
                '📌 基础参数': [],
                '📐 尺寸参数': [],
                '⚙️ 生成参数': [],
                '📁 输出参数': []
            }
            for inp in inputs:
                name = inp.get('name', '')
                if name in ['prompt', 'negative_prompt', 'model_name']:
                    groups['📌 基础参数'].append(inp)
                elif name in ['width', 'height']:
                    groups['📐 尺寸参数'].append(inp)
                elif name in ['steps', 'cfg_scale', 'seed', 'batch_size', 'scheduler']:
                    groups['⚙️ 生成参数'].append(inp)
                else:
                    groups['📁 输出参数'].append(inp)
        
        elif skill_name == 'ImageToolbox':
            groups = {
                '📌 必填参数': [],
                '🖼️ 图片操作': [],
                '💧 水印设置': [],
                '✂️ 裁剪/旋转': [],
                '🎨 颜色调整': [],
                '📁 输出参数': []
            }
            for inp in inputs:
                name = inp.get('name', '')
                if name in ['source_dir', 'operations']:
                    groups['📌 必填参数'].append(inp)
                elif name in ['target_format', 'width', 'height', 'quality']:
                    groups['🖼️ 图片操作'].append(inp)
                elif name in ['watermark_text', 'watermark_position', 'watermark_opacity']:
                    groups['💧 水印设置'].append(inp)
                elif name in ['crop_x', 'crop_y', 'crop_width', 'crop_height', 'rotate_angle', 'flip_direction']:
                    groups['✂️ 裁剪/旋转'].append(inp)
                elif name in ['brightness', 'contrast', 'saturation']:
                    groups['🎨 颜色调整'].append(inp)
                else:
                    groups['📁 输出参数'].append(inp)
        
        elif skill_name == 'ImageViewer':
            groups = {
                '📌 必填参数': [],
                '🔍 浏览参数': [],
                '🎞️ 幻灯片参数': [],
                '📤 导出参数': []
            }
            for inp in inputs:
                name = inp.get('name', '')
                if name in ['action', 'file']:
                    groups['📌 必填参数'].append(inp)
                elif name in ['source_dir', 'view_mode', 'sort_by', 'sort_order', 'filter', 'thumbnail_size']:
                    groups['🔍 浏览参数'].append(inp)
                elif name in ['slideshow_interval', 'fullscreen']:
                    groups['🎞️ 幻灯片参数'].append(inp)
                elif name in ['export_format', 'export_quality', 'export_size']:
                    groups['📤 导出参数'].append(inp)
                else:
                    groups['📤 导出参数'].append(inp)
        
        elif skill_name == 'DocGenerator':
            groups = {
                '📌 必填参数': [],
                '📄 文档参数': []
            }
            for inp in inputs:
                if inp.get('required', False):
                    groups['📌 必填参数'].append(inp)
                else:
                    groups['📄 文档参数'].append(inp)
        
        elif skill_name == 'NovelWriterOllama':
            groups = {
                '📌 必填参数': [],
                '📝 写作参数': []
            }
            for inp in inputs:
                if inp.get('required', False):
                    groups['📌 必填参数'].append(inp)
                else:
                    groups['📝 写作参数'].append(inp)
        
        else:
            # 默认：按必填/可选分组
            groups = {
                '📌 必填参数': [],
                '🔧 可选参数': []
            }
            for inp in inputs:
                if inp.get('required', False):
                    groups['📌 必填参数'].append(inp)
                else:
                    groups['🔧 可选参数'].append(inp)
        
        # 移除空分组
        return {k: v for k, v in groups.items() if v}
    

    def _toggle_group(self, content_frame):
        """切换分组折叠状态"""
        if hasattr(content_frame, '_is_expanded') and content_frame._is_expanded:
            content_frame.pack_forget()
            content_frame._is_expanded = False
            if hasattr(content_frame, '_toggle_btn'):
                # 获取当前文本，去掉前面的图标
                current_text = content_frame._toggle_btn.cget('text')
                # 如果以 ▼ 开头，改为 ▶
                if current_text.startswith('▼'):
                    content_frame._toggle_btn.config(text=f"▶ {current_text[2:]}")
                else:
                    content_frame._toggle_btn.config(text=f"▶ {current_text}")
        else:
            content_frame.pack(fill=tk.X, padx=(20, 0))
            content_frame._is_expanded = True
            if hasattr(content_frame, '_toggle_btn'):
                current_text = content_frame._toggle_btn.cget('text')
                if current_text.startswith('▶'):
                    content_frame._toggle_btn.config(text=f"▼ {current_text[2:]}")
                else:
                    content_frame._toggle_btn.config(text=f"▼ {current_text}")
                
    def _render_param(self, parent, inp: Dict):
        """渲染单个参数"""
        name = inp.get('name', '')
        desc = inp.get('description', '')
        required = inp.get('required', False)
        param_type = inp.get('type', 'string')
        
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        # 标签
        label_text = name
        if required:
            label_text += " *"
        label = ttk.Label(frame, text=label_text, width=18, anchor=tk.W,
                         font=('Arial', 9))
        label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 输入框
        if param_type in ['integer', 'float']:
            var = tk.StringVar(value='')
            entry = ttk.Entry(frame, textvariable=var, width=30)
            entry.pack(side=tk.LEFT)
            self.param_widgets[name] = {'var': var, 'type': param_type}
        elif param_type == 'boolean':
            var = tk.BooleanVar(value=False)
            check = ttk.Checkbutton(frame, variable=var)
            check.pack(side=tk.LEFT)
            self.param_widgets[name] = {'var': var, 'type': 'boolean'}
        else:
            var = tk.StringVar(value='')
            entry = ttk.Entry(frame, textvariable=var, width=30)
            entry.pack(side=tk.LEFT)
            self.param_widgets[name] = {'var': var, 'type': 'string'}
        
        # 描述（缩短）
        if desc:
            short_desc = desc[:35] + '...' if len(desc) > 35 else desc
            ttk.Label(frame, text=short_desc, font=('Arial', 8), 
                      foreground='gray').pack(side=tk.LEFT, padx=5)
    
    def _get_params(self) -> Dict:
        """获取所有参数值"""
        params = {}
        for name, widget in self.param_widgets.items():
            val = widget['var'].get()
            if widget['type'] == 'integer':
                try:
                    val = int(val) if val else None
                except:
                    val = None
            elif widget['type'] == 'float':
                try:
                    val = float(val) if val else None
                except:
                    val = None
            elif widget['type'] == 'boolean':
                val = bool(val)
            if val is not None and val != '':
                params[name] = val
        return params
    
    def _execute_skill(self):
        """执行选中的技能"""
        if not self.current_skill or self.running:
            return
        
        # 获取参数
        params = self._get_params()
        
        # 禁用按钮
        self.running = True
        self.execute_btn.config(state=tk.DISABLED, text="⏳ 执行中...")
        self.status_label.config(text="⏳ 正在执行...")
        
        self._log(f"\n{'='*60}", 'highlight')
        self._log(f"🚀 执行技能: {self.current_skill}", 'highlight')
        if params:
            self._log(f"📋 参数: {json.dumps(params, ensure_ascii=False, indent=2)}", 'info')
        self._log('-'*60, 'info')
        
        # 在新线程中执行（避免UI卡死）
        def run():
            try:
                result = self.executor.execute(self.current_skill, **params)
                self.root.after(0, lambda: self._show_result(result))
            except Exception as e:
                self.root.after(0, lambda: self._show_error(str(e)))
        
        threading.Thread(target=run, daemon=True).start()
    
    def _show_result(self, result: Dict):
        """显示执行结果"""
        self.running = False
        self.execute_btn.config(state=tk.NORMAL, text="▶️ 执行技能")
        
        if result.get('status') == 'success':
            self.status_label.config(text="✅ 执行成功")
            self._log("✅ 执行成功!", 'success')
            
            result_data = result.get('result', {})
            if result_data:
                self._log("\n📊 结果:", 'highlight')
                for key, value in result_data.items():
                    if isinstance(value, (list, dict)):
                        value_str = json.dumps(value, ensure_ascii=False, indent=2)
                        if len(value_str) > 500:
                            value_str = value_str[:500] + "..."
                        self._log(f"  {key}: {value_str}", 'info')
                    else:
                        self._log(f"  {key}: {value}", 'info')
            else:
                self._log("⚠️ 没有返回结果数据", 'warn')
        else:
            self.status_label.config(text="❌ 执行失败")
            error = result.get('error', '未知错误')
            self._log(f"\n❌ 执行失败: {error}", 'error')
            messagebox.showerror("执行失败", error)
        
        self._log(f"\n{'='*60}\n", 'highlight')
    
    def _show_error(self, error: str):
        """显示错误"""
        self.running = False
        self.execute_btn.config(state=tk.NORMAL, text="▶️ 执行技能")
        self.status_label.config(text="❌ 执行失败")
        self._log(f"\n❌ 错误: {error}", 'error')
        messagebox.showerror("执行失败", error)
    
    def _log(self, message: str, tag: str = 'info'):
        """输出日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        self.output_text.insert(tk.END, line, tag)
        self.output_text.see(tk.END)
        self.root.update()
    
    def _clear_output(self):
        """清空输出"""
        self.output_text.delete(1.0, tk.END)
        self._log("🗑️ 输出已清空", 'warn')
    
    def _open_skill_dir(self):
        """打开技能目录"""
        skill_path = self.skill_dir.absolute()
        if not skill_path.exists():
            skill_path.mkdir(parents=True)
        
        if platform.system() == 'Windows':
            os.startfile(str(skill_path))
        elif platform.system() == 'Darwin':
            subprocess.run(['open', str(skill_path)])
        else:
            subprocess.run(['xdg-open', str(skill_path)])
        
        self._log(f"📂 打开技能目录: {skill_path}", 'info')
    
    def _show_help(self):
        """显示帮助"""
        help_text = """🚀 MarkFlow GUI 使用帮助

📌 基本操作：
  1. 从左侧列表选择技能
  2. 在右侧填写参数
  3. 点击"执行技能"运行

📦 技能说明：
  - 每个技能有独立的输入参数
  - 必填参数标记为 *
  - 参数类型包括: string, integer, float, boolean

📋 执行日志：
  - 显示执行过程和结果
  - 支持清空和滚动查看

💡 提示：
  - 技能通过 build 命令构建
  - 技能文件保存在 ./skills/ 目录
  - 点击"打开技能目录"查看"""
        
        messagebox.showinfo("MarkFlow 帮助", help_text)
    
    def run(self):
        """运行 GUI"""
        self.root.mainloop()


def main():
    """启动 GUI"""
    app = MarkFlowLauncher()
    app.run()


if __name__ == "__main__":
    main()