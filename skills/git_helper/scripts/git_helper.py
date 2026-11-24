"""Conservative Git CLI; conflict resolution requires human choice."""
import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path


def git(repo, *args, check=True):
    p = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if check and p.returncode:
        raise ValueError(p.stderr.decode('utf-8', 'replace').strip() or 'Git 操作失败')
    return p


def text(repo, *args):
    return git(repo, *args).stdout.decode('utf-8', 'replace').strip()


def unmerged(repo):
    return git(repo, 'ls-files', '-u', '-z').stdout


def idle(repo):
    if unmerged(repo):
        raise ValueError('存在冲突，先运行 conflicts 并让用户选择方案')
    for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply', 'sequencer'):
        if Path(text(repo, 'rev-parse', '--git-path', name)).exists():
            raise ValueError('存在进行中的 Git 操作：' + name)


def feature(repo, cfg):
    name = text(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    if name in cfg['protected_branches'] or not re.fullmatch(cfg['feature_pattern'], name):
        raise ValueError('必须使用 feature 分支，当前为：' + name)
    return name


def display(data):
    if b'\0' in data:
        return '<binary: %d bytes>' % len(data)
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return '<non-UTF-8: %d bytes; inspect original blob>' % len(data)


def conflicts(repo):
    raw = unmerged(repo)
    if not raw:
        print('没有未解决的索引冲突')
        return
    backup = Path(text(repo, 'rev-parse', '--git-path', 'git-helper-backups')) / uuid.uuid4().hex
    backup.mkdir(parents=True, exist_ok=False)
    (backup / 'index-entries.bin').write_bytes(raw)
    index = Path(text(repo, 'rev-parse', '--git-path', 'index'))
    if index.is_file():
        (backup / 'index.bin').write_bytes(index.read_bytes())
    (backup / 'status.bin').write_bytes(git(repo, 'status', '--porcelain=v1', '-z').stdout)
    (backup / 'head.txt').write_text(text(repo, 'rev-parse', 'HEAD'), encoding='utf-8')
    paths = {}
    for entry in filter(None, raw.split(b'\0')):
        meta, path = entry.split(b'\t', 1)
        mode, blob, stage = meta.decode('ascii').split()
        paths.setdefault(path, []).append((mode, blob, stage))
    for number, (path, stages) in enumerate(paths.items()):
        folder = backup / str(number)
        folder.mkdir()
        (folder / 'path.bin').write_bytes(path)
        file = repo / os.fsdecode(path)
        print('\nFILE ' + repr(str(file.relative_to(repo))))
        if any(parent.is_symlink() for parent in file.parents if parent != repo and repo in parent.parents):
            print('<symlink ancestor; working copy not read>')
        elif file.is_symlink():
            (folder / 'symlink.txt').write_text(str(file.readlink()), encoding='utf-8')
            print('<symlink>')
        elif file.is_file():
            data = file.read_bytes()
            (folder / 'working.bin').write_bytes(data)
            print('WORKING:\n' + display(data))
        else:
            print('<working file absent or non-regular>')
        for mode, blob, stage in stages:
            print('STAGE %s mode=%s blob=%s' % (stage, mode, blob))
            if mode == '160000':
                continue
            data = git(repo, 'cat-file', 'blob', blob).stdout
            (folder / ('stage-' + stage + '.bin')).write_bytes(data)
            print(display(data))
    print('\n备份：' + str(backup.resolve()))
    print('选项：保留当前侧 / 保留传入侧 / 人工组合 / 暂不处理。先展示候选代码并由用户选择。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'config.json')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('status', 'pull', 'push', 'conflicts'):
        sub.add_parser(name)
    sub.add_parser('branch').add_argument('name')
    sub.add_parser('commit').add_argument('-m', '--message', required=True)
    a = parser.parse_args()
    cfg = json.loads(a.config.read_text(encoding='utf-8'))
    repo = Path(text(Path(a.repo).resolve(), 'rev-parse', '--show-toplevel')).resolve()
    os.chdir(repo)
    if a.command == 'status':
        print(text(repo, 'status', '--short', '--branch'))
        print(text(repo, 'remote', '-v'))
        return
    if a.command == 'conflicts':
        conflicts(repo)
        return
    idle(repo)
    if a.command == 'branch':
        if a.name in cfg['protected_branches'] or not re.fullmatch(cfg['feature_pattern'], a.name):
            raise ValueError('分支名必须符合 feature 分支规范')
        if text(repo, 'status', '--porcelain'):
            raise ValueError('切换分支前请先处理工作区修改')
        git(repo, 'check-ref-format', '--branch', a.name)
        print(text(repo, 'switch', '-c', a.name))
        return
    branch = feature(repo, cfg)
    if a.command == 'commit':
        subject = a.message.splitlines()[0] if a.message else ''
        types = '|'.join(re.escape(t) for t in cfg['commit_types'])
        if not re.fullmatch(r'(?:' + types + r')(?:\([a-zA-Z0-9._/-]+\))?!?: \S.*', subject) or len(subject) > cfg['max_subject_length']:
            raise ValueError('提交说明不符合 Conventional Commits 或标题过长')
        p = git(repo, 'diff', '--cached', '--quiet', check=False)
        if p.returncode == 0:
            raise ValueError('暂存区为空')
        if p.returncode != 1:
            raise ValueError('无法读取暂存区')
        git(repo, 'diff', '--cached', '--check')
        names = git(repo, 'diff', '--cached', '--name-only', '--diff-filter=ACMRT', '-z').stdout
        for path in filter(None, names.split(b'\0')):
            name = os.fsdecode(path)
            # Gitlinks are not text blobs.
            entry = git(repo, 'ls-files', '--stage', '--', name).stdout
            if entry.startswith(b'160000 '):
                continue
            data = git(repo, 'show', ':' + name).stdout
            if b'\0' not in data and re.search(rb'(?m)^(?:<{7,}|={7,}|>{7,}|\|{7,})[^\r\n]*\r?$', data):
                raise ValueError('暂存文件含疑似冲突标记：' + name)
        print(text(repo, 'commit', '-m', a.message))
        return
    remote = cfg['remote']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', remote):
        raise ValueError('remote 必须是已配置的远程名称')
    print('目标：' + text(repo, 'remote', 'get-url', remote) + ' 分支：' + branch, flush=True)
    if text(repo, 'status', '--porcelain'):
        raise ValueError('拉取或推送前工作区必须干净')
    if a.command == 'pull':
        upstream = text(repo, 'rev-parse', '--abbrev-ref', '@{upstream}')
        if upstream != remote + '/' + branch:
            raise ValueError('upstream 必须是同名远程分支')
        print(text(repo, 'pull', '--ff-only', '--no-rebase', remote, branch))
    else:
        print(text(repo, 'push', '--set-upstream', remote, 'HEAD:refs/heads/' + branch))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print('停止：' + str(exc), file=sys.stderr)
        sys.exit(1)
