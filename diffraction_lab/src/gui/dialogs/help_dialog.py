import os
import re
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLineEdit,
    QPushButton, QLabel, QSplitter, QWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel


def _get_help_dir() -> str:
    """获取帮助文档目录，兼容开发环境和 PyInstaller 打包环境"""
    base_path = getattr(sys, '_MEIPASS', None)
    if base_path is not None:
        return os.path.join(base_path, 'assets', 'help')
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))),
        'assets', 'help'
    )


HELP_DIR = _get_help_dir()

HELP_PAGES = [
    ('guide', '使用指南', 'guide.md'),
    ('parameters', '参数说明', 'parameters.md'),
    ('chromatic', '彩色衍射说明', 'chromatic.md'),
    ('advanced', '高级功能说明', 'advanced.md'),
]

DARK_CSS = """
:root {
    --bg-primary: #1a1b2e;
    --bg-secondary: #1e1f38;
    --bg-tertiary: #252640;
    --border-color: #3a3b5e;
    --border-light: #2a2b4e;
    --text-primary: #d8d8e8;
    --text-secondary: #a0a0c0;
    --accent: #7c8cf8;
    --accent-light: #9aa4ff;
    --accent-hover: #8c9cff;
    --code-bg: #252640;
    --code-color: #a0b0ff;
    --table-hover: #252640;
}

body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 15px;
    line-height: 1.8;
    padding: 24px 36px;
    margin: 0;
}

h1 {
    color: var(--accent-light);
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 10px;
    margin-top: 28px;
    margin-bottom: 16px;
    font-size: 22px;
    letter-spacing: 0.5px;
}

h2 {
    color: var(--accent-hover);
    border-bottom: 1px solid var(--border-light);
    padding-bottom: 8px;
    margin-top: 24px;
    margin-bottom: 12px;
    font-size: 18px;
}

h3 {
    color: var(--accent);
    margin-top: 20px;
    margin-bottom: 10px;
    font-size: 16px;
}

p { margin: 10px 0; }

table {
    border-collapse: collapse;
    margin: 16px 0;
    width: 100%;
    font-size: 14px;
}

th {
    background-color: var(--bg-tertiary);
    color: var(--accent-light);
    padding: 10px 14px;
    border: 1px solid var(--border-color);
    text-align: left;
    font-weight: 600;
}

td {
    padding: 10px 14px;
    border: 1px solid var(--border-color);
    vertical-align: top;
}

tr:nth-child(even) { background-color: var(--bg-secondary); }
tr:hover { background-color: var(--table-hover); }

code {
    background-color: var(--code-bg);
    color: var(--code-color);
    padding: 2px 8px;
    border-radius: 4px;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 13px;
}

pre {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid var(--border-color);
    line-height: 1.5;
}

pre code { background: none; padding: 0; }

blockquote {
    border-left: 4px solid var(--accent);
    margin: 16px 0;
    padding: 10px 20px;
    background-color: var(--bg-secondary);
    border-radius: 0 6px 6px 0;
}

hr {
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 24px 0;
}

ul, ol { padding-left: 28px; }
li { margin: 6px 0; }

mjx-container {
    color: var(--text-primary) !important;
}
"""

