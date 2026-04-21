from src.core import Interpreter, InterpreterType, VirtualMemory

virtual_memory: VirtualMemory = VirtualMemory()
conn_id: int = 0

virtual_memory.add_conn_id(conn_id)

interpreter: Interpreter = Interpreter(
    type=InterpreterType.command_line,
    virtual_memory=virtual_memory,
    conn_id=conn_id,
)
interpreter.start()
