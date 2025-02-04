![domain:innovation-lab](https://img.shields.io/badge/innovation--lab-3D8BD3)

**Description**: This AI Agent returns the answer to a plain text NLP query which requires math operations. The agent builds python code which is run in a python executor to get non-hallucinated output.

**Input Data Model**

```
class Message(Model):
    message: str
    address: Optional[str]
```
