import os
import subprocess
import tempfile

def validate_lua(code: str):

    '''Валидирует lua код. Использует проверку luac

    args: 
        code(str): код lua как строка

    returns: 
        (bool, str): (Работает/Не работает, ошибка(если есть))
        '''
    
    try:
        if 'os.exit' in code:
            return False, 'forbidden operation: os.exit'
    
        with tempfile.NamedTemporaryFile(suffix='.lua', delete=False, mode='wb') as f:
            f.write(code.encode('utf-8'))
            path = f.name

        output = subprocess.run(
            ['luac', '-p', path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=3
        )

        if output.returncode == 0:
            return True, None

        error = output.stderr.split('\n')[0].replace(path, '').replace('luac:', '').strip()
        return False, 'syntax error: ' + error
    
    except subprocess.TimeoutExpired:
        return False, 'timeout execution (probably infinite loop)'
    
    finally:
        if path and os.path.exists(path):
            os.remove(path)


def execute_lua(code: str):
    '''
    Проверяет выполнение lua кода

    args: 
        code(str): код lua как строка

    returns: 
        (bool, str): (Работает/Не работает, ошибка(если есть))
    '''
    try:
        if 'os.exit' in code:
            return False, 'forbidden operation: os.exit'
        with tempfile.NamedTemporaryFile(suffix='.lua', delete=False, mode='wb') as f:
            f.write(code.encode('utf-8'))
            path = f.name
        output = subprocess.run(
            ['lua', path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=3
        )

        if output.returncode == 0:
            if len(output.stdout.strip()) > 500:
                return True, output.stdout.strip()[:500] + '..truncated'
            return True, output.stdout.strip()

        error = output.stderr.split('\n')[0].replace(path, '').replace('lua:', '').strip()

        return False, 'runtime error: ' + error
    
    except subprocess.TimeoutExpired:
        return False, 'timeout execution (probably infinite loop)'
    
    finally:
        if path and os.path.exists(path):
            os.remove(path)