LIGHT_CSS = """
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f6fa;
    --bg-tertiary: #e8e9f5;
    --border-color: #d0d2e0;
    --border-light: #e0e2f0;
    --text-primary: #2c3e50;
    --text-secondary: #5a6a80;
    --accent: #5b6abf;
    --accent-light: #4a5abf;
    --accent-hover: #6c7bd0;
    --code-bg: #f0f1f5;
    --code-color: #5b6abf;
    --table-hover: #e8e9f0;
}

body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 15px;
    line-height: 1.8;
    padding: 24px 36px;
    margin: 0;
}

h1 {
    color: var(--accent-light);
    border-bottom: 2px solid var(--border-light);
    padding-bottom: 10px;
    margin-top: 28px;
    margin-bottom: 16px;
    font-size: 22px;
    letter-spacing: 0.5px;
}

h2 {
    color: var(--accent);
    border-bottom: 1px solid var(--border-light);
    padding-bottom: 8px;
    margin-top: 24px;
    margin-bottom: 12px;
    font-size: 18px;
}

h3 {
    color: var(--accent-hover);
    margin-top: 20px;
    margin-bottom: 10px;
    font-size: 16px;
}

p { margin: 10px 0; }

table {
    border-collapse: collapse;
    margin: 16px 0;
    width: 100%;
    font-size: 14px;
}

th {
    background-color: var(--bg-tertiary);
    color: var(--accent-light);
    padding: 10px 14px;
    border: 1px solid var(--border-color);
    text-align: left;
    font-weight: 600;
}

td {
    padding: 10px 14px;
    border: 1px solid var(--border-color);
    vertical-align: top;
}

tr:nth-child(even) { background-color: var(--bg-secondary); }
tr:hover { background-color: var(--table-hover); }

code {
    background-color: var(--code-bg);
    color: var(--code-color);
    padding: 2px 8px;
    border-radius: 4px;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 13px;
}

pre {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid var(--border-color);
    line-height: 1.5;
}

pre code { background: none; padding: 0; }

blockquote {
    border-left: 4px solid var(--accent);
    margin: 16px 0;
    padding: 10px 20px;
    background-color: var(--bg-secondary);
    border-radius: 0 6px 6px 0;
}

hr {
    border: none;
    border-top: 1px solid var(--border-light);
    margin: 24px 0;
}

ul, ol { padding-left: 28px; }
li { margin: 6px 0; }

mjx-container {
    color: var(--text-primary) !important;
}
"""

MATHJAX_CONFIG = """
<script>
MathJax = {
    tex: {
        inlineMath: [['$', '$']],
        displayMath: [['$$', '$$']],
        processEscapes: true
    },
    svg: {
        fontCache: 'global'
    },
    startup: {
        ready: function() {
            MathJax.startup.defaultReady();
        }
    }
};
</script>
<script id="MathJax-script" async
    src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
</script>
"""

MATHJAX_OFFLINE = """
<script>
MathJax = {
    tex: {
        inlineMath: [['$', '$']],
        displayMath: [['$$', '$$']],
        processEscapes: true
    },
    svg: {
        fontCache: 'global'
    }
};
</script>
<script id="MathJax-script" async
    src="file:///""" + os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'assets', 'js', 'mathjax', 'tex-svg.js').replace('\\', '/') + """">
</script>
"""


def _markdown_to_html_body(md_text: str) -> str:
    try:
        import markdown
        html = markdown.markdown(
            md_text,
            extensions=['tables', 'fenced_code', 'toc'],
            output_format='html5'
        )
        return html
    except ImportError:
        return _simple_markdown_to_html(md_text)


def _simple_markdown_to_html(text: str) -> str:
    lines = text.split('\n')
    html_lines = []
    in_code_block = False
    in_table = False
    table_rows = []

    for line in lines:
        if line.strip().startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                html_lines.append('<pre><code>')
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(line)
            continue

        stripped = line.strip()

        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            content = stripped.lstrip('#').strip()
            content = _simple_format(content)
            html_lines.append(f'<h{min(level, 6)}>{content}</h{min(level, 6)}>')
            continue

        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                continue
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        elif in_table:
            html_lines.append('<table>')
            for i, row in enumerate(table_rows):
                tag = 'th' if i == 0 else 'td'
                html_lines.append('<tr>' + ''.join(
                    f'<{tag}>{_simple_format(c)}</{tag}>' for c in row) + '</tr>')
            html_lines.append('</table>')
            in_table = False
            table_rows = []

        if stripped == '---':
            html_lines.append('<hr>')
            continue

        if stripped.startswith('- ') or stripped.startswith('* '):
            content = _simple_format(stripped[2:])
            html_lines.append(f'<ul><li>{content}</li></ul>')
            continue

        if stripped:
            html_lines.append(f'<p>{_simple_format(stripped)}</p>')

    if in_table and table_rows:
        html_lines.append('<table>')
        for i, row in enumerate(table_rows):
            tag = 'th' if i == 0 else 'td'
            html_lines.append('<tr>' + ''.join(
                f'<{tag}>{_simple_format(c)}</{tag}>' for c in row) + '</tr>')
        html_lines.append('</table>')

    return '\n'.join(html_lines)


