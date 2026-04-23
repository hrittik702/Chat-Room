# 💬 Chat Room : Custom - Server

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Status](https://img.shields.io/badge/Status-Active_Development-orange)

### 🏗️ System Architecture 

```mermaid
sequenceDiagram
    participant A as Client A (Room: 1234)
    participant S as Server
    participant B as Client B (Room: 1234)
    participant C as Client C (Room: 9999)
    
    A->>S: Connect & Join (Room Code: 1234)
    B->>S: Connect & Join (Room Code: 1234)
    C->>S: Connect & Join (Room Code: 9999)
    
    A->>S: Send Message: "Hello Room!"
    
    Note over S: Server searches dictionary for<br/>clients mapped to Room 1234
    
    S->>B: Broadcast: "Client A: Hello Room!"
    Note over S, C: Client C receives nothing (Different Room)
```
## Tech Stacks used : 

1. Python 3.12
2. Python **Socket Module** (for connecting end nodes) [{click here}](https://realpython.com/python-sockets/)
3. Python **Threading Module** (for multithreading) [{click here}](https://realpython.com/intro-to-python-threading/)
4. Python **tkinter Module** (for Providing GUI) [{Click here}](https://youtube.com/playlist?list=PLu0W_9lII9ajLcqRcj4PoEihkukF_OTzA&si=d2chqVaFU95K4isR)

