"""
GitHub Pages 초기 설정 스크립트 (최초 1회 실행)

실행: python setup_github.py
"""
import subprocess
import sys
import io
from pathlib import Path

# Windows 콘솔 UTF-8 강제 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)


def run(cmd: list, cwd=None) -> tuple[bool, str]:
    result = subprocess.run(
        cmd, cwd=cwd,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


GITIGNORE = """\
# 민감 정보
config.yaml
.env

# Python
__pycache__/
*.pyc
*.pyo

# 출력 파일 (로컬 전용)
output_*.txt
preview*.txt
run_out.txt
send_out.txt
send_*.txt
stibee_*.txt
check_sites.txt
grants.txt
*.log

# docs/ 는 추적 (GitHub Pages)
!docs/
"""


def main():
    repo_dir = Path(__file__).parent

    print("=" * 50)
    print("  HIZ 뉴스레터 GitHub Pages 초기 설정")
    print("=" * 50)

    # git 설치 확인
    ok, ver = run(["git", "--version"])
    if not ok:
        print("\n❌ git이 설치되지 않았습니다.")
        print("   https://git-scm.com 에서 설치 후 다시 실행하세요.")
        sys.exit(1)
    print(f"\n✓ {ver}")

    # git 초기화
    git_dir = repo_dir / ".git"
    if not git_dir.exists():
        run(["git", "init", "-b", "main"], cwd=repo_dir)
        print("✓ git 저장소 초기화 (main 브랜치)")
    else:
        print("✓ git 저장소 이미 존재")

    # .gitignore 생성
    gitignore_path = repo_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(GITIGNORE, encoding="utf-8")
        print("✓ .gitignore 생성")
    else:
        print("✓ .gitignore 이미 존재")

    # docs/ 폴더 준비
    docs_dir = repo_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "newsletters").mkdir(exist_ok=True)

    # docs/.gitkeep (폴더 추적용)
    gitkeep = docs_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")

    print("✓ docs/ 폴더 준비")

    # GitHub 원격 저장소 설정
    ok, remotes = run(["git", "remote", "-v"], cwd=repo_dir)
    if "origin" in remotes:
        print(f"✓ 원격 저장소 이미 설정됨")
        for line in remotes.splitlines()[:2]:
            print(f"    {line}")
    else:
        print("\n─────────────────────────────────────")
        print("GitHub에 새 저장소를 만들고 URL을 입력하세요.")
        print("예) https://github.com/hiz-agency/newsletter.git")
        print("─────────────────────────────────────")
        url = input("저장소 URL: ").strip()
        if not url:
            print("URL이 없으면 나중에 직접 실행하세요:")
            print("  git remote add origin <URL>")
        else:
            run(["git", "remote", "add", "origin", url], cwd=repo_dir)
            print(f"✓ origin 설정: {url}")

    # 초기 커밋
    print("\n─── 초기 커밋 ───")
    run(["git", "add", ".gitignore", "docs/"], cwd=repo_dir)
    ok, out = run(["git", "commit", "-m", "init: HIZ newsletter GitHub Pages"], cwd=repo_dir)
    if ok:
        print("✓ 초기 커밋 완료")
    elif "nothing to commit" in out:
        print("✓ 커밋할 변경 없음 (이미 커밋됨)")
    else:
        print(f"  커밋 결과: {out}")

    # 현재 브랜치 확인
    ok, branch = run(["git", "branch", "--show-current"], cwd=repo_dir)
    branch = branch.strip() or "main"

    # 푸시
    print(f"\n─── GitHub 푸시 ({branch}) ───")
    ok, out = run(["git", "push", "-u", "origin", branch], cwd=repo_dir)
    if ok:
        print("✓ 푸시 완료")
    else:
        print(f"  {out}")
        print(f"\n  나중에 직접 실행: git push -u origin {branch}")

    print(f"""
{"=" * 50}
  설정 완료! 다음 단계를 따라주세요
{"=" * 50}

1. GitHub 저장소 → Settings → Pages
2. Source: "Deploy from a branch" 선택
3. Branch: {branch}  /  Folder: /docs  선택
4. Save 클릭

─── GitHub Pages URL ───
   https://[username].github.io/[repo-name]/

이후 python main.py --now 실행 시
  → HTML 자동 생성
  → GitHub Pages 자동 업데이트
""")


if __name__ == "__main__":
    main()
