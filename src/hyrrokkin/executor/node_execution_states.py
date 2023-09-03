
import enum

class NodeExecutionStates(enum.Enum):

    pending = "pending"
    executing = "executing"
    executed = "executed"
    failed = "failed"