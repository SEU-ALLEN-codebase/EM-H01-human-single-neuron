from jupyter_backend import JupyterKernel

class CodeExecutor:
    def __init__(self, work_dir):
        self.jupyter_kernel = JupyterKernel(work_dir)
        self.code_executing = False

    def execute_code(self, code: str) -> str:
        self.code_executing = True
        try:
            output: str = self.jupyter_kernel.execute_code(code)
            return output
        except Exception as e:
            return f"An error occurred while executing the code: {str(e)}"
        finally:
            self.code_executing = False

    def restart_jupyter_kernel(self):
        self.jupyter_kernel.restart_jupyter_kernel()