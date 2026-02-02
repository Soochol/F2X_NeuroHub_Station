"""
STM32CubeProgrammer CLI 진단 스크립트
배포 PC에서 실행하여 에러 원인 파악

Usage:
    python diagnose_stm32_cli.py
"""
import subprocess
import traceback
import sys
import os

PROGRAMMER_PATH = r"C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe"


def test_path_exists():
    """1. 경로 존재 확인"""
    print("=" * 60)
    print("Test 1: Path Exists")
    print("=" * 60)
    exists = os.path.exists(PROGRAMMER_PATH)
    print(f"  Path: {PROGRAMMER_PATH}")
    print(f"  Exists: {exists}")
    return exists


def test_shell_true():
    """2. shell=True로 실행 (현재 코드 방식)"""
    print("\n" + "=" * 60)
    print("Test 2: subprocess.run with shell=True")
    print("=" * 60)

    cmd = f'"{PROGRAMMER_PATH}" --version'
    print(f"  Command: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            shell=True,
        )
        print(f"  Return code: {result.returncode}")
        print(f"  Stdout: {result.stdout[:200] if result.stdout else '(empty)'}")
        print(f"  Stderr: {result.stderr[:200] if result.stderr else '(empty)'}")
        return True
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}")
        print(f"  Message: {e}")
        print(f"  Repr: {repr(e)}")
        print(f"  Args: {e.args}")
        print(f"  Traceback:\n{traceback.format_exc()}")
        return False


def test_shell_false():
    """3. shell=False로 실행 (권장 방식)"""
    print("\n" + "=" * 60)
    print("Test 3: subprocess.run with shell=False (Recommended)")
    print("=" * 60)

    cmd_list = [PROGRAMMER_PATH, "--version"]
    print(f"  Command: {cmd_list}")

    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
        print(f"  Return code: {result.returncode}")
        print(f"  Stdout: {result.stdout[:200] if result.stdout else '(empty)'}")
        print(f"  Stderr: {result.stderr[:200] if result.stderr else '(empty)'}")
        return True
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}")
        print(f"  Message: {e}")
        print(f"  Repr: {repr(e)}")
        print(f"  Args: {e.args}")
        print(f"  Traceback:\n{traceback.format_exc()}")
        return False


def test_with_creation_flags():
    """4. CREATE_NO_WINDOW 플래그로 실행 (GUI 앱 권장)"""
    print("\n" + "=" * 60)
    print("Test 4: subprocess.run with CREATE_NO_WINDOW")
    print("=" * 60)

    cmd_list = [PROGRAMMER_PATH, "--version"]
    print(f"  Command: {cmd_list}")

    try:
        # Windows에서 콘솔 창 없이 실행
        CREATE_NO_WINDOW = 0x08000000
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
            creationflags=CREATE_NO_WINDOW,
        )
        print(f"  Return code: {result.returncode}")
        print(f"  Stdout: {result.stdout[:200] if result.stdout else '(empty)'}")
        print(f"  Stderr: {result.stderr[:200] if result.stderr else '(empty)'}")
        return True
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}")
        print(f"  Message: {e}")
        print(f"  Repr: {repr(e)}")
        print(f"  Args: {e.args}")
        print(f"  Traceback:\n{traceback.format_exc()}")
        return False


def test_encoding():
    """5. 인코딩 문제 테스트"""
    print("\n" + "=" * 60)
    print("Test 5: Encoding test with explicit encoding")
    print("=" * 60)

    cmd_list = [PROGRAMMER_PATH, "--version"]
    print(f"  Command: {cmd_list}")
    print(f"  System encoding: {sys.getdefaultencoding()}")
    print(f"  Stdout encoding: {sys.stdout.encoding}")

    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            timeout=10,
            shell=False,
            # 바이트로 받아서 직접 디코딩
        )
        print(f"  Return code: {result.returncode}")

        # 다양한 인코딩으로 디코딩 시도
        for encoding in ['utf-8', 'cp949', 'cp1252', 'latin-1']:
            try:
                stdout = result.stdout.decode(encoding, errors='replace')
                print(f"  Stdout ({encoding}): {stdout[:100] if stdout else '(empty)'}")
                break
            except:
                pass
        return True
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}")
        print(f"  Message: {e}")
        # 예외 메시지의 인코딩 확인
        try:
            msg_bytes = str(e).encode('utf-8', errors='replace')
            print(f"  Message bytes: {msg_bytes}")
        except:
            pass
        print(f"  Traceback:\n{traceback.format_exc()}")
        return False


def test_environment():
    """6. 환경변수 확인"""
    print("\n" + "=" * 60)
    print("Test 6: Environment Check")
    print("=" * 60)

    print(f"  Python: {sys.version}")
    print(f"  Executable: {sys.executable}")
    print(f"  Frozen (PyInstaller): {getattr(sys, 'frozen', False)}")
    print(f"  PATH set: {'PATH' in os.environ}")
    print(f"  COMSPEC: {os.environ.get('COMSPEC', 'NOT SET')}")

    # PATH에서 STM32 관련 경로 확인
    path_dirs = os.environ.get('PATH', '').split(';')
    stm32_paths = [p for p in path_dirs if 'stm32' in p.lower()]
    print(f"  STM32 in PATH: {stm32_paths if stm32_paths else 'None'}")


def main():
    print("STM32CubeProgrammer CLI Diagnostic Tool")
    print("=" * 60)
    print(f"Running on: {sys.platform}")
    print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # 테스트 실행
    test_path_exists()
    test_environment()
    test_shell_true()
    test_shell_false()
    test_with_creation_flags()
    test_encoding()

    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    print("\nPlease share the output above to diagnose the issue.")


if __name__ == "__main__":
    main()
