"""V1.4补充规则模型。纯内存、无网络、无实际并发；不证明实现或硬件通过。"""
from dataclasses import dataclass, field
from copy import deepcopy
from pathlib import Path
import json
class Refused(Exception): pass
def need(ok):
    if not ok: raise Refused()
@dataclass
class EventLedger:
    events: dict=field(default_factory=dict)
    conflicts: list=field(default_factory=list)
    task: str='RESERVED'
    applied_count: int=0
    case: bool=False
    def receive(self,eid,digest):
        if eid in self.events:
            if self.events[eid]['hash']!=digest:
                self.conflicts.append((eid,digest));return 'CONFLICT'
            return self.events[eid]['state']
        self.events[eid]={'hash':digest,'state':'RECEIVED'};return 'RECEIVED'
    def apply(self,eid):
        e=self.events[eid]
        if e['state']=='APPLIED':return
        need(e['state']=='RECEIVED');e['state']='APPLIED';self.applied_count+=1;self.task='BORROWED'
    def query(self,eid,expired=False):
        if self.events[eid]['state']=='APPLIED':return 'APPLIED'
        if expired:self.case=True;return 'REVIEW_REQUIRED'
        return 'RECEIVED'
@dataclass
class Route:
    bin_cycle:int=1
    capacity:int=1
    permits:dict=field(default_factory=dict)
    used:int=0
    online:bool=True
    actual_bin:str=''
    frozen:bool=False
    def reserve(self,rid):
        if rid in self.permits:return
        need(self.online and self.used+sum(p['state']=='RESERVED' for p in self.permits.values())<self.capacity)
        self.permits[rid]={'cycle':self.bin_cycle,'state':'RESERVED'}
    def start(self,rid):
        p=self.permits[rid];need(self.online and p['state']=='RESERVED' and p['cycle']==self.bin_cycle)
        # Started still consumes capacity: transform reservation into occupied capacity atomically.
        p['state']='STARTED';self.used+=1
    def finish(self,rid):
        p=self.permits[rid];need(p['state']=='STARTED');p['state']='TRANSFERRED';self.actual_bin=f'BIN/{p["cycle"]}'
        self.frozen=not self.online
    def replace_bin(self):
        need(not any(p['state']=='STARTED' for p in self.permits.values()));self.bin_cycle+=1;self.used=0
        for p in self.permits.values():
            if p['state']=='RESERVED':p['state']='INVALIDATED'
@dataclass
class Permit:
    permit_id:str='P1'
    revision:int=1
    released:bool=False
    old_revoked:bool=False
    executions:int=0
    def repeat(self):return self.permit_id,self.revision
    def revoke(self,confirmed_not_started):
        need(confirmed_not_started and not self.released);self.old_revoked=True
    def renew(self):
        need(self.old_revoked and not self.released);self.revision+=1;self.old_revoked=False
    def release(self,revision):
        need(revision==self.revision and not self.old_revoked)
        if self.released:return
        self.released=True;self.executions+=1
@dataclass
class Case:
    assigned:str='值班甲'
    accepted:str=''
    custodian:str='物业甲'
    location:str='隔离01'
    frozen:bool=True
    overdue:bool=False
    closed:bool=False
    def handover(self,to,location,signed):
        need(signed);self.custodian=to;self.location=location
    def close(self,evidence,child_accepted=False,policy=False):
        need(evidence or (policy and child_accepted));self.closed=True

def refuse_unchanged(obj,fn):
    before=deepcopy(obj)
    try:fn()
    except Refused:assert obj==before;return
    raise AssertionError('应拒绝且状态不变')
results=[]
def test(name,fn):fn();results.append({'name':name,'status':'PASS'})
def received_not_applied():
    x=EventLedger();x.receive('e','h');assert x.query('e')=='RECEIVED' and x.task=='RESERVED'
def final_lost():
    x=EventLedger();x.receive('e','h');x.apply('e');assert x.query('e')=='APPLIED'
def timeout():
    x=EventLedger();x.receive('e','h');assert x.query('e',True)=='REVIEW_REQUIRED' and x.case and x.task=='RESERVED'
def conflict():
    x=EventLedger();x.receive('e','h');x.apply('e');assert x.receive('e','changed')=='CONFLICT';assert x.events['e']['hash']=='h' and x.applied_count==1

def duplicate():
    x=EventLedger()
    for _ in range(4):x.receive('e','h');x.apply('e')
    assert x.applied_count==1

def capacity():
    for first,second in [('r1','r2'),('r2','r1')]:
        x=Route();x.reserve(first);refuse_unchanged(x,lambda:x.reserve(second));x.start(first);refuse_unchanged(x,lambda:x.reserve(second))
def swapped():
    x=Route();x.reserve('r');x.replace_bin();refuse_unchanged(x,lambda:x.start('r'));assert x.used==0

def during():
    x=Route();x.reserve('r');x.start('r');refuse_unchanged(x,x.replace_bin);x.online=False;x.finish('r');assert x.actual_bin=='BIN/1' and x.frozen

def before():
    x=Route();x.reserve('r');x.online=False;refuse_unchanged(x,lambda:x.start('r'));assert not x.actual_bin

def permit_repeat():
    p=Permit();assert p.repeat()==p.repeat()==('P1',1);p.release(1);p.release(1);assert p.executions==1

def renewal():
    p=Permit();refuse_unchanged(p,p.renew);p.revoke(True);p.renew();refuse_unchanged(p,lambda:p.release(1));p.release(2);assert p.executions==1 and p.permit_id=='P1'
def no_revoke_after_release():
    p=Permit();p.release(1);refuse_unchanged(p,lambda:p.revoke(True))
def custody():
    c=Case();assert c.accepted=='';refuse_unchanged(c,lambda:c.handover('运输乙','封存批次02',False));c.handover('运输乙','封存批次02',True);assert c.frozen and c.location=='封存批次02'
def close_case():
    c=Case();c.overdue=True;refuse_unchanged(c,lambda:c.close(False));refuse_unchanged(c,lambda:c.close(False,False,True));c.close(False,True,True);assert c.closed and c.frozen
for name,fn in [('收到不等于应用',received_not_applied),('丢最终通知后可查',final_lost),('超结算期限保留占用并建单',timeout),('同ID异内容不覆盖',conflict),('重复应用只一次',duplicate),('最后容量两种竞争顺序',capacity),('换箱使旧路线失效',swapped),('转移中禁止换箱且离线保留真实位置',during),('转移前断网不进入正常箱',before),('重复许可与释放不增加动作',permit_repeat),('续期需撤销且旧版本拒绝',renewal),('已释放不能假定未开始撤销',no_revoke_after_release),('签收转保管不解除业务冻结',custody),('超期不自动关单且政策处置需子单接收',close_case)]:test(name,fn)
out={'version':'V1.4','checks':len(results),'passed':len(results),'failed':0,'real_hardware_cases_executed':0,'limitations':['纯内存顺序模型','不验证掉电持久化或真实并发','许可真实性、传感器与授权为输入假设','不覆盖全部C01-C44'],'results':results}
Path(__file__).with_name('闭环边界模型结果_V1.4.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
