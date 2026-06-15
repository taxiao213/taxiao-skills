#!/usr/bin/env python3
"""
HTML 转微信复制粘贴版（保留全部样式）

与 html_to_wechat.py（API版）不同，本转换器：
1. 将 <style> 中的 CSS 转为内联 style（微信编辑器会剥离 <style> 标签）
2. 将 <div> 转为 <section>（微信编辑器原生使用 <section>）
3. 保留所有 CSS 属性（flex, grid, box-shadow 等——复制粘贴路径支持）
4. 解析 CSS 变量 var(--xxx) 为实际值
5. 移除 <head>, <body> 等无关标签

用法:
    python3 html_to_copy.py "input.html" -o "output.html"
"""

import re
import sys
import os
from html.parser import HTMLParser


CSS_VARS = {
    "--blue-primary": "#1976D2",
    "--blue-dark": "#1565C0",
    "--blue-mid": "#2196F3",
    "--blue-light": "#64B5F6",
    "--blue-pale": "#BBDEFB",
    "--blue-bg": "#E3F2FD",
    "--blue-white": "#F5F9FF",
    "--white": "#FFFFFF",
    "--gray-50": "#FAFBFC",
    "--gray-100": "#F0F2F5",
    "--gray-200": "#E4E7EB",
    "--gray-400": "#9CA3AF",
    "--gray-600": "#4B5563",
    "--gray-800": "#1F2937",
    "--text-primary": "#1A2332",
    "--text-secondary": "#4A5568",
    "--text-muted": "#718096",
    "--border": "#E2E8F0",
    "--shadow-sm": "0 1px 3px rgba(25,118,210,0.06)",
    "--shadow-md": "0 4px 16px rgba(25,118,210,0.08)",
    "--shadow-lg": "0 8px 32px rgba(25,118,210,0.1)",
}


def resolve_css_vars(css_str: str) -> str:
    def var_replacer(m):
        var_name = m.group(1).strip()
        fallback = m.group(2).strip() if m.group(2) else None
        return CSS_VARS.get(var_name, fallback or "")
    return re.sub(r'var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\s*\)', var_replacer, css_str)


class CSSRule:
    def __init__(self, selector, declarations):
        self.raw_selector = selector.strip()
        self.declarations = resolve_css_vars(declarations.strip())
        self.selector_paths = self._parse(self.raw_selector)

    def _parse(self, selector):
        paths = []
        for sel in selector.split(','):
            sel = sel.strip()
            if not sel: continue
            levels = []
            for part in sel.split():
                tag, classes, pseudo = None, [], None
                if ':' in part:
                    part, pseudo = part.split(':', 1)
                if part.startswith('.'):
                    classes = part[1:].split('.')
                elif '.' in part:
                    tag = part.split('.')[0]
                    classes = part.split('.')[1:]
                else:
                    tag = part
                levels.append({'tag': tag, 'classes': classes, 'pseudo': pseudo})
            paths.append(levels)
        return paths


def parse_css_rules(css_text):
    rules = []
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
    # 移除 @media 块
    def remove_media(text):
        result, i = [], 0
        while i < len(text):
            if text[i:i+7] == '@media ':
                bs = text.find('{', i)
                if bs == -1:
                    result.append(text[i:]); break
                depth, j = 0, bs
                while j < len(text):
                    if text[j] == '{': depth += 1
                    elif text[j] == '}':
                        depth -= 1
                        if depth == 0: break
                    j += 1
                i = j + 1
            else:
                result.append(text[i]); i += 1
        return ''.join(result)
    css_text = remove_media(css_text)
    for m in re.finditer(r'([^{]+)\{([^}]*)\}', css_text):
        sel, decl = m.group(1).strip(), m.group(2).strip()
        if sel.startswith('@'): continue
        if decl: rules.append(CSSRule(sel, decl))
    return rules


def merge_style(existing, new_style):
    if not existing: return new_style
    if not new_style: return existing
    props = {}
    for s in (existing, new_style):
        for prop in s.split(';'):
            prop = prop.strip()
            if ':' in prop:
                k, v = prop.split(':', 1)
                props[k.strip()] = v.strip()
    return ';'.join(f"{k}:{v}" for k, v in props.items()) + ';'