def _simple_format(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def _build_full_html(body_html: str, css: str, is_dark: bool) -> str:
    bg_color = "#1a1b2e" if is_dark else "#ffffff"
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{css}</style>
{MATHJAX_CONFIG}
</head>
<body style="background-color: {bg_color};">
{body_html}
</body>
</html>"""


class HelpDialog(QDialog):

    def __init__(self, parent=None, is_dark: bool = True):
        super().__init__(parent)
        self.setWindowTitle("帮助文档")
        self.setMinimumSize(950, 680)
        self.resize(1100, 750)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self._is_dark = is_dark
        self._pages = {}
        self._current_page_id = None
        self._setup_ui()
        self._load_pages()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        search_bar = QWidget()
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(12, 10, 12, 6)

        search_label = QLabel("搜索:")
        search_label.setFixedWidth(36)
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(160)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        splitter.addWidget(self.nav_list)

        self.web_view = QWebEngineView()
        self.web_view.page().setBackgroundColor(
            __import__('PyQt6.QtGui', fromlist=['QColor']).QColor(
                26, 27, 46) if self._is_dark else
            __import__('PyQt6.QtGui', fromlist=['QColor']).QColor(
                255, 255, 255)
        )
        splitter.addWidget(self.web_view)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        bottom_bar = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(12, 6, 12, 10)

        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)
        layout.addWidget(bottom_bar)

    def _load_pages(self):
        for page_id, title, filename in HELP_PAGES:
            filepath = os.path.join(HELP_DIR, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    html_body = _markdown_to_html_body(md_content)
                    self._pages[page_id] = {
                        'title': title,
                        'html_body': html_body,
                        'md': md_content,
                    }
                    item = QListWidgetItem(title)
                    item.setData(Qt.ItemDataRole.UserRole, page_id)
                    self.nav_list.addItem(item)
                except Exception as e:
                    self._pages[page_id] = {
                        'title': title,
                        'html_body': f'<p>加载帮助文件失败: {e}</p>',
                        'md': '',
                    }
                    item = QListWidgetItem(title)
                    item.setData(Qt.ItemDataRole.UserRole, page_id)
                    self.nav_list.addItem(item)

        if self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)

    def _on_nav_changed(self, row: int):
        if row < 0 or row >= self.nav_list.count():
            return
        item = self.nav_list.item(row)
        page_id = item.data(Qt.ItemDataRole.UserRole)
        self._show_page(page_id)

    def _show_page(self, page_id: str):
        page = self._pages.get(page_id)
        if not page:
            return

        self._current_page_id = page_id
        css = DARK_CSS if self._is_dark else LIGHT_CSS
        full_html = _build_full_html(page['html_body'], css, self._is_dark)
        self.web_view.setHtml(full_html)
        self.status_label.setText(page['title'])

    def _on_search(self, text: str):
        text = text.strip().lower()
        if not text:
            return

        best_page = None
        best_score = -1

        for page_id, page in self._pages.items():
            md_lower = page['md'].lower()
            score = 0
            if text in page['title'].lower():
                score += 100
            idx = md_lower.find(text)
            if idx >= 0:
                score += 50
                count = md_lower.count(text)
                score += min(count, 20)
            if score > best_score:
                best_score = score
                best_page = page_id

        if best_page:
            for i in range(self.nav_list.count()):
                item = self.nav_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == best_page:
                    self.nav_list.setCurrentRow(i)
                    break

            self.web_view.findText(text)

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        bg = __import__('PyQt6.QtGui', fromlist=['QColor']).QColor
        self.web_view.page().setBackgroundColor(
            bg(26, 27, 46) if is_dark else bg(255, 255, 255))
        if self._current_page_id:
            self._show_page(self._current_page_id)
