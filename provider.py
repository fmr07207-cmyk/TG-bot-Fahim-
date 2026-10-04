"""Safe mock/test data provider. No live third-party OTP fetching or relaying."""
import random, time
class MockProvider:
    def __init__(self):
        self.events=[]
        self._ranges=[
            {"range":"TEST-001","service":"Demo SMS","hits":0},
            {"range":"TEST-002","service":"QA Sandbox","hits":0},
            {"range":"TEST-003","service":"Internal Test","hits":0},
        ]
    def get_number(self):
        return "+880TEST" + str(random.randint(100000,999999))
    def create_event(self):
        ev={"service":"Demo SMS","number":self.get_number(),"code":str(random.randint(100000,999999)),"time":time.strftime("%Y-%m-%d %H:%M:%S")}
        self.events.insert(0,ev); self.events=self.events[:50]
        return ev
    def latest(self): return self.events[0] if self.events else None
    def ranges(self): return self._ranges