class CopyHTMLConverter(HTMLParser):
    def __init__(self, css_rules):
        super().__init__()
        self.css_rules = css_rules
        self.output = []
        self.stack = []
        self._in_style = self._in_head = self._in_script = False
        self._capture = False

    def _match(self, sel_levels, path):
        if len(sel_levels) > len(path): return False
        if len(sel_levels) == 1:
            s, e = sel_levels[0], path[-1]
            if s['tag'] and s['tag'] != e['tag']: return False
            if s['classes'] and not all(c in e['classes'] for c in s['classes']): return False
            if not self._check_pseudo(s.get('pseudo'), e): return False
            return True
        # 多层：最后一个必须匹配当前元素
        ls, le = sel_levels[-1], path[-1]
        if ls['tag'] and ls['tag'] != le['tag']: return False
        if ls['classes'] and not all(c in le['classes'] for c in ls['classes']): return False
        if not self._check_pseudo(ls.get('pseudo'), le): return False
        si, pi = len(sel_levels) - 2, len(path) - 2
        while si >= 0 and pi >= 0:
            s, e = sel_levels[si], path[pi]
            ok = True
            if s['tag'] and s['tag'] != e['tag']: ok = False
            if s['classes'] and not all(c in e['classes'] for c in s['classes']): ok = False
            if ok: si -= 1
            pi -= 1
        return si < 0

    def _check_pseudo(self, pseudo, elem):
        """检查伪类条件（:last-child, :first-child, :nth-child 等）"""
        if not pseudo:
            return True
        pseudo = pseudo.strip()
        if pseudo == 'last-child':
            return elem.get('is_last', False)
        elif pseudo == 'first-child':
            return elem.get('is_first', False)
        elif pseudo.startswith('nth-child('):
            n = pseudo[len('nth-child('):-1].strip()
            idx = elem.get('child_index', 0) + 1  # 1-based
            if n == 'odd': return idx % 2 == 1
            elif n == 'even': return idx % 2 == 0
            elif n.endswith('n'):
                return idx % int(n[:-1] if n[:-1] else 1) == 0
            else:
                return idx == int(n)
        # 未知伪类，默认匹配
        return True

    def _get_styles(self, tag, classes):
        matched = []
        for rule in self.css_rules:
            for sp in rule.selector_paths:
                if self._match(sp, self.stack):
                    matched.append(rule.declarations)
                    break
        return matched

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        classes = [c for c in ad.get("class", "").split() if c]
        style = ad.get("style", "")

        if tag in ("head", "script", "link", "meta", "!doctype", "html"):
            if tag == "head": self._in_head = True
            if tag == "script": self._in_script = True
            return
        if tag == "style": self._in_style = True; return
        if tag == "body": self._capture = True; return
        if not self._capture: return

        # 同级计数
        si = 0
        if self.stack:
            p = self.stack[-1]
            si = p.get('cc', 0)
            p['cc'] = si + 1

        self.stack.append({'tag': tag, 'classes': classes, 'cc': 0, 'first': si == 0})

        # 合并样式（保留所有属性，不过滤）
        for s in self._get_styles(tag, classes):
            style = merge_style(style, s)
        style = resolve_css_vars(style)

        # 构建属性
        new_attrs = []
        for k, v in attrs:
            if k == "class": continue
            if k == "style":
                if style: new_attrs.append(('style', style))
                continue
            new_attrs.append((k, v))
        if style and "style" not in ad:
            new_attrs.append(("style", style))

        attr_str = ''.join(f' {k}="{v}"' for k, v in new_attrs)

        # div → section
        out_tag = 'section' if tag == 'div' else tag

        if tag in ("img", "br", "hr"):
            if tag == "br":
                self.output.append("<br />")
            elif tag == "img":
                self.output.append(f"<img{attr_str} />")
            else:
                self.output.append(f"<{out_tag}{attr_str} />")
        else:
            self.output.append(f"<{out_tag}{attr_str}>")

    def handle_endtag(self, tag):
        if tag == "head": self._in_head = False; return
        if tag == "style": self._in_style = False; return
        if tag == "script": self._in_script = False; return
        if tag in ("html", "body", "!doctype"): return
        if not self._capture: return
        if tag in ("img", "br", "hr"):
            if self.stack and self.stack[-1]['tag'] == tag: self.stack.pop()
            return
        out_tag = 'section' if tag == 'div' else tag
        self.output.append(f"</{out_tag}>")
        if self.stack: self.stack.pop()

    def handle_data(self, data):
        if self._in_style or self._in_head or self._in_script: return
        if not self._capture: return
        self.output.append(data)

    def handle_entityref(self, name):
        if self._in_style or self._in_head or self._in_script: return
        if not self._capture: return
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        if self._in_style or self._in_head or self._in_script: return
        if not self._capture: return
        self.output.append(f"&#{name};")

    def get_result(self):
        r = "".join(self.output)
        r = resolve_css_vars(r)
        r = r.replace("<br></br>", "<br />").replace("</br>", "").replace("</img>", "")
        return r


def extract_css(html):
    css = ""
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE):
        css += "\n" + m.group(1)
    return css


def convert(html):
    css_text = extract_css(html)
    rules = parse_css_rules(css_text)
    c = CopyHTMLConverter(rules)
    c.feed(html)
    return c.get_result()


def main():
    if len(sys.argv) < 2:
        print("用法: python3 html_to_copy.py <input.html> [-o output.html]")
        sys.exit(1)
    inp = sys.argv[1]
    out = None
    if "-o" in sys.argv:
        out = sys.argv[sys.argv.index("-o") + 1]
    if not out:
        base, ext = os.path.splitext(inp)
        out = f"{base}_复制版{ext}"
    with open(inp, 'r', encoding='utf-8') as f:
        html = f.read()
    result = convert(html)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"转换完成: {out}")
    print(f"  输入: {len(html)} 字符")
    print(f"  输出: {len(result)} 字符")


if __name__ == "__main__":
    main()
