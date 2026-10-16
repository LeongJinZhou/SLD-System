"""Regenerate the source reference without importing application code or secrets."""
import ast
import hashlib
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[1]


def clean(value):return str(value).replace('|',' / ').replace('\n',' ').strip()


def build():
    lines=['# Source reference','',
           'Generated from the current source by `python tools/build_reference.py`. This is a static navigation reference, not proof of runtime behavior. Read ARCHITECTURE.md and FUNCTION_FLOWS.md for business contracts and use the linked test inventory for observed behavior. No application modules are imported and no credentials are read.','']
    routes=[];kinds=set();module_calls={};count=0
    sources=sorted(ROOT.glob('*.py'))+sorted((ROOT/'tools').glob('*.py'))
    for path in sources:
        relative=path.relative_to(ROOT).as_posix();source=path.read_text(encoding='utf-8-sig');tree=ast.parse(source)
        functions=[]
        def visit(node,parent=''):
            nonlocal count
            for child in ast.iter_child_nodes(node):
                name=(parent+'.' if parent else '')+child.name if isinstance(child,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) else parent
                if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    calls=sorted({ast.unparse(n.func) for n in ast.walk(child) if isinstance(n,ast.Call)})
                    functions.append((name,child.lineno,ast.get_docstring(child) or '',calls));count+=1
                    method='GET' if child.name in ('do_GET','handle_get') else 'POST' if child.name in ('do_POST','handle_post') else 'helper'
                    for item in ast.walk(child):
                        if isinstance(item,ast.Constant) and isinstance(item.value,str) and item.value.startswith('/api/'):
                            routes.append((item.value,method,relative,child.lineno))
                visit(child,name)
        visit(tree)
        for item in ast.walk(tree):
            if isinstance(item,ast.Call) and isinstance(item.func,ast.Attribute) and item.func.attr in ('all','get','put') and item.args and isinstance(item.args[0],ast.Constant) and isinstance(item.args[0].value,str):kinds.add(item.args[0].value)
        imports=sorted({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module} | {alias.name for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names})
        module_calls[relative]=imports
        lines+=['## '+relative,'','SHA-256: `'+hashlib.sha256(path.read_bytes()).hexdigest()+'`','',clean(ast.get_docstring(tree) or 'Application/support source.'),'','| Function or method | Line | Stated purpose | Direct call names observed in AST |','|---|---:|---|---|']
        for name,line,doc,calls in functions:
            lines.append('| `'+name+'` | '+str(line)+' | '+clean(doc or 'See function body and FUNCTION_FLOWS.md.')+' | '+clean(', '.join(calls))+' |')
        lines+=['']
    javascript=ROOT/'web/app.js';source=javascript.read_text(encoding='utf-8')
    lines+=['## web/app.js','','Frontend names are extracted syntactically; inline anonymous event handlers are located by their containing named function. Call relationships are established by reading the function and its controller tests.','',
            '| Function | Line |','|---|---:|']
    js_count=0
    for match in re.finditer(r'\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(',source):
        lines.append('| `'+match[1]+'` | '+str(source[:match.start()].count('\n')+1)+' |');js_count+=1
    lines+=['','## API path literals','','These are observed path literals or regex prefixes. Dynamic IDs and dispatch helpers still need the method/permission contracts in FUNCTION_FLOWS.md. This section does not infer an endpoint from arbitrary user content.','',
            '| Path or prefix | Method context | Source |','|---|---|---|']
    for route,method,path,line in sorted(set(routes)):lines.append('| `'+clean(route)+'` | '+method+' | '+path+':'+str(line)+' |')
    lines+=['','## Imported module relationships','','| Source | Imports |','|---|---|']
    for path,imports in module_calls.items():lines.append('| '+path+' | '+clean(', '.join(imports))+' |')
    lines+=['','## Observed record-kind literals','','`'+'`, `'.join(sorted(kinds))+'`','','Record payload fields and immutable-version rules are documented in SPECIFICATION.md. Additional batch record kinds are visible in put_batch tuples and the feature flow document.','',
            '## Verification source inventory','']
    for path in sorted((ROOT/'tests').glob('test_*')):
        if path.suffix in ('.py','.js'):lines.append('- `'+path.relative_to(ROOT).as_posix()+'`')
    lines+=['',f'Inventory: {count} Python functions/methods; {js_count} named JavaScript functions. Re-run this generator after source changes.','']
    (ROOT/'docs/SOURCE_REFERENCE.md').write_text('\n'.join(lines),encoding='utf-8')
    return count,js_count


if __name__=='__main__':print('Generated source reference:',build())
